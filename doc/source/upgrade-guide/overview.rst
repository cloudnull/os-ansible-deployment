Overview
========

The Juno to Kilo upgrade process contains two major components that make the
upgrade process more complex than previous upgrades.

  * The OpenStack code is updated from Juno to Kilo
  * References to Rackspace Private Cloud are removed

Openstack Ansible is based on Rackspace Private Cloud powered by OpenStack.
As such, the original code base contained a number of references to Rackspace
and Rackspace naming. These references have been removed in the community
release.

Because of these changes, the Juno to Kilo upgrade process requires many
adjustments to clean up those references and to ensure that the environment
is prepared for future versions. These steps will ensure that future upgrades
are simpler.
