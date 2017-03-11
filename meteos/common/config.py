# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright 2012 Red Hat, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Command-line flag library.

Emulates gflags by wrapping cfg.ConfigOpts.

The idea is to move fully to cfg eventually, and this wrapper is a
stepping stone.

"""

import socket

from oslo_config import cfg
from oslo_log import log
from oslo_middleware import cors
from oslo_utils import netutils


CONF = cfg.CONF
log.register_options(CONF)


core_opts = [
    cfg.StrOpt('api_paste_config',
               default="api-paste.ini",
               help='File name for the paste.deploy config for meteos-api.'),
    cfg.StrOpt('state_path',
               default='/var/lib/meteos',
               help="Top-level directory for maintaining meteos's state."),
    cfg.StrOpt('os_region_name',
               help='Region name of this node.'),
]

debug_opts = [
]

CONF.register_cli_opts(core_opts)
CONF.register_cli_opts(debug_opts)

global_opts = [
    cfg.StrOpt('my_ip',
               default=netutils.get_my_ipv4(),
               sample_default='<your_ip>',
               help='IP address of this host.'),
    cfg.StrOpt('scheduler_topic',
               default='meteos-scheduler',
               help='The topic scheduler nodes listen on.'),
    cfg.StrOpt('learning_topic',
               default='meteos-engine',
               help='The topic learning nodes listen on.'),
    cfg.StrOpt('data_topic',
               default='meteos-data',
               help='The topic data nodes listen on.'),
    cfg.BoolOpt('api_rate_limit',
                default=True,
                help='Whether to rate limit the API.'),
    cfg.ListOpt('osapi_learning_ext_list',
                default=[],
                help='Specify list of extensions to load when using osapi_'
                     'learning_extension option with meteos.api.contrib.'
                     'select_extensions.'),
    cfg.ListOpt('osapi_learning_extension',
                default=['meteos.api.contrib.standard_extensions'],
                help='The osapi learning extensions to load.'),
    cfg.StrOpt('sqlite_db',
               default='meteos.sqlite',
               help='The filename to use with sqlite.'),
    cfg.BoolOpt('sqlite_synchronous',
                default=True,
                help='If passed, use synchronous mode for sqlite.'),
    cfg.IntOpt('sql_idle_timeout',
               default=3600,
               help='Timeout before idle SQL connections are reaped.'),
    cfg.IntOpt('sql_max_retries',
               default=10,
               help='Maximum database connection retries during startup. '
                    '(setting -1 implies an infinite retry count).'),
    cfg.IntOpt('sql_retry_interval',
               default=10,
               help='Interval between retries of opening a SQL connection.'),
    cfg.StrOpt('engine_manager',
               default='meteos.engine.manager.LearningManager',
               help='Full class name for the learning manager.'),
    cfg.StrOpt('host',
               default=socket.gethostname(),
               sample_default='<your_hostname>',
               help='Name of this node.  This can be an opaque identifier.  '
                    'It is not necessarily a hostname, FQDN, or IP address.'),
    # NOTE(vish): default to nova for compatibility with nova installs
    cfg.StrOpt('storage_availability_zone',
               default='nova',
               help='Availability zone of this node.'),
    cfg.StrOpt('default_learning_type',
               help='Default learning type to use.'),
    cfg.ListOpt('memcached_servers',
                help='Memcached servers or None for in process cache.'),
    cfg.StrOpt('learning_usage_audit_period',
               default='month',
               help='Time period to generate learning usages for.  '
                    'Time period must be hour, day, month or year.'),
    cfg.StrOpt('root_helper',
               default='sudo',
               help='Deprecated: command to use for running commands as '
                    'root.'),
    cfg.StrOpt('rootwrap_config',
               help='Path to the rootwrap configuration file to use for '
                    'running commands as root.'),
    cfg.BoolOpt('monkey_patch',
                default=False,
                help='Whether to log monkey patching.'),
    cfg.ListOpt('monkey_patch_modules',
                default=[],
                help='List of modules or decorators to monkey patch.'),
    cfg.IntOpt('service_down_time',
               default=60,
               help='Maximum time since last check-in for up service.'),
    cfg.StrOpt('learning_api_class',
               default='meteos.engine.api.API',
               help='The full class name of the learning API class to use.'),
    cfg.StrOpt('auth_strategy',
               default='keystone',
               help='The strategy to use for auth. Supports noauth, keystone, '
                    'and deprecated.'),
    cfg.ListOpt('enabled_learning_backends',
                help='A list of learning backend names to use. These backend '
                     'names should be backed by a unique [CONFIG] group '
                     'with its options.'),
]

CONF.register_opts(global_opts)


def set_middleware_defaults():
    """Update default configuration options for oslo.middleware."""

    cors.set_defaults(cors.CORS_OPTS,
        allow_headers=['X-Auth-Token',
                       'X-OpenStack-Request-ID',
                       'X-Openstack-Meteos-Api-Version',
                       'X-OpenStack-Meteos-API-Experimental',
                       'X-Identity-Status',
                       'X-Roles',
                       'X-Service-Catalog',
                       'X-User-Id',
                       'X-Tenant-Id'],
        expose_headers=['X-Auth-Token',
                        'X-OpenStack-Request-ID',
                        'X-Openstack-Meteos-Api-Version',
                        'X-OpenStack-Meteos-API-Experimental',
                        'X-Subject-Token',
                        'X-Service-Token'],
        allow_methods=['GET',
                       'PUT',
                       'POST',
                       'DELETE',
                       'PATCH']
    )
