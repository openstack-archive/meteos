# Copyright (c) 2011 OpenStack Foundation
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

from meteos.api.openstack import api_version_request as api_version
from meteos.api.openstack import wsgi as os_wsgi
from meteos.api.v1 import datasets
from meteos import context
from meteos import test

from meteos.tests.unit import matchers


fake_dataset = {'dataset': {
                            'id': 'e71dbd349248a4187be134e1118cff29fcd6121e',
                            'created_at': '2017-2-15 15:40:39',
                            'status': 'active',
                            'name': 'test dataset',
                            'description': 'test dataset',
                            'user_id': '085058bfb20429e669c0e92b599a96d269032f1f',
                            'project_id': 'b462a3b8cd0ccbf374dd140315ec1c431a8546be',
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


class FakeEngine(object):

    def API(self):
        return self

    def get_dataset(self, context, id):
        return result['dataset']


class FakeRequest(object):
    environ = {"meteos.context": context.get_admin_context()}
    GET = {}

    def __init__(self, version=os_wsgi.DEFAULT_API_VERSION):
        super(FakeRequest, self).__init__()
        self.api_version_request = api_version.APIVersionRequest(version)


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
        id = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        self.req = FakeRequest()
        result = self.controller.show(self.req, id)
        expected_server = fake_dataset
        self.assertThat(result, matchers.DictMatches(expected_server))
