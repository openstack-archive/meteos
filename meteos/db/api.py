# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Defines interface for DB access.

The underlying driver is loaded as a :class:`LazyPluggable`.

Functions in this module are imported into the meteos.db namespace. Call these
functions from meteos.db namespace, not the meteos.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.


**Related Flags**

:backend:  string to lookup in the list of LazyPluggable backends.
           `sqlalchemy` is the only supported backend right now.

:connection:  string specifying the sqlalchemy connection to use, like:
              `sqlite:///var/lib/meteos/meteos.sqlite`.

:enable_new_services:  when adding a new service to the database, is it in the
                       pool of available hardware (Default: True)

"""
from oslo_config import cfg
from oslo_db import api as db_api

db_opts = [
    cfg.StrOpt('db_backend',
               default='sqlalchemy',
               help='The backend to use for database.'),
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create.'),
    cfg.StrOpt('learning_name_template',
               default='learning-%s',
               help='Template string to be used to generate learning names.'),
    cfg.StrOpt('learning_snapshot_name_template',
               default='learning-snapshot-%s',
               help='Template string to be used to generate learning snapshot '
                    'names.'),
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

_BACKEND_MAPPING = {'sqlalchemy': 'meteos.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF, backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    return IMPL.authorize_project_context(context, project_id)


def authorize_quota_class_context(context, class_name):
    """Ensures a request has permission to access the given quota class."""
    return IMPL.authorize_quota_class_context(context, class_name)


#


def service_destroy(context, service_id):
    """Destroy the service or raise if it does not exist."""
    return IMPL.service_destroy(context, service_id)


def service_get(context, service_id):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get(context, service_id)


def service_get_by_host_and_topic(context, host, topic):
    """Get a service by host it's on and topic it listens to."""
    return IMPL.service_get_by_host_and_topic(context, host, topic)


def service_get_all(context, disabled=None):
    """Get all services."""
    return IMPL.service_get_all(context, disabled)


def service_get_all_by_topic(context, topic):
    """Get all services for a given topic."""
    return IMPL.service_get_all_by_topic(context, topic)


def service_get_all_learning_sorted(context):
    """Get all learning services sorted by learning count.

    :returns: a list of (Service, learning_count) tuples.

    """
    return IMPL.service_get_all_learning_sorted(context)


def service_get_by_args(context, host, binary):
    """Get the state of an service by node name and binary."""
    return IMPL.service_get_by_args(context, host, binary)


def service_create(context, values):
    """Create a service from the values dictionary."""
    return IMPL.service_create(context, values)


def service_update(context, service_id, values):
    """Set the given properties on an service and update it.

    Raises NotFound if service does not exist.

    """
    return IMPL.service_update(context, service_id, values)


#


def experiment_create(context, experiment_values):
    """Create new experiment."""
    return IMPL.experiment_create(context, experiment_values)


def experiment_update(context, experiment_id, values):
    """Update experiment fields."""
    return IMPL.experiment_update(context, experiment_id, values)


def experiment_get(context, experiment_id):
    """Get experiment by id."""
    return IMPL.experiment_get(context, experiment_id)


def experiment_get_all(context, filters=None, sort_key=None, sort_dir=None):
    """Get all experiments."""
    return IMPL.experiment_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def experiment_get_all_by_project(context, project_id, filters=None,
                                  sort_key=None, sort_dir=None):
    """Returns all experiments with given project ID."""
    return IMPL.experiment_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def experiment_delete(context, experiment_id):
    """Delete experiment."""
    return IMPL.experiment_delete(context, experiment_id)


#


def template_create(context, template_values):
    """Create new template."""
    return IMPL.template_create(context, template_values)


def template_update(context, template_id, values):
    """Update template fields."""
    return IMPL.template_update(context, template_id, values)


def template_get(context, template_id):
    """Get template by id."""
    return IMPL.template_get(context, template_id)


def template_get_all(context, filters=None, sort_key=None, sort_dir=None):
    """Get all templates."""
    return IMPL.template_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def template_get_all_by_project(context, project_id, filters=None,
                                sort_key=None, sort_dir=None):
    """Returns all templates with given project ID."""
    return IMPL.template_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def template_delete(context, template_id):
    """Delete template."""
    return IMPL.template_delete(context, template_id)


#


def dataset_create(context, dataset_values):
    """Create new dataset."""
    return IMPL.dataset_create(context, dataset_values)


def dataset_update(context, dataset_id, values):
    """Update dataset fields."""
    return IMPL.dataset_update(context, dataset_id, values)


def dataset_get(context, dataset_id):
    """Get dataset by id."""
    return IMPL.dataset_get(context, dataset_id)


def dataset_get_all(context, filters=None, sort_key=None, sort_dir=None):
    """Get all datasets."""
    return IMPL.dataset_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def dataset_get_all_by_project(context, project_id, filters=None,
                               sort_key=None, sort_dir=None):
    """Returns all datasets with given project ID."""
    return IMPL.dataset_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def dataset_delete(context, dataset_id):
    """Delete dataset."""
    return IMPL.dataset_delete(context, dataset_id)


#


def model_create(context, model_values):
    """Create new model."""
    return IMPL.model_create(context, model_values)


def model_update(context, model_id, values):
    """Update model fields."""
    return IMPL.model_update(context, model_id, values)


def model_get(context, model_id):
    """Get model by id."""
    return IMPL.model_get(context, model_id)


def model_get_all(context, filters=None, sort_key=None, sort_dir=None):
    """Get all models."""
    return IMPL.model_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def model_get_all_by_project(context, project_id, filters=None,
                             sort_key=None, sort_dir=None):
    """Returns all models with given project ID."""
    return IMPL.model_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def model_delete(context, model_id):
    """Delete model."""
    return IMPL.model_delete(context, model_id)


#


def model_evaluation_create(context, model_evaluation_values):
    """Create new model_evaluation."""
    return IMPL.model_evaluation_create(context, model_evaluation_values)


def model_evaluation_update(context, model_evaluation_id, values):
    """Update model_evaluation fields."""
    return IMPL.model_evaluation_update(context, model_evaluation_id, values)


def model_evaluation_get(context, model_evaluation_id):
    """Get model_evaluation by id."""
    return IMPL.model_evaluation_get(context, model_evaluation_id)


def model_evaluation_get_all(context, filters=None,
                             sort_key=None, sort_dir=None):
    """Get all model_evaluations."""
    return IMPL.model_evaluation_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def model_evaluation_get_all_by_project(context, project_id, filters=None,
                                        sort_key=None, sort_dir=None):
    """Returns all model_evaluations with given project ID."""
    return IMPL.model_evaluation_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def model_evaluation_delete(context, model_evaluation_id):
    """Delete model_evaluation."""
    return IMPL.model_evaluation_delete(context, model_evaluation_id)


#


def learning_create(context, learning_values):
    """Create new learning."""
    return IMPL.learning_create(context, learning_values)


def learning_update(context, learning_id, values):
    """Update learning fields."""
    return IMPL.learning_update(context, learning_id, values)


def learning_get(context, learning_id):
    """Get learning by id."""
    return IMPL.learning_get(context, learning_id)


def learning_get_all(context, filters=None, sort_key=None, sort_dir=None):
    """Get all learnings."""
    return IMPL.learning_get_all(
        context, filters=filters, sort_key=sort_key, sort_dir=sort_dir,
    )


def learning_get_all_by_project(context, project_id, filters=None,
                                sort_key=None, sort_dir=None):
    """Returns all learnings with given project ID."""
    return IMPL.learning_get_all_by_project(
        context, project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )


def learning_delete(context, learning_id):
    """Delete learning."""
    return IMPL.learning_delete(context, learning_id)
