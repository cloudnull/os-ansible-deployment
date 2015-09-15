Upgrade playbooks
=================

This section describes the playbooks that are used in the upgrade process in
further detail.

Within the main :file:`scripts` directory there is an :file:`upgrade-utilities`
directory, which contains an additional playbooks directory. These playbooks
facilitate the upgrade process.


cinder-adjustments.yml
----------------------

This playbook corrects looks for and removes duplicate **udev dev devtmpfs**
entries in cinder-volume container configuration files.


container-network-adjustments.yml
---------------------------------

This playbook logs into the containers throughout the deployment and removes
the Juno network interface files in the :file:`interface.d` directory. These
files are removed because the layout and syntax has changed in the the
community release of OpenStack Ansible, and if they are present  during the
upgrade process, they may cause interface or IP conflicts within the container
infrastructures.


container-network-bounce.yml
----------------------------

This playbook logs into the containers and bounces all networks that have an
interface file in the :file:`interfaces.d` directory.


horizon-adjustments.yml
-----------------------

This playbook corrects several user and group permissions in the horizon
containers. This prevents permission issues with existing data.


host-adjustments.yml
--------------------

This playbook corrects container configuration files to remove items that will
conflict in the upgrade and redeployment process. This play also iterates
through and fixes log locations that may be locked or otherwise located in the
wrong place.


keystone-adjustments.yml
------------------------

This playbook corrects permissions throughout the keystone containers for all
log files.


remove-juno-log-rotate.yml
--------------------------

This playbook removes the log rotation files that were created in the Juno
release. The log rotation process in Kilo has been revised, and the Juno files
would conflict with the new processes.


swift-ring-adjustments.yml
--------------------------

This playbook ensures that the swift ring is located on the appropriate swift
nodes. This co-location of the swift ring ensures that the deployment host is
no longer a potential single point of failure for swift.
