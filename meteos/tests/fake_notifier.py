# Copyright 2014 Red Hat, Inc.
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

import collections
import functools

import oslo_messaging as messaging
from oslo_serialization import jsonutils

from meteos import rpc

NOTIFICATIONS = []


def reset():
    del NOTIFICATIONS[:]


FakeMessage = collections.namedtuple(
    'Message',
    ['publisher_id', 'priority', 'event_type', 'payload'],
)


class FakeNotifier(object):

    def __init__(self, transport, publisher_id, serializer=None):
        self.transport = transport
        self.publisher_id = publisher_id
        for priority in ['debug', 'info', 'warn', 'error', 'critical']:
            setattr(self, priority,
                    functools.partial(self._notify, priority.upper()))
        self._serializer = serializer or messaging.serializer.NoOpSerializer()

    def prepare(self, publisher_id=None):
        if publisher_id is None:
            publisher_id = self.publisher_id
        return self.__class__(self.transport, publisher_id, self._serializer)

    def _notify(self, priority, ctxt, event_type, payload):
        payload = self._serializer.serialize_entity(ctxt, payload)
        # NOTE(sileht): simulate the kombu serializer
        # this permit to raising an exception if something have not
        # been serialized correctly
        jsonutils.to_primitive(payload)
        msg = dict(publisher_id=self.publisher_id,
                   priority=priority,
                   event_type=event_type,
                   payload=payload)
        NOTIFICATIONS.append(msg)


def stub_notifier(testcase):
    testcase.mock_object(messaging, 'Notifier', FakeNotifier)
    if rpc.NOTIFIER:
        serializer = getattr(rpc.NOTIFIER, '_serializer', None)
        testcase.mock_object(rpc, 'NOTIFIER',
                             FakeNotifier(rpc.NOTIFIER.transport,
                                          rpc.NOTIFIER.publisher_id,
                                          serializer=serializer))
