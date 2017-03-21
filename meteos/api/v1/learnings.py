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

"""The learnings api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import learnings as learning_views
from meteos.common import constants
from meteos import engine
from meteos import exception
from meteos import utils

LOG = log.getLogger(__name__)


class LearningController(wsgi.Controller, wsgi.AdminActionsMixin):

    """The Learnings API v1 controller for the OpenStack API."""
    resource_name = 'learning'
    _view_builder_class = learning_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given learning."""
        context = req.environ['meteos.context']

        try:
            learning = self.engine_api.get_learning(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, learning)

    def delete(self, req, id):
        """Delete a learning."""
        context = req.environ['meteos.context']

        LOG.info("Delete learning with id: %s", id, context=context)

        try:
            self.engine_api.delete_learning(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of learnings."""
        return self._get_learnings(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of learnings."""
        return self._get_learnings(req, is_detail=True)

    def _get_learnings(self, req, is_detail):
        """Returns a list of learnings, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to learning attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        learnings = self.engine_api.get_all_learnings(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(learnings, req)

        if is_detail:
            learnings = self._view_builder.detail_list(req, limited_list)
        else:
            learnings = self._view_builder.summary_list(req, limited_list)
        return learnings

    def create(self, req, body):
        """Creates a new learning."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'learning'):
            raise exc.HTTPUnprocessableEntity()

        learning = body['learning']

        LOG.debug("Create learning with request: %s", learning)

        display_name = learning.get('display_name')
        display_description = learning.get('display_description')
        model_id = learning.get('model_id')
        method = learning.get('method')
        args = learning.get('args')

        try:
            model = self.engine_api.get_model(context, model_id)
            utils.is_valid_status(model.__class__.__name__,
                                  model.status,
                                  (constants.STATUS_AVAILABLE,
                                   constants.STATUS_ACTIVE))
            experiment = self.engine_api.get_experiment(
                context,
                model.experiment_id)
            utils.is_valid_status(experiment.__class__.__name__,
                                  experiment.status,
                                  constants.STATUS_AVAILABLE)
            template = self.engine_api.get_template(
                context,
                experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidStatus:
            raise

        new_learning = self.engine_api.create_learning(
            context,
            display_name,
            display_description,
            model.status,
            model_id,
            method,
            model.model_type,
            model.dataset_format,
            args,
            template.id,
            template.job_template_id,
            model.experiment_id,
            experiment.cluster_id)

        return self._view_builder.detail(req, new_learning)


def create_resource():
    return wsgi.Resource(LearningController())
