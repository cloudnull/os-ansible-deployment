`Home <common-front.html>`__ OpenStack Ansible Installation Guide

Host networking
---------------

The combination of containers and flexible deployment options requires
implementation of advanced Linux networking features such as bridges and
namespaces.

*Bridges* provide layer 2 connectivity (similar to switches) among
physical, logical, and virtual network interfaces within a host. After
creating a bridge, the network interfaces are virtually "plugged in" to
it.

RPC software uses bridges to connect physical and logical network
interfaces on the host to virtual network interfaces within containers
on the host.

*Namespaces* provide logically separate layer 3 environments (similar to
routers) within a host. Namespaces use virtual interfaces to connect
with other namespaces including the host namespace. These interfaces,
often called ``veth`` pairs, are virtually "plugged in" between
namespaces similar to patch cables connecting physical devices such as
switches and routers.

Each container has a namespace that connects to the host namespace with
one or more ``veth`` pairs. Unless specified, the system generates
random names for ``veth`` pairs.

The relationship between physical interfaces, logical interfaces,
bridges, and virtual interfaces within containers is shown in
`Figure 2.2, "Network
components" <sec_overview_host-networking.html#fig_overview_networkcomponents>`__.

 

**Figure 2.2. Network components**

|image2|

| 

Target hosts can contain the following network bridges:

-  LXC internal ``lxcbr0``:

   -  Mandatory (automatic).

   -  Provides external (typically internet) connectivity to containers.

   -  Automatically created and managed by LXC. Does not directly attach
      to any physical or logical interfaces on the host because iptables
      handle connectivity. Attaches to ``eth0`` in each container.

-  Container management ``br-mgmt``:

   -  Mandatory.

   -  Provides management of and communication among infrastructure and
      OpenStack services.

   -  Manually created and attaches to a physical or logical interface,
      typically a ``bond0`` VLAN subinterface. Also attaches to ``eth1``
      in each container.

-  Storage ``br-storage``:

   -  Optional.

   -  Provides segregated access to block storage devices between
      Compute and Block Storage hosts.

   -  Manually created and attaches to a physical or logical interface,
      typically a ``bond0`` VLAN subinterface. Also attaches to ``eth2``
      in each associated container.

-  OpenStack Networking tunnel/overlay ``br-vxlan``:

   -  Mandatory.

   -  Provides infrastructure for VXLAN tunnel/overlay networks.

   -  Manually created and attaches to a physical or logical interface,
      typically a ``bond1`` VLAN subinterface. Also attaches to
      ``eth10`` in each associated container.

-  OpenStack Networking provider ``br-vlan``:

   -  Mandatory.

   -  Provides infrastructure for VLAN and flat networks.

   -  Manually created and attaches to a physical or logical interface,
      typically ``bond1``. Also attaches to ``eth11`` in each associated
      container. Does not contain an IP address because it only handles
      layer 2 connectivity.

`Figure 2.3, "Container network
architecture" <sec_overview_host-networking.html#fig_overview_networkarch-container>`__
provides a visual representation of network components for services in
containers.

 

**Figure 2.3. Container network architecture**

|image3|

| 

The RPC software installs the Compute service in a bare metal
environment rather than within a container. `Figure 2.4, "Bare/Metal
network
architecture" <sec_overview_host-networking.html#fig_overview_networkarch-bare>`__
provides a visual representation of the unique layout of network
components on a Compute host.

 

**Figure 2.4. Bare/Metal network architecture**

|image4|

| 

--------------

.. include:: navigation.txt

.. |image2| image:: figures/1/a/a/a/rpc-common/figures/rpc9-networkcomponents.png
.. |image3| image:: figures/1/a/a/a/rpc-common/figures/rpc9-networkarch-container-external.png
.. |image4| image:: figures/1/a/a/a/rpc-common/figures/rpc9-networkarch-bare-external.png
