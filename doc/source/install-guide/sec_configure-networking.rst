`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Configuring target host networking
----------------------------------

Edit the ``/etc/openstack_deploy/openstack_user_config.yml`` file to
configure target host networking.

#. Configure the IP address ranges associated with each network in the
   ``cidr_networks`` section:

   .. code-block:: yaml

       cidr_networks:
       # Management (same range as br-mgmt on the target hosts)
       management: CONTAINER_MGMT_CIDR
       # Tunnel endpoints for VXLAN tenant networks
       # (same range as br-vxlan on the target hosts)
       tunnel: TUNNEL_CIDR
       #Storage (same range as br-storage on the target hosts)
       storage: STORAGE_CIDR

   Replace *``*_CIDR``* with the appropriate IP address range in CIDR
   notation. For example, 203.0.113.0/24.

   Use the same IP address ranges as the underlying physical network
   interfaces or bridges configured in `the section called "Configuring
   the network" <sec-hosts-target-network.html>`__. For example, if the
   container network uses 203.0.113.0/24, the *``CONTAINER_MGMT_CIDR``*
   should also use 203.0.113.0/24.

   The default configuration includes the optional storage and service
   networks. To remove one or both of them, comment out the appropriate
   network name.

#. Configure the existing IP addresses in the ``used_ips`` section:

   .. code-block:: yaml

       used_ips:
         - EXISTING_IP_ADDRESSES

   Replace *``EXISTING_IP_ADDRESSES``* with a list of existing IP
   addresses in the ranges defined in the previous step. This list
   should include all IP addresses manually configured on target hosts
   in the `the section called "Configuring the
   network" <sec-hosts-target-network.html>`__, internal load balancers,
   service network bridge, and any other devices to avoid conflicts
   during the automatic IP address generation process.

   Add individual IP addresses on separate lines. For example, to
   prevent use of 203.0.113.101 and 201:

   .. code-block:: yaml

       used_ips:
         - 203.0.113.101
         - 203.0.113.201

   Add a range of IP addresses using a comma. For example, to prevent
   use of 203.0.113.101-201:

   .. code-block:: yaml

       used_ips:
         - 203.0.113.101, 203.0.113.201

#. Configure load balancing in the ``global_overrides`` section:

   .. code-block:: yaml

       global_overrides:
         # Internal load balancer VIP address
         internal_lb_vip_address: INTERNAL_LB_VIP_ADDRESS
         # External (DMZ) load balancer VIP address
         external_lb_vip_address: EXTERNAL_LB_VIP_ADDRESS
         # Container network bridge device
         management_bridge: "MGMT_BRIDGE"
         # Tunnel network bridge device
         tunnel_bridge: "TUNNEL_BRIDGE"

   Replace *``INTERNAL_LB_VIP_ADDRESS``* with the internal IP address of
   the load balancer. Infrastructure and OpenStack services use this IP
   address for internal communication.

   Replace *``EXTERNAL_LB_VIP_ADDRESS``* with the external, public, or
   DMZ IP address of the load balancer. Users primarily use this IP
   address for external API and web interfaces access.

   Replace *``MGMT_BRIDGE``* with the container bridge device name,
   typically ``br-mgmt``.

   Replace *``TUNNEL_BRIDGE``* with the tunnel/overlay bridge device
   name, typically ``br-vxlan``.

#. Configure optional networks in the ``provider_networks`` subsection:

   .. code-block:: yaml

         provider_networks:
           - network:
               group_binds:
                 - glance_api
                 - cinder_api
                 - cinder_volume
                 - nova_compute
               type: "raw"
               container_bridge: "br-storage"
               container_interface: "eth2"
               ip_from_q: "storage"

   The default configuration includes the optional storage and service
   networks. To remove one or both of them, comment out the entire
   associated stanza beginning with the *- network:* line.

#. Configure OpenStack Networking tunnel/overlay network in the
   ``provider_networks`` subsection:

   .. code-block:: yaml

         provider_networks:
           - network:
               group_binds:
                 - neutron_linuxbridge_agent
               container_bridge: "br-vxlan"
               container_interface: "eth10"
               ip_from_q: "tunnel"
               type: "vxlan"
               range: "TUNNEL_ID_RANGE"
               net_name: "vxlan"

   Replace *``TUNNEL_ID_RANGE``* with the tunnel ID range. For example,
   1:1000.

#. Configure OpenStack Networking provider networks in the
   ``provider_networks`` subsection:

   .. code-block:: yaml

         provider_networks:
           - network:
               group_binds:
                 - neutron_linuxbridge_agent
               container_bridge: "br-vlan"
               container_interface: "eth11"
               type: "flat"
               net_name: "vlan"
           - network:
               group_binds:
                 - neutron_linuxbridge_agent
               container_bridge: "br-vlan"
               container_interface: "eth11"
               type: "vlan"
               range: VLAN_ID_RANGE
               net_name: "vlan"

   Replace *``VLAN_ID_RANGE``* with the VLAN ID range for each VLAN
   provider network. For example, 1:1000. Create a similar stanza for
   each additional provider network.

--------------

.. include:: navigation.txt
