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

"""The model_evaluations api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import model_evaluations as model_evaluation_views
from meteos.common import constants
from meteos import engine
from meteos import exception
from meteos import utils

LOG = log.getLogger(__name__)


class ModelEvaluationController(wsgi.Controller, wsgi.AdminActionsMixin):

    """The ModelEvaluations API v1 controller for the OpenStack API."""
    resource_name = 'model_evaluation'
    _view_builder_class = model_evaluation_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given model evaluation."""
        context = req.environ['meteos.context']

        try:
            model_evaluation = self.engine_api.get_model_evaluation(context,
                                                                    id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, model_evaluation)

    def delete(self, req, id):
        """Delete a model evaluation."""
        context = req.environ['meteos.context']

        LOG.info("Delete model evaluation with id: %s", id, context=context)

        try:
            self.engine_api.delete_model_evaluation(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of model evaluations."""
        return self._get_model_evaluations(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of model evaluations."""
        return self._get_model_evaluations(req, is_detail=True)

    def _get_model_evaluations(self, req, is_detail):
        """Returns a list of model evaluations, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to model_evaluation attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        model_evaluations = self.engine_api.get_all_model_evaluations(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(model_evaluations, req)

        if is_detail:
            model_evaluations = self._view_builder.detail_list(req, limited_list)
        else:
            model_evaluations = self._view_builder.summary_list(req, limited_list)
        return model_evaluations

    def create(self, req, body):
        """Creates a new model evaluation."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'model_evaluation'):
            raise exc.HTTPUnprocessableEntity()

        model_evaluation = body['model_evaluation']

        LOG.debug("Create model evaluation with request: %s", model_evaluation)

        display_name = model_evaluation.get('display_name')
        model_id = model_evaluation.get('model_id')
        source_dataset_url = model_evaluation.get('source_dataset_url')

        swift_tenant = model_evaluation.get('swift_tenant')
        swift_username = model_evaluation.get('swift_username')
        swift_password = model_evaluation.get('swift_password')

        try:
            model = self.engine_api.get_model(context, model_id)
            utils.is_valid_status(model.__class__.__name__,
                                  model.status,
                                  constants.STATUS_AVAILABLE)
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

        new_model_evaluation = self.engine_api.create_model_evaluation(
            context,
            display_name,
            source_dataset_url,
            model_id,
            model.model_type,
            model.dataset_format,
            template.id,
            template.job_template_id,
            model.experiment_id,
            experiment.cluster_id,
            swift_tenant,
            swift_username,
            swift_password)

        return self._view_builder.detail(req, new_model_evaluation)


def create_resource():
    return wsgi.Resource(ModelEvaluationController())
