# Copyright 2016 SAP SE
# All Rights Reserved
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

import copy

from keystoneauth1 import loading as ks_loading
from keystoneauth1.loading._plugins.identity import v2
from keystoneauth1.loading._plugins.identity import v3
from oslo_config import cfg
from oslo_log import log

from meteos import exception
from meteos.i18n import _

CONF = cfg.CONF
LOG = log.getLogger(__name__)

"""Helper class to support keystone v2 and v3 for clients

Builds auth and session context before instantiation of the actual
client. In order to build this context a dedicated config group is
needed to load all needed parameters dynamically.


"""


class AuthClientLoader(object):

    def __init__(self, client_class, exception_module, cfg_group,
                 deprecated_opts_for_v2=None, opts_for_v3=None,
                 url=None, token=None):
        self.client_class = client_class
        self.exception_module = exception_module
        self.group = cfg_group
        self.admin_auth = None
        self.conf = CONF
        self.session = None
        self.auth_plugin = None
        self.deprecated_opts_for_v2 = deprecated_opts_for_v2
        self.opts_for_v3 = opts_for_v3
        self.url = url
        self.token = token

    @staticmethod
    def list_opts(group):
        """Generates a list of config option for a given group

        :param group: group name
        :return: list of auth default configuration
        """
        opts = copy.deepcopy(ks_loading.register_session_conf_options(
                             CONF, group))
        opts.insert(0, ks_loading.get_auth_common_conf_options()[0])

        for plugin_option in ks_loading.get_auth_plugin_conf_options(
                'password'):
            found = False
            for option in opts:
                if option.name == plugin_option.name:
                    found = True
                    break
            if not found:
                opts.append(plugin_option)
        opts.sort(key=lambda x: x.name)
        return [(group, opts)]

    def _load_auth_plugin(self):
        if self.admin_auth:
            return self.admin_auth
        self.auth_plugin = ks_loading.load_auth_from_conf_options(
            CONF, self.group)

        if self.url.find('v2') > -1:
            self.auth_plugin = v2.Token().load_from_options(
                **self.deprecated_opts_for_v2)
        else:
            self.auth_plugin = v3.Token().load_from_options(
                **self.opts_for_v3)

        if self.auth_plugin:
            return self.auth_plugin

        msg = _('Cannot load auth plugin for %s') % self.group
        raise self.exception_module.Unauthorized(message=msg)

    def get_client(self, context, admin=False, **kwargs):
        """Get's the client with the correct auth/session context

        """
        if not self.session:
            self.session = ks_loading.load_session_from_conf_options(
                self.conf, self.group)

        if not self.admin_auth:
            self.admin_auth = self._load_auth_plugin()
        auth_plugin = self.admin_auth

        return self.client_class(version='1.0',
                                 session=self.session,
                                 auth=auth_plugin,
                                 **kwargs)
