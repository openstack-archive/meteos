# Copyright (c) 2014 SUSE Linux Products GmbH.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

__all__ = [
    'list_opts'
]

import copy
import itertools

import oslo_concurrency.opts
import oslo_log._options
import oslo_middleware.opts
import oslo_policy.opts

import meteos.api.common
import meteos.api.middleware.auth
import meteos.cluster.sahara
import meteos.common.config
import meteos.db.api
import meteos.db.base
import meteos.engine.api
import meteos.engine.driver
import meteos.engine.drivers.generic
import meteos.engine.manager
import meteos.exception
import meteos.service
import meteos.wsgi


# List of *all* options in [DEFAULT] namespace of meteos.
# Any new option list or option needs to be registered here.
_global_opt_lists = [
    # Keep list alphabetically sorted
    meteos.api.common.api_common_opts,
    [meteos.api.middleware.auth.use_forwarded_for_opt],
    meteos.common.config.core_opts,
    meteos.common.config.debug_opts,
    meteos.common.config.global_opts,
    meteos.cluster.sahara.sahara_opts,
    meteos.db.api.db_opts,
    [meteos.db.base.db_driver_opt],
    meteos.exception.exc_log_opts,
    meteos.service.service_opts,
    meteos.engine.driver.ssh_opts,
    meteos.engine.drivers.generic.learning_opts,
    meteos.engine.manager.engine_manager_opts,
    meteos.wsgi.eventlet_opts,
    meteos.wsgi.socket_opts,
]

_opts = [
    (None, list(itertools.chain(*_global_opt_lists)))
]

_opts.extend(oslo_concurrency.opts.list_opts())
_opts.extend(oslo_log._options.list_opts())
_opts.extend(oslo_middleware.opts.list_opts())
_opts.extend(oslo_policy.opts.list_opts())


def list_opts():
    """Return a list of oslo.config options available in Meteos."""
    return [(m, copy.deepcopy(o)) for m, o in _opts]
