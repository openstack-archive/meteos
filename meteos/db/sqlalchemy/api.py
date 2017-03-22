# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright (c) 2014 Mirantis, Inc.
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

"""Implementation of SQLAlchemy backend."""

import copy
from functools import wraps
import sys
import warnings

# NOTE(uglide): Required to override default oslo_db Query class
import meteos.db.sqlalchemy.query  # noqa

from oslo_config import cfg
from oslo_db import api as oslo_db_api
from oslo_db import options as db_options
from oslo_db.sqlalchemy import session
from oslo_db.sqlalchemy import utils as db_utils
from oslo_log import log
from oslo_utils import uuidutils
from sqlalchemy.sql import func

from meteos.db.sqlalchemy import models
from meteos import exception
from meteos.i18n import _

CONF = cfg.CONF

LOG = log.getLogger(__name__)

_DEFAULT_QUOTA_NAME = 'default'
PER_PROJECT_QUOTAS = []

_FACADE = None

_DEFAULT_SQL_CONNECTION = 'sqlite://'
db_options.set_defaults(cfg.CONF,
                        connection=_DEFAULT_SQL_CONNECTION)


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = session.EngineFacade.from_config(cfg.CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    """The backend is this module itself."""

    return sys.modules[__name__]


def is_admin_context(context):
    """Indicates if the request context is an administrator."""
    if not context:
        warnings.warn(_('Use of empty request context is deprecated'),
                      DeprecationWarning)
        raise Exception('die')
    return context.is_admin


def is_user_context(context):
    """Indicates if the request context is a normal user."""
    if not context:
        return False
    if context.is_admin:
        return False
    if not context.user_id or not context.project_id:
        return False
    return True


def authorize_project_context(context, project_id):
    """Ensures a request has permission to access the given project."""
    if is_user_context(context):
        if not context.project_id:
            raise exception.NotAuthorized()
        elif context.project_id != project_id:
            raise exception.NotAuthorized()


def authorize_user_context(context, user_id):
    """Ensures a request has permission to access the given user."""
    if is_user_context(context):
        if not context.user_id:
            raise exception.NotAuthorized()
        elif context.user_id != user_id:
            raise exception.NotAuthorized()


def authorize_quota_class_context(context, class_name):
    """Ensures a request has permission to access the given quota class."""
    if is_user_context(context):
        if not context.quota_class:
            raise exception.NotAuthorized()
        elif context.quota_class != class_name:
            raise exception.NotAuthorized()


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]):
            raise exception.AdminRequired()
        return f(*args, **kwargs)
    return wrapper


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`authorize_project_context` and
    :py:func:`authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not is_admin_context(args[0]) and not is_user_context(args[0]):
            raise exception.NotAuthorized()
        return f(*args, **kwargs)
    return wrapper


def model_query(context, model, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param model: model to query. Must be a subclass of ModelBase.
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('project_only')
    kwargs = dict()

    if project_only and not context.is_admin:
        kwargs['project_id'] = context.project_id
    if read_deleted in ('no', 'n', False):
        kwargs['deleted'] = False
    elif read_deleted in ('yes', 'y', True):
        kwargs['deleted'] = True

    return db_utils.model_query(
        model=model, session=session, args=args, **kwargs)


def exact_filter(query, model, filters, legal_keys):
    """Applies exact match filtering to a query.

    Returns the updated query.  Modifies filters argument to remove
    filters consumed.

    :param query: query to apply filters to
    :param model: model object the query applies to, for IN-style
                  filtering
    :param filters: dictionary of filters; values that are lists,
                    tuples, sets, or frozensets cause an 'IN' test to
                    be performed, while exact matching ('==' operator)
                    is used for other values
    :param legal_keys: list of keys to apply exact filtering to
    """

    filter_dict = {}

    # Walk through all the keys
    for key in legal_keys:
        # Skip ones we're not filtering on
        if key not in filters:
            continue

        # OK, filtering on this key; what value do we search for?
        value = filters.pop(key)

        if isinstance(value, (list, tuple, set, frozenset)):
            # Looking for values in a list; apply to query directly
            column_attr = getattr(model, key)
            query = query.filter(column_attr.in_(value))
        else:
            # OK, simple exact match; save for later
            filter_dict[key] = value

    # Apply simple exact matches
    if filter_dict:
        query = query.filter_by(**filter_dict)

    return query


def ensure_dict_has_id(model_dict):
    if not model_dict.get('id'):
        model_dict['id'] = uuidutils.generate_uuid()
    return model_dict


#


@require_admin_context
def service_destroy(context, service_id):
    session = get_session()
    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.soft_delete(session)


@require_admin_context
def service_get(context, service_id, session=None):
    result = model_query(
        context,
        models.Service,
        session=session).\
        filter_by(id=service_id).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=service_id)

    return result


@require_admin_context
def service_get_all(context, disabled=None):
    query = model_query(context, models.Service)

    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    return query.all()


@require_admin_context
def service_get_all_by_topic(context, topic):
    return model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(topic=topic).\
        all()


@require_admin_context
def service_get_by_host_and_topic(context, host, topic):
    result = model_query(
        context, models.Service, read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(host=host).\
        filter_by(topic=topic).\
        first()
    if not result:
        raise exception.ServiceNotFound(service_id=host)
    return result


@require_admin_context
def _service_get_all_topic_subquery(context, session, topic, subq, label):
    sort_value = getattr(subq.c, label)
    return model_query(context, models.Service,
                       func.coalesce(sort_value, 0),
                       session=session, read_deleted="no").\
        filter_by(topic=topic).\
        filter_by(disabled=False).\
        outerjoin((subq, models.Service.host == subq.c.host)).\
        order_by(sort_value).\
        all()


@require_admin_context
def service_get_all_learning_sorted(context):
    session = get_session()
    with session.begin():
        topic = CONF.learning_topic
        label = 'learning_gigabytes'
        subq = model_query(context, models.Share,
                           func.sum(models.Share.size).label(label),
                           session=session, read_deleted="no").\
            join(models.ShareInstance,
                 models.ShareInstance.learning_id == models.Share.id).\
            group_by(models.ShareInstance.host).\
            subquery()
        return _service_get_all_topic_subquery(context,
                                               session,
                                               topic,
                                               subq,
                                               label)


@require_admin_context
def service_get_by_args(context, host, binary):
    result = model_query(context, models.Service).\
        filter_by(host=host).\
        filter_by(binary=binary).\
        first()

    if not result:
        raise exception.HostBinaryNotFound(host=host, binary=binary)

    return result


@require_admin_context
def service_create(context, values):
    session = get_session()

    service_ref = models.Service()
    service_ref.update(values)
    if not CONF.enable_new_services:
        service_ref.disabled = True

    with session.begin():
        service_ref.save(session)
        return service_ref


@require_admin_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def service_update(context, service_id, values):
    session = get_session()

    with session.begin():
        service_ref = service_get(context, service_id, session=session)
        service_ref.update(values)
        service_ref.save(session=session)


#


def _experiment_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Experiment, session=session)


@require_context
def experiment_get(context, experiment_id, session=None):
    result = _experiment_get_query(
        context, session).filter_by(id=experiment_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
def experiment_create(context, experiment_values):
    values = copy.deepcopy(experiment_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    experiment_ref = models.Experiment()
    experiment_ref.update(values)

    with session.begin():
        experiment_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return experiment_get(context, experiment_ref['id'], session=session)


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def experiment_update(context, experiment_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        experiment_ref = experiment_get(
            context, experiment_id, session=session)

        experiment_ref.update(values)
        experiment_ref.save(session=session)
        return experiment_ref


def _experiment_get_all_with_filters(context, project_id=None, filters=None,
                                     sort_key=None, sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _experiment_get_query(context).join()
    )

    query = query.filter(models.Experiment.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(model, query):
        sort_attr = getattr(model, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Experiment, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of experiments that satisfy filters.
    query = query.all()
    return query


@require_context
def experiment_get_all_by_project(context, project_id, filters=None,
                                  sort_key=None, sort_dir=None):
    """Returns list of experiments with given project ID."""
    query = _experiment_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def experiment_delete(context, experiment_id):
    session = get_session()

    with session.begin():
        experiment_ref = experiment_get(context, experiment_id, session)
        experiment_ref.soft_delete(session=session)


#


def _template_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Template, session=session)


@require_context
def template_get(context, template_id, session=None):
    result = _template_get_query(
        context, session).filter_by(id=template_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
def template_create(context, template_values):
    values = copy.deepcopy(template_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    template_ref = models.Template()
    template_ref.update(values)

    with session.begin():
        template_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return template_get(context, template_ref['id'], session=session)


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def template_update(context, template_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        template_ref = template_get(context, template_id, session=session)

        template_ref.update(values)
        template_ref.save(session=session)
        return template_ref


def _template_get_all_with_filters(context, project_id=None, filters=None,
                                   sort_key=None, sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _template_get_query(context).join()
    )

    query = query.filter(models.Template.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(model, query):
        sort_attr = getattr(model, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Template, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of templates that satisfy filters.
    query = query.all()
    return query


@require_context
def template_get_all_by_project(context, project_id, filters=None,
                                sort_key=None, sort_dir=None):
    """Returns list of templates with given project ID."""
    query = _template_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def template_delete(context, template_id):
    session = get_session()

    with session.begin():
        template_ref = template_get(context, template_id, session)
        template_ref.soft_delete(session=session)


#


def _dataset_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Dataset, session=session)


@require_context
def dataset_get(context, dataset_id, session=None):
    result = _dataset_get_query(
        context, session).filter_by(id=dataset_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
def dataset_create(context, dataset_values):
    values = copy.deepcopy(dataset_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    dataset_ref = models.Dataset()
    dataset_ref.update(values)

    with session.begin():
        dataset_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return dataset_get(context, dataset_ref['id'], session=session)


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def dataset_update(context, dataset_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        dataset_ref = dataset_get(context, dataset_id, session=session)

        dataset_ref.update(values)
        dataset_ref.save(session=session)
        return dataset_ref


def _dataset_get_all_with_filters(context, project_id=None, filters=None,
                                  sort_key=None, sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _dataset_get_query(context).join()
    )

    query = query.filter(models.Dataset.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(model, query):
        sort_attr = getattr(model, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Dataset, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of datasets that satisfy filters.
    query = query.all()
    return query


@require_context
def dataset_get_all_by_project(context, project_id, filters=None,
                               sort_key=None, sort_dir=None):
    """Returns list of datasets with given project ID."""
    query = _dataset_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def dataset_delete(context, dataset_id):
    session = get_session()

    with session.begin():
        dataset_ref = dataset_get(context, dataset_id, session)
        dataset_ref.soft_delete(session=session)


#


def _model_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Model, session=session)


@require_context
def model_get(context, model_id, session=None):
    result = _model_get_query(context, session).filter_by(id=model_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
def model_create(context, model_values):
    values = copy.deepcopy(model_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    model_ref = models.Model()
    model_ref.update(values)

    with session.begin():
        model_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return model_get(context, model_ref['id'], session=session)


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def model_update(context, model_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        model_ref = model_get(context, model_id, session=session)

        model_ref.update(values)
        model_ref.save(session=session)
        return model_ref


def _model_get_all_with_filters(context, project_id=None, filters=None,
                                sort_key=None, sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _model_get_query(context).join()
    )

    query = query.filter(models.Model.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(model, query):
        sort_attr = getattr(model, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Model, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of models that satisfy filters.
    query = query.all()
    return query


@require_context
def model_get_all_by_project(context, project_id, filters=None,
                             sort_key=None, sort_dir=None):
    """Returns list of models with given project ID."""
    query = _model_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def model_delete(context, model_id):
    session = get_session()

    with session.begin():
        model_ref = model_get(context, model_id, session)
        model_ref.soft_delete(session=session)


#


def _model_evaluation_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Model_Evaluation, session=session)


@require_context
def model_evaluation_get(context, model_evaluation_id, session=None):
    result = _model_evaluation_get_query(
        context, session).filter_by(id=model_evaluation_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def model_evaluation_update(context, model_evaluation_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        model_evaluation_ref = model_evaluation_get(context,
                                                    model_evaluation_id,
                                                    session=session)

        model_evaluation_ref.update(values)
        model_evaluation_ref.save(session=session)
        return model_evaluation_ref


@require_context
def model_evaluation_create(context, model_evaluation_values):
    values = copy.deepcopy(model_evaluation_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    model_evaluation_ref = models.Model_Evaluation()
    model_evaluation_ref.update(values)

    with session.begin():
        model_evaluation_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return model_evaluation_get(context,
                                    model_evaluation_ref['id'],
                                    session=session)


def _model_evaluation_get_all_with_filters(context, project_id=None,
                                           filters=None, sort_key=None,
                                           sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _model_evaluation_get_query(context).join()
    )

    query = query.filter(models.Model_Evaluation.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(model_evaluation, query):
        sort_attr = getattr(model_evaluation, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Model_Evaluation, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of model_evaluations that satisfy filters.
    query = query.all()
    return query


@require_context
def model_evaluation_get_all_by_project(context, project_id, filters=None,
                                        sort_key=None, sort_dir=None):
    """Returns list of model_evaluations with given project ID."""
    query = _model_evaluation_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def model_evaluation_delete(context, model_evaluation_id):
    session = get_session()

    with session.begin():
        model_evaluation_ref = model_evaluation_get(context,
                                                    model_evaluation_id,
                                                    session)
        model_evaluation_ref.soft_delete(session=session)


#


def _learning_get_query(context, session=None):
    if session is None:
        session = get_session()
    return model_query(context, models.Learning, session=session)


@require_context
def learning_get(context, learning_id, session=None):
    result = _learning_get_query(
        context, session).filter_by(id=learning_id).first()

    if result is None:
        raise exception.NotFound()

    return result


@require_context
def learning_create(context, learning_values):
    values = copy.deepcopy(learning_values)
    values = ensure_dict_has_id(values)

    session = get_session()
    learning_ref = models.Learning()
    learning_ref.update(values)

    with session.begin():
        learning_ref.save(session=session)

        # NOTE(u_glide): Do so to prevent errors with relationships
        return learning_get(context, learning_ref['id'], session=session)


@require_context
@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def learning_update(context, learning_id, update_values):
    session = get_session()
    values = copy.deepcopy(update_values)

    with session.begin():
        learning_ref = learning_get(context, learning_id, session=session)

        learning_ref.update(values)
        learning_ref.save(session=session)
        return learning_ref


def _learning_get_all_with_filters(context, project_id=None, filters=None,
                                   sort_key=None, sort_dir=None):
    if not sort_key:
        sort_key = 'created_at'
    if not sort_dir:
        sort_dir = 'desc'
    query = (
        _learning_get_query(context).join()
    )

    query = query.filter(models.Learning.project_id == project_id)

    # Apply filters
    if not filters:
        filters = {}

    # Apply sorting
    if sort_dir.lower() not in ('desc', 'asc'):
        msg = _("Wrong sorting data provided: sort key is '%(sort_key)s' "
                "and sort direction is '%(sort_dir)s'.") % {
                    "sort_key": sort_key, "sort_dir": sort_dir}
        raise exception.InvalidInput(reason=msg)

    def apply_sorting(learning, query):
        sort_attr = getattr(learning, sort_key)
        sort_method = getattr(sort_attr, sort_dir.lower())
        return query.order_by(sort_method())

    try:
        query = apply_sorting(models.Learning, query)
    except AttributeError:
        msg = _("Wrong sorting key provided - '%s'.") % sort_key
        raise exception.InvalidInput(reason=msg)

    # Returns list of learnings that satisfy filters.
    query = query.all()
    return query


@require_context
def learning_get_all_by_project(context, project_id, filters=None,
                                sort_key=None, sort_dir=None):
    """Returns list of learnings with given project ID."""
    query = _learning_get_all_with_filters(
        context, project_id=project_id, filters=filters,
        sort_key=sort_key, sort_dir=sort_dir,
    )
    return query


@require_context
def learning_delete(context, learning_id):
    session = get_session()

    with session.begin():
        learning_ref = learning_get(context, learning_id, session)
        learning_ref.soft_delete(session=session)
