# Copyright 2011 OpenStack LLC.
# Copyright 2011 United States Government as represented by the
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

"""
WSGI middleware for OpenStack Learning API v1.
"""

import meteos.api.openstack
from meteos.api.v1 import datasets
from meteos.api.v1 import experiments
from meteos.api.v1 import learnings
from meteos.api.v1 import model_evaluations
from meteos.api.v1 import models
from meteos.api.v1 import templates
from meteos.api import versions


class APIRouter(meteos.api.openstack.APIRouter):
    """Route API requests.

    Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    def _setup_routes(self, mapper, ext_mgr):
        self.resources['versions'] = versions.create_resource()
        mapper.connect("versions", "/",
                       controller=self.resources['versions'],
                       action='index')

        mapper.redirect("", "/")

        self.resources['templates'] = templates.create_resource()
        mapper.resource("template", "templates",
                        controller=self.resources['templates'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

        self.resources['experiments'] = experiments.create_resource()
        mapper.resource("experiment", "experiments",
                        controller=self.resources['experiments'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

        self.resources['learnings'] = learnings.create_resource()
        mapper.resource("learning", "learnings",
                        controller=self.resources['learnings'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

        self.resources['datasets'] = datasets.create_resource()
        mapper.resource("dataset", "datasets",
                        controller=self.resources['datasets'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

        self.resources['models'] = models.create_resource()
        mapper.resource("model", "models",
                        controller=self.resources['models'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

        self.resources['model_evaluations'] = model_evaluations.create_resource()
        mapper.resource("model_evaluations", "model_evaluations",
                        controller=self.resources['model_evaluations'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})
