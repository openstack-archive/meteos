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

    _collection_name = 'models'
    _detail_version_modifiers = []

    def summary_list(self, request, models):
        """Show a list of models without many details."""
        return self._list_view(self.summary, request, models)

    def detail_list(self, request, models):
        """Detailed view of a list of models."""
        return self._list_view(self.detail, request, models)

    def summary(self, request, model):
        """Generic, non-detailed view of a model."""
        return {
            'model': {
                'id': model.get('id'),
                'source_dataset_url': model.get('source_dataset_url'),
                'name': model.get('display_name'),
                'description': model.get('display_description'),
                'experiment_id': model.get('experiment_id'),
                'type': model.get('model_type'),
                'params': model.get('model_params'),
                'status': model.get('status'),
                'stdout': model.get('stdout'),
                'created_at': model.get('created_at'),
                'links': self._get_links(request, model['id'])
            }
        }

    def detail(self, request, model):
        """Detailed view of a single model."""
        model_dict = {
            'id': model.get('id'),
            'created_at': model.get('created_at'),
            'status': model.get('status'),
            'name': model.get('display_name'),
            'description': model.get('display_description'),
            'experiment_id': model.get('experiment_id'),
            'user_id': model.get('user_id'),
            'project_id': model.get('project_id'),
            'type': model.get('model_type'),
            'params': model.get('model_params'),
            'stdout': model.get('stdout'),
            'stderr': model.get('stderr'),
        }

        self.update_versioned_resource_dict(request, model_dict, model)

        return {'model': model_dict}

    def _list_view(self, func, request, models):
        """Provide a view for a list of models."""
        models_list = [func(request, model)['model'] for model in models]
        models_links = self._get_collection_links(request,
                                                  models,
                                                  self._collection_name)
        models_dict = dict(models=models_list)

        if models_links:
            models_dict['models_links'] = models_links

        return models_dict
