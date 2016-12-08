#!/usr/bin/env bash

# Sanity check that Meteos started if enabled

echo "*********************************************************************"
echo "Begin DevStack Exercise: $0"
echo "*********************************************************************"

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
set -o errexit

# Print the commands being run so that we can see the command that triggers
# an error.  It is also useful for following allowing as the install occurs.
set -o xtrace


# Settings
# ========

# Keep track of the current directory
EXERCISE_DIR=$(cd $(dirname "$0") && pwd)
TOP_DIR=$(cd $EXERCISE_DIR/..; pwd)

# Import common functions
source $TOP_DIR/functions

# Import configuration
source $TOP_DIR/openrc

# Import exercise configuration
source $TOP_DIR/exerciserc

is_service_enabled meteos || exit 55

if is_ssl_enabled_service "meteos" ||\
    is_ssl_enabled_service "meteos-api" ||\
    is_service_enabled tls-proxy; then
    METEOS_SERVICE_PROTOCOL="https"
fi

METEOS_SERVICE_PROTOCOL=${METEOS_SERVICE_PROTOCOL:-$SERVICE_PROTOCOL}

$CURL_GET $METEOS_SERVICE_PROTOCOL://$SERVICE_HOST:8989/ 2>/dev/null \
                | grep -q 'Auth' || die $LINENO "Meteos API isn't functioning!"

set +o xtrace
echo "*********************************************************************"
echo "SUCCESS: End DevStack Exercise: $0"
echo "*********************************************************************"
