# Copyright 2012 NetApp
# Copyright 2015 Mirantis inc.
# All Rights Reserved.
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
"""
Drivers for learnings.

"""

from oslo_config import cfg
from oslo_log import log


LOG = log.getLogger(__name__)

ssh_opts = [
    cfg.StrOpt(
        'ssh_user',
        default='ubuntu',
        help='SSH login user.'),
    cfg.StrOpt(
        'ssh_password',
        default='ubuntu',
        help='SSH login password.'),
    cfg.IntOpt(
        'ssh_port',
        default=22,
        help='SSH connection port number.'),
    cfg.IntOpt(
        'ssh_conn_timeout',
        default=60,
        help='Backend server SSH connection timeout.'),
    cfg.IntOpt(
        'ssh_min_pool_conn',
        default=1,
        help='Minimum number of connections in the SSH pool.'),
    cfg.IntOpt(
        'ssh_max_pool_conn',
        default=10,
        help='Maximum number of connections in the SSH pool.'),
]

CONF = cfg.CONF
CONF.register_opts(ssh_opts)


class LearningDriver(object):

    """Class defines interface of NAS driver."""

    def __init__(self, driver_handles_learning_servers, *args, **kwargs):
        """Implements base functionality for learning drivers.

        :param driver_handles_learning_servers: expected boolean value or
            tuple/list/set of boolean values.
            There are two possible approaches for learning drivers in Meteos.
            First is when learning driver is able to handle learning-servers
            and second when not.
            Drivers can support either both (indicated by a tuple/set/list with
            (True, False)) or only one of these approaches. So, it is allowed
            to be 'True' when learning driver does support handling of learning
            servers and allowed to be 'False' when it does support usage of
            unhandled learning-servers that are not tracked by Meteos.
            Learning drivers are allowed to work only in one of two possible
            driver modes, that is why only one should be chosen.
        :param config_opts: tuple, list or set of config option lists
            that should be registered in driver's configuration right after
            this attribute is created. Useful for usage with mixin classes.
        """
        super(LearningDriver, self).__init__()
        self.configuration = kwargs.get('configuration', None)
        self.initialized = False
        self._stats = {}

        self.pools = []

        for config_opt_set in kwargs.get('config_opts', []):
            self.configuration.append_config_values(config_opt_set)

    def create_template(self, context, request_specs):
        """Is called to create template."""
        raise NotImplementedError()

    def delete_template(self, context, request_specs):
        """Is called to delete template."""
        raise NotImplementedError()

    def create_experiment(self, context, request_specs):
        """Is called to create experimnet."""
        raise NotImplementedError()

    def delete_experiment(self, context, request_specs):
        """Is called to delete experimnet."""
        raise NotImplementedError()

    def create_dataset(self, context, request_specs):
        """Is called to create dataset."""
        raise NotImplementedError()

    def delete_dataset(self, context, request_specs):
        """Is called to delete dataset."""
        raise NotImplementedError()

    def create_model(self, context, request_specs):
        """Is called to create model."""
        raise NotImplementedError()

    def delete_model(self, context, request_specs):
        """Is called to delete model."""
        raise NotImplementedError()

    def load_model(self, context, request_specs):
        """Is called to load model."""
        raise NotImplementedError()

    def unload_model(self, context, request_specs):
        """Is called to unload model."""
        raise NotImplementedError()
