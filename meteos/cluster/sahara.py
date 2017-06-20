# Copyright 2014 Mirantis Inc.
# All Rights Reserved.
# Copyright (c) 2016 NEC Corporation.
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
Handles all requests relating to volumes + sahara.
"""

from keystoneauth1 import loading as ks_loading
from osc_lib import exceptions as sahara_exception
from oslo_config import cfg
from saharaclient import client as sahara_client

from meteos.common import client_auth
from meteos.common.config import core_opts
from meteos.db import base

SAHARA_GROUP = 'sahara'

sahara_opts = [
    cfg.StrOpt('auth_url',
               default='http://localhost/identity/v3',
               help='Identity service URL.',
               deprecated_group='DEFAULT')
]

CONF = cfg.CONF
CONF.register_opts(core_opts)
CONF.register_opts(sahara_opts, SAHARA_GROUP)
ks_loading.register_session_conf_options(CONF, SAHARA_GROUP)
ks_loading.register_auth_conf_options(CONF, SAHARA_GROUP)


def list_opts():
    return client_auth.AuthClientLoader.list_opts(SAHARA_GROUP)


def saharaclient(context):
    deprecated_opts_for_v2 = {
        'auth_url': CONF.sahara.auth_url,
        'token': context.auth_token,
        'tenant_id': context.tenant,
    }
    opts_for_v3 = {
        'auth_url': CONF.sahara.auth_url,
        'token': context.auth_token,
        'project_id': context.tenant,
    }
    AUTH_OBJ = client_auth.AuthClientLoader(
        client_class=sahara_client.Client,
        exception_module=sahara_exception,
        cfg_group=SAHARA_GROUP,
        deprecated_opts_for_v2=deprecated_opts_for_v2,
        opts_for_v3=opts_for_v3,
        url=CONF.sahara.auth_url,
        token=context.auth_token)
    return AUTH_OBJ.get_client(context)


class API(base.Base):

    """API for interacting with the data processing manager."""

    def image_set(self, context, id, user_name):
        item = saharaclient(context).images.update_image(id, user_name)
        return item.image['id']

    def image_tags_add(self, context, id, data):
        saharaclient(context).images.update_tags(id, data)

    def image_remove(self, context, id):
        saharaclient(context).images.unregister_image(id)

    def create_node_group_template(self, context, name, plugin_name, version,
                                   flavor_id, node_processes, floating_ip_pool,
                                   auto_security_group):
        item = saharaclient(context).node_group_templates.create(
            name,
            plugin_name,
            version,
            flavor_id,
            node_processes=node_processes,
            floating_ip_pool=floating_ip_pool,
            auto_security_group=auto_security_group)

        return item.id

    def delete_node_group_template(self, context, id):
        saharaclient(context).node_group_templates.delete(id)

    def create_cluster_template(self, context, name, plugin_name,
                                version, node_groups):
        item = saharaclient(context).cluster_templates.create(
            name,
            plugin_name,
            version,
            node_groups=node_groups)

        return item.id

    def delete_cluster_template(self, context, id):
        saharaclient(context).cluster_templates.delete(id)

    def get_job_binary_data(self, context, id):
        item = saharaclient(context).job_binary_internals.get(id)
        return item.id

    def create_job_binary_data(self, context, name, data):
        item = saharaclient(context).job_binary_internals.create(name, data)
        return item.id

    def delete_job_binary_data(self, context, id):
        saharaclient(context).job_binary_internals.delete(id)

    def create_job_binary(self, context, name, url):
        item = saharaclient(context).job_binaries.create(name, url)
        return item.id

    def delete_job_binary(self, context, id):
        saharaclient(context).job_binaries.delete(id)

    def create_job_template(self, context, name, type, mains):
        item = saharaclient(context).jobs.create(name, type, mains=mains)
        return item.id

    def delete_job_template(self, context, id):
        saharaclient(context).jobs.delete(id)

    def get_node_groups(self, context, id):
        item = saharaclient(context).clusters.get(id)
        return item.node_groups

    def create_cluster(self, context, name, plugin, version, image_id,
                       template_id, keypair, neutron_management_network):

        item = saharaclient(context).clusters.create(
            name,
            plugin,
            version,
            cluster_template_id=template_id,
            default_image_id=image_id,
            user_keypair_id=keypair,
            net_id=neutron_management_network)

        return item.id

    def delete_cluster(self, context, id):
        saharaclient(context).clusters.delete(id)

    def get_cluster(self, context, id):
        item = saharaclient(context).clusters.get(id)
        return item

    def job_create(self, context, job_template_id, cluster_id, configs):
        item = saharaclient(context).job_executions.create(
            job_template_id, cluster_id, configs=configs)
        return item.id

    def job_delete(self, context, id):
        saharaclient(context).job_executions.delete(id)

    def get_job(self, context, id):
        item = saharaclient(context).job_executions.get(id)
        return item
