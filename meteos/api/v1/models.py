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

"""The models api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import models as model_views
from meteos.common import constants
from meteos import engine
from meteos import exception
from meteos import utils

LOG = log.getLogger(__name__)


class ModelMixin(object):
    """Mixin class for Model API Controllers."""

    def _load(self, req, id, body):
        """Load model for online prediction"""
        context = req.environ['meteos.context']

        LOG.debug("Load model with request: %s", id)

        try:
            model = self.engine_api.get_model(context, id)
            utils.is_valid_status(model.__class__.__name__,
                                  model.status,
                                  constants.STATUS_AVAILABLE)
            experiment = self.engine_api.get_experiment(
                context, model.experiment_id)
            template = self.engine_api.get_template(
                context, experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        self.engine_api.load_model(context,
                                   id,
                                   model.dataset_format,
                                   model.model_type,
                                   template.job_template_id,
                                   model.experiment_id,
                                   model.cluster_id)

        return {'model': {'id': id}}

    def _unload(self, req, id, body):
        """Unload model for online prediction"""
        context = req.environ['meteos.context']

        LOG.debug("Unload model with request: %s", id)

        try:
            model = self.engine_api.get_model(context, id)
            utils.is_valid_status(model.__class__.__name__,
                                  model.status,
                                  constants.STATUS_ACTIVE)
            experiment = self.engine_api.get_experiment(
                context, model.experiment_id)
            template = self.engine_api.get_template(
                context, experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        self.engine_api.unload_model(context,
                                     id,
                                     model.dataset_format,
                                     model.model_type,
                                     template.job_template_id,
                                     model.experiment_id,
                                     model.cluster_id)

        return {'model': {'id': id}}

    def _recreate(self, req, id, body):
        """Recreate model with new Dataset"""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'os-recreate'):
            raise exc.HTTPUnprocessableEntity()

        b_model = body['os-recreate']

        LOG.debug("Recreate model with request: %s", b_model)

        try:
            model = self.engine_api.get_model(context, id)
            utils.is_valid_status(model.__class__.__name__,
                                  model.status,
                                  constants.STATUS_AVAILABLE)
            experiment = self.engine_api.get_experiment(
                context, model.experiment_id)
            template = self.engine_api.get_template(
                context, experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        display_name = b_model.get('display_name')
        display_description = b_model.get('display_description')
        source_dataset_url = b_model.get('source_dataset_url')
        dataset_format = b_model.get('dataset_format', 'csv')
        model_type = b_model.get('model_type')
        model_params = b_model.get('model_params')
        swift_tenant = b_model.get('swift_tenant')
        swift_username = b_model.get('swift_username')
        swift_password = b_model.get('swift_password')

        new_model = self.engine_api.recreate_model(id,
                                                   context,
                                                   display_name,
                                                   display_description,
                                                   source_dataset_url,
                                                   dataset_format,
                                                   model_type,
                                                   model_params,
                                                   template.id,
                                                   template.job_template_id,
                                                   experiment.id,
                                                   experiment.cluster_id,
                                                   swift_tenant,
                                                   swift_username,
                                                   swift_password)

        return self._view_builder.detail(req, new_model)


class ModelController(wsgi.Controller, ModelMixin, wsgi.AdminActionsMixin):

    """The Models API v1 controller for the OpenStack API."""
    resource_name = 'model'
    _view_builder_class = model_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given model."""
        context = req.environ['meteos.context']

        try:
            model = self.engine_api.get_model(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, model)

    def delete(self, req, id):
        """Delete a model."""
        context = req.environ['meteos.context']

        LOG.info("Delete model with id: %s", id, context=context)

        try:
            self.engine_api.delete_model(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of models."""
        return self._get_models(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of models."""
        return self._get_models(req, is_detail=True)

    def _get_models(self, req, is_detail):
        """Returns a list of models, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to model attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        models = self.engine_api.get_all_models(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(models, req)

        if is_detail:
            models = self._view_builder.detail_list(req, limited_list)
        else:
            models = self._view_builder.summary_list(req, limited_list)
        return models

    def create(self, req, body):
        """Creates a new model."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'model'):
            raise exc.HTTPUnprocessableEntity()

        model = body['model']

        LOG.debug("Create model with request: %s", model)

        try:
            experiment = self.engine_api.get_experiment(
                context, model['experiment_id'])
            utils.is_valid_status(experiment.__class__.__name__,
                                  experiment.status,
                                  constants.STATUS_AVAILABLE)
            template = self.engine_api.get_template(
                context, experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidStatus:
            raise

        display_name = model.get('display_name')
        display_description = model.get('display_description')
        experiment_id = model.get('experiment_id')
        source_dataset_url = model.get('source_dataset_url')
        dataset_format = model.get('dataset_format', 'csv')
        model_type = model.get('model_type')
        model_params = model.get('model_params')
        swift_tenant = model.get('swift_tenant')
        swift_username = model.get('swift_username')
        swift_password = model.get('swift_password')

        new_model = self.engine_api.create_model(context,
                                                 display_name,
                                                 display_description,
                                                 source_dataset_url,
                                                 dataset_format,
                                                 model_type,
                                                 model_params,
                                                 template.id,
                                                 template.job_template_id,
                                                 experiment_id,
                                                 experiment.cluster_id,
                                                 swift_tenant,
                                                 swift_username,
                                                 swift_password)

        return self._view_builder.detail(req, new_model)

    @wsgi.action('os-load')
    def load(self, req, id, body):
        """Load model."""
        return self._load(req, id, body)

    @wsgi.action('os-unload')
    def unload(self, req, id, body):
        """Unload model."""
        return self._unload(req, id, body)

    @wsgi.action('os-recreate')
    def recreate(self, req, id, body):
        """Recreate model."""
        return self._recreate(req, id, body)


def create_resource():
    return wsgi.Resource(ModelController())
