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

"""The experiments api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import experiments as experiment_views
from meteos.common import constants
from meteos import engine
from meteos import exception
from meteos import utils

LOG = log.getLogger(__name__)


class ExperimentController(wsgi.Controller, wsgi.AdminActionsMixin):

    """The Experiments API v1 controller for the OpenStack API."""
    resource_name = 'experiment'
    _view_builder_class = experiment_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given experiment."""
        context = req.environ['meteos.context']

        try:
            experiment = self.engine_api.get_experiment(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, experiment)

    def delete(self, req, id):
        """Delete a experiment."""
        context = req.environ['meteos.context']

        LOG.info("Delete experiment with id: %s", id, context=context)

        try:
            self.engine_api.delete_experiment(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of experiments."""
        return self._get_experiments(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of experiments."""
        return self._get_experiments(req, is_detail=True)

    def _get_experiments(self, req, is_detail):
        """Returns a list of experiments, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to experiment attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        experiments = self.engine_api.get_all_experiments(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(experiments, req)

        if is_detail:
            experiments = self._view_builder.detail_list(req, limited_list)
        else:
            experiments = self._view_builder.summary_list(req, limited_list)
        return experiments

    def create(self, req, body):
        """Creates a new experiment."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'experiment'):
            raise exc.HTTPUnprocessableEntity()

        experiment = body['experiment']

        LOG.debug("Create experiment with request: %s", experiment)

        try:
            template = self.engine_api.get_template(context,
                                                    experiment['template_id'])
            utils.is_valid_status(template.__class__.__name__,
                                  template.status,
                                  constants.STATUS_AVAILABLE)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidStatus:
            raise

        display_name = experiment.get('display_name')
        display_description = experiment.get('display_description')
        template_id = experiment.get('template_id')
        key_name = experiment.get('key_name')
        neutron_management_network = experiment.get(
            'neutron_management_network')

        new_experiment = self.engine_api.create_experiment(
            context,
            display_name,
            display_description,
            template_id,
            key_name,
            neutron_management_network)

        return self._view_builder.detail(req, new_experiment)


def create_resource():
    return wsgi.Resource(ExperimentController())
