# Functional Architecture

The following image is automatically generated from the current full demo compose file. It shows the ROS nodes assigned to different namespaces and their communication topics and types.

[![ROS 2 Graph Export](./assets/ros2-graph-export.svg)](./assets/ros2-graph-export.svg)

*Click the diagram to download the full-size image for zooming.*

## Interfaces

For communication between nodes, [common interfaces](https://github.com/ros2/common_interfaces) are used whereever possible. For specific automated driving messages, the following additional interface defitions are used.

### Common perception message definitions and tools

[`perception_interfaces`](https://github.com/ika-rwth-aachen/perception_interfaces) 🔗

Provides extensible ROS message definitions for the perception task in Cooperative Intelligent Transport Systems. It follows a "code-first" approach and provides tools for easy data access, coordinate transformations and data visualization.

### Common planning message definitions and tools

[`planning_interfaces`](https://github.com/ika-rwth-aachen/planning_interfaces) 🔗

Provides extensible ROS message definitions for the planning task in Cooperative Intelligent Transport Systems. It follows a "code-first" approach and provides tools for easy data access, coordinate transformations and data visualization.

### ROS 2 Support for ETSI ITS messages for V2X Communication

[`etsi_its_messages`](https://github.com/ika-rwth-aachen/etsi_its_messages) 🔗

ROS message definitions for V2X applications (e.g. `CAM`, `CPM`, `DENM`, `MAPEM`, `SPATEM`) generated from the `ASN.1` files officially published by the [European Telecommunications Standards Institute](https://forge.etsi.org/rep/ITS/asn1)

## Functional Modules (OpenADServices)

