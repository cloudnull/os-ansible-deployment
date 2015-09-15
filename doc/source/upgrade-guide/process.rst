Process
=======

This document describes how to run the upgrade process using the
``run-upgrade.sh`` script and what the script is doing during its execution.
The intention is to cover enough of the process so that a deployer can
understand what is happening, when it is happening, and why it is happening.
This information will assist a deployer in recovering from upgrade script
failure and also enables the deployer to customize the upgrade path and
process.


About the script
----------------

The ``run-upgrade.sh`` script enables a deployer to initiate the upgrade,
which then proceeds in a programmatic fashion. The script orchestrates the
required components to ensure that the upgrade is successful. If the script
fails in any way, helpful information will be printed to the screen, including
a list of steps that have not run and in what order to execute these steps
to continue the process.

Failed upgrades may require manual intervention, so you many need to log in to
individual components of the environment to troubleshoot. However, if the
original RPC Juno deployment is close to the reference architecture, the script
is expected to perform successfully, and there should not be any issues in the
process.

Important Notes:
  * Before running the upgrade script, review the environment. Ensure that you
  know which VMs you have online and how they were provisioned.

  * Halt any VM that was created using "boot from volume".

  * To ensure that there is no data loss or corruption, it is recommended that
  you halt any VMs that use block storage. This is optional, since block storage
  backends have different capabilities and some solutions may be resilient.
  However, when using the cinder default LVM-backed storage, it is  *HIGHLY*
  recommended that you shut down down block storage-attached VMs.

  * Before running the ``run-upgrade.sh`` script, schedule a maintenance
  window for the process. While this is an "online" upgrade, the API will be
  interrupted while upgrading. Size your maintenance window appropriately based
  on the size of your environment.

  * Neutron L3 networking may be interrupted while upgrading. During the
  upgrade, VMs that are connected to one another may not be able to
  communicate until the neutron agents services are restarted. While we have
  tried to ensure that this potential downtime is minimal, container restart
  and subsequent service reloads will cause this interruption.


Running the upgrade script
--------------------------

The script will prompt you to accept the upgrade before it begins. To run the
script, execute the following command from the root directory where you cloned
the :file:`openstack-ansible` repository.

.. code-block:: bash

    ./scripts/run-upgrade.sh

The upgrade script will run all of the required steps to complete a successful
upgrade.


Running the upgrade by hand
---------------------------

While the recommended upgrade process is through the use of the script,
it may be necessary to break up the process for environment stability,
scale, or other reasons. This section describes the process for a manual
upgrade.

Getting started
^^^^^^^^^^^^^^^

Navigate to the playbooks directory located in the repository root. All steps
for the upgrade execution will be performed in this directory.

Creating two environment variables will simplify the execution paths to the
utilities that are used in the upgrade. The variables set the locations of
the playbooks and the upgrade script.

.. code-block:: bash

    export UPGRADE_PLAYBOOKS="/opt/openstack-ansible/upgrade-utilities/playbooks"
    export UPGRADE_SCRIPTS="/opt/openstack-ansible/upgrade-utilities/scripts"

.. note::

   This is an optional step. If you prefer to call the files directly, use the
   path name instead of the variable, and the process will work normally.


Executing the pre-work scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run ``create-new-openstack-deploy-structure.sh``. This script creates the new
directory structure required to use OpenStack-Ansible on your deployment host.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/create-new-openstack-deploy-structure.sh


----

Upgrade and install the latest required version of Ansible.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/bootstrap-new-ansible.sh


----

Optional: run the following script, which searches for and separates all
known RPC variables that are used for RPC-specific product offerings. Many
of these options are likely to be located within the :file:`user_variables.yml`
file.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/juno-rpc-extras-create.py


----

Populate your user variables files with the new defaults that are required
for the Kilo release of OpenStack-Ansible.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/new-variable-prep.sh


----

If you have been using keystone with LDAP support, run the following script to
convert the variables to the new LDAP syntax.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/juno-kilo-ldap-conversion.py


----

If you have not already populated your user configuration files with the repo
infrastructure components, run this script to ensure that the repo infrastructure
exists in your :file:`openstack_user_config.yml` file.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/juno-kilo-add-repo-infra.py


----

If you've updated the environment to use **is_metal** for components where
it is not the *default*, run the following script to populate the new
environment with the changes you made in the old environment.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/juno-is-metal-preserve.py


----

Run the old variable removal script to ensure that old options are cleaned up.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/old-variable-remove.sh


----

Run the final upgrade script to clean up any containers and components
throughout the stack that will no longer be needed.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/juno-container-cleanup.sh



Executing the playbooks
^^^^^^^^^^^^^^^^^^^^^^^

If you have **Haproxy** installed on your deployment, run the haproxy play.

.. code-block:: bash

    openstack-ansible haproxy-install.yml


----

Run the container network adjustment play to ensure that the containers
have any erroneous network configuration files removed. The command is forced
to return ``true``. This is because there are containers in the inventory that
have not been built yet and some of the tasks in this play may fail. This is
expected behavior.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/container-network-adjustments.yml || true


----

Run the host adjustments play. This ensures that the container configuration
files are running to the proper spec and that anything that may have been
deprecated or otherwise changed between the RPC Juno and the OpenStack-Ansible
Kilo releases is cleaned up.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/host-adjustments.yml


----

Run the Keystone adjsutments play to correct permissions issues within the
keystone containers.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/keystone-adjustments.yml


----

Run the horizon adjsutments play to correct permissions issues within the
horizon containers.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/horizon-adjustments.yml


----

Run the cinder adjsutments play to correct a potential duplicate container
configuration entry within the cinder containers that has the potential to
impact its ability to start from a stopped state.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/cinder-adjustments.yml


----

If you're upgrading from one of the later releases of Juno, run the log rotate
removal play. The log rotate configuration used in RPC Juno was completly
redesigned in the OpenStack Ansible Kilo release. Notice that this play forces
the return value to 0. This is because there are containers that may not exist
within the environment at this time and the execution of this play should not
fail because of the missing containers.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/remove-juno-log-rotate.yml || true


----

Run the basic host setup play to ensure you have the latest configurations in
place.

.. code-block:: bash

    openstack-ansible setup-hosts.yml


----

When the host setup play has completed, run the to bounce all container networks
throughout the environment. This ensures that all containers have functional
networking. This command is forced to return true.This is because there are
new containers that may not exist within the environment at this time. This
play ensures that those containers are created with the correct configuration.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/container-network-bounce.yml || true


----

Run the infrastructure setup play with the options needed to ensure upgrades to
services such as rabbitmq and galera.

.. code-block:: bash

    openstack-ansible setup-infrastructure.yml -e 'rabbitmq_upgrade=true' -e 'galera_ignore_cluster_state=true'


----

If you were running swift as deployed from RPC Juno, run the swift ring adjustment
play to ensure that the rings are in the appropriate locations.

.. code-block:: bash

    openstack-ansible ${UPGRADE_PLAYBOOKS}/swift-ring-adjustments.yml


----

Run all of the OpenStack plays.

.. code-block:: bash

    openstack-ansible setup-openstack.yml


----

Optional: When the OpenStack setup plays have finished, you can run the the
post-upgrade cleanup. Note that this script removes the original galera
monitoring user, ``haproxy``. If you are still using this user for monitoring,
do not execute this script.

.. code-block:: bash

    ${UPGRADE_SCRIPTS}/post-upgrade-cleanup.sh


Migration and Upgrade Complete
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You should now review the environment and ensure that everything is functional.
If each of the scripts and plays executed successfully, the environment should
be completely upgraded
