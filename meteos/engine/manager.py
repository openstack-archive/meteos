# Copyright (c) 2014 NetApp Inc.
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
"""NAS learning manager managers creating learnings and access rights.

**Related Flags**

:learning_driver: Used by :class:`LearningManager`.
"""

import copy
import datetime
import functools

from oslo_config import cfg
from oslo_log import log
from oslo_serialization import jsonutils
from oslo_service import periodic_task
from oslo_utils import excutils
from oslo_utils import importutils
from oslo_utils import strutils
from oslo_utils import timeutils
import six

from meteos.common import constants
from meteos import context
from meteos import exception
from meteos.i18n import _, _LE, _LI, _LW
from meteos import manager
from meteos.engine import api
import meteos.engine.configuration
from meteos.engine import rpcapi as engine_rpcapi
from meteos import utils

LOG = log.getLogger(__name__)

engine_manager_opts = [
    cfg.StrOpt('learning_driver',
               default='meteos.engine.drivers.generic.GenericLearningDriver',
               help='Driver to use for learning creation.'),
]

CONF = cfg.CONF
CONF.register_opts(engine_manager_opts)
CONF.import_opt('periodic_interval', 'meteos.service')


class LearningManager(manager.Manager):

    """Manages Learning resources."""

    RPC_API_VERSION = '1.0'

    def __init__(self, learning_driver=None, service_name=None,
                 *args, **kwargs):
        """Load the driver from args, or from flags."""
        self.configuration = meteos.engine.configuration.Configuration(
            engine_manager_opts,
            config_group=service_name)
        super(LearningManager, self).__init__(*args, **kwargs)

        if not learning_driver:
            learning_driver = self.configuration.learning_driver

        self.driver = importutils.import_object(
            learning_driver, configuration=self.configuration,
        )

    def _update_status(self, context, resource_name,
                       id, job_id, stdout, stderr):

        if stderr:
            status = constants.STATUS_ERROR
            LOG.error(_LI("Fail to create %s %s."), resource_name, id)
        else:
            status = constants.STATUS_AVAILABLE
            LOG.info(_LI("%s %s created successfully."), resource_name, id)

        updates = {
            'status': status,
            'job_id': job_id,
            'launched_at': timeutils.utcnow(),
            'stderr': stderr,
        }

        if resource_name == 'DataSet':
            updates['head'] = stdout
            self.db.dataset_update(context, id, updates)

        elif resource_name == 'Model':
            updates['stdout'] = stdout
            self.db.model_update(context, id, updates)

        elif resource_name == 'Learning':
            updates['stdout'] = stdout.rstrip('\n')
            self.db.learning_update(context, id, updates)

    def create_template(self, context, request_spec=None):
        """Creates a template."""
        context = context.elevated()

        LOG.debug("Create template with request: %s", request_spec)

        try:
            response = self.driver.create_template(
                context, request_spec)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("template %s failed on creation."),
                          request_spec['id'])
                self.db.template_update(
                    context, request_spec['id'],
                    {'status': constants.STATUS_ERROR}
                )

        LOG.info(_LI("template %s created successfully."),
                 request_spec['id'])

        updates = response
        updates['status'] = constants.STATUS_AVAILABLE
        updates['launched_at'] = timeutils.utcnow()

        self.db.template_update(context, request_spec['id'], updates)

    def delete_template(self, context, id=None):
        """Deletes a template."""
        context = context.elevated()

        try:
            template = self.db.template_get(context, id)
            self.driver.delete_template(context, template)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Template %s failed on deletion."), id)
                self.db.template_update(
                    context, id,
                    {'status': constants.STATUS_ERROR_DELETING}
                )

        LOG.info(_LI("Template %s deleted successfully."), id)
        self.db.template_delete(context, id)

    def create_experiment(self, context, request_spec=None):
        """Creates a Experiment."""
        context = context.elevated()

        LOG.debug("Create experiment with request: %s", request_spec)

        try:
            template = self.db.template_get(
                context, request_spec['template_id'])
            cluster_id = self.driver.create_experiment(
                context, request_spec, template.sahara_image_id,
                template.cluster_template_id, template.spark_version)
            self.driver.wait_for_cluster_create(context, cluster_id)

            experiment = request_spec

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Experiment %s failed on creation."),
                          request_spec['id'])
                self.db.experiment_update(
                    context, request_spec['id'],
                    {'status': constants.STATUS_ERROR}
                )

        LOG.info(_LI("Experiment %s created successfully."),
                 experiment['id'])
        updates = {
            'status': constants.STATUS_AVAILABLE,
            'launched_at': timeutils.utcnow(),
            'cluster_id': cluster_id,
        }
        self.db.experiment_update(context, experiment['id'], updates)

    def delete_experiment(self, context, id=None):
        """Deletes a experiment."""
        context = context.elevated()

        try:
            experiment = self.db.experiment_get(context, id)
            self.driver.delete_experiment(context, experiment['cluster_id'])

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Experiment %s failed on deletion."), id)
                self.db.experiment_update(
                    context, id,
                    {'status': constants.STATUS_ERROR_DELETING}
                )

        LOG.info(_LI("Experiment %s deleted successfully."), id)
        self.db.experiment_delete(context, id)

    def create_dataset(self, context, request_spec=None):
        """Create a Dataset."""
        context = context.elevated()

        LOG.debug("Create dataset with request: %s", request_spec)

        try:
            job_id = self.driver.create_dataset(context, request_spec)
            stdout, stderr = self.driver.get_job_result(
                context,
                job_id,
                request_spec['template_id'],
                request_spec['cluster_id'])

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Dataset %s failed on creation."),
                          request_spec['id'])
                self.db.dataset_update(
                    context, request_spec['id'],
                    {'status': constants.STATUS_ERROR}
                )

        self._update_status(context, 'DataSet', request_spec['id'],
                            job_id, stdout, stderr)

    def delete_dataset(self, context, cluster_id=None, job_id=None, id=None):
        """Deletes a Dataset."""
        context = context.elevated()

        try:
            self.driver.delete_dataset(context, cluster_id, job_id, id)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Dataset %s failed on deletion."), id)
                self.db.dataset_update(
                    context, id,
                    {'status': constants.STATUS_ERROR_DELETING}
                )

        LOG.info(_LI("Dataset %s deleted successfully."), id)
        self.db.dataset_delete(context, id)

    def create_model(self, context, request_spec=None):
        """Create a Model."""
        context = context.elevated()

        LOG.debug("Create model with request: %s", request_spec)

        try:
            job_id = self.driver.create_model(context, request_spec)
            stdout, stderr = self.driver.get_job_result(
                context,
                job_id,
                request_spec['template_id'],
                request_spec['cluster_id'])

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Model %s failed on creation."),
                          request_spec['id'])
                self.db.model_update(
                    context, request_spec['id'],
                    {'status': constants.STATUS_ERROR}
                )

        self._update_status(context, 'Model', request_spec['id'],
                            job_id, stdout, stderr)

    def delete_model(self, context, cluster_id=None, job_id=None, id=None):
        """Deletes a Model."""
        context = context.elevated()

        try:
            self.driver.delete_model(context, cluster_id, job_id, id)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Model %s failed on deletion."), id)
                self.db.model_update(
                    context, id,
                    {'status': constants.STATUS_ERROR_DELETING}
                )

        LOG.info(_LI("Model %s deleted successfully."), id)
        self.db.model_delete(context, id)

    def create_learning(self, context, request_spec=None):
        """Create a Learning."""
        context = context.elevated()

        LOG.debug("Create learning with request: %s", request_spec)

        try:
            job_id = self.driver.create_learning(context, request_spec)
            stdout, stderr = self.driver.get_job_result(
                context,
                job_id,
                request_spec['template_id'],
                request_spec['cluster_id'])

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Learning %s failed on creation."),
                          request_spec['id'])
                self.db.learning_update(
                    context, request_spec['id'],
                    {'status': constants.STATUS_ERROR}
                )

        self._update_status(context, 'Learning', request_spec['id'],
                            job_id, stdout, stderr)

    def delete_learning(self, context, cluster_id=None, job_id=None, id=None):
        """Deletes a Learning."""
        context = context.elevated()

        try:
            self.driver.delete_learning(context, cluster_id, job_id, id)

        except Exception as e:
            with excutils.save_and_reraise_exception():
                LOG.error(_LE("Learning %s failed on deletion."), id)
                self.db.learning_update(
                    context, id,
                    {'status': constants.STATUS_ERROR_DELETING}
                )

        self.db.learning_delete(context, id)
        LOG.info(_LI("Learning %s deleted successfully."), id)
