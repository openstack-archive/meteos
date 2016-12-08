#!/bin/bash
#
# lib/meteos

# Dependencies:
# ``functions`` file
# ``DEST``, ``DATA_DIR``, ``STACK_USER`` must be defined

# ``stack.sh`` calls the entry points in this order:
#
# install_meteos
# install_python_meteosclient
# configure_meteos
# start_meteos
# stop_meteos
# cleanup_meteos

# Save trace setting
XTRACE=$(set +o | grep xtrace)
set +o xtrace


# Functions
# ---------

# create_meteos_accounts() - Set up common required meteos accounts
#
# Tenant      User       Roles
# ------------------------------
# service     meteos    admin
function create_meteos_accounts {

    create_service_user "meteos"

    get_or_create_service "meteos" "machine-learning" "Meteos Machine Learning"
    get_or_create_endpoint "machine-learning" \
        "$REGION_NAME" \
        "$METEOS_SERVICE_PROTOCOL://$METEOS_SERVICE_HOST:$METEOS_SERVICE_PORT/v1/\$(tenant_id)s" \
        "$METEOS_SERVICE_PROTOCOL://$METEOS_SERVICE_HOST:$METEOS_SERVICE_PORT/v1/\$(tenant_id)s" \
        "$METEOS_SERVICE_PROTOCOL://$METEOS_SERVICE_HOST:$METEOS_SERVICE_PORT/v1/\$(tenant_id)s"
}

# cleanup_meteos() - Remove residual data files, anything left over from
# previous runs that would need to clean up.
function cleanup_meteos {

    # Cleanup auth cache dir
    sudo rm -rf $METEOS_AUTH_CACHE_DIR
}

# configure_meteos() - Set config files, create data dirs, etc
function configure_meteos {
    sudo install -d -o $STACK_USER $METEOS_CONF_DIR

    if [[ -f $METEOS_DIR/etc/meteos/policy.json ]]; then
        cp -p $METEOS_DIR/etc/meteos/policy.json $METEOS_CONF_DIR
    fi

    cp -p $METEOS_DIR/etc/meteos/api-paste.ini $METEOS_CONF_DIR

    # Create auth cache dir
    sudo install -d -o $STACK_USER -m 700 $METEOS_AUTH_CACHE_DIR
    rm -rf $METEOS_AUTH_CACHE_DIR/*

    configure_auth_token_middleware \
        $METEOS_CONF_FILE meteos $METEOS_AUTH_CACHE_DIR

    # Set admin user parameters needed for trusts creation
    iniset $METEOS_CONF_FILE \
        keystone_authtoken admin_tenant_name $SERVICE_TENANT_NAME
    iniset $METEOS_CONF_FILE keystone_authtoken admin_user meteos
    iniset $METEOS_CONF_FILE \
        keystone_authtoken admin_password $SERVICE_PASSWORD

    iniset_rpc_backend meteos $METEOS_CONF_FILE DEFAULT

    # Set configuration to send notifications
    iniset $METEOS_CONF_FILE DEFAULT debug $ENABLE_DEBUG_LOG_LEVEL

    iniset $METEOS_CONF_FILE DEFAULT plugins $METEOS_ENABLED_PLUGINS

    iniset $METEOS_CONF_FILE \
        database connection `database_connection_url meteos`

    # Format logging
    if [ "$LOG_COLOR" == "True" ] && [ "$SYSLOG" == "False" ]; then
        setup_colorized_logging $METEOS_CONF_FILE DEFAULT
    fi

    recreate_database meteos
    $METEOS_BIN_DIR/meteos-manage \
        --config-file $METEOS_CONF_FILE db sync
}

# install_meteos() - Collect source and prepare
function install_meteos {
    setup_develop $METEOS_DIR
}

# install_python_meteosclient() - Collect source and prepare
function install_python_meteosclient {
    git_clone $METEOSCLIENT_REPO $METEOSCLIENT_DIR $METEOSCLIENT_BRANCH
    setup_develop $METEOSCLIENT_DIR
}

# start_meteos() - Start running processes, including screen
function start_meteos {
    local service_port=$METEOS_SERVICE_PORT
    local service_protocol=$METEOS_SERVICE_PROTOCOL

    run_process meteos-all "$METEOS_BIN_DIR/meteos-all \
        --config-file $METEOS_CONF_FILE"
    run_process meteos-api "$METEOS_BIN_DIR/meteos-api \
        --config-file $METEOS_CONF_FILE"
    run_process meteos-eng "$METEOS_BIN_DIR/meteos-engine \
        --config-file $METEOS_CONF_FILE"

    echo "Waiting for Meteos to start..."
    if ! wait_for_service $SERVICE_TIMEOUT \
                $service_protocol://$METEOS_SERVICE_HOST:$service_port; then
        die $LINENO "Meteos did not start"
    fi
}

# configure_tempest_for_meteos() - Tune Tempest configuration for Meteos
function configure_tempest_for_meteos {
    if is_service_enabled tempest; then
        iniset $TEMPEST_CONFIG service_available meteos True
        iniset $TEMPEST_CONFIG data-processing-feature-enabled plugins $METEOS_ENABLED_PLUGINS
    fi
}

# stop_meteos() - Stop running processes
function stop_meteos {
    # Kill the Meteos screen windows
    stop_process meteos-all
    stop_process meteos-api
    stop_process meteos-eng
}

# is_meteos_enabled. This allows is_service_enabled meteos work
# correctly throughout devstack.
function is_meteos_enabled {
    if is_service_enabled meteos-api || \
        is_service_enabled meteos-eng || \
        is_service_enabled meteos-all; then
        return 0
    else
        return 1
    fi
}

# Dispatcher for Meteos plugin
if is_service_enabled meteos; then
    if [[ "$1" == "stack" && "$2" == "install" ]]; then
        echo_summary "Installing meteos"
        install_meteos
        install_python_meteosclient
        cleanup_meteos
    elif [[ "$1" == "stack" && "$2" == "post-config" ]]; then
        echo_summary "Configuring meteos"
        configure_meteos
        create_meteos_accounts
    elif [[ "$1" == "stack" && "$2" == "extra" ]]; then
        echo_summary "Initializing meteos"
        start_meteos
    elif [[ "$1" == "stack" && "$2" == "test-config" ]]; then
        echo_summary "Configuring tempest"
        configure_tempest_for_meteos
    fi

    if [[ "$1" == "unstack" ]]; then
        stop_meteos
    fi

    if [[ "$1" == "clean" ]]; then
        cleanup_meteos
    fi
fi


# Restore xtrace
$XTRACE

# Local variables:
# mode: shell-script
# End:
