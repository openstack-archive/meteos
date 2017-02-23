# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
SQLAlchemy models for Meteos data.
"""

from oslo_config import cfg
from oslo_db.sqlalchemy import models
from oslo_log import log
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DateTime, Boolean, Text

from meteos.common import constants

CONF = cfg.CONF
BASE = declarative_base()

LOG = log.getLogger(__name__)


class MeteosBase(models.ModelBase,
                 models.TimestampMixin,
                 models.SoftDeleteMixin):

    """Base class for Meteos Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    metadata = None

    def to_dict(self):
        model_dict = {}
        for k, v in self.items():
            if not issubclass(type(v), MeteosBase):
                model_dict[k] = v
        return model_dict

    def soft_delete(self, session, update_status=False,
                    status_field_name='status'):
        """Mark this object as deleted."""
        if update_status:
            setattr(self, status_field_name, constants.STATUS_DELETED)

        return super(MeteosBase, self).soft_delete(session)


class Service(BASE, MeteosBase):

    """Represents a running service on a host."""

    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    host = Column(String(255))  # , ForeignKey('hosts.id'))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)


class Template(BASE, MeteosBase):

    __tablename__ = 'templates'
    id = Column(String(36), primary_key=True)
    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))

    display_name = Column(String(255))
    display_description = Column(String(255))

    sahara_image_id = Column(String(36))
    master_node_id = Column(String(36))
    slave_node_id = Column(String(36))
    binary_data_id = Column(String(36))
    binary_id = Column(String(36))
    cluster_template_id = Column(String(36))
    job_template_id = Column(String(36))

    master_flavor_id = Column(String(36))
    worker_flavor_id = Column(String(36))
    master_nodes_num = Column(Integer)
    worker_nodes_num = Column(Integer)
    floating_ip_pool = Column(String(36))
    spark_version = Column(String(36))

    status = Column(String(255))
    launched_at = Column(DateTime)


class Experiment(BASE, MeteosBase):

    __tablename__ = 'experiments'
    id = Column(String(36), primary_key=True)
    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))

    display_name = Column(String(255))
    display_description = Column(String(255))
    template_id = Column(String(36))
    cluster_id = Column(String(36))
    key_name = Column(String(36))
    neutron_management_network = Column(String(36))

    status = Column(String(255))
    launched_at = Column(DateTime)


class Dataset(BASE, MeteosBase):

    __tablename__ = 'data_sets'
    id = Column(String(36), primary_key=True)
    source_dataset_url = Column(String(255))
    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))
    experiment_id = Column(String(36))
    cluster_id = Column(String(36))
    job_id = Column(String(36))

    display_name = Column(String(255))
    display_description = Column(String(255))

    container_name = Column(String(255))
    object_name = Column(String(255))
    user = Column(String(255))
    password = Column(String(255))

    status = Column(String(255))
    launched_at = Column(DateTime)

    head = Column(Text)
    stderr = Column(Text)


class Model(BASE, MeteosBase):

    __tablename__ = 'models'
    id = Column(String(36), primary_key=True)
    source_dataset_url = Column(String(255))
    dataset_format = Column(String(255))
    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))
    experiment_id = Column(String(36))
    cluster_id = Column(String(36))
    job_id = Column(String(36))

    display_name = Column(String(255))
    display_description = Column(String(255))

    model_type = Column(String(255))
    model_params = Column(Text)

    status = Column(String(255))
    launched_at = Column(DateTime)

    stdout = Column(Text)
    stderr = Column(Text)


class Model_Evaluation(BASE, MeteosBase):

    __tablename__ = 'model_evaluations'
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36))
    model_type = Column(String(255))
    source_dataset_url = Column(String(255))
    dataset_format = Column(String(255))
    cluster_id = Column(String(36))
    job_id = Column(String(36))

    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))

    display_name = Column(String(255))

    status = Column(String(255))
    launched_at = Column(DateTime)

    stdout = Column(Text)
    stderr = Column(Text)


class Learning(BASE, MeteosBase):

    __tablename__ = 'learnings'
    id = Column(String(36), primary_key=True)
    model_id = Column(String(36))
    model_type = Column(String(255))
    deleted = Column(String(36), default='False')
    user_id = Column(String(255))
    project_id = Column(String(255))
    experiment_id = Column(String(36))
    cluster_id = Column(String(36))
    job_id = Column(String(36))

    display_name = Column(String(255))
    display_description = Column(String(255))

    method = Column(String(255))
    args = Column(String(255))

    status = Column(String(255))
    launched_at = Column(DateTime)

    stdout = Column(Text)
    stderr = Column(Text)
