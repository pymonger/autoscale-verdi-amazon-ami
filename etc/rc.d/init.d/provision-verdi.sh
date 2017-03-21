#!/bin/bash

# default creds must be first before other profiles for this to pull the right creds
export AWS_ACCESS_KEY_ID="$(grep aws_access_key_id $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
export AWS_SECRET_ACCESS_KEY="$(grep aws_secret_access_key $HOME/.aws/credentials | head -1 | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
export BUNDLE_URL="$(curl http://169.254.169.254/latest/user-data/ | grep BUNDLE_URL | cut -d= -f 2 | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
export BUNDLE_BASENAME="$(basename $BUNDLE_URL 2>/dev/null)"


# check that bundle was found
if [ -z $BUNDLE_URL ]; then
  echo "Couldn't detect BUNDLE_URL from user-data."
  exit 1
fi


# download bundle
rm -rf /tmp/${BUNDLE_BASENAME}
aws s3 cp ${BUNDLE_URL} /tmp/${BUNDLE_BASENAME}


# extract bundle
mkdir -p ${VERDI_DIR}/ops
tar --extract --directory ${VERDI_DIR}/ops --file /tmp/${BUNDLE_BASENAME}


# install
${VERDI_DIR}/ops/install.sh
