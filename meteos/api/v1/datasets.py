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

"""The datasets api."""

from oslo_log import log
import six
import webob
from webob import exc

from meteos.api import common
from meteos.api.openstack import wsgi
from meteos.api.views import datasets as dataset_views
from meteos.common import constants
from meteos import engine
from meteos import exception
from meteos import utils

LOG = log.getLogger(__name__)


class DatasetController(wsgi.Controller, wsgi.AdminActionsMixin):

    """The Datasets API v1 controller for the OpenStack API."""
    resource_name = 'dataset'
    _view_builder_class = dataset_views.ViewBuilder

    def __init__(self):
        super(self.__class__, self).__init__()
        self.engine_api = engine.API()

    def show(self, req, id):
        """Return data about the given dataset."""
        context = req.environ['meteos.context']

        try:
            dataset = self.engine_api.get_dataset(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()

        return self._view_builder.detail(req, dataset)

    def delete(self, req, id):
        """Delete a dataset."""
        context = req.environ['meteos.context']

        LOG.info("Delete dataset with id: %s", id, context=context)

        try:
            self.engine_api.delete_dataset(context, id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidLearning as e:
            raise exc.HTTPForbidden(explanation=six.text_type(e))

        return webob.Response(status_int=202)

    def index(self, req):
        """Returns a summary list of datasets."""
        return self._get_datasets(req, is_detail=False)

    def detail(self, req):
        """Returns a detailed list of datasets."""
        return self._get_datasets(req, is_detail=True)

    def _get_datasets(self, req, is_detail):
        """Returns a list of datasets, transformed through view builder."""
        context = req.environ['meteos.context']

        search_opts = {}
        search_opts.update(req.GET)

        # Remove keys that are not related to dataset attrs
        search_opts.pop('limit', None)
        search_opts.pop('offset', None)
        sort_key = search_opts.pop('sort_key', 'created_at')
        sort_dir = search_opts.pop('sort_dir', 'desc')

        datasets = self.engine_api.get_all_datasets(
            context, search_opts=search_opts, sort_key=sort_key,
            sort_dir=sort_dir)

        limited_list = common.limited(datasets, req)

        if is_detail:
            datasets = self._view_builder.detail_list(req, limited_list)
        else:
            datasets = self._view_builder.summary_list(req, limited_list)
        return datasets

    def create(self, req, body):
        """Creates a new dataset."""
        context = req.environ['meteos.context']

        if not self.is_valid_body(body, 'dataset'):
            raise exc.HTTPUnprocessableEntity()

        dataset = body['dataset']

        LOG.debug("Create dataset with request: %s", dataset)

        try:
            experiment = self.engine_api.get_experiment(
                context, dataset['experiment_id'])
            utils.is_valid_status(experiment.__class__.__name__,
                                  experiment.status,
                                  constants.STATUS_AVAILABLE)
            template = self.engine_api.get_template(
                context, experiment.template_id)
        except exception.NotFound:
            raise exc.HTTPNotFound()
        except exception.InvalidStatus:
            raise

        display_name = dataset.get('display_name')
        display_description = dataset.get('display_description')
        method = dataset.get('method')
        experiment_id = dataset.get('experiment_id')
        source_dataset_url = dataset.get('source_dataset_url')
        params = dataset.get('params')
        swift_tenant = dataset.get('swift_tenant')
        swift_username = dataset.get('swift_username')
        swift_password = dataset.get('swift_password')
        percent_train = dataset.get('percent_train', '0.7')
        percent_test = dataset.get('percent_test', '0.3')

        if (method == 'split'
                and not float(percent_train) + float(percent_test) == 1.0):
            raise exc.HTTPUnprocessableEntity()

        new_dataset = self.engine_api.create_dataset(context,
                                                     display_name,
                                                     display_description,
                                                     method,
                                                     source_dataset_url,
                                                     params,
                                                     template.id,
                                                     template.job_template_id,
                                                     experiment_id,
                                                     experiment.cluster_id,
                                                     swift_tenant,
                                                     swift_username,
                                                     swift_password,
                                                     percent_train,
                                                     percent_test)

        return self._view_builder.detail(req, new_dataset)


def create_resource():
    return wsgi.Resource(DatasetController())
