OpenStack magnum
################
:tags: openstack, containers, cloud, ansible, magnum
:category: \*nix

Role to install magnum as the alarm functionality of Telemetry

This role will install the following:
    * magnum-api
    * magnum-conductor

.. code-block:: yaml

    - name: Install magnum services
      hosts: magnum_all
      user: root
      roles:
        - { role: "os_magnum", tags: [ "os-magnum" ] }
      vars:
        external_lb_vip_address: 172.16.24.1
        internal_lb_vip_address: 192.168.0.1
        galera_address: "{{ internal_lb_vip_address }}"
