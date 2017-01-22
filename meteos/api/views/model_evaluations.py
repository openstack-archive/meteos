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

    _collection_name = 'model_evaluations'
    _detail_version_modifiers = []

    def summary_list(self, request, model_evaluations):
        """Show a list of model evaluations without many details."""
        return self._list_view(self.summary, request, model_evaluations)

    def detail_list(self, request, model_evaluations):
        """Detailed view of a list of model evaluations."""
        return self._list_view(self.detail, request, model_evaluations)

    def summary(self, request, model_evaluation):
        """Generic, non-detailed view of a model evaluation."""
        return {
            'model_evaluation': {
                'id': model_evaluation.get('id'),
                'name': model_evaluation.get('display_name'),
                'status': model_evaluation.get('status'),
                'source_dataset_url': model_evaluation.get('source_dataset_url'),
                'model_id': model_evaluation.get('model_id'),
                'model_type': model_evaluation.get('model_type'),
                'stdout': model_evaluation.get('stdout'),
                'created_at': model_evaluation.get('created_at'),
                'links': self._get_links(request, model_evaluation['id'])
            }
        }

    def detail(self, request, model_evaluation):
        """Detailed view of a single model evaluation."""
        model_evaluation_dict = {
            'id': model_evaluation.get('id'),
            'name': model_evaluation.get('display_name'),
            'status': model_evaluation.get('status'),
            'source_dataset_url': model_evaluation.get('source_dataset_url'),
            'model_id': model_evaluation.get('model_id'),
            'model_type': model_evaluation.get('model_type'),
            'user_id': model_evaluation.get('user_id'),
            'project_id': model_evaluation.get('project_id'),
            'created_at': model_evaluation.get('created_at'),
            'stdout': model_evaluation.get('stdout'),
            'stderr': model_evaluation.get('stderr'),
        }

        self.update_versioned_resource_dict(request,
                                            model_evaluation_dict,
                                            model_evaluation)

        return {'model_evaluation': model_evaluation_dict}

    def _list_view(self, func, request, model_evaluations):
        """Provide a view for a list of model evaluations."""
        model_evaluations_list = [func(request, model_evaluation)['model_evaluation']
                                  for model_evaluation in model_evaluations]
        model_evaluations_links = self._get_collection_links(request,
                                                             model_evaluations,
                                                             self._collection_name)
        model_evaluations_dict = dict(model_evaluations=model_evaluations_list)

        if model_evaluations_links:
            model_evaluations_dict['model_evaluations_links'] = model_evaluations_links

        return model_evaluations_dict
