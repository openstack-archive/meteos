#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# Copyright 2016 NEC Corpocation All Rights Reserved.
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


import base64
import os
import sys
import uuid
import socket
from ast import literal_eval
from numpy import array
from math import sqrt
from pyspark import SparkContext

from pyspark.mllib.linalg import SparseVector
from pyspark.mllib.classification import LogisticRegressionWithSGD
from pyspark.mllib.classification import LogisticRegressionModel
from pyspark.mllib.clustering import KMeans, KMeansModel
from pyspark.mllib.feature import Word2Vec
from pyspark.mllib.feature import Word2VecModel
from pyspark.mllib.fpm import FPGrowth
from pyspark.mllib.fpm import FPGrowthModel
from pyspark.mllib.evaluation import BinaryClassificationMetrics
from pyspark.mllib.evaluation import RegressionMetrics
from pyspark.mllib.evaluation import MulticlassMetrics
from pyspark.mllib.evaluation import RankingMetrics
from pyspark.mllib.recommendation import ALS, MatrixFactorizationModel, Rating
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.regression import LinearRegressionWithSGD
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.tree import DecisionTree, DecisionTreeModel
from pyspark.mllib.util import MLUtils


EXIT_CODE='80577372-9349-463a-bbc3-1ca54f187cc9'


class ModelController(object):

    """Class defines interface of Model Controller."""

    def __init__(self):
        super(ModelController, self).__init__()

    def create_model(self, data, params):
        """Is called to create mode."""
        raise NotImplementedError()

    def create_model_libsvm(self, data, params):
        """Is called to create mode."""
        raise NotImplementedError()

    def evaluate_model(self, context, model, data):
        """Is called to evaluate mode."""
        raise NotImplementedError()

    def load_model(self, context, path):
        """Is called to load mode."""
        raise NotImplementedError()

    def predict(self, context, params):
        """Is called to predict value."""
        raise NotImplementedError()

    def predict_libsvm(self, context, params):
        """Is called to predict value."""
        raise NotImplementedError()

    def parsePoint(self, line):
        values = [float(s) for s in line.split(',')]
        if values[0] == -1:
            values[0] = 0
        return LabeledPoint(values[0], values[1:])


class KMeansModelController(ModelController):

    def __init__(self):
        super(KMeansModelController, self).__init__()

    def create_model(self, data, params):

        numClasses = params.get('numClasses', 2)
        numIterations = params.get('numIterations', 10)
        runs = params.get('runs', 10)
        mode = params.get('mode', 'random')

        parsedData = data.map(
            lambda line: array([float(x) for x in line.split(',')]))

        return KMeans.train(parsedData,
                            numClasses,
                            maxIterations=numIterations,
                            runs=runs,
                            initializationMode=mode)

    def load_model(self, context, path):
        return KMeansModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))


class RecommendationController(ModelController):

    def __init__(self):
        super(RecommendationController, self).__init__()

    def _create_ratings(self, data):

        return data.map(lambda l: l.split(','))\
                   .map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

    def create_model(self, data, params):

        # Build the recommendation model using Alternating Least Squares
        rank = params.get('rank', 10)
        numIterations = params.get('numIterations', 10)

        ratings = self._create_ratings(data)

        return ALS.train(ratings, rank, numIterations)

    def evaluate_model(self, context, model, data):

        ratings = self._create_ratings(data)
        testData = ratings.map(lambda p: (p.user, p.product))

        predictions = model.predictAll(testData)\
                          .map(lambda r: ((r.user, r.product), r.rating))

        ratingsTuple = ratings.map(lambda r: ((r.user, r.product), r.rating))
        scoreAndLabels = predictions.join(ratingsTuple).map(lambda tup: tup[1])

        # Instantiate regression metrics to compare predicted and actual ratings
        metrics = RegressionMetrics(scoreAndLabels)

        result = "{}: {}".format("MAE", metrics.meanAbsoluteError) + os.linesep\
               + "{}: {}".format("MSE", metrics.meanSquaredError) + os.linesep\
               + "{}: {}".format("RMSE", metrics.rootMeanSquaredError) + os.linesep\
               + "{}: {}".format("R-squared", metrics.r2)

        return result

    def load_model(self, context, path):
        return MatrixFactorizationModel.load(context, path)

    def predict(self, model, params):

        parsedData = params.split(',')
        return model.predict(parsedData[0], parsedData[1])


class LinearRegressionModelController(ModelController):

    def __init__(self):
        super(LinearRegressionModelController, self).__init__()

    def create_model(self, data, params):

        iterations = params.get('numIterations', 10)
        step = params.get('step', 0.00000001)

        points = data.map(self.parsePoint)
        return LinearRegressionWithSGD.train(points,
                                             iterations=iterations,
                                             step=step)

    def create_model_libsvm(self, data, params):

        iterations = params.get('numIterations', 10)
        step = params.get('step', 0.00000001)

        return LinearRegressionWithSGD.train(data,
                                             iterations=iterations,
                                             step=step)

    def evaluate_model(self, context, model, data):

        points = data.map(self.parsePoint)
        scoreAndLabels = points.map(lambda p: (float(model.predict(p.features)), p.label))

        metrics = RegressionMetrics(scoreAndLabels)

        result = "{}: {}".format("MAE", metrics.meanAbsoluteError) + os.linesep\
               + "{}: {}".format("MSE", metrics.meanSquaredError) + os.linesep\
               + "{}: {}".format("RMSE", metrics.rootMeanSquaredError) + os.linesep\
               + "{}: {}".format("R-squared", metrics.r2)

        return result

    def load_model(self, context, path):
        return LinearRegressionModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        return self.predict(model, params)


class LogisticRegressionModelController(ModelController):

    def __init__(self):
        super(LogisticRegressionModelController, self).__init__()

    def create_model(self, data, params):

        numIterations = params.get('numIterations', 10)

        points = data.map(self.parsePoint)
        return LogisticRegressionWithSGD.train(points, numIterations)

    def create_model_libsvm(self, data, params):

        numIterations = params.get('numIterations', 10)

        return LogisticRegressionWithSGD.train(data, numIterations)

    def evaluate_model(self, context, model, data):

        predictionAndLabels = data.map(self.parsePoint)\
                                  .map(lambda lp: (float(model.predict(lp.features)), lp.label))

        metrics = BinaryClassificationMetrics(predictionAndLabels)

        result = "{}: {}".format("Area under PR", metrics.areaUnderPR) + os.linesep\
               + "{}: {}".format("Area under ROC", metrics.areaUnderROC)

        return result

    def load_model(self, context, path):
        return LogisticRegressionModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        return self.predict(model, params)


class DecisionTreeModelController(ModelController):

    def __init__(self):
        super(DecisionTreeModelController, self).__init__()

    def _parse_to_libsvm(self, param):

        index_l = []
        value_l = []

        param_l = param.split(' ')
        param_len = str(len(param_l) * 2)

        for p in param_l:
            index_l.append(str(int(p.split(':')[0]) - 1))
            value_l.append(p.split(':')[1])

        index = ','.join(index_l)
        value = ','.join(value_l)

        parsed_str = '(' + param_len + ', [' + index  + '],[' + value  + '])'

        return SparseVector.parse(parsed_str)

    def create_model_libsvm(self, data, params):

        impurity = params.get('impurity', 'variance')
        maxDepth = params.get('maxDepth', 5)
        maxBins = params.get('maxBins', 32)

        return DecisionTree.trainRegressor(data,
                                           categoricalFeaturesInfo={},
                                           impurity=impurity,
                                           maxDepth=maxDepth,
                                           maxBins=maxBins)

    def evaluate_model(self, context, model, data):

        predictions = model.predict(data.map(lambda x: x.features))
        predictionAndLabels = data.map(lambda lp: lp.label).zip(predictions)
        metrics = MulticlassMetrics(predictionAndLabels)

        result = "{}: {}".format("Precision", metrics.precision()) + os.linesep\
               + "{}: {}".format("Recall", metrics.recall()) + os.linesep\
               + "{}: {}".format("F1 Score", metrics.fMeasure())

        return result

    def load_model(self, context, path):
        return DecisionTreeModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        parsed_params = self._parse_to_libsvm(params)
        return model.predict(parsed_params)


class Word2VecModelController(ModelController):

    def __init__(self):
        super(Word2VecModelController, self).__init__()

    def create_model(self, data, params):

        learningRate = params.get('learningRate', 0.025)
        numIterations = params.get('numIterations', 10)
        minCount = params.get('minCount', 5)

        word2vec = Word2Vec()
        word2vec.setLearningRate(learningRate)
        word2vec.setNumIterations(numIterations)
        word2vec.setMinCount(minCount)

        inp = data.map(lambda row: row.split(" "))
        return word2vec.fit(inp)

    def load_model(self, context, path):
        return Word2VecModel.load(context, path)

    def predict(self, model, params):

        dic_params = literal_eval(params)

        keyword = dic_params.get('word')
        num = dic_params.get('num', 2)

        synonyms = model.findSynonyms(keyword, num)

        result = ""

        for word, cosine_distance in synonyms:
            result += "{}: {}".format(word, cosine_distance) + os.linesep

        return result


class FPGrowthModelController(ModelController):

    def __init__(self):
        super(FPGrowthModelController, self).__init__()

    def create_model(self, data, params):

        minSupport = params.get('minSupport', 0.2)
        numPartitions = params.get('numPartitions', 10)
        limits = params.get('limits', 10)

        transactions = data.map(lambda line: line.strip().split(' '))

        model= FPGrowth.train(transactions,
                              minSupport=minSupport,
                              numPartitions=numPartitions)

        result = model.freqItemsets().collect()

        for index, fi in enumerate(result):
            if index == limits:
                break
            print(str(fi.items) + ':' + str(fi.freq))


class MeteosSparkController(object):

    def init_context(self):

        self.base_hostname = socket.gethostname().split(".")[0]
        master_node = 'spark://' + self.base_hostname + ':7077'
        self.context = SparkContext(master_node, 'INFO')

    def parse_args(self, args):

        self.id = args[3]
        decoded_args = base64.b64decode(args[4])
        self.job_args = literal_eval(decoded_args)

        self.datapath = 'data-' + self.id
        self.modelpath = 'model-' + self.id

    def init_model_controller(self):

        model_type = self.job_args['model']['type']

        if model_type == 'KMeans':
            self.controller = KMeansModelController()
        elif model_type == 'Recommendation':
            self.controller = RecommendationController()
        elif model_type == 'LogisticRegression':
            self.controller = LogisticRegressionModelController()
        elif model_type == 'LinearRegression':
            self.controller = LinearRegressionModelController()
        elif model_type == 'DecisionTreeRegression':
            self.controller = DecisionTreeModelController()
        elif model_type == 'Word2Vec':
            self.controller = Word2VecModelController()
        elif model_type == 'FPGrowth':
            self.controller = FPGrowthModelController()

    def save_data(self, collect=True):

        if collect:
            self.data.collect()
        self.data.saveAsTextFile(self.datapath)
        print self.data.take(10)

    def load_data(self):

        source_dataset_url = self.job_args['source_dataset_url']

        if source_dataset_url.count('swift'):
            swift = self.job_args['swift']
            tenant = swift['tenant']
            username = swift['username']
            password = swift['password']
            container_name = source_dataset_url.split('/')[2]
            object_name = source_dataset_url.split('/')[3]

            prefix = 'fs.swift.service.sahara'
            hconf = self.context._jsc.hadoopConfiguration()
            hconf.set(prefix + '.tenant', tenant)
            hconf.set(prefix + '.username', username)
            hconf.set(prefix + '.password', password)
            hconf.setInt(prefix + ".http.port", 8080)

            self.data = self._load_data('swift://' + container_name + '.sahara/' + object_name)
        else:
            dataset_path = 'data-' + source_dataset_url.split('/')[2]
            self.data = self._load_data(dataset_path)

    def _load_data(self, path):

        dataset_format = self.job_args.get('dataset_format')

        if dataset_format == 'libsvm':
            return MLUtils.loadLibSVMFile(self.context, path)
        else:
            return self.context.textFile(path).cache()

    def create_and_save_model(self):

        model_params = self.job_args['model']['params']
        params = base64.b64decode(model_params)
        list_params = literal_eval(params)

        dataset_format = self.job_args.get('dataset_format')

        if dataset_format == 'libsvm':
            self.model = self.controller.create_model_libsvm(self.data, list_params)
        else:
            self.model = self.controller.create_model(self.data, list_params)

        if self.model:
            self.model.save(self.context, self.modelpath)

    def evaluate_model(self):

        self.load_data()
        self.model = self.controller.load_model(self.context,
                                                self.modelpath)

        output = self.controller.evaluate_model(self.context,
                                                self.model,
                                                self.data)

        if output is not None:
            print(output)

    def download_dataset(self):

        self.load_data()
        self.save_data()

    def parse_dataset(self):

        self.load_data()

        dataset_param = self.job_args['dataset']['params']
        params = base64.b64decode(dataset_param)
        list_params = literal_eval(params)

        cmd = ''

        for param in list_params:
            cmd = cmd + '.' + param['method'] + '(' + param['args'] + ')'

        exec('self.data = self.data' + cmd)
        self.save_data()

    def create_model(self):

        self.load_data()
        self.create_and_save_model()

    def _predict(self, dataset_format, params):

        if dataset_format == 'libsvm':
            return self.controller.predict_libsvm(self.model, params)
        else:
            return self.controller.predict(self.model, params)

    def online_predict(self):

        host = 'localhost'
        port = int(self.job_args['model']['port'])
        buf = 8192
        dataset_format = self.job_args.get('dataset_format')

        self.model = self.controller.load_model(self.context, self.modelpath)

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_addr = (host, port)
        s.bind(s_addr)

        s.listen(1)

        while(True):

            conn, c_addr = s.accept()
            EXIT = False

            try:
                while(True):

                    input_value = conn.recv(buf)
                    params = base64.b64decode(input_value)

                    if params == EXIT_CODE:
                        EXIT = True
                    elif params:
                        output = self._predict(dataset_format, params)
                        conn.sendall(str(output))
                    else:
                        break
            except Exception:
                pass
            finally:
                conn.close()

            if EXIT:
                break

    def predict(self):

        predict_params = self.job_args['learning']['params']
        params = base64.b64decode(predict_params)

        self.model = self.controller.load_model(self.context, self.modelpath)

        dataset_format = self.job_args.get('dataset_format')

        output = self._predict(dataset_format, params)

        if output is not None:
            print(output)


if __name__ == '__main__':

    meteos = MeteosSparkController()
    meteos.parse_args(sys.argv)
    meteos.init_model_controller()
    meteos.init_context()

    getattr(meteos, meteos.job_args['method'])()
