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

    _collection_name = 'experiments'
    _detail_version_modifiers = []

    def summary_list(self, request, experiments):
        """Show a list of experiments without many details."""
        return self._list_view(self.summary, request, experiments)

    def detail_list(self, request, experiments):
        """Detailed view of a list of experiments."""
        return self._list_view(self.detail, request, experiments)

    def summary(self, request, experiment):
        """Generic, non-detailed view of a experiment."""
        return {
            'experiment': {
                'id': experiment.get('id'),
                'name': experiment.get('display_name'),
                'description': experiment.get('display_description'),
                'status': experiment.get('status'),
                'template_id': experiment.get('template_id'),
                'key_name': experiment.get('key_name'),
                'management_network': experiment.get('neutron_management_network'),
                'created_at': experiment.get('created_at'),
                'links': self._get_links(request, experiment['id'])
            }
        }

    def detail(self, request, experiment):
        """Detailed view of a single experiment."""
        experiment_dict = {
            'id': experiment.get('id'),
            'created_at': experiment.get('created_at'),
            'status': experiment.get('status'),
            'name': experiment.get('display_name'),
            'description': experiment.get('display_description'),
            'template_id': experiment.get('template_id'),
            'project_id': experiment.get('project_id'),
            'user_id': experiment.get('user_id'),
            'key_name': experiment.get('key_name'),
            'management_network': experiment.get('neutron_management_network'),
        }

        self.update_versioned_resource_dict(
            request, experiment_dict, experiment)

        return {'experiment': experiment_dict}

    def _list_view(self, func, request, experiments):
        """Provide a view for a list of experiments."""
        experiments_list = [func(request, experiment)['experiment']
                            for experiment in experiments]
        experiments_links = self._get_collection_links(request,
                                                       experiments,
                                                       self._collection_name)
        experiments_dict = dict(experiments=experiments_list)

        if experiments_links:
            experiments_dict['experiments_links'] = experiments_links

        return experiments_dict
