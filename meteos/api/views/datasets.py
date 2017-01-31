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

    _collection_name = 'datasets'
    _detail_version_modifiers = []

    def summary_list(self, request, datasets):
        """Show a list of datasets without many details."""
        return self._list_view(self.summary, request, datasets)

    def detail_list(self, request, datasets):
        """Detailed view of a list of datasets."""
        return self._list_view(self.detail, request, datasets)

    def summary(self, request, dataset):
        """Generic, non-detailed view of a dataset."""
        return {
            'dataset': {
                'id': dataset.get('id'),
                'source_dataset_url': dataset.get('source_dataset_url'),
                'name': dataset.get('display_name'),
                'description': dataset.get('display_description'),
                'status': dataset.get('status'),
                'created_at': dataset.get('created_at'),
                'head': dataset.get('head'),
                'links': self._get_links(request, dataset['id'])
            }
        }

    def detail(self, request, dataset):
        """Detailed view of a single dataset."""
        dataset_dict = {
            'id': dataset.get('id'),
            'created_at': dataset.get('created_at'),
            'status': dataset.get('status'),
            'name': dataset.get('display_name'),
            'description': dataset.get('display_description'),
            'user_id': dataset.get('user_id'),
            'project_id': dataset.get('project_id'),
            'head': dataset.get('head'),
            'stderr': dataset.get('stderr'),
        }

        self.update_versioned_resource_dict(request, dataset_dict, dataset)

        return {'dataset': dataset_dict}

    def _list_view(self, func, request, datasets):
        """Provide a view for a list of datasets."""
        datasets_list = [func(request, dataset)['dataset']
                         for dataset in datasets]
        datasets_links = self._get_collection_links(request,
                                                    datasets,
                                                    self._collection_name)
        datasets_dict = dict(datasets=datasets_list)

        if datasets_links:
            datasets_dict['datasets_links'] = datasets_links

        return datasets_dict
