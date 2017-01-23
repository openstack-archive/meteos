======================
 Enabling in Devstack
======================

1. Download DevStack

2. Add this repo as an external repository in ``local.conf``

.. sourcecode:: bash

     [[local|localrc]]
     enable_plugin meteos git://git.openstack.org/openstack/meteos

Optionally, a git refspec may be provided as follows:

.. sourcecode:: bash

     [[local|localrc]]
     enable_plugin meteos git://git.openstack.org/openstack/meteos <refspec>

3. run ``stack.sh``

For additional configuration information please see details in the `Meteos on
DevStack`_ section of the Meteos wiki.

.. _Meteos on DevStack: https://wiki.openstack.org/wiki/Meteos/Devstack
