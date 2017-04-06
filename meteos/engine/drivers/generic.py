# Copyright (c) 2014 NetApp, Inc.
# All Rights Reserved.
# Copyright (c) 2016 NEC Corporation.
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

"""Generic Driver for learnings."""

import base64
from eventlet import greenthread
import os
import random
import time

from oslo_concurrency import processutils
from oslo_config import cfg
from oslo_log import log
from oslo_utils import excutils

from meteos import cluster
from meteos.common import constants as const
from meteos import context
from meteos.engine import driver
from meteos import exception
from meteos.i18n import _
from meteos import utils

EXIT_CODE = '80577372-9349-463a-bbc3-1ca54f187cc9'
LOG = log.getLogger(__name__)

learning_opts = [
    cfg.IntOpt(
        'create_experiment_timeout',
        default=600,
        help="Time to wait for creating experiment (seconds)."),
    cfg.IntOpt(
        'load_model_timeout',
        default=600,
        help="Time to wait for loading model (seconds)."),
    cfg.IntOpt(
        'execute_job_timeout',
        default=600,
        help='Timeout for executing job (seconds).'),
    cfg.IntOpt(
        'api_retry_interval',
        default=10,
        help='The number of seconds to wait before retrying the request.'),
]


CONF = cfg.CONF
CONF.register_opts(learning_opts)

SAHARA_GROUP = 'sahara'
PLUGIN_NAME = 'spark'
SPARK_USER_NAME = 'ubuntu'
METEOS_JOB_TYPE = 'Spark'


class GenericLearningDriver(driver.LearningDriver):

    """Executes commands relating to Learnings."""

    def __init__(self, *args, **kwargs):
        """Do initialization."""
        super(GenericLearningDriver, self).__init__([False, True],
                                                    *args,
                                                    **kwargs)
        self.admin_context = context.get_admin_context()
        self.cluster_api = cluster.API()
        self.sshpool = None

    def _run_ssh(self, ip, cmd_list, check_exit_code=True, attempts=1):

        ssh_conn_timeout = self.configuration.ssh_conn_timeout
        ssh_port = self.configuration.ssh_port
        ssh_user = self.configuration.ssh_user
        ssh_password = self.configuration.ssh_password
        min_size = self.configuration.ssh_min_pool_conn
        max_size = self.configuration.ssh_max_pool_conn
        command = ' '. join(cmd_list)

        if not self.sshpool:
            self.sshpool = utils.SSHPool(
                ip,
                ssh_port,
                ssh_conn_timeout,
                ssh_user,
                ssh_password,
                min_size=min_size,
                max_size=max_size)
        last_exception = None
        try:
            with self.sshpool.item() as ssh:
                while attempts > 0:
                    attempts -= 1
                    try:
                        return processutils.ssh_execute(
                            ssh,
                            command,
                            check_exit_code=check_exit_code)
                    except Exception as e:
                        LOG.error(e)
                        last_exception = e
                        greenthread.sleep(random.randint(20, 500) / 100.0)
                try:
                    raise processutils.ProcessExecutionError(
                        exit_code=last_exception.exit_code,
                        stdout=last_exception.stdout,
                        stderr=last_exception.stderr,
                        cmd=last_exception.cmd)
                except AttributeError:
                    raise processutils.ProcessExecutionError(
                        exit_code=-1,
                        stdout="",
                        stderr="Error running SSH command",
                        cmd=command)

        except Exception:
            with excutils.save_and_reraise_exception():
                LOG.error("Error running SSH command: %s", command)

    def _delete_hdfs_dir(self, context, cluster_id, dir_name):

        cluster = self.cluster_api.get_cluster(context, cluster_id)
        node_groups = cluster.node_groups

        for node in node_groups:
            if 'master' in node['node_processes']:
                ip = node['instances'][0]['management_ip']

        path = '/user/ubuntu/' + dir_name

        cmd = ['sudo', '-u', 'hdfs', 'hadoop', 'fs', '-rm', '-r', path]

        try:
            self._run_ssh(ip, cmd)
        except Exception:
            pass

    def _execute_job(self, context, method, request_specs):
        """Execute Sahara Job."""

        job_args = {}

        job_template_id = request_specs.get('job_template_id')
        cluster_id = request_specs.get('cluster_id')

        job_args['method'] = method

        # Set parameters of DataSet
        job_args['source_dataset_url'] = request_specs\
            .get('source_dataset_url')
        job_args['dataset_format'] = request_specs.get('dataset_format')
        dataset_args = {'params': request_specs.get('params'),
                        'test_dataset': request_specs.get('test_dataset'),
                        'percent_train': request_specs.get('percent_train'),
                        'percent_test': request_specs.get('percent_test')}
        job_args['dataset'] = dataset_args

        # Set parameters of Swift
        swift_args = {'tenant': request_specs.get('swift_tenant'),
                      'username': request_specs.get('swift_username'),
                      'password': request_specs.get('swift_password')}
        job_args['swift'] = swift_args

        # Set parameters of Model
        model_args = {'type': request_specs.get('model_type'),
                      'port': request_specs.get('port'),
                      'params': request_specs.get('model_params')}
        job_args['model'] = model_args

        # Set parameters of Learning
        learning_args = {'params': request_specs.get('args')}
        job_args['learning'] = learning_args

        LOG.debug("Execute %s job with args: %s", method, job_args)

        configs = {'configs': {'edp.java.main_class': 'sahara.dummy',
                               'edp.spark.adapt_for_swift': True},
                   'args': [request_specs.get('id'),
                            base64.b64encode(str(job_args))]}

        result = self.cluster_api.job_create(
            context, job_template_id, cluster_id, configs)

        return result

    def create_template(self, context, request_specs):
        """Creates Template."""

        image_id = request_specs['image_id']
        master_nodes_num = request_specs['master_nodes_num']
        master_flavor_id = request_specs['master_flavor_id']
        worker_nodes_num = request_specs['worker_nodes_num']
        worker_flavor_id = request_specs['worker_flavor_id']
        floating_ip_pool = request_specs['floating_ip_pool']
        spark_version = request_specs['spark_version']

        master_node_name = 'master-tmpl-' + request_specs['id']
        slave_node_name = 'slave-tmpl-' + request_specs['id']
        cluster_node_name = 'cluster-tmpl-' + request_specs['id']
        job_binary_name = 'meteos-' + request_specs['id'] + '.py'
        job_name = 'meteos-job-' + request_specs['id']

        sahara_image_id = self.cluster_api.image_set(
            context, image_id, SPARK_USER_NAME)
        self.cluster_api.image_tags_add(
            context, sahara_image_id, ['spark', spark_version])

        master_node_id = self.cluster_api.create_node_group_template(
            context, master_node_name, PLUGIN_NAME, spark_version,
            master_flavor_id, ['master', 'namenode'], floating_ip_pool, True)

        slave_node_id = self.cluster_api.create_node_group_template(
            context, slave_node_name, PLUGIN_NAME, spark_version,
            worker_flavor_id, ["slave", "datanode"], floating_ip_pool, True)

        cluster_node_groups = [
            {
                "name": "master",
                "node_group_template_id": master_node_id,
                "count": master_nodes_num
            },
            {
                "name": "workers",
                "node_group_template_id": slave_node_id,
                "count": worker_nodes_num
            }]

        cluster_template_id = self.cluster_api.create_cluster_template(
            context,
            cluster_node_name,
            PLUGIN_NAME, spark_version,
            cluster_node_groups)

        filename = 'meteos-script-' + spark_version + '.py'
        filepath = os.path.dirname(__file__) + '/../../cluster/binary/' + filename

        data = utils.file_open(filepath)

        binary_data_id = self.cluster_api.create_job_binary_data(
            context, job_binary_name, data)

        binary_url = 'internal-db://' + binary_data_id
        binary_id = self.cluster_api.create_job_binary(
            context, job_binary_name, binary_url)
        mains = [binary_id]
        job_template_id = self.cluster_api.create_job_template(
            context, job_name, METEOS_JOB_TYPE, mains)

        response = {'sahara_image_id': sahara_image_id,
                    'master_node_id': master_node_id,
                    'slave_node_id': slave_node_id,
                    'binary_data_id': binary_data_id,
                    'binary_id': binary_id,
                    'cluster_template_id': cluster_template_id,
                    'job_template_id': job_template_id}

        return response

    def delete_template(self, context, request_specs):
        """Delete Template."""

        self.cluster_api.delete_job_template(
            context, request_specs['job_template_id'])
        self.cluster_api.delete_job_binary(context, request_specs['binary_id'])
        self.cluster_api.delete_job_binary_data(
            context, request_specs['binary_data_id'])
        self.cluster_api.delete_cluster_template(
            context, request_specs['cluster_template_id'])
        self.cluster_api.delete_node_group_template(
            context, request_specs['slave_node_id'])
        self.cluster_api.delete_node_group_template(
            context, request_specs['master_node_id'])
        # self.cluster_api.image_remove(context,
        # request_specs['sahara_image_id'])

    def create_experiment(self, context, request_specs,
                          image_id, cluster_id, spark_version):
        """Creates Experiment."""

        cluster_name = 'cluster-' + request_specs['id'][0:8]
        key_name = request_specs['key_name']
        neutron_management_network = request_specs[
            'neutron_management_network']

        cluster_id = self.cluster_api.create_cluster(
            context,
            cluster_name,
            PLUGIN_NAME,
            spark_version,
            image_id,
            cluster_id,
            key_name,
            neutron_management_network)

        return cluster_id

    def delete_experiment(self, context, id):
        """Delete Experiment."""
        self.cluster_api.delete_cluster(context, id)

    def wait_for_cluster_create(self, context, id):

        starttime = time.time()
        deadline = starttime + self.configuration.create_experiment_timeout
        interval = self.configuration.api_retry_interval
        tries = 0

        while True:
            cluster = self.cluster_api.get_cluster(context, id)

            if cluster.status == const.STATUS_SAHARA_ACTIVE:
                break

            tries += 1
            now = time.time()
            if now > deadline:
                msg = _("Timeout trying to create experiment "
                        "%s") % id
                raise exception.Invalid(reason=msg)

            LOG.debug("Waiting for cluster to complete: Current status: %s",
                      cluster.status)
            time.sleep(interval)

    def get_job_result(self, context, job_id, template_id, cluster_id):

        stdout = ""
        stderr = ""

        starttime = time.time()
        deadline = starttime + self.configuration.execute_job_timeout
        interval = self.configuration.api_retry_interval
        tries = 0

        while True:
            job = self.cluster_api.get_job(context, job_id)

            if job.info['status'] == const.STATUS_JOB_SUCCESS:
                stdout = self._get_job_result(context,
                                              template_id,
                                              cluster_id,
                                              job_id)
                break
            elif job.info['status'] == const.STATUS_JOB_ERROR:
                stderr = self._get_job_result(context,
                                              template_id,
                                              cluster_id,
                                              job_id)
                break

            tries += 1
            now = time.time()
            if now > deadline:
                msg = _("Timeout trying to create experiment "
                        "%s") % job_id
                raise exception.Invalid(reason=msg)

            LOG.debug("Waiting for job to complete: Current status: %s",
                      job.info['status'])
            time.sleep(interval)
        return stdout, stderr

    def create_dataset(self, context, request_specs):
        """Create Dataset."""

        method = request_specs['method'] + '_dataset'

        return self._execute_job(context,
                                 method,
                                 request_specs)

    def delete_dataset(self, context, cluster_id, job_id, id):
        """Delete Dataset."""

        dir_name = 'data-' + id

        self._delete_hdfs_dir(context, cluster_id, dir_name)
        self.cluster_api.job_delete(context, job_id)

    def create_model(self, context, request_specs):
        """Create Model."""

        return self._execute_job(context,
                                 'create_model',
                                 request_specs)

    def delete_model(self, context, cluster_id, job_id, id):
        """Delete Model."""

        dir_name = 'model-' + id

        self._delete_hdfs_dir(context, cluster_id, dir_name)
        self.cluster_api.job_delete(context, job_id)

    def _wait_for_model_to_load(self, ip, port, unload=False):

        stdout = ""
        stderr = ""

        starttime = time.time()
        deadline = starttime + self.configuration.load_model_timeout
        interval = self.configuration.api_retry_interval
        tries = 0

        while True:

            try:
                stdout, stderr = self._run_ssh(ip,
                                               ['netstat',
                                                '-tnl',
                                                '|',
                                                'grep',
                                                port])
            except processutils.ProcessExecutionError:
                pass

            if not stdout and unload:
                break
            if stdout and not unload:
                break

            tries += 1
            now = time.time()
            if now > deadline:
                msg = _("Timeout trying to load/unload model "
                        "%s") % id
                raise exception.Invalid(reason=msg)

            LOG.debug("Waiting for load/unload to complete")
            time.sleep(interval)

    def load_model(self, context, request_specs):
        """Load Model."""

        cluster_id = request_specs.get('cluster_id')
        ip = self._get_master_ip(context, cluster_id)
        port = request_specs['port']

        result = self._execute_job(context,
                                   'online_predict',
                                   request_specs)

        self._wait_for_model_to_load(ip, port)

        return result

    def unload_model(self, context, request_specs):
        """Unload Model."""

        ip = self._get_master_ip(context, request_specs['cluster_id'])
        port = request_specs['port']

        self._run_ssh(ip, ['echo',
                            base64.b64encode(EXIT_CODE),
                            '|',
                            'netcat',
                            'localhost',
                            port])

        self._wait_for_model_to_load(ip, port, unload=True)

    def create_model_evaluation(self, context, request_specs):
        """Create Model Evaluation."""

        request_specs['id'] = request_specs['model_id']

        return self._execute_job(context,
                                 'evaluate_model',
                                 request_specs)

    def delete_model_evaluation(self, context, cluster_id, job_id, id):
        """Delete Model Evaluation."""

        self.cluster_api.job_delete(context, job_id)

    def create_learning(self, context, request_specs):
        """Create Learning."""

        request_specs['id'] = request_specs['model_id']

        return self._execute_job(context,
                                 request_specs['method'],
                                 request_specs)

    def create_online_learning(self, context, request_specs):
        """Create Learning."""

        ip = self._get_master_ip(context, request_specs['cluster_id'])
        learning_args = request_specs['args']
        port = request_specs['port']

        LOG.debug("Execute job with args: %s", learning_args)

        return self._run_ssh(ip, ['echo',
                                  learning_args,
                                  '|',
                                  'netcat',
                                  'localhost',
                                  port])

    def delete_learning(self, context, cluster_id, job_id, id):
        """Delete Learning."""

        self.cluster_api.job_delete(context, job_id)

    def _get_master_ip(self, context, cluster_id):

        cluster = self.cluster_api.get_cluster(context, cluster_id)
        node_groups = cluster.node_groups

        for node in node_groups:
            if 'master' in node['node_processes']:
                ip = node['instances'][0]['management_ip']

        return ip

    def _get_job_result(self, context, template_id, cluster_id, job_id):

        ip = self._get_master_ip(context, cluster_id)

        path = '/tmp/spark-edp/meteos-job-' + \
            template_id + '/' + job_id + '/stdout'

        stdout, stderr = self._run_ssh(ip, ['cat', path])

        return stdout
