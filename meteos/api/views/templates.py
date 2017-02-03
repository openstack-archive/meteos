# Copyright 2013 OpenStack LLC.
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

from meteos.api import common


class ViewBuilder(common.ViewBuilder):

    """Model a server API response as a python dictionary."""

    _collection_name = 'templates'
    _detail_version_modifiers = []

    def summary_list(self, request, templates):
        """Show a list of templates without many details."""
        return self._list_view(self.summary, request, templates)

    def detail_list(self, request, templates):
        """Detailed view of a list of templates."""
        return self._list_view(self.detail, request, templates)

    def summary(self, request, template):
        """Generic, non-detailed view of a template."""
        return {
            'template': {
                'id': template.get('id'),
                'name': template.get('display_name'),
                'description': template.get('display_description'),
                'master_nodes': template.get('master_nodes_num'),
                'master_flavor': template.get('master_flavor_id'),
                'worker_nodes': template.get('worker_nodes_num'),
                'worker_flavor': template.get('worker_flavor_id'),
                'spark_version': template.get('spark_version'),
                'status': template.get('status'),
                'links': self._get_links(request, template['id'])
            }
        }

    def detail(self, request, template):
        """Detailed view of a single template."""
        template_dict = {
            'id': template.get('id'),
            'created_at': template.get('created_at'),
            'status': template.get('status'),
            'name': template.get('display_name'),
            'description': template.get('display_description'),
            'user_id': template.get('user_id'),
            'project_id': template.get('project_id'),
            'master_nodes': template.get('master_nodes_num'),
            'master_flavor': template.get('master_flavor_id'),
            'worker_nodes': template.get('worker_nodes_num'),
            'worker_flavor': template.get('worker_flavor_id'),
            'spark_version': template.get('spark_version'),
            'cluster_id': template.get('cluster_id'),
        }

        self.update_versioned_resource_dict(request, template_dict, template)

        return {'template': template_dict}

    def _list_view(self, func, request, templates):
        """Provide a view for a list of templates."""
        templates_list = [func(request, template)['template']
                          for template in templates]
        templates_links = self._get_collection_links(request,
                                                     templates,
                                                     self._collection_name)
        templates_dict = dict(templates=templates_list)

        if templates_links:
            templates_dict['templates_links'] = templates_links

        return templates_dict
