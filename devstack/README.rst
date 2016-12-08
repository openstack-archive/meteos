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
