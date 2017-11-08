#!/bin/bash
export HYSDS_HOME=$HOME
export DATA_DIR=/data
mkdir -p ${DATA_DIR}/work
chown -R ops:ops $DATA_DIR
cd /home/ops/verdi/ops/hysds-dockerfiles/verdi
/usr/local/bin/docker-compose up -d
