# Copyright (c) 2017 OpenStack Foundation
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

import copy
import mock
import webob

from meteos.api.openstack import api_version_request as api_version
from meteos.api.openstack import wsgi as os_wsgi
from meteos.api.v1 import experiments
from meteos import context
from meteos import test


fake_experiment = {'experiment': {
    'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
    'created_at': '2017-2-15 15:40:39',
    'status': 'creating',
    'name': 'test experiment',
    'description': 'test experiment',
    'template_id': '437092518172770c549dabafaf9f81e3766719ce',
    'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
    'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
    'key_name': 'key1',
    'management_network': 'da8863-mZ-461b-9334500'}}

result = {'experiment': {
    'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
    'created_at': '2017-2-15 15:40:39',
    'status': 'creating',
    'display_name': 'test experiment',
    'display_description': 'test experiment',
    'template_id': '437092518172770c549dabafaf9f81e3766719ce',
    'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
    'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
    'key_name': 'key1',
    'management_network': 'da8863-mZ-461b-9334500'}}

fakeexperiment_list = [{
    'id': '6bd3561e9db3175f07299818ddb46a8ac7c72a12',
    'created_at': '2017-2-16 10:16:39',
    'status': 'creating',
    'display_name': 'second test experiment',
    'display_description': 'second test experiment',
    'template_id': 'ec49b237367b5d4b4337abee52260f1169f9b76e',
    'user_id': 'adcf0c50cd87c68abef7c3bb4785a07d3545be5d',
    'project_id': '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832',
    'key_name': 'key2',
    'management_network': 'fada8863-56b7-461b-b647-9334500c25df'},
    fake_experiment['experiment']]

base = 'http://www.meteos.com'
project_id = '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832'
data_id1 = '6bd3561e9db3175f07299818ddb46a8ac7c72a12'
data_id2 = 'e71dbd349248a4187be134e1118cff29fcd6121e'
href11 = base + '/v1.1/123/' + project_id + '/experiments/' + data_id1
href12 = base + '/123/' + project_id + '/experiments/' + data_id1
href21 = base + '/v1.1/123/' + project_id + '/experiments/' + data_id2
href22 = base + '/123/' + project_id + '/experiments/' + data_id2

expect_result = {
    'experiments': [
        {
            'created_at': '2017-2-16 10:16:39',
            'description': 'second test experiment',
            'key_name': 'key2',
            'id': '6bd3561e9db3175f07299818ddb46a8ac7c72a12',
            'links': [
                {
                    'href': href11,
                    'rel': 'self'
                },
                {
                    'href': href12,
                    'rel': 'bookmark'
                }
            ],
            'name': 'second test experiment',
            'template_id': 'ec49b237367b5d4b4337abee52260f1169f9b76e',
            'user_id': 'adcf0c50cd87c68abef7c3bb4785a07d3545be5d',
            'project_id': '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832',
            'management_network': 'fada8863-56b7-461b-b647-9334500c25df',
            'status': 'creating'
        },
        {
            'created_at': '2017-2-15 15:40:39',
            'description': None,
            'key_name': 'key1',
            'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
            'links': [
                {
                    'href': href21,
                    'rel': 'self'
                },
                {
                    'href': href22,
                    'rel': 'bookmark'
                }
            ],
            'name': None,
            'template_id': '437092518172770c549dabafaf9f81e3766719ce',
            'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
            'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
            'management_network': 'da8863-mZ-461b-9334500',
            'status': 'creating'
        }
    ]
}


class FakeTemplate(object):
    def __init__(self):
        self.id = "124567890"
        self.template_id = "1234567890"
        self.status = "available"
        self.job_template_id = "11111111111"


class FakeEngine(object):

    def API(self):
        return self

    def get_experiment(self, context, id):
        mng_net = result['experiment']['management_network']
        del result['experiment']['management_network']
        result['experiment']['neutron_management_network'] = mng_net
        return result['experiment']

    def delete_experiment(self, context, id):
        pass

    def get_all_experiments(self, context, search_opts=None,
                           sort_key='created_at', sort_dir='desc'):
        experiments = copy.deepcopy(fakeexperiment_list)
        mng_net1 = experiments[0]['management_network']
        del experiments[0]['management_network']
        experiments[0]['neutron_management_network'] = mng_net1
        mng_net2 = experiments[1]['management_network']
        del experiments[1]['management_network']
        experiments[1]['neutron_management_network'] = mng_net2
        return experiments

    def get_template(self, context, template_id):
        return FakeTemplate()

    def create_experiment(self, context, display_name, description,
                          template_id, key_name, neutron_management_network):
        return {
            "created_at": "2016-11-30T06:57:28.000000",
            "description": "This is a sample experiment",
            "display_description": "This is a sample experiment",
            "key_name": "test key",
            "id": "9fd54ac9-2da4-4c56-b8f1-fc05fda635b2",
            "name": "sample-experiment",
            "display_name": "sample-experiment",
            "project_id": "475312c52eb941d3ab072fba9271d9c1",
            "status": "creating",
            "template_id": "437092518172770c549dabafaf9f81e3766719ce",
            "user_id": "511c049d52524ba9b14b0ff33867d3b8",
            'neutron_management_network': 'da8863-mZ-461b-9334500'
        }


class FakeRequest(object):
    environ = {"meteos.context": context.get_admin_context()}
    environ['meteos.context'].project_id = ('7a1e6f042f00ac94ec30bb8c6b'
                                            'f5d05b34623832')

    GET = {}

    def __init__(self, version=os_wsgi.DEFAULT_API_VERSION):
        super(FakeRequest, self).__init__()
        self.api_version_request = api_version.APIVersionRequest(version)
        self.application_url = 'http://www.meteos.com/v1.1/123'
        self.params = {}


class ExperimentTestCase(test.TestCase):
    """Test Case for experiment."""
    Controller = experiments.ExperimentController

    def _setup_stubs(self):
        self.stub_out('meteos.engine.API',
                      FakeEngine().API)

    def setUp(self):

        self._setup_stubs()

        super(ExperimentTestCase, self).setUp()
        self.controller = self.Controller()

    def test_show_experiment(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        result = self.controller.show(self.req, id)
        self.assertDictMatch(result, fake_experiment)

    def test_delete_experiment(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        response = self.controller.delete(self.req, id)
        self.assertEqual('202 Accepted', response._status)

    def test_index_experiment(self):
        self.req = FakeRequest()
        result = self.controller.index(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['experiments'][0]['user_id']
        del expect['experiments'][0]['project_id']
        del expect['experiments'][1]['user_id']
        del expect['experiments'][1]['project_id']
        self.assertDictMatch(expect, result)

    def test_detail_experiment(self):
        self.req = FakeRequest()
        result = self.controller.detail(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['experiments'][0]['links']
        del expect['experiments'][1]['links']
        self.assertDictMatch(expect, result)

    def test_create_experiment(self):
        self.req = FakeRequest()
        fake_body = {
            "experiment": {
                "created_at": "2016-11-30T06:54:08.000000",
                "description": "This is a sample experiment",
                "key_name": "test key",
                "id": "da6131ae-783f-45b5-a3eb-56050f0eed46",
                "name": "sample-experiment",
                "display_name": "sample-experiment",
                "project_id": "475312c52eb941d3ab072fba9271d9c1",
                "status": "creating",
                "template_id": "437092518172770c549dabafaf9f81e3766719ce",
                "user_id": "511c049d52524ba9b14b0ff33867d3b8",
                'management_network': 'da8863-mZ-461b-9334500'
            }
        }
        expect = {
            "experiment": {
                "created_at": "2016-11-30T06:57:28.000000",
                "description": "This is a sample experiment",
                "key_name": "test key",
                "id": "9fd54ac9-2da4-4c56-b8f1-fc05fda635b2",
                "name": "sample-experiment",
                "project_id": "475312c52eb941d3ab072fba9271d9c1",
                "status": "creating",
                "template_id": "437092518172770c549dabafaf9f81e3766719ce",
                "user_id": "511c049d52524ba9b14b0ff33867d3b8",
                'management_network': 'da8863-mZ-461b-9334500'
            }
        }
        result = self.controller.create(self.req, fake_body)
        self.assertDictMatch(expect, result)
