Meteos Overview
==============

What is Meteos?
~~~~~~~~~~~~~~~

Meteos is an OpenStack project to provide "Machine Learning as a service".

* **Component based architecture:** Quickly add new behaviors
* **Highly available:** Scale to very serious workloads
* **Fault-Tolerant:** Isolated processes avoid cascading failures
* **Recoverable:** Failures should be easy to diagnose, debug, and rectify
* **Open Standards:** Be a reference implementation for a community-driven api
* **API Compatibility:** Meteos strives to provide API-compatible with popular systems like Amazon EC2


Main use cases
~~~~~~~~~~~~~~

Machine Learning consists of the following phases.

* **Learning Phase** - Analyze huge amounts of data and create a Prediction Model
* **Prediction Phase** - Predict a value according to the input value by using Prediction Model

Use case in Learning Phase
--------------------------

* Upload Raw Data - Upload a raw data to Object Storage
* Parse Raw Data - Parse a raw data to enable MLllib (Apache Spark's scalable
  machine learning library) to handle it. Users are allowed to parse the parsed data again.
* Create Prediction Model - Create a Prediction Model by using MLlib

Use case in Prediction Phase
----------------------------

* Predict - Input any value and retrieve predicted value
