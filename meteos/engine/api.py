# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
# Copyright (c) 2015 Tom Barron.  All rights reserved.
# Copyright (c) 2015 Mirantis Inc.
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
Handles all requests relating to learnings.
"""

import copy
from oslo_log import log
from oslo_utils import excutils
import six

from meteos.common import constants
from meteos.db import base
from meteos.engine import rpcapi as engine_rpcapi
from meteos import exception
from meteos.i18n import _
from meteos import policy
from meteos import utils

DELETE_VALID_STATUSES = (constants.STATUS_AVAILABLE,
                         constants.STATUS_ERROR,
                         constants.STATUS_INACTIVE)
LOG = log.getLogger(__name__)


class API(base.Base):

    """API for interacting with the learning manager."""

    def __init__(self, db_driver=None):
        self.engine_rpcapi = engine_rpcapi.LearningAPI()
        super(API, self).__init__(db_driver)

    def get_all_templates(self, context, search_opts=None,
                          sort_key='created_at', sort_dir='desc'):
        policy.check_policy(context, 'template', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for templates by: %s", six.text_type(search_opts))

        project_id = context.project_id

        templates = self.db.template_get_all_by_project(context, project_id,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in templates:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            templates = results
        return templates

    def get_template(self, context, template_id):
        rv = self.db.template_get(context, template_id)
        return rv

    def create_template(self, context, name, description, image_id=None,
                        master_nodes_num=None, master_flavor_id=None,
                        worker_nodes_num=None, worker_flavor_id=None,
                        spark_version=None, floating_ip_pool=None):
        """Create new Expariment."""
        policy.check_policy(context, 'template', 'create')

        template = {'id': None,
                    'user_id': context.user_id,
                    'project_id': context.project_id,
                    'display_name': name,
                    'display_description': description,
                    'image_id': image_id,
                    'master_nodes_num': master_nodes_num,
                    'master_flavor_id': master_flavor_id,
                    'worker_nodes_num': worker_nodes_num,
                    'worker_flavor_id': worker_flavor_id,
                    'spark_version': spark_version,
                    'floating_ip_pool': floating_ip_pool,
                    }

        try:
            result = self.db.template_create(context, template)
            self.engine_rpcapi.create_template(context, result)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.template_delete(context, result['id'])

        # Retrieve the learning with instance details
        template = self.db.template_get(context, result['id'])

        return template

    def delete_template(self, context, id, force=False):
        """Delete template."""

        policy.check_policy(context, 'template', 'delete')

        template = self.db.template_get(context, id)

        utils.is_valid_status(template.__class__.__name__,
                              template['status'],
                              DELETE_VALID_STATUSES)

        self.engine_rpcapi.delete_template(context, id)

    def get_all_experiments(self, context, search_opts=None,
                            sort_key='created_at', sort_dir='desc'):

        policy.check_policy(context, 'experiment', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for experiments by: %s",
                  six.text_type(search_opts))

        project_id = context.project_id

        experiments = self.db.experiment_get_all_by_project(
            context, project_id,
            sort_key=sort_key, sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in experiments:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            experiments = results
        return experiments

    def get_experiment(self, context, experiment_id):
        rv = self.db.experiment_get(context, experiment_id)
        return rv

    def create_experiment(self, context, name, description, template_id,
                          key_name, neutron_management_network):
        """Create new Experiment."""
        policy.check_policy(context, 'experiment', 'create')

        experiment = {'id': None,
                      'user_id': context.user_id,
                      'project_id': context.project_id,
                      'display_name': name,
                      'display_description': description,
                      'template_id': template_id,
                      'key_name': key_name,
                      'neutron_management_network': neutron_management_network,
                      }

        try:
            result = self.db.experiment_create(context, experiment)
            self.engine_rpcapi.create_experiment(context, result)
            updates = {'status': constants.STATUS_CREATING}

            LOG.info("Accepted creation of experiment %s.", result['id'])
            self.db.experiment_update(context, result['id'], updates)

        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.experiment_delete(context, result['id'])

        # Retrieve the learning with instance details
        experiment = self.db.experiment_get(context, result['id'])

        return experiment

    def delete_experiment(self, context, id, force=False):
        """Delete experiment."""

        policy.check_policy(context, 'experiment', 'delete')

        experiment = self.db.experiment_get(context, id)

        utils.is_valid_status(experiment.__class__.__name__,
                              experiment['status'],
                              DELETE_VALID_STATUSES)

        self.engine_rpcapi.delete_experiment(context, id)

    def get_all_datasets(self, context, search_opts=None,
                         sort_key='created_at', sort_dir='desc'):

        policy.check_policy(context, 'dataset', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for datasets by: %s", six.text_type(search_opts))

        project_id = context.project_id

        datasets = self.db.dataset_get_all_by_project(context,
                                                      project_id,
                                                      sort_key=sort_key,
                                                      sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in datasets:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            datasets = results
        return datasets

    def get_dataset(self, context, dataset_id):
        rv = self.db.dataset_get(context, dataset_id)
        return rv

    def create_dataset(self, context, name, description, method,
                       source_dataset_url, params, template_id,
                       job_template_id, experiment_id, cluster_id,
                       swift_tenant, swift_username, swift_password,
                       percent_train, percent_test):
        """Create a Dataset"""
        policy.check_policy(context, 'dataset', 'create')

        dataset = {'id': None,
                   'display_name': name,
                   'display_description': description,
                   'method': method,
                   'source_dataset_url': source_dataset_url,
                   'user_id': context.user_id,
                   'project_id': context.project_id,
                   'experiment_id': experiment_id,
                   'cluster_id': cluster_id,
                   'params': params,
                   }

        test_dataset = {}

        if method == 'split':
            train_data_name = name + '_train_' + percent_train
            test_data_name = name + '_test_' + percent_test

            tmp_dataset = copy.deepcopy(dataset)

            dataset['display_name'] = train_data_name

            tmp_dataset['display_name'] = test_data_name

            try:
                test_dataset = self.db.dataset_create(context, tmp_dataset)
            except Exception:
                with excutils.save_and_reraise_exception():
                    self.db.dataset_delete(context, test_dataset['id'])

        try:
            result = self.db.dataset_create(context, dataset)
            result['template_id'] = template_id
            result['job_template_id'] = job_template_id
            result['swift_tenant'] = swift_tenant
            result['swift_username'] = swift_username
            result['swift_password'] = swift_password
            result['test_dataset'] = test_dataset
            result['percent_train'] = percent_train
            result['percent_test'] = percent_test

            self.engine_rpcapi.create_dataset(context, result)
            updates = {'status': constants.STATUS_CREATING}
            LOG.info("Accepted parsing of dataset %s.", result['id'])
            self.db.dataset_update(context, result['id'], updates)

            if result['test_dataset']:
                self.db.dataset_update(context,
                                       result['test_dataset']['id'],
                                       updates)

        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.dataset_delete(context, result['id'])

        # Retrieve the learning with instance details
        dataset = self.db.dataset_get(context, result['id'])

        return dataset

    def delete_dataset(self, context, id, force=False):
        """Delete dataset."""

        policy.check_policy(context, 'dataset', 'delete')

        dataset = self.db.dataset_get(context, id)

        utils.is_valid_status(dataset.__class__.__name__,
                              dataset['status'],
                              DELETE_VALID_STATUSES)

        self.engine_rpcapi.delete_dataset(context,
                                          dataset['cluster_id'],
                                          dataset['job_id'],
                                          id)

    def _enable_load_model(self, context):

        project_id = context.project_id
        models = self.db.model_get_all_by_project(context,
                                                  project_id)
        l_status = [model.status for model in models]

        if constants.STATUS_ACTIVE in l_status:
            return False

        return True

    def get_all_models(self, context, search_opts=None, sort_key='created_at',
                       sort_dir='desc'):
        policy.check_policy(context, 'model', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for models by: %s", six.text_type(search_opts))

        project_id = context.project_id

        models = self.db.model_get_all_by_project(context,
                                                  project_id,
                                                  sort_key=sort_key,
                                                  sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in models:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            models = results
        return models

    def get_model(self, context, model_id):
        rv = self.db.model_get(context, model_id)
        return rv

    def create_model(self, context, name, description, source_dataset_url,
                     dataset_format, model_type, model_params, template_id,
                     job_template_id, experiment_id, cluster_id,
                     swift_tenant, swift_username, swift_password):
        """Create a Model"""
        policy.check_policy(context, 'model', 'create')

        model = {'id': None,
                 'display_name': name,
                 'display_description': description,
                 'source_dataset_url': source_dataset_url,
                 'dataset_format': dataset_format,
                 'user_id': context.user_id,
                 'project_id': context.project_id,
                 'model_type': model_type,
                 'model_params': model_params,
                 'experiment_id': experiment_id,
                 'cluster_id': cluster_id
                 }

        try:
            result = self.db.model_create(context, model)
            result['job_template_id'] = job_template_id
            result['template_id'] = template_id
            result['swift_tenant'] = swift_tenant
            result['swift_username'] = swift_username
            result['swift_password'] = swift_password
            self.engine_rpcapi.create_model(context, result)
            updates = {'status': constants.STATUS_CREATING}

            LOG.info("Accepted creation of model %s.", result['id'])
            self.db.model_update(context, result['id'], updates)
        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.model_delete(context, result['id'])

        # Retrieve the learning with instance details
        model = self.db.model_get(context, result['id'])

        return model

    def recreate_model(self, id, context, name, description,
                       source_dataset_url, dataset_format,
                       model_type, model_params, template_id,
                       job_template_id, experiment_id, cluster_id,
                       swift_tenant, swift_username, swift_password):
        """Recreate a Model"""
        policy.check_policy(context, 'model', 'recreate')

        model = {'display_name': name,
                 'display_description': description,
                 'source_dataset_url': source_dataset_url,
                 'dataset_format': dataset_format,
                 'model_type': model_type,
                 'model_params': model_params,
                 'experiment_id': experiment_id,
                 'cluster_id': cluster_id,
                 'status': constants.STATUS_RECREATING
                 }

        try:
            self.delete_model(context, id, recreate=True)
            self.db.model_update(context, id, model)
            model['id'] = id
            model['job_template_id'] = job_template_id
            model['template_id'] = template_id
            model['swift_tenant'] = swift_tenant
            model['swift_username'] = swift_username
            model['swift_password'] = swift_password
            self.engine_rpcapi.create_model(context, model)
            LOG.info("Accepted recreation of model %s.", id)

        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.model_delete(context, id)

        # Retrieve the learning with instance details
        model = self.db.model_get(context, id)

        return model

    def delete_model(self, context, id, force=False, recreate=False):
        """Delete model."""

        policy.check_policy(context, 'model', 'delete')

        model = self.db.model_get(context, id)

        utils.is_valid_status(model.__class__.__name__,
                              model['status'],
                              DELETE_VALID_STATUSES)

        self.engine_rpcapi.delete_model(context,
                                        model['cluster_id'],
                                        model['job_id'],
                                        id,
                                        recreate)

    def load_model(self, context, id, dataset_format, model_type,
                   job_template_id, experiment_id, cluster_id):
        """Load a Model"""
        policy.check_policy(context, 'model', 'load')

        model = {'id': id,
                 'dataset_format': dataset_format,
                 'model_type': model_type,
                 'job_template_id': job_template_id,
                 'experiment_id': experiment_id,
                 'cluster_id': cluster_id
                 }

        if not self._enable_load_model(context):
            msg = _("Can not load multiple models at the same time.")
            raise exception.InvalidLearning(reason=msg)

        try:
            self.engine_rpcapi.load_model(context, model)
            updates = {'status': constants.STATUS_ACTIVATING}

            LOG.info("Accepted load of model %s.", id)
            self.db.model_update(context, id, updates)
        except Exception:
            with excutils.save_and_reraise_exception():
                updates = {'status': constants.STATUS_ERROR}
                self.db.model_update(context, id, updates)

    def unload_model(self, context, id, dataset_format, model_type,
                     job_template_id, experiment_id, cluster_id):
        """Unload a Model"""
        policy.check_policy(context, 'model', 'unload')

        model = {'id': id,
                 'dataset_format': dataset_format,
                 'model_type': model_type,
                 'job_template_id': job_template_id,
                 'experiment_id': experiment_id,
                 'cluster_id': cluster_id
                 }

        try:
            self.engine_rpcapi.unload_model(context, model)
            updates = {'status': constants.STATUS_DEACTIVATING}

            LOG.info("Accepted unload of model %s.", id)
            self.db.model_update(context, id, updates)
        except Exception:
            with excutils.save_and_reraise_exception():
                updates = {'status': constants.STATUS_ERROR}
                self.db.model_update(context, id, updates)

    def get_all_model_evaluations(self, context, search_opts=None,
                                  sort_key='created_at', sort_dir='desc'):
        policy.check_policy(context, 'model_evaluation', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for model evaluations by: %s",
                  six.text_type(search_opts))

        project_id = context.project_id

        model_evaluations = self.db.model_evaluation_get_all_by_project(
            context,
            project_id,
            sort_key=sort_key,
            sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in model_evaluations:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            model_evaluations = results
        return model_evaluations

    def get_model_evaluation(self, context, model_evaluation_id):
        rv = self.db.model_evaluation_get(context, model_evaluation_id)
        return rv

    def create_model_evaluation(self, context, name, source_dataset_url,
                                model_id, model_type, dataset_format,
                                template_id, job_template_id, experiment_id,
                                cluster_id, swift_tenant, swift_username,
                                swift_password):
        """Create a Model Evaluation"""
        policy.check_policy(context, 'model_evaluation', 'create')

        model_evaluation = {'id': None,
                            'display_name': name,
                            'model_id': model_id,
                            'model_type': model_type,
                            'source_dataset_url': source_dataset_url,
                            'dataset_format': dataset_format,
                            'user_id': context.user_id,
                            'project_id': context.project_id,
                            'cluster_id': cluster_id
                            }

        try:
            result = self.db.model_evaluation_create(context, model_evaluation)
            result['template_id'] = template_id
            result['job_template_id'] = job_template_id
            result['swift_tenant'] = swift_tenant
            result['swift_username'] = swift_username
            result['swift_password'] = swift_password

            self.engine_rpcapi.create_model_evaluation(context, result)
            updates = {'status': constants.STATUS_CREATING}
            self.db.model_evaluation_update(context,
                                            result['id'],
                                            updates)

            LOG.info("Accepted creation of model evaluation %s.",
                     result['id'])
        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.model_evaluation_delete(context, result['id'])

        # Retrieve the model_evaluation with instance details
        model_evaluation = self.db.model_evaluation_get(context, result['id'])

        return model_evaluation

    def delete_model_evaluation(self, context, id, force=False):
        """Delete model evaluation."""

        policy.check_policy(context, 'model_evaluation', 'delete')

        model_evaluation = self.db.model_evaluation_get(context, id)

        utils.is_valid_status(model_evaluation.__class__.__name__,
                              model_evaluation['status'],
                              DELETE_VALID_STATUSES)

        if model_evaluation.job_id:
            self.engine_rpcapi\
                .delete_model_evaluation(context,
                                         model_evaluation['cluster_id'],
                                         model_evaluation['job_id'],
                                         id)
        else:
            self.db.model_evaluation_delete(context, id)

    def get_all_learnings(self, context, search_opts=None,
                          sort_key='created_at', sort_dir='desc'):
        policy.check_policy(context, 'learning', 'get_all')

        if search_opts is None:
            search_opts = {}

        LOG.debug("Searching for learnings by: %s", six.text_type(search_opts))

        project_id = context.project_id

        learnings = self.db.learning_get_all_by_project(context,
                                                        project_id,
                                                        sort_key=sort_key,
                                                        sort_dir=sort_dir)

        if search_opts:
            results = []
            for s in learnings:
                # values in search_opts can be only strings
                if all(s.get(k, None) == v for k, v in search_opts.items()):
                    results.append(s)
            learnings = results
        return learnings

    def get_learning(self, context, learning_id):
        rv = self.db.learning_get(context, learning_id)
        return rv

    def create_learning(self, context, name, description, status, model_id,
                        method, model_type, dataset_format, args, template_id,
                        job_template_id, experiment_id, cluster_id):
        """Create a Learning"""
        policy.check_policy(context, 'learning', 'create')

        learning = {'id': None,
                    'display_name': name,
                    'display_description': description,
                    'model_id': model_id,
                    'model_type': model_type,
                    'user_id': context.user_id,
                    'project_id': context.project_id,
                    'method': method,
                    'args': args,
                    'job_template_id': job_template_id,
                    'experiment_id': experiment_id,
                    'cluster_id': cluster_id
                    }

        try:
            result = self.db.learning_create(context, learning)
            result['template_id'] = template_id
            result['job_template_id'] = job_template_id
            result['cluster_id'] = cluster_id
            result['dataset_format'] = dataset_format

            LOG.info("Status of Model %s.", status)

            if status == constants.STATUS_AVAILABLE:
                self.engine_rpcapi.create_learning(context, result)
                updates = {'status': constants.STATUS_CREATING}
                self.db.learning_update(context,
                                        result['id'],
                                        updates)

            elif status == constants.STATUS_ACTIVE:
                self.engine_rpcapi.create_online_learning(context,
                                                          result)

            LOG.info("Accepted creation of learning %s.", result['id'])
        except Exception:
            with excutils.save_and_reraise_exception():
                self.db.learning_delete(context, result['id'])

        # Retrieve the learning with instance details
        learning = self.db.learning_get(context, result['id'])

        return learning

    def delete_learning(self, context, id, force=False):
        """Delete learning."""

        policy.check_policy(context, 'learning', 'delete')

        learning = self.db.learning_get(context, id)

        utils.is_valid_status(learning.__class__.__name__,
                              learning['status'],
                              DELETE_VALID_STATUSES)

        if learning.job_id:
            self.engine_rpcapi.delete_learning(context,
                                               learning['cluster_id'],
                                               learning['job_id'],
                                               id)
        else:
            self.db.learning_delete(context, id)
