# Functional Architecture

The following image is automatically generated from the current full demo compose file. It shows the ROS nodes assigned to different namespaces and their communication topics and types.

![ROS 2 Graph Export](./assets/ros2-graph-export.svg)

> [!NOTE]
> Repositories tagged with 🔗 are not hosted in the [openads-project](https://github.com/openads-project/) GitHub organization

## Interfaces

For communication between nodes, [common interfaces](https://github.com/ros2/common_interfaces) are used whenever possible. For specific automated driving messages, the following additional interface defitions are used.

| Interface Repository | Description |
| --- | --- |
| [perception_interfaces](https://github.com/ika-rwth-aachen/perception_interfaces)🔗 | Message definitions related to perception tasks in Intelligent Transportation Systems |
| [planning_interfaces](https://github.com/ika-rwth-aachen/planning_interfaces)🔗 | Message definitions and actions related to route planning tasks in Intelligent Transportation Systems; message definitions related to trajectory planning tasks in Intelligent Transportation Systems |

## Functional Modules - OpenADServices

### Localization

| OpenADService | Description |
| --- | --- |
| [lanelet2_map_server](https://github.com/openads-project/lanelet2_map_server) | Provides Lanelet2 maps to other modules |

### Perception

| OpenADService | Description |
| --- | --- |
| [point_cloud_fusion](https://github.com/openads-project/point_cloud_fusion) | Fuses multiple point clouds into a single point cloud with common target frame. |
| [point_cloud_object_detection](https://github.com/openads-project/point_cloud_object_detection) | Provides a C++ ROS 2 node for point cloud object detection. |

### Understanding

| OpenADService | Description |
| --- | --- |
| [autoware_multi_object_tracker](https://github.com/thinking-cars/autoware_multi_object_tracker)🔗 | ROS 2 package for tracking multiple objects from configurable detection inputs using data association and extended Kalman filters. |
| [lanelet2_object_list_prediction](https://github.com/openads-project/lanelet2_object_list_prediction) | Predicts future states of multiple objects based on a Lanelet2 Map |

### Planning

| OpenADService | Description |
| --- | --- |
| [lanelet2_route_planning](https://github.com/openads-project/lanelet2_route_planning) | Plans a route on a Lanelet2 map |
| [simple_planner](https://github.com/openads-project/simple_planner) | Generates route-following reference trajectories with safe-stop, traffic-light, turn-signal, and object-aware speed handling. |
| [trajectory_optimization](https://github.com/openads-project/trajectory_optimization) | Periodically solves a nonlinear OCP to generate optimized trajectories for automated driving. |

### Control

| OpenADService | Description |
| --- | --- |
| [ackermann_trajectory_control](https://github.com/openads-project/ackermann_trajectory_control) | Controls Ackermann-steered vehicles based on planned trajectories. |
