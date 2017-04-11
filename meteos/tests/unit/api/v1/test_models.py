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
from meteos.api.v1 import models
from meteos import context
from meteos import test


fake_model = {"model": {
    "created_at": "2016-11-30T07:03:33.000000",
    "description": 'null',
    "id": "c8707239-ae83-40c8-9d1b-273981ba209d",
    "name": 'null',
    "params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "status": "available",
    "source_dataset_url": "swift://meteos/linear_data.txt",
    "stderr": "",
    "experiment_id": "2ddd9a75b6fc888e0842589255",
    "stdout": "",
    "type": "LinearRegression",
    "user_id": "511c049d52524ba9b14b0ff33867d3b8"}}

result = {"model": {
    "created_at": "2016-11-30T07:03:33.000000",
    "description": 'null',
    "id": "c8707239-ae83-40c8-9d1b-273981ba209d",
    "name": 'null',
    "params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "experiment_id": "2ddd9a75b6fc888e0842589255",
    "status": "available",
    "stderr": "",
    "stdout": "",
    "type": "LinearRegression",
    "user_id": "511c049d52524ba9b14b0ff33867d3b8"}}

fakemodel_list = [fake_model['model'], {
    "id": "8227e5ff9fa099b529b906cecfe5e2a1c8c86214",
    "description": 'null',
    "name": "null",
    "created_at": "2016-11-30T07:03:33.000000",
    "experiment_id": "aaaa-bbbb-cccc-eeee-dddd",
    "params": "aaaabbbbbccccdddddb25zJzogMSwgJ2Rlc23V0cHV0JzowfQ==",
    "type": "LinearRegression",
    "user_id": "892f96b98daf797fdbfcdd559f69d43e322590f1",
    "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
    "source_dataset_url": "swift://meteos/linear_data2.txt",
    "status": "available",
    "stdout": "",
    "swift_password": "nova",
    "stderr": "",
    "swift_tenant": "demo",
    "swift_username": "demo"}]

base = 'http://www.meteos.com'
project_id = '7a1e6f042f00ac94ec30bb8c6bf5d05b34623832'
model_id1 = 'c8707239-ae83-40c8-9d1b-273981ba209d'
model_id2 = '8227e5ff9fa099b529b906cecfe5e2a1c8c86214'
href11 = base + '/v1.1/123/' + project_id + '/models/' + model_id1
href12 = base + '/123/' + project_id + '/models/' + model_id1
href21 = base + '/v1.1/123/' + project_id + '/models/' + model_id2
href22 = base + '/123/' + project_id + '/models/' + model_id2

expect_result = {
    'models': [
        {
            "id": "c8707239-ae83-40c8-9d1b-273981ba209d",
            "experiment_id": "2ddd9a75b6fc888e0842589255",
            "params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
            "type": "LinearRegression",
            "created_at": "2016-11-30T07:03:33.000000",
            "source_dataset_url": "swift://meteos/linear_data.txt",
            "user_id": "511c049d52524ba9b14b0ff33867d3b8",
            "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
            "status": "available",
            "description": 'null',
            "name": "null",
            "stdout": "",
            "stderr": "",
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
            "id": "8227e5ff9fa099b529b906cecfe5e2a1c8c86214",
            "experiment_id": "aaaa-bbbb-cccc-eeee-dddd",
            "params": "aaaabbbbbccccdddddb25zJzogMSwgJ2Rlc23V0cHV0JzowfQ==",
            "type": "LinearRegression",
            "source_dataset_url": "swift://meteos/linear_data2.txt",
            "status": "available",
            "created_at": "2016-11-30T07:03:33.000000",
            "user_id": "892f96b98daf797fdbfcdd559f69d43e322590f1",
            "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
            "name": "null",
            "description": 'null',
            "stdout": "",
            "stderr": "",
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


class FakeTemplate(object):
    def __init__(self):
        self.id = "124567890"
        self.template_id = "1234567890"
        self.job_template_id = "11111111111"


class FakeExperiment(object):
    def __init__(self):
        self.id = "124567890"
        self.status = 'available'
        self.template_id = "1234567890"
        self.cluster_id = "11111111111"


class FakeModel(object):
    def __init__(self, **entries):
        self.add_entries(**entries)

    def add_entries(self, **entries):
        for key, value in entries.items():
            if type(value) is dict:
                self.__dict__[key] = FakeModel(**value)
            else:
                self.__dict__[key] = value

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key):
        return getattr(self, key)


class FakeEngine(object):

    def API(self):
        return self

    def get_model(self, context, id):
        model = copy.deepcopy(result['model'])
        desc = model.get("description")
        del model['description']
        model['display_description'] = desc
        name = model.get("name")
        del model['name']
        model['display_name'] = name
        params = model.get("params")
        del model['params']
        model['model_params'] = params
        ttype = model.get("type")
        del model['type']
        model['model_type'] = ttype

        fake_model = FakeModel(**model)
        fake_model.dataset_format = 'fake_format'
        fake_model.job_template_id = '111111'
        fake_model.cluster_id = '22222'
        if id == 'Ia1a0a6bdf0707ccf96a02dec36f94f0c68b165fc':
            fake_model.status = 'active'
        return fake_model

    def delete_model(self, context, id):
        pass

    def get_all_models(self, context, search_opts=None,
                       sort_key='created_at', sort_dir='desc'):
        fs = copy.deepcopy(fakemodel_list)
        for flist in fs:
            desc = flist.get("description")
            del flist['description']
            flist['display_description'] = desc
            name = flist.get("name")
            del flist['name']
            flist['display_name'] = name
            params = flist.get("params")
            del flist['params']
            flist['model_params'] = params
            ttype = flist.get("type")
            del flist['type']
            flist['model_type'] = ttype
        return fs

    def get_template(self, context, template_id):
        return FakeTemplate()

    def get_experiment(self, context, model_id):
        return FakeExperiment()

    def create_model(self, context, display_name, description,
                     source_dataset_url, dataset_format, model_type,
                     model_params, template_id, job_template_id,
                     experiment_id, cluster_id, swift_tenant,
                     swift_username, swift_password):
        return {
            "id": "f78676d89eebe539bdc4a498f7572624cc65afb3",
            "status": 'active',
            "display_name": "null",
            "display_description": 'null',
            "user_id": "892f96b98daf797fdbfcdd559f69d43e322590f1",
            "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
            "experiment_id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
            "model_params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
            "model_type": "LinearRegression",
            "source_dataset_url": "swift://meteos/linear_data.txt",
            "created_at": "2016-11-30T07:03:33.000000",
            "stdout": "null",
            "stderr": "null"
        }

    def load_model(self, context, id, dataset_format, model_type,
                   job_template_id, experiment_id, cluster_id):
        pass

    def unload_model(self, context, id, dataset_format, model_type,
                     job_template_id, experiment_id, cluster_id):
        pass

    def recreate_model(self, context, id, source_dataset_url, dataset_format,
                       model_type, model_params, template_id,
                       job_template_id, experiment_id, cluster_id,
                       swift_tenant, swift_username, swift_password):
        pass


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


class ModelTestCase(test.TestCase):
    """Test Case for model."""
    Controller = models.ModelController

    def _setup_stubs(self):
        self.stub_out('meteos.engine.API',
                      FakeEngine().API)

    def setUp(self):

        self._setup_stubs()

        super(ModelTestCase, self).setUp()
        self.controller = self.Controller()

    def test_show_model(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        result = self.controller.show(self.req, id)
        expected = copy.deepcopy(fake_model)
        del expected['model']['source_dataset_url']
        self.assertDictMatch(result, expected)

    def test_delete_model(self):
        id = 'e71dbd349248a4187be134e1118cff29fcd6121e'
        self.req = FakeRequest()
        response = self.controller.delete(self.req, id)
        self.assertEqual('202 Accepted', response._status)

    def test_index_model(self):
        self.req = FakeRequest()
        result = self.controller.index(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['models'][0]['user_id']
        del expect['models'][0]['project_id']
        del expect['models'][1]['user_id']
        del expect['models'][1]['project_id']
        del expect['models'][0]['stderr']
        del expect['models'][1]['stderr']
        self.assertDictMatch(expect, result)

    def test_detail_model(self):
        self.req = FakeRequest()
        result = self.controller.detail(self.req)
        expect = copy.deepcopy(expect_result)
        del expect['models'][0]['links']
        del expect['models'][1]['links']
        del expect['models'][0]['source_dataset_url']
        del expect['models'][1]['source_dataset_url']
        self.assertDictMatch(expect, result)

    def test_create_model(self):
        self.req = FakeRequest()
        fake_body = {
            "model": {
                "experiment_id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
                "model_params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
                "model_type": "LinearRegression",
                "source_dataset_url": "swift://meteos/linear_data.txt",
                "swift_password": "nova",
                "swift_tenant": "demo",
                "swift_username": "demo"
            }
        }
        expect = {
            "model": {
                "status": 'active',
                "description": 'null',
                "stdout": 'null',
                "id": "f78676d89eebe539bdc4a498f7572624cc65afb3",
                "user_id": "892f96b98daf797fdbfcdd559f69d43e322590f1",
                "project_id": "7a1e6f042f00ac94ec30bb8c6bf5d05b34623832",
                "name": "null",
                "stderr": 'null',
                "created_at": "2016-11-30T07:03:33.000000",
                "experiment_id": "b45fb6a9-6f93-4e4b-93ec-0b128927b62d",
                "params": "eydudW1JdGVyYXRpb25zJzogMSwgJ2Rlc2lyZWRfb3V0cHV0JzowfQ==",
                "type": "LinearRegression",
            }
        }
        result = self.controller.create(self.req, fake_body)
        self.assertDictMatch(expect, result)

    def test_model_load(self):
        mid = "f78676d89eebe539bdc4a498f7572624cc65afb3"
        self.req = FakeRequest()
        body = {}
        result = self.controller.load(self.req, mid, body)
        expect = {'model': {'id': mid}}
        self.assertDictMatch(expect, result)

    def test_model_unload(self):
        mid = "Ia1a0a6bdf0707ccf96a02dec36f94f0c68b165fc"
        self.req = FakeRequest()
        body = {}
        result = self.controller.unload(self.req, mid, body)
        expect = {'model': {'id': mid}}
        self.assertDictMatch(expect, result)

    def test_model_recreate(self):
        mid = "Ia1a0a6bdf0707ccf96a02dec36f94f0c68b165fc"
        self.req = FakeRequest()
        body = {}
        result = self.controller.unload(self.req, mid, body)
        expect = {'model': {'id': mid}}
        self.assertDictMatch(expect, result)
