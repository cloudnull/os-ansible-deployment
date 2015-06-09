`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Configuring Secure Shell (SSH) keys
-----------------------------------

Ansible uses Secure Shell (SSH) for connectivity between the deployment
and target hosts.

#. Copy the contents of the public key file on the deployment host to
   the ``/root/.ssh/authorized_keys`` on each target host.

#. Test public key authentication from the deployment host to each
   target host. SSH should provide a shell without asking for a
   password.

--------------

.. include:: navigation.txt
