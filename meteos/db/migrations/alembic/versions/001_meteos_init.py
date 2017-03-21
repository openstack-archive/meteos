# Copyright 2012 OpenStack LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""meteos_init

Revision ID: 001
Revises: None
Create Date: 2016-09-27 17:51:57.077203

"""

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None

from alembic import op
from oslo_log import log
from sqlalchemy import Boolean, Column, DateTime, Text
from sqlalchemy import Integer, MetaData, String, Table


LOG = log.getLogger(__name__)


def upgrade():
    migrate_engine = op.get_bind().engine
    meta = MetaData()
    meta.bind = migrate_engine

    services = Table(
        'services', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', Integer, default=0),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('host', String(length=255)),
        Column('binary', String(length=255)),
        Column('topic', String(length=255)),
        Column('report_count', Integer, nullable=False),
        Column('disabled', Boolean),
        Column('availability_zone', String(length=255)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    templates = Table(
        'templates', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('display_description', String(length=255)),
        Column('sahara_image_id', String(length=36)),
        Column('master_node_id', String(length=36)),
        Column('slave_node_id', String(length=36)),
        Column('binary_data_id', String(length=36)),
        Column('binary_id', String(length=36)),
        Column('cluster_template_id', String(length=36)),
        Column('job_template_id', String(length=36)),
        Column('master_flavor_id', String(length=36)),
        Column('master_nodes_num', Integer),
        Column('worker_flavor_id', String(length=36)),
        Column('worker_nodes_num', Integer),
        Column('spark_version', String(length=36)),
        Column('floating_ip_pool', String(length=36)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    experiments = Table(
        'experiments', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('display_description', String(length=255)),
        Column('template_id', String(length=36)),
        Column('cluster_id', String(length=36)),
        Column('key_name', String(length=36)),
        Column('neutron_management_network', String(length=36)),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    data_sets = Table(
        'data_sets', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('source_dataset_url', String(length=255)),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('experiment_id', String(length=36)),
        Column('cluster_id', String(length=36)),
        Column('job_id', String(length=36)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('display_description', String(length=255)),
        Column('container_name', String(length=255)),
        Column('object_name', String(length=255)),
        Column('user', String(length=255)),
        Column('password', String(length=255)),
        Column('head', Text),
        Column('stderr', Text),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    models = Table(
        'models', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('source_dataset_url', String(length=255)),
        Column('dataset_format', String(length=255)),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('experiment_id', String(length=36)),
        Column('cluster_id', String(length=36)),
        Column('job_id', String(length=36)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('display_description', String(length=255)),
        Column('model_type', String(length=255)),
        Column('model_params', Text),
        Column('stdout', Text),
        Column('stderr', Text),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    model_evaluations = Table(
        'model_evaluations', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('model_id', String(length=36)),
        Column('model_type', String(length=255)),
        Column('source_dataset_url', String(length=255)),
        Column('dataset_format', String(length=255)),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('cluster_id', String(length=36)),
        Column('job_id', String(length=36)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('stdout', Text),
        Column('stderr', Text),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    learnings = Table(
        'learnings', meta,
        Column('created_at', DateTime),
        Column('updated_at', DateTime),
        Column('deleted_at', DateTime),
        Column('deleted', String(length=36), default='False'),
        Column('id', String(length=36), primary_key=True, nullable=False),
        Column('model_id', String(length=36)),
        Column('model_type', String(length=255)),
        Column('user_id', String(length=255)),
        Column('project_id', String(length=255)),
        Column('experiment_id', String(length=36)),
        Column('cluster_id', String(length=36)),
        Column('job_id', String(length=36)),
        Column('status', String(length=255)),
        Column('scheduled_at', DateTime),
        Column('launched_at', DateTime),
        Column('terminated_at', DateTime),
        Column('display_name', String(length=255)),
        Column('display_description', String(length=255)),
        Column('method', String(length=255)),
        Column('args', String(length=255)),
        Column('stdout', Text),
        Column('stderr', Text),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    # create all tables
    # Take care on create order for those with FK dependencies
    tables = [services,
              templates,
              learnings,
              experiments,
              data_sets,
              models,
              model_evaluations]

    for table in tables:
        if not table.exists():
            try:
                table.create()
            except Exception:
                LOG.info(repr(table))
                LOG.exception('Exception while creating table.')
                raise

    if migrate_engine.name == "mysql":
        tables = ["services", "learnings"]

        migrate_engine.execute("SET foreign_key_checks = 0")
        for table in tables:
            migrate_engine.execute(
                "ALTER TABLE %s CONVERT TO CHARACTER SET utf8" % table)
        migrate_engine.execute("SET foreign_key_checks = 1")
        migrate_engine.execute(
            "ALTER DATABASE %s DEFAULT CHARACTER SET utf8" %
            migrate_engine.url.database)
        migrate_engine.execute("ALTER TABLE %s Engine=InnoDB" % table)


def downgrade():
    raise NotImplementedError('Downgrade from initial Meteos install is not'
                              ' supported.')
