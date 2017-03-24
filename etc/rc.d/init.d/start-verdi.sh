#!/bin/bash
export HYSDS_HOME=$HOME
export DATA_DIR=/data
cd /home/ops/verdi/ops/hysds-dockerfiles/verdi
/usr/local/bin/docker-compose up -d
