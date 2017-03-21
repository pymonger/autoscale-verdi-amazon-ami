#!/bin/bash

# instance id
az=`curl -s http://169.254.169.254/latest/meta-data/placement/availability-zone`
region="`echo \"$az\" | sed -e 's:\([0-9][0-9]*\)[a-z]*\$:\\1:'`"
region_underscores="`echo \"$region\" | sed -e 's/-/_/g'`"
instance_id=`curl -s http://169.254.169.254/latest/meta-data/instance-id`

# set to terminate on instance initiated shutdown
aws --region $region ec2 modify-instance-attribute \
  --instance-initiated-shutdown-behavior terminate \
  --instance-id $instance_id || \
  echo "Failed to set instance $instance_id to terminate on shutdown." 1>&2

# print setting
aws --region $region ec2 describe-instance-attribute \
  --attribute instanceInitiatedShutdownBehavior \
  --instance-id $instance_id
