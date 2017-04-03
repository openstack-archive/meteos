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
import socket
import sys
import uuid

from ast import literal_eval
from math import sqrt
from numpy import array
from pyspark import SparkContext

from pyspark.mllib.classification import LogisticRegressionModel
from pyspark.mllib.classification import LogisticRegressionWithSGD
from pyspark.mllib.classification import NaiveBayes
from pyspark.mllib.classification import NaiveBayesModel
from pyspark.mllib.clustering import KMeans
from pyspark.mllib.clustering import KMeansModel
from pyspark.mllib.evaluation import MulticlassMetrics
from pyspark.mllib.evaluation import RegressionMetrics
from pyspark.mllib.feature import HashingTF
from pyspark.mllib.feature import IDF
from pyspark.mllib.feature import Word2Vec
from pyspark.mllib.feature import Word2VecModel
from pyspark.mllib.fpm import FPGrowth
from pyspark.mllib.fpm import FPGrowthModel
from pyspark.mllib.linalg import SparseVector
from pyspark.mllib.recommendation import ALS
from pyspark.mllib.recommendation import MatrixFactorizationModel
from pyspark.mllib.recommendation import Rating
from pyspark.mllib.regression import LabeledPoint
from pyspark.mllib.regression import LinearRegressionModel
from pyspark.mllib.regression import LinearRegressionWithSGD
from pyspark.mllib.regression import RidgeRegressionModel
from pyspark.mllib.regression import RidgeRegressionWithSGD
from pyspark.mllib.tree import DecisionTree
from pyspark.mllib.tree import DecisionTreeModel
from pyspark.mllib.tree import RandomForest
from pyspark.mllib.tree import RandomForestModel
from pyspark.mllib.util import MLUtils


EXIT_CODE = '80577372-9349-463a-bbc3-1ca54f187cc9'


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

    def create_model_text(self, data, params):
        """Is called to create mode."""
        raise NotImplementedError()

    def evaluate_model(self, context, model, data):
        """Is called to evaluate mode."""
        raise NotImplementedError()

    def evaluate_model_libsvm(self, context, model, data):
        """Is called to evaluate mode."""
        raise NotImplementedError()

    def evaluate_model_text(self, context, model, data):
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

    def predict_text(self, context, params):
        """Is called to predict value."""
        raise NotImplementedError()

    def parsePoint(self, line):
        values = [float(s) for s in line.split(',')]
        if values[0] == -1:
            values[0] = 0
        return LabeledPoint(values[0], values[1:])

    def textToIndex(self, text):
        return HashingTF().transform(text.split(" "))

    def parseTextRDDToIndex(self, data, label=True):

        if label:
            labels = data.map(lambda line: float(line.split(" ", 1)[0]))
            documents = data.map(lambda line: line.split(" ", 1)[1].split(" "))
        else:
            documents = data.map(lambda line: line.split(" "))

        tf = HashingTF().transform(documents)
        tf.cache()

        idfIgnore = IDF(minDocFreq=2).fit(tf)
        index = idfIgnore.transform(tf)

        if label:
            return labels.zip(index).map(lambda line: LabeledPoint(line[0], line[1]))
        else:
            return index

    def evaluateClassification(self, predictionAndLabels):

        metrics = MulticlassMetrics(predictionAndLabels)
        cm = metrics.confusionMatrix()

        result = {}

        result['Matrix'] = cm.toArray().tolist()
        result['Precision'] = metrics.precision()
        result['Recall'] = metrics.recall()
        result['F1 Score'] = metrics.fMeasure()

        return result

    def evaluateRegression(self, scoreAndLabels):

        metrics = RegressionMetrics(scoreAndLabels)

        result = {}

        result['MAE'] = metrics.meanAbsoluteError
        result['MSE'] = metrics.meanSquaredError
        result['RMSE'] = metrics.rootMeanSquaredError
        result['R-squared'] = metrics.r2

        return result


class KMeansModelController(ModelController):

    def __init__(self):
        super(KMeansModelController, self).__init__()
        self.model_params = {}

    def _parse_model_params(self, params):

        p = {}
        p['numClasses'] = int(params.get('numClasses', 2))
        p['maxIterations'] = int(params.get('numIterations', 10))
        p['runs'] = int(params.get('runs', 10))
        p['initializationMode'] = params.get('mode', 'random')

        self.model_params = p

    def create_model(self, data, params):

        self._parse_model_params(params)
        numClasses = self.model_params.pop('numClasses')

        parsedData = data.map(
            lambda line: array([float(x) for x in line.split(',')]))

        return KMeans.train(parsedData,
                            numClasses,
                            **self.model_params)

    def create_model_text(self, data, params):

        self._parse_model_params(params)
        numClasses = self.model_params.pop('numClasses')

        parsedData = self.parseTextRDDToIndex(data, label=False)

        return KMeans.train(parsedData,
                            numClasses,
                            **self.model_params)

    def load_model(self, context, path):
        return KMeansModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_text(self, model, params):
        index = self.textToIndex(params)
        return model.predict(index)


class RecommendationController(ModelController):

    def __init__(self):
        super(RecommendationController, self).__init__()

    def _create_ratings(self, data):

        return data.map(lambda l: l.split(','))\
                   .map(lambda l: Rating(int(l[0]), int(l[1]), float(l[2])))

    def create_model(self, data, params):

        # Build the recommendation model using Alternating Least Squares
        rank = int(params.get('rank', 10))
        numIterations = int(params.get('numIterations', 10))

        ratings = self._create_ratings(data)

        return ALS.train(ratings, rank, numIterations)

    def evaluate_model(self, context, model, data):

        ratings = self._create_ratings(data)
        testData = ratings.map(lambda p: (p.user, p.product))

        predictions = model.predictAll(testData)\
                           .map(lambda r: ((r.user, r.product), r.rating))

        ratingsTuple = ratings.map(lambda r: ((r.user, r.product), r.rating))
        scoreAndLabels = predictions.join(ratingsTuple).map(lambda tup: tup[1])

        return self.evaluateRegression(scoreAndLabels)

    def load_model(self, context, path):
        return MatrixFactorizationModel.load(context, path)

    def predict(self, model, params):

        parsedData = params.split(',')
        return model.predict(parsedData[0], parsedData[1])


class RegressionModelController(ModelController):

    def __init__(self, train_name, model_name):
        super(RegressionModelController, self).__init__()
        self.train_class = eval(train_name)
        self.model_class = eval(model_name)
        self.model_params = {}

    def _parse_model_params(self, params):

        p = {}
        p['iterations'] = int(params.get('numIterations', 100))
        p['step'] = float(params.get('step', 0.00000001))
        p['miniBatchFraction'] = float(params.get('miniBatchFraction', 1.0))
        p['convergenceTol'] = float(params.get('convergenceTol', 0.001))
        if self.__class__.__name__ == 'LinearRegressionModelController':
            p['regParam'] = float(params.get('regParam', 0.0))
        elif self.__class__.__name__ == 'RidgeRegressionModelController':
            p['regParam'] = float(params.get('regParam', 0.01))

        self.model_params = p

    def create_model(self, data, params):

        self._parse_model_params(params)

        points = data.map(self.parsePoint)
        return getattr(self.train_class, 'train')(points, **self.model_params)

    def create_model_libsvm(self, data, params):

        self._parse_model_params(params)

        return getattr(self.train_class, 'train')(data, **self.model_params)

    def evaluate_model(self, context, model, data):

        points = data.map(self.parsePoint)
        scoreAndLabels = points.map(lambda p: (float(model.predict(p.features)), p.label))

        return self.evaluateRegression(scoreAndLabels)

    def evaluate_model_libsvm(self, context, model, data):
        return self.evaluate_model(context, model, data)

    def load_model(self, context, path):
        return getattr(self.model_class, 'load')(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        return self.predict(model, params)


class LinearRegressionModelController(RegressionModelController):

    def __init__(self):
        train_name = 'LinearRegressionWithSGD'
        model_name = 'LinearRegressionModel'
        super(LinearRegressionModelController, self).__init__(train_name,
                                                             model_name)


class RidgeRegressionModelController(RegressionModelController):

    def __init__(self):
        train_name = 'RidgeRegressionWithSGD'
        model_name = 'RidgeRegressionModel'
        super(RidgeRegressionModelController, self).__init__(train_name,
                                                             model_name)


class LogisticRegressionModelController(ModelController):

    def __init__(self):
        super(LogisticRegressionModelController, self).__init__()

    def create_model(self, data, params):

        numIterations = int(params.get('numIterations', 10))

        points = data.map(self.parsePoint)
        return LogisticRegressionWithSGD.train(points, numIterations)

    def create_model_libsvm(self, data, params):

        numIterations = int(params.get('numIterations', 10))

        return LogisticRegressionWithSGD.train(data, numIterations)

    def evaluate_model(self, context, model, data):

        predictionAndLabels = data.map(self.parsePoint)\
                                  .map(lambda lp: (float(model.predict(lp.features)), lp.label))

        return self.evaluateClassification(predictionAndLabels)

    def evaluate_model_libsvm(self, context, model, data):
        return self.evaluate_model(context, model, data)

    def load_model(self, context, path):
        return LogisticRegressionModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        return self.predict(model, params)


class NaiveBayesModelController(ModelController):

    def __init__(self):
        super(NaiveBayesModelController, self).__init__()

    def create_model(self, data, params):

        lambda_ = float(params.get('lambda', 1.0))

        points = data.map(self.parsePoint)
        return NaiveBayes.train(points, lambda_)

    def create_model_text(self, data, params):

        lambda_ = float(params.get('lambda', 1.0))

        points = self.parseTextRDDToIndex(data)

        return NaiveBayes.train(points, lambda_)

    def evaluate_model(self, context, model, data):

        predictionAndLabels = data.map(self.parsePoint)\
                                  .map(lambda lp: (float(model.predict(lp.features)), lp.label))

        return self.evaluateClassification(predictionAndLabels)

    def evaluate_model_libsvm(self, context, model, data):
        return self.evaluate_model(context, model, data)

    def evaluate_model_text(self, context, model, data):

        points = self.parseTextRDDToIndex(data)
        predictionAndLabels = points.map(lambda lp: (float(model.predict(lp.features)), lp.label))

        return self.evaluateClassification(predictionAndLabels)

    def load_model(self, context, path):
        return NaiveBayesModel.load(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_text(self, model, params):
        index = self.textToIndex(params)
        return model.predict(index)


class TreeModelController(ModelController):

    def __init__(self, train_name, model_name, algorithm):
        super(TreeModelController, self).__init__()
        self.train_class = eval(train_name)
        self.model_class = eval(model_name)
        self.algorithm = algorithm
        self.model_params = {}

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

        parsed_str = '(' + param_len + ', [' + index + '],[' + value + '])'

        return SparseVector.parse(parsed_str)

    def _parse_model_params(self, params):

        p = {}
        p['maxDepth'] = int(params.get('maxDepth', 5))
        p['maxBins'] = int(params.get('maxBins', 32))

        if self.algorithm == 'Classification':
            p['numClasses'] = int(params.get('numClasses', 2))

        if self.__class__.__name__ == 'RandomForestModelController':
            p['numTrees'] = int(params.get('numTrees', 3))

        self.model_params = p

    def _create_model(self, data, params, format='csv'):

        self._parse_model_params(params)
        if format == 'csv':
            points = data.map(self.parsePoint)
        else:
            points = data

        if (self.__class__.__name__ == 'DecisionTreeModelController' and
           self.algorithm == 'Regression'):

            return getattr(self.train_class,
                           'trainRegressor')(points,
                                             {},
                                             **self.model_params)

        elif (self.__class__.__name__ == 'DecisionTreeModelController' and
              self.algorithm == 'Classification'):

            numClasses = self.model_params.pop('numClasses')

            return getattr(self.train_class,
                           'trainClassifier')(points,
                                              numClasses,
                                              {},
                                              **self.model_params)

        if (self.__class__.__name__ == 'RandomForestModelController' and
           self.algorithm == 'Regression'):

            numTrees = self.model_params.pop('numTrees')

            return getattr(self.train_class,
                           'trainRegressor')(points,
                                             {},
                                             numTrees,
                                             **self.model_params)

        elif (self.__class__.__name__ == 'RandomForestModelController' and
              self.algorithm == 'Classification'):

            numClasses = self.model_params.pop('numClasses')
            numTrees = self.model_params.pop('numTrees')

            return getattr(self.train_class,
                           'trainClassifier')(points,
                                              numClasses,
                                              {},
                                              numTrees,
                                              **self.model_params)

    def create_model(self, data, params):
        return self._create_model(data, params)

    def create_model_libsvm(self, data, params):
        return self._create_model(data, params, format='libsvm')

    def evaluate_model(self, context, model, data):

        points = data.map(self.parsePoint)
        predictions = model.predict(points.map(lambda lp: lp.features))
        predictionAndLabels = points.map(lambda lp: lp.label).zip(predictions)

        return self.evaluateClassification(predictionAndLabels)

    def evaluate_model_libsvm(self, context, model, data):

        predictions = model.predict(data.map(lambda x: x.features))
        predictionAndLabels = data.map(lambda lp: lp.label).zip(predictions)

        return self.evaluateClassification(predictionAndLabels)

    def load_model(self, context, path):
        return getattr(self.model_class, 'load')(context, path)

    def predict(self, model, params):
        return model.predict(params.split(','))

    def predict_libsvm(self, model, params):
        parsed_params = self._parse_to_libsvm(params)
        return model.predict(parsed_params)


class DecisionTreeModelController(TreeModelController):

    def __init__(self, algorithm):
        train_name = 'DecisionTree'
        model_name = 'DecisionTreeModel'
        super(DecisionTreeModelController, self).__init__(train_name,
                                                          model_name,
                                                          algorithm)


class RandomForestModelController(TreeModelController):

    def __init__(self, algorithm):
        train_name = 'RandomForest'
        model_name = 'RandomForestModel'
        super(RandomForestModelController, self).__init__(train_name,
                                                          model_name,
                                                          algorithm)


class Word2VecModelController(ModelController):

    def __init__(self):
        super(Word2VecModelController, self).__init__()

    def create_model_text(self, data, params):

        learningRate = float(params.get('learningRate', 0.025))
        numIterations = int(params.get('numIterations', 10))
        minCount = int(params.get('minCount', 5))

        word2vec = Word2Vec()
        word2vec.setLearningRate(learningRate)
        word2vec.setNumIterations(numIterations)
        word2vec.setMinCount(minCount)

        inp = data.map(lambda row: row.split(" "))
        return word2vec.fit(inp)

    def load_model(self, context, path):
        return Word2VecModel.load(context, path)

    def predict_text(self, model, params):

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

    def create_model_text(self, data, params):

        minSupport = float(params.get('minSupport', 0.2))
        numPartitions = int(params.get('numPartitions', 10))
        limits = int(params.get('limits', 10))

        transactions = data.map(lambda line: line.strip().split(' '))

        model = FPGrowth.train(transactions,
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
        elif model_type == 'RidgeRegression':
            self.controller = RidgeRegressionModelController()
        elif model_type == 'DecisionTreeRegression':
            self.controller = DecisionTreeModelController('Regression')
        elif model_type == 'DecisionTreeClassification':
            self.controller = DecisionTreeModelController('Classification')
        elif model_type == 'RandomForestRegression':
            self.controller = RandomForestModelController('Regression')
        elif model_type == 'RandomForestClassification':
            self.controller = RandomForestModelController('Classification')
        elif model_type == 'Word2Vec':
            self.controller = Word2VecModelController()
        elif model_type == 'FPGrowth':
            self.controller = FPGrowthModelController()
        elif model_type == 'NaiveBayes':
            self.controller = NaiveBayesModelController()

    def save_data(self, collect=True):

        if collect:
            self.data.collect()
        self.data.saveAsTextFile(self.datapath)
        print(self.data.take(10))

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
            self.model = self.controller.create_model_libsvm(self.data,
                                                             list_params)
        elif dataset_format == 'text':
            self.model = self.controller.create_model_text(self.data,
                                                           list_params)
        else:
            self.model = self.controller.create_model(self.data, list_params)

        if self.model:
            self.model.save(self.context, self.modelpath)

    def evaluate_model(self):

        self.load_data()
        self.model = self.controller.load_model(self.context,
                                                self.modelpath)
        dataset_format = self.job_args.get('dataset_format')

        if dataset_format == 'libsvm':
            output = self.controller.evaluate_model_libsvm(self.context,
                                                           self.model,
                                                           self.data)
        elif dataset_format == 'text':
            output = self.controller.evaluate_model_text(self.context,
                                                         self.model,
                                                         self.data)
        else:
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

    def split_dataset(self):

        self.load_data()

        percent_train = self.job_args['dataset']['percent_train']
        percent_test = self.job_args['dataset']['percent_test']

        # Split the data into training and test sets
        (trainData, testData) = self.data.randomSplit([float(percent_train),
                                                       float(percent_test)])
        self.data = trainData
        self.save_data()

        # save testData
        testData.collect()
        datapath = 'data-' + self.job_args['dataset']['test_dataset']['id']
        testData.saveAsTextFile(datapath)

    def create_model(self):

        self.load_data()
        self.create_and_save_model()

    def _predict(self, dataset_format, params):

        if dataset_format == 'libsvm':
            return self.controller.predict_libsvm(self.model, params)
        elif dataset_format == 'text':
            return self.controller.predict_text(self.model, params)
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
