#!/bin/bash
export HYSDS_HOME=$HOME
export FACTER_ipaddress=`ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}'`
cd /home/ops/verdi/ops/hysds-dockerfiles/verdi
/usr/local/bin/docker-compose up
