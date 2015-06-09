`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Configuring target hosts
------------------------

Modify the ``/etc/openstack_deploy/openstack_user_config.yml`` file to
configure the target hosts.

Do not assign the same IP address to different target hostnames.
Unexpected results may occur. Each IP address and hostname must be a
matching pair. To use the same host in multiple roles, for example
infrastructure and networking, specify the same hostname and IP in each
section.

Use short hostnames rather than fully-qualified domain names (FQDN) to
prevent length limitation issues with LXC and SSH. For example, a
suitable short hostname for a compute host might be:
``123456-Compute001``.

#. Configure a list containing at least three infrastructure target
   hosts in the ``infra_hosts`` section:

   .. code-block:: yaml

       infra_hosts:
         603975-infra01:
           ip: INFRA01_IP_ADDRESS
         603989-infra02:
           ip: INFRA02_IP_ADDRESS
         627116-infra03:
           ip: INFRA03_IP_ADDRESS
         628771-infra04: ...

   Replace *``*_IP_ADDRESS``* with the IP address of the ``br-mgmt``
   container management bridge on each infrastructure target host. Use
   the same net block as bond0 on the nodes, for example:

   .. code-block:: yaml

       infra_hosts:
         603975-infra01:
           ip: 10.240.0.80
         603989-infra02:
           ip: 10.240.0.81
         627116-infra03:
           ip: 10.240.0.184

#. Configure a list containing at least one network target host in the
   ``network_hosts`` section:

   .. code-block:: yaml

       network_hosts:
         602117-network01:
           ip: NETWORK01_IP_ADDRESS
         602534-network02: ...

   Replace *``*_IP_ADDRESS``* with the IP address of the ``br-mgmt``
   container management bridge on each network target host.

#. Configure a list containing at least one compute target host in the
   ``compute_hosts`` section:

   .. code-block:: yaml

       compute_hosts:
         900089-compute001:
           ip: COMPUTE001_IP_ADDRESS
         900090-compute002: ...

   Replace *``*_IP_ADDRESS``* with the IP address of the ``br-mgmt``
   container management bridge on each compute target host.

#. Configure a list containing at least one logging target host in the
   ``log_hosts`` section:

   .. code-block:: yaml

       log_hosts:
         900088-logging01:
           ip: LOGGER1_IP_ADDRESS
         903877-logging02: ...

   Replace *``*_IP_ADDRESS``* with the IP address of the ``br-mgmt``
   container management bridge on each logging target host.

#. Configure a list containing at least one optional storage host in the
   ``storage_hosts`` section:

   .. code-block:: yaml

       storage_hosts:
         100338-storage01:
           ip: STORAGE01_IP_ADDRESS
         100392-storage02: ...

   Replace *``*_IP_ADDRESS``* with the IP address of the ``br-mgmt``
   container management bridge on each storage target host. Each storage
   host also requires additional configuration to define the back end
   driver.

   The default configuration includes an optional storage host. To
   install without storage hosts, comment out the stanza beginning with
   the *storage\_hosts:* line.

--------------

.. include:: navigation.txt
