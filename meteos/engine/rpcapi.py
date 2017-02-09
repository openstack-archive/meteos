# Copyright 2012, Intel, Inc.
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
Client side of the learning RPC API.
"""

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_serialization import jsonutils

from meteos import rpc

CONF = cfg.CONF


class LearningAPI(object):
    """Client side of the learning rpc API.

    API version history:

        1.0  - Initial version.
    """

    BASE_RPC_API_VERSION = '1.0'

    def __init__(self, topic=None):
        super(LearningAPI, self).__init__()
        target = messaging.Target(topic=CONF.learning_topic,
                                  version=self.BASE_RPC_API_VERSION)
        self._client = rpc.get_client(target, version_cap='1.12')

    @staticmethod
    def make_msg(method, **kwargs):
        return method, kwargs

    def call(self, ctxt, msg, version=None, timeout=None):
        method, kwargs = msg

        if version is not None:
            client = self._client.prepare(version=version)
        else:
            client = self._client

        if timeout is not None:
            client = client.prepare(timeout=timeout)

        return client.call(ctxt, method, **kwargs)

    def cast(self, ctxt, msg, version=None):
        method, kwargs = msg
        if version is not None:
            client = self._client.prepare(version=version)
        else:
            client = self._client
        return client.cast(ctxt, method, **kwargs)

    def create_template(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.call(context, self.make_msg('create_template',
                                                request_spec=request_spec_p))

    def delete_template(self, context, id):
        return self.call(context, self.make_msg('delete_template',
                                                id=id))

    def create_experiment(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('create_experiment',
                                                request_spec=request_spec_p))

    def delete_experiment(self, context, id):
        return self.cast(context, self.make_msg('delete_experiment',
                                                id=id))

    def create_dataset(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('create_dataset',
                                                request_spec=request_spec_p))

    def delete_dataset(self, context, cluster_id, job_id, id):
        return self.call(context, self.make_msg('delete_dataset',
                                                cluster_id=cluster_id,
                                                job_id=job_id,
                                                id=id))

    def create_model(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('create_model',
                                                request_spec=request_spec_p))

    def delete_model(self, context, cluster_id, job_id, id, recreate):
        return self.call(context, self.make_msg('delete_model',
                                                cluster_id=cluster_id,
                                                job_id=job_id,
                                                id=id,
                                                recreate=recreate))

    def load_model(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('load_model',
                                                request_spec=request_spec_p))

    def unload_model(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('unload_model',
                                                request_spec=request_spec_p))

    def create_model_evaluation(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('create_model_evaluation',
                                                request_spec=request_spec_p))

    def delete_model_evaluation(self, context, cluster_id, job_id, id):
        return self.call(context, self.make_msg('delete_model_evaluation',
                                                cluster_id=cluster_id,
                                                job_id=job_id,
                                                id=id))

    def create_learning(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.cast(context, self.make_msg('create_learning',
                                                request_spec=request_spec_p))

    def create_online_learning(self, context, request_spec):
        request_spec_p = jsonutils.to_primitive(request_spec)
        return self.call(context, self.make_msg('create_online_learning',
                                                request_spec=request_spec_p))

    def delete_learning(self, context, cluster_id, job_id, id):
        return self.call(context, self.make_msg('delete_learning',
                                                cluster_id=cluster_id,
                                                job_id=job_id,
                                                id=id))
