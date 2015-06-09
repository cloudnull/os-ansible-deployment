`Home <common-front.html>`__ OpenStack Ansible Installation Guide

``extra_container.yml`` configuration file
------------------------------------------

.. code-block:: yaml

    ---

    component_skel:
      example_api:
        belongs_to:
          # This is a meta group of a given component type.
          - example_all

    container_skel:
      example_api_container:
        belongs_to:
          # This is a group of containers mapped to a physical host.
          - example-infra_containers
        contains:
          # This maps back to an item in the component_skel.
          - example_api
        properties:
          # These are arbitrary key value pairs.
          service_name: example_service
          # This is the image that the lxc container will be built from.
          container_release: trusty

    physical_skel:
      # This maps back to items in the container_skel.
      example-infra_containers:
        belongs_to:
          - all_containers
      # This is a required pair for the container physical entry.
      example-infra_hosts:
        belongs_to:
          - hosts


--------------

.. include:: navigation.txt