Scripts
=======

This section describes the scripts that are used in the upgrade process in
further detail.

Within the main :file:`scripts` directory there is an :file:`upgrade-utilities`
directory, which contains additional scripts. These scripts facilitate the
initial upgrade process.


bootstrap-new-ansible.sh
------------------------

This bash script ensures that the correct version of Ansible is installed.
In the process of installing Ansible, the script will check for, backup, and
remove any :file:`pip.conf` file that may be found within the home folder of
the user running the upgrade. Typically this is ``root``.


create-new-openstack-deploy-structure.sh
----------------------------------------

This bash script creates the new directory script used in OpenStack-Ansible.
The script backs up the original :file:`rpc_deploy` configuration files and
inventory and then migrates these items to :file:`openstack_deploy`. When this
script is executed, the original :file:`rpc_deploy` directory will be archived as
:file:`pre-upgrade-backup.tgz`, which is stored in the executing user's home
folder. Later, the directory will be moved to :file:`/etc/rpc_deploy.OLD`, and a
:file:``DEPRECATED.txt` text file will be created to indicate that the old
directory is no longer in service. The original :file:`/etc/rpc_deploy.OLD`
directory remains on disk is to ensure that you have something to refer back
to immediately if there are any failures or errors during the upgrade.


juno-container-cleanup.sh
-------------------------

This bash script removes several containers from all hosts and inventory, which
cleans up any containers that re no longer needed. This also cleans up haproxy
installations and configurations, as well as pip configurations throughout all
running containers and hosts.


juno-is-metal-preserve.py
-------------------------

This python script looks through the existing environment.yml file and collects
data on any container component that may have had the variable **is_metal** set
to true. If anything is found, the script updates the current :file:`environment.yml`
files with the appropriate settings. This ensures that the value is carried over
for the upgrade.


juno-kilo-add-repo-infra.py
---------------------------

This python script looks through the existing :file:`openstack_user_variables.yml`
file and ensures that the repo infrastructure has been assigned to a host. If the
script is unable to determine the location of the repo infrastructure, the script
will use the existing infra nodes as targets for the new repo server deployment.
If the script needs to create entries for the repo infrastructure it will do so
within the :file:`/etc/openstack_deploy/conf.d directory` using the file :file:`repo-servers.yml`.


juno-kilo-ldap-conversion.py
----------------------------

This python script looks through all available user variable files and attempts
to identify settings that are used for ``keystone_ldap_.*``. If the variables
are found the script will write the new dictionary and generator syntax into the
:file:`/etc/openstack_deploy/user_secrets.yml` file.

.. note::
   The reason that the LDAP variables are written into the ``user_secrets.yml``
   from ``user_variables.yml`` is because we believe that the deploy should take
   extra steps to protect the LDAP configuration. This move allows the deployer
   to encrypt that one file using the **ansible-vault** command if the so desire.


juno-rpc-extras-create.py
-------------------------

This python script looks for and moves Rackspace-specific configuration options
from the generic :file:`user_variables.yml` file and into the
:file:`/etc/openstack_deploy/user_extras_variables.yml` file. This separates
the values set for RPC from those set for OpenStack Ansible. These variables are
important to what can be implemented using the rpc-openstack software repository
found here: https://github.com/rcbops/rpc-openstack


new-variable-prep.sh
--------------------

This bash script adds variables that may be missing when upgrading from Juno to
Kilo, appending variables to the system as needed. There are several new secret
items that have been added to the configuration files, and randomly generated
passwords will be created for these items upon execution of the script.


old-variable-remove.sh
----------------------

This bash script removes variables from the user variable files that may be
duplicates, have changed, or are otherwise no longer needed.


post-upgrade-cleanup.sh
-----------------------

This bash script cleans up any remaining items that may need to be removed
upon completion of the upgrade.
