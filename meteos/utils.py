# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Justin Santa Barbara
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

"""Utilities and helper functions."""

import errno
import functools
import inspect
import os
import pyclbr
import sys
import time

from eventlet import pools
from oslo_concurrency import lockutils
from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log
from oslo_utils import importutils
from oslo_utils import timeutils
import paramiko
import six

from meteos.common import constants
from meteos.db import api as db_api
from meteos import exception
from meteos.i18n import _

CONF = cfg.CONF
LOG = log.getLogger(__name__)

synchronized = lockutils.synchronized_with_prefix('meteos-')


def _get_root_helper():
    return 'sudo meteos-rootwrap %s' % CONF.rootwrap_config


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() function."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    return processutils.execute(*cmd, **kwargs)


def trycmd(*args, **kwargs):
    """Convenience wrapper around oslo's trycmd() function."""
    if 'run_as_root' in kwargs and 'root_helper' not in kwargs:
        kwargs['root_helper'] = _get_root_helper()
    return processutils.trycmd(*args, **kwargs)


class SSHPool(pools.Pool):
    """A simple eventlet pool to hold ssh connections."""

    def __init__(self, ip, port, conn_timeout, login, password=None,
                 privatekey=None, *args, **kwargs):
        self.ip = ip
        self.port = port
        self.login = login
        self.password = password
        self.conn_timeout = conn_timeout if conn_timeout else None
        self.path_to_private_key = privatekey
        super(SSHPool, self).__init__(*args, **kwargs)

    def create(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        look_for_keys = True
        if self.path_to_private_key:
            self.path_to_private_key = os.path.expanduser(
                self.path_to_private_key)
            look_for_keys = False
        elif self.password:
            look_for_keys = False
        try:
            ssh.connect(self.ip,
                        port=self.port,
                        username=self.login,
                        password=self.password,
                        key_filename=self.path_to_private_key,
                        look_for_keys=look_for_keys,
                        timeout=self.conn_timeout)
            # Paramiko by default sets the socket timeout to 0.1 seconds,
            # ignoring what we set through the sshclient. This doesn't help for
            # keeping long lived connections. Hence, we have to bypass it, by
            # overriding it after the transport is initialized. We are setting
            # the sockettimeout to None and setting a keepalive packet so that,
            # the server will keep the connection open. All that does is sent
            # a keepalive packet every ssh_conn_timeout seconds.
            if self.conn_timeout:
                transport = ssh.get_transport()
                transport.sock.settimeout(None)
                transport.set_keepalive(self.conn_timeout)
            return ssh
        except Exception as e:
            msg = _("Check whether private key or password are correctly "
                    "set. Error connecting via ssh: %s") % e
            LOG.error(msg)
            raise exception.SSHException(msg)

    def get(self):
        """Return an item from the pool, when one is available.

        This may cause the calling greenthread to block. Check if a
        connection is active before returning it. For dead connections
        create and return a new connection.
        """
        if self.free_items:
            conn = self.free_items.popleft()
            if conn:
                if conn.get_transport().is_active():
                    return conn
                else:
                    conn.close()
            return self.create()
        if self.current_size < self.max_size:
            created = self.create()
            self.current_size += 1
            return created
        return self.channel.get()

    def remove(self, ssh):
        """Close an ssh client and remove it from free_items."""
        ssh.close()
        ssh = None
        if ssh in self.free_items:
            self.free_items.pop(ssh)
        if self.current_size > 0:
            self.current_size -= 1


class LazyPluggable(object):
    """A pluggable backend loaded lazily based on some value."""

    def __init__(self, pivot, **backends):
        self.__backends = backends
        self.__pivot = pivot
        self.__backend = None

    def __get_backend(self):
        if not self.__backend:
            backend_name = CONF[self.__pivot]
            if backend_name not in self.__backends:
                raise exception.Error(_('Invalid backend: %s') % backend_name)

            backend = self.__backends[backend_name]
            if isinstance(backend, tuple):
                name = backend[0]
                fromlist = backend[1]
            else:
                name = backend
                fromlist = backend

            self.__backend = __import__(name, None, None, fromlist)
            LOG.debug('backend %s', self.__backend)
        return self.__backend

    def __getattr__(self, key):
        backend = self.__get_backend()
        return getattr(backend, key)


def monkey_patch():
    """Patch decorator.

    If the Flags.monkey_patch set as True,
    this function patches a decorator
    for all functions in specified modules.
    You can set decorators for each modules
    using CONF.monkey_patch_modules.
    The format is "Module path:Decorator function".
    Example: 'meteos.api.ec2.cloud:' \
     meteos.openstack.common.notifier.api.notify_decorator'

    Parameters of the decorator is as follows.
    (See meteos.openstack.common.notifier.api.notify_decorator)

    name - name of the function
    function - object of the function
    """
    # If CONF.monkey_patch is not True, this function do nothing.
    if not CONF.monkey_patch:
        return
    # Get list of modules and decorators
    for module_and_decorator in CONF.monkey_patch_modules:
        module, decorator_name = module_and_decorator.split(':')
        # import decorator function
        decorator = importutils.import_class(decorator_name)
        __import__(module)
        # Retrieve module information using pyclbr
        module_data = pyclbr.readmodule_ex(module)
        for key in module_data.keys():
            # set the decorator for the class methods
            if isinstance(module_data[key], pyclbr.Class):
                clz = importutils.import_class("%s.%s" % (module, key))
                # NOTE(vponomaryov): we need to distinguish class methods types
                # for py2 and py3, because the concept of 'unbound methods' has
                # been removed from the python3.x
                if six.PY3:
                    member_type = inspect.isfunction
                else:
                    member_type = inspect.ismethod
                for method, func in inspect.getmembers(clz, member_type):
                    setattr(
                        clz, method,
                        decorator("%s.%s.%s" % (module, key, method), func))
            # set the decorator for the function
            if isinstance(module_data[key], pyclbr.Function):
                func = importutils.import_class("%s.%s" % (module, key))
                setattr(sys.modules[module], key,
                        decorator("%s.%s" % (module, key), func))


def file_open(filename):
    """Open file

    see built-in file() documentation for more details

    Note: The reason this is kept in a separate module is to easily
          be able to provide a stub module that doesn't alter system
          state at all (for unit tests)
    """

    try:
        fd = open(filename)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
    else:
        data = fd.read()
        fd.close()

    return data


def service_is_up(service):
    """Check whether a service is up based on last heartbeat."""
    last_heartbeat = service['updated_at'] or service['created_at']
    # Timestamps in DB are UTC.
    tdelta = timeutils.utcnow() - last_heartbeat
    elapsed = tdelta.total_seconds()
    return abs(elapsed) <= CONF.service_down_time


def validate_service_host(context, host):
    service = db_api.service_get_by_host_and_topic(context, host,
                                                   'meteos-engine')
    if not service_is_up(service):
        raise exception.ServiceIsDown(service=service['host'])

    return service


def walk_class_hierarchy(clazz, encountered=None):
    """Walk class hierarchy, yielding most derived classes first."""
    if not encountered:
        encountered = []
    for subclass in clazz.__subclasses__():
        if subclass not in encountered:
            encountered.append(subclass)
            # drill down to leave first
            for subsubclass in walk_class_hierarchy(subclass, encountered):
                yield subsubclass
            yield subclass


class IsAMatcher(object):
    def __init__(self, expected_value=None):
        self.expected_value = expected_value

    def __eq__(self, actual_value):
        return isinstance(actual_value, self.expected_value)


class ComparableMixin(object):
    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)


def require_driver_initialized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # we can't do anything if the driver didn't init
        if not self.driver.initialized:
            driver_name = self.driver.__class__.__name__
            raise exception.DriverNotInitialized(driver=driver_name)
        return func(self, *args, **kwargs)
    return wrapper


def wait_for_access_update(context, db, learning_instance,
                           migration_wait_access_rules_timeout):
    starttime = time.time()
    deadline = starttime + migration_wait_access_rules_timeout
    tries = 0

    while True:
        instance = db.learning_instance_get(context, learning_instance['id'])

        if instance['access_rules_status'] == constants.STATUS_ACTIVE:
            break

        tries += 1
        now = time.time()
        if instance['access_rules_status'] == constants.STATUS_ERROR:
            msg = _("Failed to update access rules"
                    " on learning instance %s") % learning_instance['id']
            raise exception.LearningMigrationFailed(reason=msg)
        elif now > deadline:
            msg = _("Timeout trying to update access rules"
                    " on learning instance %(learning_id)s. Timeout "
                    "was %(timeout)s seconds.") % {
                'learning_id': learning_instance['id'],
                'timeout': migration_wait_access_rules_timeout}
            raise exception.LearningMigrationFailed(reason=msg)
        else:
            time.sleep(tries ** 2)


def is_valid_status(resource_name, status, valid_statuses):
    if status not in valid_statuses:
        msg = _("%(resource_name)s status must be %(valid_statuses)s") % {
            "resource_name": resource_name,
            "valid_statuses": valid_statuses}
        raise exception.InvalidStatus(reason=msg)
