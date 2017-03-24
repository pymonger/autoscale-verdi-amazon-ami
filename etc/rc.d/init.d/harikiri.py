#!/usr/bin/env python
import os, sys, time, re, requests, logging, argparse, traceback, backoff
from random import randint
from subprocess import call
from datetime import datetime
import boto3
from botocore.exceptions import ClientError


log_format = "[%(asctime)s: %(levelname)s/%(funcName)s] %(message)s"
logging.basicConfig(format=log_format, level=logging.INFO)


DAY_DIR_RE = re.compile(r'jobs/\d{4}/\d{2}/\d{2}/\d{2}/\d{2}$')

NO_JOBS_TIMER = None


def is_jobless(root_work, inactivity_secs):
    """Check if no jobs are running and hasn't run in the past 
       amount of time passed in.
    """

    global NO_JOBS_TIMER
    most_recent = None
    for root, dirs, files in os.walk(root_work, followlinks=True):
        match = DAY_DIR_RE.search(root)
        if not match: continue
        dirs.sort()
        for d in dirs:
            job_dir = os.path.join(root, d)
            done_file = os.path.join(job_dir, '.done')
            if not os.path.exists(done_file):
                logging.info("%s: no .done file found. Not jobless yet." % job_dir)
                return False
            t = os.path.getmtime(done_file)
            done_dt = datetime.fromtimestamp(t)
            age = (datetime.utcnow() - done_dt).total_seconds()
            if most_recent is None or age < most_recent: most_recent = age
            logging.info("%s: age=%s" % (job_dir, age))
    if most_recent is None:
        if NO_JOBS_TIMER is None: NO_JOBS_TIMER = time.time()
        else:
            if (time.time() - NO_JOBS_TIMER) > inactivity_secs: return True
        return False
    if most_recent > inactivity_secs: return True
    return False


@backoff.on_exception(backoff.expo, ClientError, max_tries=10, max_value=512)
def get_all_groups(c):
    """Get all AutoScaling groups."""
    return c.describe_auto_scaling_groups()['AutoScalingGroups']


@backoff.on_exception(backoff.expo, ClientError, max_value=512)
def detach_instance(c, as_group, id):
    """Detach instance from AutoScaling group."""
    c.detach_instances(InstanceIds=[id], AutoScalingGroupName=as_group,
                       ShouldDecrementDesiredCapacity=True)


def seppuku():
    """Shutdown supervisord and the instance if it detects that it is 
       currently part of an autoscale group."""

    logging.info("Initiating seppuku.")

    # introduce random sleep
    meditation_time = randint(0, 600)
    logging.info("Meditating for %s seconds to avoid thundering herd." % meditation_time)
    time.sleep(meditation_time)

    # check if instance part of an autoscale group
    as_group = None
    id = str(requests.get('http://169.254.169.254/latest/meta-data/instance-id').content)
    logging.info("Our instance id: %s" % id)
    c = boto3.client('autoscaling')
    for group in get_all_groups(c):
        group_name = str(group['AutoScalingGroupName'])
        logging.info("Checking group: %s" % group_name)
        for i in group['Instances']:
            asg_inst_id = str(i['InstanceId'])
            logging.info("Checking group instance: %s" % asg_inst_id)
            if id == asg_inst_id:
                as_group = group_name
                logging.info("Matched!")
                break
    if as_group is None:
        logging.info("This instance %s is not part of any autoscale group. Cancelling seppuku." % id)
        return

    # gracefully shutdown
    while True:
        try: graceful_shutdown(as_group, id)
        except Exception, e:
            logging.error("Got exception in graceful_shutdown(): %s\n%s" %
                          (str(e), traceback.format_exc()))
        time.sleep(randint(0, 600))


def graceful_shutdown(as_group, id):
    """Gracefully shutdown supervisord, detach from AutoScale group,
       and shutdown."""

    # get client
    c = boto3.client('autoscaling')

    # stop docker containers
    try:
        logging.info("Stopping all docker containers.")
        os.system("/usr/bin/docker stop --time=30 $(/usr/bin/docker ps -aq)")
    except: pass

    # shutdown supervisord
    try:
        logging.info("Stopping supervisord.")
        call(["/usr/bin/sudo", "/usr/bin/systemctl", "stop", "supervisord"])
    except: pass

    # let supervisord shutdown its processes
    time.sleep(60)

    # detach and die
    logging.info("Committing seppuku.")
    detach_instance(c, as_group, id)
    time.sleep(60)
    call(["/usr/bin/sudo", "/sbin/shutdown", "-h", "now"])


def harikiri(root_work, inactivity_secs, check_interval):
    """If no jobs are running and the last job finished more than the 
       threshold, shutdown supervisord gracefully then shutdown the 
       instance.
    """

    logging.info("harikiri configuration:")
    logging.info("root_work_dir=%s" % root_work)
    logging.info("inactivity=%d" % inactivity_secs)
    logging.info("check=%d" % check_interval)

    while True:
        if is_jobless(root_work, inactivity_secs):
            try: seppuku()
            except Exception, e:
                logging.error("Got exception in seppuku(): %s\n%s" %
                              (str(e), traceback.format_exc()))
        time.sleep(check_interval)


if __name__ == "__main__":
    desc = "HySDS inactivity daemon to perform autoscale group detachment and harikiri"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('root_work_dir',
                        help="root HySDS work directory, e.g. /data/work")
    parser.add_argument('-i', '--inactivity', type=int, default=600,
                        help="inactivity threshold in seconds")
    parser.add_argument('-c', '--check', type=int, default=60,
                         help="check for inactivity every N seconds")
    args = parser.parse_args()
    harikiri(args.root_work_dir, args.inactivity, args.check)
