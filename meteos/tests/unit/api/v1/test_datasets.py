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
from meteos.api.v1 import datasets
from meteos import context
from meteos import test


fake_dataset = {'dataset': {
    'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
    'created_at': '2017-2-15 15:40:39',
    'status': 'active',
    'name': 'test dataset',
    'description': 'test dataset',
    'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
    'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
    'source_dataset_url': 'swift://meteos/linear_data1.txt',
    'head': 'dataset head',
    'stderr': 'No error'}}

result = {'dataset': {
    'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
    'created_at': '2017-2-15 15:40:39',
    'status': 'active',
    'display_name': 'test dataset',
    'display_description': 'test dataset',
    'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
    'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
    'head': 'dataset head',
    'stderr': 'No error'}}

fakedataset_list = [{
    'id': '6bd3561e9db3175f07299818ddb46a8ac7c72a12',
    'created_at': '2017-2-16 10:16:39',
    'status': 'active',
    'display_name': 'second test dataset',
    'display_description': 'second test dataset',
    'user_id': 'adcf0c50cd87c68abef7c3bb4785a07d3545be5d',
    'project_id': '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832',
    'head': '0x3 0x4 0x5',
    'source_dataset_url': 'swift://meteos/linear_data2.txt',
    'stderr': 'No error'}, fake_dataset['dataset']]

base = 'http://www.meteos.com'
project_id = '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832'
data_id1 = '6bd3561e9db3175f07299818ddb46a8ac7c72a12'
data_id2 = 'e71dbd349248a4187be134e1118cff29fcd6121e'
href11 = base + '/v1.1/123/' + project_id + '/datasets/' + data_id1
href12 = base + '/123/' + project_id + '/datasets/' + data_id1
href21 = base + '/v1.1/123/' + project_id + '/datasets/' + data_id2
href22 = base + '/123/' + project_id + '/datasets/' + data_id2

expect_result = {
    'datasets': [
        {
            'created_at': '2017-2-16 10:16:39',
            'description': 'second test dataset',
            'head': '0x3 0x4 0x5',
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
            'name': 'second test dataset',
            'user_id': 'adcf0c50cd87c68abef7c3bb4785a07d3545be5d',
            'project_id': '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832',
            'stderr': 'No error',
            'source_dataset_url': 'swift://meteos/linear_data2.txt',
            'status': 'active'
        },
        {
            'created_at': '2017-2-15 15:40:39',
            'description': None,
            'head': 'dataset head',
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
            'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
            'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
            'source_dataset_url': 'swift://meteos/linear_data1.txt',
            'stderr': 'No error',
            'status': 'active'
        }
    ]
}


class FakeExperiment(object):
    def __init__(self):
        self.status = "available"
        self.template_id = "1234567890"
        self.cluster_id = "0987654321"


class FakeTemplate(object):
    def __init__(self):
        self.id = "124567890"
        self.template_id = "1234567890"
        self.job_template_id = "11111111111"


class FakeEngine(object):

    def API(self):
        return self

    def get_dataset(self, context, id):
        return result['dataset']

    def delete_dataset(self, context, id):
        pass

    def get_all_datasets(self, context, search_opts=None,
                         sort_key='created_at', sort_dir='desc'):
        return fakedataset_list

    def get_experiment(self, context, experiment_id):
        return FakeExperiment()

    def get_template(self, context, template_id):
        return FakeTemplate()

    def create_dataset(self, context, display_name, description,
                       method, url, params, template_id, job_id,
                       experiment_id, cluster_id, swift_tenant,
                       swift_username, swift_password, precent_train,
                       percent_test):
        return {
            "created_at": "2016-11-30T06:57:28.000000",
            "description": "This is a sample dataset",
            "display_description": "This is a sample dataset",
            "head": "null",
            "id": "9fd54ac9-2da4-4c56-b8f1-fc05fda635b2",
            "name": "sample-data",
            "display_name": "sample-data",
            "project_id": "475312c52eb941d3ab072fba9271d9c1",
            "status": "creating",
            "stderr": "null",
            "user_id": "511c049d52524ba9b14b0ff33867d3b8"
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


class DatasetsTestCase(test.TestCase):
    """Test Case for datasets."""
    Controller = datasets.DatasetController

    def _setup_stubs(self):
        self.stub_out('meteos.engine.API',
                      FakeEngine().API)

    def setUp(self):

        self._setup_stubs()

        super(DatasetsTestCase, self).setUp()
        self.controller = self.Controller()

    def test_show_dataset(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        result = self.controller.show(self.req, id)
        expected_server = copy.deepcopy(fake_dataset)
        del expected_server['dataset']['source_dataset_url']
        self.assertDictMatch(result, expected_server)

    def test_delete_dataset(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        response = self.controller.delete(self.req, id)
        self.assertEqual('202 Accepted', response._status)

    def test_index_dataset(self):
        self.req = FakeRequest()
        result = self.controller.index(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['datasets'][0]['user_id']
        del expect['datasets'][0]['project_id']
        del expect['datasets'][1]['user_id']
        del expect['datasets'][1]['project_id']
        del expect['datasets'][0]['stderr']
        del expect['datasets'][1]['stderr']
        self.assertDictMatch(expect, result)

    def test_detail_dataset(self):
        self.req = FakeRequest()
        result = self.controller.detail(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['datasets'][0]['links']
        del expect['datasets'][1]['links']
        del expect['datasets'][0]['source_dataset_url']
        del expect['datasets'][1]['source_dataset_url']
        self.assertDictMatch(expect, result)

    def test_create_dataset(self):
        self.req = FakeRequest()
        fake_body = {
            "dataset": {
                "created_at": "2016-11-30T06:54:08.000000",
                "description": "This is a sample dataset",
                "head": "null",
                "id": "da6131ae-783f-45b5-a3eb-56050f0eed46",
                "name": "sample-data",
                "display_name": "sample-data",
                "project_id": "475312c52eb941d3ab072fba9271d9c1",
                "status": "creating",
                "stderr": "null",
                "user_id": "511c049d52524ba9b14b0ff33867d3b8",
                "experiment_id": "1330ce647de2727eab719ec8a0e740ffa05bfc63"
            }
        }
        expect = {
            "dataset": {
                "created_at": "2016-11-30T06:57:28.000000",
                "description": "This is a sample dataset",
                "head": "null",
                "id": "9fd54ac9-2da4-4c56-b8f1-fc05fda635b2",
                "name": "sample-data",
                "project_id": "475312c52eb941d3ab072fba9271d9c1",
                "status": "creating",
                "stderr": "null",
                "user_id": "511c049d52524ba9b14b0ff33867d3b8"
            }
        }
        result = self.controller.create(self.req, fake_body)
        self.assertDictMatch(expect, result)
