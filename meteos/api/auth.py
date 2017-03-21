# Copyright (c) 2013 OpenStack, LLC.
#
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

from oslo_log import log

from meteos.api.middleware import auth

LOG = log.getLogger(__name__)


class MeteosKeystoneContext(auth.MeteosKeystoneContext):
    def __init__(self, application):
        LOG.warning('meteos.api.auth:MeteosKeystoneContext is deprecated. '
                        'Please use '
                        'meteos.api.middleware.auth:MeteosKeystoneContext '
                        'instead.')
        super(MeteosKeystoneContext, self).__init__(application)


def pipeline_factory(loader, global_conf, **local_conf):
    LOG.warning('meteos.api.auth:pipeline_factory is deprecated. '
                    'Please use meteos.api.middleware.auth:pipeline_factory '
                    'instead.')
    auth.pipeline_factory(loader, global_conf, **local_conf)
