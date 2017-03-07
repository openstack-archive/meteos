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
from meteos.api.v1 import learnings
from meteos import context
from meteos import test


fake_learning = {"learning": {
    "id": "e71dbd349248a4187be134e1118cff29fcd6121e",
    "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
    "description": "This is a sample job",
    "name": "example-learning-job",
    "method": "predict",
    "status": "creating",
    "stdout": "1.0",
    "stderr": "none",
    "created_at": "2016-11-30T07:16:17.000000",
    "user_id": "6bd3561e9db3175f07299818ddb46a8ac7c72a12",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "model_type": "LinearRegression",
    "model_id": "27032fe5-cb88-42bc-a753-f6a1359d629e"}}

result = {"learning": {
    "id": "e71dbd349248a4187be134e1118cff29fcd6121e",
    "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
    "display_description": "This is a sample job",
    "display_name": "example-learning-job",
    "learning_id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
    "method": "predict",
    "status": "creating",
    "stdout": "1.0",
    "stderr": "none",
    "created_at": "2016-11-30T07:16:17.000000",
    "user_id": "6bd3561e9db3175f07299818ddb46a8ac7c72a12",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "type": "LinearRegression",
    "model_id": "27032fe5-cb88-42bc-a753-f6a1359d629e"}}

fakelearning_list = [{
    "id": "bd14f7f23e01968aba70f0025b85dc15f110abc1",
    "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
    "description": "This is second sample job",
    "name": "second example-learning-job",
    "learning_id": "c733d48580da2d8ac99a382fab0785becc24cdbb",
    "method": "predict",
    "status": "creating",
    "stdout": "1.0",
    "stderr": "none",
    "created_at": "2016-11-30T07:16:17.000000",
    "user_id": "6bd3561e9db3175f07299818ddb46a8ac7c72a12",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "model_type": "LinearRegression",
    "model_id": "98b28d675d3e2059e4c0d457dc42166aef286d27"},
    fake_learning['learning']]

base = 'http://www.meteos.com'
project_id = '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832'
user_id1 = 'bd14f7f23e01968aba70f0025b85dc15f110abc1'
user_id2 = 'e71dbd349248a4187be134e1118cff29fcd6121e'
href11 = base + '/v1.1/123/' + project_id + '/learnings/' + user_id1
href12 = base + '/123/' + project_id + '/learnings/' + user_id1
href21 = base + '/v1.1/123/' + project_id + '/learnings/' + user_id2
href22 = base + '/123/' + project_id + '/learnings/' + user_id2

expect_result = {
    'learnings': [
        {
            "id": "bd14f7f23e01968aba70f0025b85dc15f110abc1",
            "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
            "description": "This is second sample job",
            "name": "second example-learning-job",
            "method": "predict",
            "status": "creating",
            "stdout": "1.0",
            "stderr": "none",
            "created_at": "2016-11-30T07:16:17.000000",
            "user_id": "6bd3561e9db3175f07299818ddb46a8ac7c72a12",
            "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
            "model_id": "98b28d675d3e2059e4c0d457dc42166aef286d27",
            "type": "LinearRegression",
            'links': [
                {
                    'href': href11,
                    'rel': 'self'
                },
                {
                    'href': href12,
                    'rel': 'bookmark'
                }
            ]
        },
        {
            "id": "e71dbd349248a4187be134e1118cff29fcd6121e",
            "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
            "description": "This is a sample job",
            "name": "example-learning-job",
            "method": "predict",
            "status": "creating",
            "stdout": "1.0",
            "stderr": "none",
            "created_at": "2016-11-30T07:16:17.000000",
            "user_id": "6bd3561e9db3175f07299818ddb46a8ac7c72a12",
            "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
            "model_id": "27032fe5-cb88-42bc-a753-f6a1359d629e",
            "type": "LinearRegression",
            'links': [
                {
                    'href': href21,
                    'rel': 'self'
                },
                {
                    'href': href22,
                    'rel': 'bookmark'
                }
            ]
        }
    ]
}


class FakeExperiment(object):
    def __init__(self):
        self.id = "124567890"
        self.template_id = "1234567890"
        self.status = 'available'
        self.cluster_id = 'e1644ac1d86d4836ca26e89258b5aa6e93b9f770'


class FakeTemplate(object):
    def __init__(self):
        self.id = "124567890"
        self.template_id = "1234567890"
        self.job_template_id = '1234567890'


class FakeModel(object):
    def __init__(self):
        self.status = 'available'
        self.experiment_id = '124567890'
        self.model_type = "LinearRegression"
        self.dataset_format = "csv"
        self.experiment_id = '124567890'


class FakeEngine(object):

    def API(self):
        return self

    def get_learning(self, context, id):
        return result['learning']

    def delete_learning(self, context, id):
        pass

    def get_all_learnings(self, context, search_opts=None,
                          sort_key='created_at', sort_dir='desc'):
        learnings = copy.deepcopy(fakelearning_list)
        name = learnings[0]['name']
        del learnings[0]['name']
        learnings[0]['display_name'] = name
        description = learnings[0]['description']
        del learnings[0]['description']
        learnings[0]['display_description'] = description
        name = learnings[1]['name']
        del learnings[1]['name']
        learnings[1]['display_name'] = name
        description = learnings[1]['description']
        del learnings[1]['description']
        learnings[1]['display_description'] = description
        return learnings

    def get_experiment(self, context, experiment_id):
        return FakeExperiment()

    def get_template(self, context, template_id):
        return FakeTemplate()

    def get_model(self, context, model_id):
        return FakeModel()

    def create_learning(self, context, name, description, status, model_id,
                        method, model_type, dataset_format, args, template_id,
                        job_template_id, experiment_id, cluster_id):
        return {
            "id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
            "created_at": "2016-11-30T07:16:17.000000",
            "status": "creating",
            "display_name": "example-learning-job",
            "display_description": "This is a sample job",
            "user_id": "e6f8dbb55fc8fccb18f4ccb5ed5723a2efc3b025",
            "project_id": "bd14f7f23e01968aba70f0025b85dc15f110abc1",
            "stdout": "2",
            "stderr": "none",
            "method": "predict",
            "model_id": "27032fe5-cb88-42bc-a753-f6a1359d629e",
            "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA="
        }


class FakeRequest(object):
    environ = {"meteos.context": context.get_admin_context()}
    environ['meteos.context'].project_id = ('7a1e6f042f00ac94ec30bb8c6bf5d'
                                            '05b34623832')

    GET = {}

    def __init__(self, version=os_wsgi.DEFAULT_API_VERSION):
        super(FakeRequest, self).__init__()
        self.api_version_request = api_version.APIVersionRequest(version)
        self.application_url = 'http://www.meteos.com/v1.1/123'
        self.params = {}


class LearningTestCase(test.TestCase):
    """Test Case for learning."""
    Controller = learnings.LearningController

    def _setup_stubs(self):
        self.stub_out('meteos.engine.API',
                      FakeEngine().API)

    def setUp(self):

        self._setup_stubs()

        super(LearningTestCase, self).setUp()
        self.controller = self.Controller()

    def test_show_learning(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        result = self.controller.show(self.req, id)
        expected = copy.deepcopy(fake_learning)
        del expected['learning']['model_type']
        self.assertDictMatch(result, expected)

    def test_delete_learning(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        response = self.controller.delete(self.req, id)
        self.assertEqual('202 Accepted', response._status)

    def test_index_learning(self):
        self.req = FakeRequest()
        result = self.controller.index(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['learnings'][0]['user_id']
        del expect['learnings'][0]['project_id']
        del expect['learnings'][1]['user_id']
        del expect['learnings'][1]['project_id']
        del expect['learnings'][0]['method']
        del expect['learnings'][1]['method']
        del expect['learnings'][0]['stderr']
        del expect['learnings'][1]['stderr']
        self.assertDictMatch(expect, result)

    def test_detail_learning(self):
        self.req = FakeRequest()
        result = self.controller.detail(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['learnings'][0]['links']
        del expect['learnings'][1]['links']
        del expect['learnings'][0]['type']
        del expect['learnings'][1]['type']
        self.assertDictMatch(expect, result)

    def test_create_learning(self):
        self.req = FakeRequest()
        fake_body = {
            "learning": {
                "args": "MTEsMTAsMjAxNiwyLDAsNjcsODA=",
                "display_description": "This is a sample job",
                "display_name": "example-learning-job",
                "learning_id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
                "method": "predict",
                "model_id": "27032fe5-cb88-42bc-a753-f6a1359d629e"
            }
        }
        expect = {
            "learning": {
                'status': 'creating',
                'model_id': '27032fe5-cb88-42bc-a753-f6a1359d629e',
                'description': 'This is a sample job',
                'stdout': '2',
                'args': 'MTEsMTAsMjAxNiwyLDAsNjcsODA=',
                'id': 'b45fb6a9-6f93-4e4b-93ec-0b128927b62d',
                'user_id': 'e6f8dbb55fc8fccb18f4ccb5ed5723a2efc3b025',
                'name': 'example-learning-job',
                'created_at': '2016-11-30T07:16:17.000000',
                'stderr': 'none',
                'project_id': 'bd14f7f23e01968aba70f0025b85dc15f110abc1',
                'method': 'predict'
            }
        }
        result = self.controller.create(self.req, fake_body)
        self.assertDictMatch(expect, result)
