# Copyright (c) 2013 OpenStack, LLC.
#
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
WSGI middleware for OpenStack API controllers.
"""

from oslo_log import log
import routes

from meteos.i18n import _
from meteos import wsgi as base_wsgi

LOG = log.getLogger(__name__)


class APIMapper(routes.Mapper):
    def routematch(self, url=None, environ=None):
        if url is "":
            result = self._match("", environ)
            return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)


class ProjectMapper(APIMapper):
    def resource(self, member_name, collection_name, **kwargs):
        if 'parent_resource' not in kwargs:
            kwargs['path_prefix'] = '{project_id}/'
        else:
            parent_resource = kwargs['parent_resource']
            p_collection = parent_resource['collection_name']
            p_member = parent_resource['member_name']
            kwargs['path_prefix'] = '{project_id}/%s/:%s_id' % (p_collection,
                                                                p_member)
        routes.Mapper.resource(self,
                               member_name,
                               collection_name,
                               **kwargs)


class APIRouter(base_wsgi.Router):
    """Routes requests on the API to the appropriate controller and method."""
    ExtensionManager = None  # override in subclasses

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`meteos.wsgi.Router` doesn't have."""
        return cls()

    def __init__(self, ext_mgr=None):
        mapper = ProjectMapper()
        self.resources = {}
        self._setup_routes(mapper, ext_mgr)
        super(APIRouter, self).__init__(mapper)

    def _setup_routes(self, mapper, ext_mgr):
        raise NotImplementedError


class FaultWrapper(base_wsgi.Middleware):
    def __init__(self, application):
        LOG.warning('meteos.api.openstack:FaultWrapper is deprecated. '
                    'Please use '
                    'meteos.api.middleware.fault:FaultWrapper instead.')
        # Avoid circular imports from here.
        from meteos.api.middleware import fault
        super(FaultWrapper, self).__init__(fault.FaultWrapper(application))
