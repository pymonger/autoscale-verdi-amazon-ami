#!/bin/bash
export HYSDS_HOME=$HOME
export DATA_DIR=/data
export HOST_UID=$(id -u)
export HOST_GID=$(id -g)
mkdir -p ${DATA_DIR}/work
chown -R ${HOST_UID}:${HOST_GID} $DATA_DIR
cd ${HOME}/verdi/ops/hysds-dockerfiles/verdi
/usr/local/bin/docker-compose up -d
