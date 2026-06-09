# docker-compose-essentials

TODO

| Service Template              | Description                                                  |
| :---------------------------- | :----------------------------------------------------------- |
| `base-service`                | Base service                                                 |
| `x11-service`                 | Enables X11 GUI forwarding                                   |
| `gpu-service`                 | Makes all NVIDIA GPUs available                              |
| `nvidia-soc-service`          | Makes integrated NVIDIA SoC GPU available                    |
| `gpu-x11-service`             | Enables X11 GUI forwarding for `gpu-service`                 |
| `nvidia-soc-x11-service`      | Enables X11 GUI forwarding for `nvidia-soc-service`          |
| `ros2-service`                | Base ROS 2 service with configurable RMW                     |
| `ros2-zenoh-service`          | Base ROS 2 service with RMW Zenoh                            |
| `ros2-fastrtps-service`       | Base ROS 2 service with RMW Fast RTPS                        |
| `ros2-cyclone-service`        | Base ROS 2 service with RMW Cyclone DDS                      |
| `ros2-x11-service`            | Enables X11 GUI forwarding for `ros2-service`                |
| `ros2-gpu-service`            | Makes all NVIDIA GPUs available for `ros2-service`           |
| `ros2-nvidia-soc-service`     | Makes integrated NVIDIA SoC GPU available for `ros2-service` |
| `ros2-gpu-x11-service`        | Enables X11 GUI forwarding for `ros2-gpu-service`            |
| `ros2-nvidia-soc-x11-service` | Enables X11 GUI forwarding for `ros2-nvidia-soc-service`     |
| `zenoh-router`                | Zenoh router for ROS 2 services with Zenoh RMW               |

```mermaid
flowchart BT

    %% === LEGEND ===

    subgraph legend["Legend"]
        key4["ROS 2"]
        key2["GPU"]
        key3["NVIDIA SoC"]
        key1["X11"]
    end

    %% === NODES & EDGES ===

    x11-service --> base-service
    gpu-service --> base-service
    nvidia-soc-service --> base-service
    gpu-x11-service --> gpu-service
    nvidia-soc-x11-service --> nvidia-soc-service

    ros2-zenoh-service --> base-service
    ros2-fastrtps-service --> base-service
    ros2-cyclone-service --> base-service

    ros2-service --> ros2-zenoh-service
    ros2-service -.-> ros2-fastrtps-service
    ros2-service -.-> ros2-cyclone-service

    ros2-x11-service --> ros2-service
    ros2-gpu-service --> ros2-service
    ros2-nvidia-soc-service --> ros2-service
    ros2-gpu-x11-service --> ros2-gpu-service
    ros2-nvidia-soc-x11-service --> ros2-nvidia-soc-service

    zenoh-router

    %% === STYLE ===

    classDef ros fill:#22314E,color:#ffffff,stroke:#22314E
    classDef gpu stroke:#1f77b4,stroke-width:3px
    classDef soc stroke:#76B900,stroke-width:3px
    classDef x11 stroke-dasharray:5 5

    class ros2-service,ros2-zenoh-service,ros2-fastrtps-service,ros2-cyclone-service,ros2-x11-service,ros2-gpu-service,ros2-nvidia-soc-service,ros2-gpu-x11-service,ros2-nvidia-soc-x11-service,key4 ros
    class gpu-service,gpu-x11-service,ros2-gpu-service,ros2-gpu-x11-service,key2 gpu
    class nvidia-soc-service,nvidia-soc-x11-service,ros2-nvidia-soc-service,ros2-nvidia-soc-x11-service,key3 soc
    class gpu-x11-service,ros2-gpu-x11-service x11
    class nvidia-soc-x11-service,ros2-nvidia-soc-x11-service x11

    style key1 stroke:#ffffff,stroke-width:3px,stroke-dasharray:5 5
    style x11-service stroke:#ffffff,stroke-width:3px,stroke-dasharray:5 5
```
