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

"""Meteos base exception handling.

Includes decorator for re-raising Meteos-type exceptions.

SHOULD include dedicated exception logging.

"""
import re

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log
import six
import webob.exc

from meteos.i18n import _

LOG = log.getLogger(__name__)

exc_log_opts = [
    cfg.BoolOpt('fatal_exception_format_errors',
                default=False,
                help='Whether to make exception message format errors fatal.'),
]

CONF = cfg.CONF
CONF.register_opts(exc_log_opts)


ProcessExecutionError = processutils.ProcessExecutionError


class ConvertedException(webob.exc.WSGIHTTPException):
    def __init__(self, code=400, title="", explanation=""):
        self.code = code
        self.title = title
        self.explanation = explanation
        super(ConvertedException, self).__init__()


class Error(Exception):
    pass


class MeteosException(Exception):
    """Base Meteos Exception

    To correctly use this class, inherit from it and define
    a 'message' property. That message will get printf'd
    with the keyword arguments provided to the constructor.

    """
    message = _("An unknown exception occurred.")
    code = 500
    headers = {}
    safe = False

    def __init__(self, message=None, detail_data={}, **kwargs):
        self.kwargs = kwargs
        self.detail_data = detail_data

        if 'code' not in self.kwargs:
            try:
                self.kwargs['code'] = self.code
            except AttributeError:
                pass
        for k, v in self.kwargs.items():
            if isinstance(v, Exception):
                self.kwargs[k] = six.text_type(v)

        if not message:
            try:
                message = self.message % kwargs

            except Exception:
                # kwargs doesn't match a variable in the message
                # log the issue and the kwargs
                LOG.exception('Exception in string format operation.')
                for name, value in kwargs.items():
                    LOG.error("%(name)s: %(value)s", {
                        'name': name, 'value': value})
                if CONF.fatal_exception_format_errors:
                    raise
                else:
                    # at least get the core message out if something happened
                    message = self.message
        elif isinstance(message, Exception):
            message = six.text_type(message)

        if re.match('.*[^\.]\.\.$', message):
            message = message[:-1]
        self.msg = message
        super(MeteosException, self).__init__(message)


class Conflict(MeteosException):
    message = _("%(err)s")
    code = 409


class Invalid(MeteosException):
    message = _("Unacceptable parameters.")
    code = 400


class InvalidRequest(Invalid):
    message = _("The request is invalid.")


class InvalidResults(Invalid):
    message = _("The results are invalid.")


class InvalidInput(Invalid):
    message = _("Invalid input received: %(reason)s.")


class InvalidContentType(Invalid):
    message = _("Invalid content type %(content_type)s.")


class InvalidParameterValue(Invalid):
    message = _("%(err)s")


class InvalidUUID(Invalid):
    message = _("Expected a uuid but received %(uuid)s.")


class InvalidLearning(Invalid):
    message = _("Invalid learning: %(reason)s.")


class InvalidStatus(Invalid):
    message = _("Invalid Status: %(reason)s.")


class NotAuthorized(MeteosException):
    message = _("Not authorized.")
    code = 403


class NotFound(MeteosException):
    message = _("Resource could not be found.")
    code = 404
    safe = True


class VersionNotFoundForAPIMethod(Invalid):
    message = _("API version %(version)s is not supported on this method.")


class HostBinaryNotFound(NotFound):
    message = _("Could not find binary %(binary)s on host %(host)s.")


class MalformedRequestBody(MeteosException):
    message = _("Malformed message body: %(reason)s.")
    code = 400


class AdminRequired(NotAuthorized):
    message = _("User does not have admin privileges.")


class PolicyNotAuthorized(NotAuthorized):
    message = _("Policy doesn't allow %(action)s to be performed.")


class DriverNotInitialized(MeteosException):
    message = _("Share driver '%(driver)s' not initialized.")


class Duplicated(MeteosException):
    message = _("Duplicate entry")
    code = 409
    safe = True
