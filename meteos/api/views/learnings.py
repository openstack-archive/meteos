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

    _collection_name = 'learnings'
    _detail_version_modifiers = []

    def summary_list(self, request, learnings):
        """Show a list of learnings without many details."""
        return self._list_view(self.summary, request, learnings)

    def detail_list(self, request, learnings):
        """Detailed view of a list of learnings."""
        return self._list_view(self.detail, request, learnings)

    def summary(self, request, learning):
        """Generic, non-detailed view of a learning."""
        return {
            'learning': {
                'id': learning.get('id'),
                'name': learning.get('display_name'),
                'description': learning.get('display_description'),
                'status': learning.get('status'),
                'model_id': learning.get('model_id'),
                'type': learning.get('model_type'),
                'args': learning.get('args'),
                'stdout': learning.get('stdout'),
                'created_at': learning.get('created_at'),
                'links': self._get_links(request, learning['id'])
            }
        }

    def detail(self, request, learning):
        """Detailed view of a single learning."""
        learning_dict = {
            'id': learning.get('id'),
            'created_at': learning.get('created_at'),
            'status': learning.get('status'),
            'name': learning.get('display_name'),
            'description': learning.get('display_description'),
            'user_id': learning.get('user_id'),
            'project_id': learning.get('project_id'),
            'stdout': learning.get('stdout'),
            'stderr': learning.get('stderr'),
            'method': learning.get('method'),
            'model_id': learning.get('model_id'),
            'args': learning.get('args'),
        }

        self.update_versioned_resource_dict(request, learning_dict, learning)

        return {'learning': learning_dict}

    def _list_view(self, func, request, learnings):
        """Provide a view for a list of learnings."""
        learnings_list = [func(request, learning)['learning']
                          for learning in learnings]
        learnings_links = self._get_collection_links(request,
                                                     learnings,
                                                     self._collection_name)
        learnings_dict = dict(learnings=learnings_list)

        if learnings_links:
            learnings_dict['learnings_links'] = learnings_links

        return learnings_dict
