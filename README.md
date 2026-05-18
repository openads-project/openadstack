# OpenADStack

<p align="center">
  <a href="https://github.com/openads-project"><img src="https://img.shields.io/badge/OpenADS-f5ff01"/></a>
  <a href="https://github.com/openads-project/openads-dev-environment/blob/main/LICENSE"><img src="https://img.shields.io/github/license/openads-project/openads-dev-environment"/></a>
</p>

> [!IMPORTANT]
> This repository is part of [***OpenADS***](https://github.com/openads-project), the *Open Automated Driving Stack*. *OpenADS* and its modules have been initiated and are currently being maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/de/).

```mermaid
flowchart TD
    I1:::hidden -->|GNSS fix| ego_state_estimation
    I2:::hidden -->|odometry| ego_state_estimation
    I3:::hidden -->|point cloud| point_cloud_object_detection
    ego_state_estimation -->|ego data| lanelet2_route_planning
    ego_state_estimation -->|ego data| simple_planner
    ego_state_estimation -->|ego data| trajectory_optimization
    ego_state_estimation -->|ego data| ackermann_trajectory_control
    lanelet2_map_server -->|map| lanelet2_object_list_prediction
    lanelet2_map_server -->|map| lanelet2_route_planning
    point_cloud_object_detection -->|object list| simple_object_tracking
    simple_object_tracking -->|object list| lanelet2_object_list_prediction
    lanelet2_object_list_prediction -->|object list| simple_planner
    lanelet2_object_list_prediction -->|object list| trajectory_optimization
    lanelet2_route_planning -->|route| simple_planner
    lanelet2_route_planning -->|route| trajectory_optimization
    simple_planner -->|reference trajectory| trajectory_optimization
    trajectory_optimization -->|trajectory| ackermann_trajectory_control
    ackermann_trajectory_control -->|acceleration/curvature| O:::hidden
```
