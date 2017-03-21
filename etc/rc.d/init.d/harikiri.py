#!/usr/bin/env python
import os, sys, time, re, requests, logging, argparse, traceback, backoff
from random import randint
from subprocess import call
from datetime import datetime
import boto.ec2.autoscale
from boto.exception import BotoServerError


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
            done_file = os.path.join(root, d, '.done')
            if not os.path.exists(done_file): return False
            t = os.path.getmtime(done_file)
            done_dt = datetime.fromtimestamp(t)
            age = (datetime.utcnow() - done_dt).total_seconds()
            if most_recent is None or age < most_recent: most_recent = age
    if most_recent is None:
        if NO_JOBS_TIMER is None: NO_JOBS_TIMER = time.time()
        else:
            if (time.time() - NO_JOBS_TIMER) > inactivity_secs: return True
        return False
    if most_recent > inactivity_secs: return True
    return False


@backoff.on_exception(backoff.expo, BotoServerError, max_tries=10, max_value=512)
def get_all_groups(conn):
    """Get all AutoScaling groups."""
    return conn.get_all_groups()


@backoff.on_exception(backoff.expo, BotoServerError, max_tries=10, max_value=512)
def terminate_instance(conn, id):
    """Terminate instance in AutoScaling group."""
    conn.terminate_instance(id)


@backoff.on_exception(backoff.expo, BotoServerError, max_value=512)
def detach_instance(conn, as_group, id):
    """Detach instance from AutoScaling group."""
    conn.detach_instances(as_group, [id])


def seppuku():
    """Shutdown supervisord and the instance if it detects that it is 
       currently part of an autoscale group."""

    # introduce random sleep
    time.sleep(randint(0, 600))

    # check if instance part of an autoscale group
    as_group = None
    id = requests.get('http://169.254.169.254/latest/meta-data/instance-id').content
    conn = boto.ec2.autoscale.AutoScaleConnection()
    for group in get_all_groups(conn):
        for i in group.instances:
            if id == i.instance_id:
                as_group = group.name
                break
    if as_group is None:
        logging.info("This instance %s is not part of any autoscale group." % id)
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

    # get connection
    conn = boto.ec2.autoscale.AutoScaleConnection()

    # shutdown supervisord
    try:
        call(["/usr/bin/sudo", "/usr/bin/systemctl", "stop", "supervisord"])
        logging.info("Stopping supervisord.")
    except: pass

    # let supervisord shutdown its processes
    time.sleep(60)

    # detach and die
    logging.info("Committing seppuku.")
    detach_instance(conn, as_group, id)
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
