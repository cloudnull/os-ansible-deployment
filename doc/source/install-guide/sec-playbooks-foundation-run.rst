`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Running the foundation playbook
-------------------------------

#. Change to the ``/opt/os-ansible-deployment/playbooks`` directory.

#. Run the host setup playbook, which runs a series of sub-playbooks:

   .. code-block:: bash

       $ openstack-ansible setup-hosts.yml
               

   Confirm satisfactory completion with zero items unreachable or
   failed:

   .. code-block:: bash

       PLAY RECAP ********************************************************************
       ...
       deployment_host                :  ok=18   changed=11   unreachable=0    failed=0

#. If using HAProxy, run the playbook to deploy it:

   .. code-block:: bash

       $ openstack-ansible haproxy-install.yml

--------------

.. include:: navigation.txt
