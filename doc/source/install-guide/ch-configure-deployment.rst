`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Configure an Object Storage deployment
--------------------------------------

Object Storage is configured using the
``/etc/openstack_deploy/conf.d/swift.yml.example`` file and the
``/etc/openstack_deploy/user_variables.yml`` file.

The group variables in the
``/etc/openstack_deploy/conf.d/swift.yml.example`` file are used by the
Ansible playbooks when installing Object Storage. Some variables cannot
be changed after they are set, while some changes require re-running the
playbooks. The values in the ``swift_hosts`` section supersede values in
the ``swift`` section.

To view the configuration files, including information about which
variables are required and which are optional, see `Appendix A, *OSAD
configuration files* <app-osad-configfiles.html>`__.

--------------

.. include:: navigation.txt