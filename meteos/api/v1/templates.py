# Copyright 2013 NetApp
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

"""The templates api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import templates as template_views
from meteos import engine
from meteos import exception

LOG = log.getLogger(__name__)


class TemplateController(wsgi.Controller, wsgi.AdminActionsMixin):

    """The Templates API v1 controller for the OpenStack API."""
    resource_name = 'template'
    _view_builder_class = template_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given template."""
        context = req.environ['meteos.context']

        try:
            template = self.engine_api.get_template(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, template)

    def delete(self, req, id):
        """Delete a template."""
        context = req.environ['meteos.context']

        LOG.info("Delete template with id: %s", id, context=context)

        try:
            self.engine_api.delete_template(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of templates."""
        return self._get_templates(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of templates."""
        return self._get_templates(req, is_detail=True)

    def _get_templates(self, req, is_detail):
        """Returns a list of templates, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to template attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        templates = self.engine_api.get_all_templates(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(templates, req)

        if is_detail:
            templates = self._view_builder.detail_list(req, limited_list)
        else:
            templates = self._view_builder.summary_list(req, limited_list)
        return templates

    def create(self, req, body):
        """Creates a new template."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'template'):
            raise exc.HTTPUnprocessableEntity()

        template = body['template']

        LOG.debug("Create template with request: %s", template)

        kwargs = {
            'image_id': template.get('image_id'),
            'master_nodes_num': template.get('master_nodes_num'),
            'master_flavor_id': template.get('master_flavor_id'),
            'worker_nodes_num': template.get('worker_nodes_num'),
            'worker_flavor_id': template.get('worker_flavor_id'),
            'spark_version': template.get('spark_version'),
            'floating_ip_pool': template.get('floating_ip_pool'),
        }

        display_name = template.get('display_name')
        display_description = template.get('display_description')

        try:
            new_template = self.engine_api.create_template(context,
                                                           display_name,
                                                           display_description,
                                                           **kwargs)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, new_template)


def create_resource():
    return wsgi.Resource(TemplateController())
