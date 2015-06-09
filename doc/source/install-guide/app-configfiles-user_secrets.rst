`Home <common-front.html>`__ OpenStack Ansible Installation Guide

``user_secrets.yml`` configuration file
---------------------------------------

.. code-block:: yaml

    ---

    ## Rabbitmq Options
    rabbitmq_password:
    rabbitmq_cookie_token:

    ## Tokens
    memcached_encryption_key:

    ## Container default user
    container_openstack_password:

    ## Galera Options
    galera_root_password:

    ## Keystone Options
    keystone_container_mysql_password:
    keystone_auth_admin_token:
    keystone_auth_admin_password:
    keystone_service_password:

    ## Cinder Options
    cinder_container_mysql_password:
    cinder_service_password:
    cinder_v2_service_password:
    cinder_profiler_hmac_key:

    ## Glance Options
    glance_container_mysql_password:
    glance_service_password:
    glance_profiler_hmac_key:

    ## Heat Options
    heat_stack_domain_admin_password:
    heat_container_mysql_password:
    ### THE HEAT AUTH KEY NEEDS TO BE 32 CHARACTERS LONG ##
    heat_auth_encryption_key:
    ### THE HEAT AUTH KEY NEEDS TO BE 32 CHARACTERS LONG ##
    heat_service_password:
    heat_cfn_service_password:
    heat_profiler_hmac_key:

    ## Horizon Options
    horizon_container_mysql_password:
    horizon_secret_key:

    ## Neutron Options
    neutron_container_mysql_password:
    neutron_service_password:

    ## Nova Options
    nova_container_mysql_password:
    nova_metadata_proxy_secret:
    nova_ec2_service_password:
    nova_service_password:
    nova_v3_service_password:
    nova_v21_service_password:
    nova_s3_service_password:

    ## Swift Options:
    swift_service_password:
    swift_container_mysql_password:
    swift_dispersion_password:
    ### Once the swift cluster has been setup DO NOT change these hash values!
    swift_hash_path_suffix:
    swift_hash_path_prefix:

      

--------------

.. include:: navigation.txt