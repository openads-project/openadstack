# Getting Started

OpenADStack is designed to be included in a larger deployment composition that provides sensor or simulation inputs, vehicle interfaces, and environment-specific configuration. Examples include operation on the [karl. research vehicle](https://karl.ac/) and closed-loop simulation with [OpenADSim](https://github.com/openads-project/openadsim). OpenADSim is the recommended entry point for complete simulation workflows with scenarios, maps, and configurable OpenADStack setups.

```{note}
See [Deployment Composition](./deployment-composition.md) for the intended boundary between OpenADStack and vehicle- or simulation-specific deployments.
```

To make OpenADStack directly accessible from this repository, the `demo` folder provides a self-contained open-loop setup. It replays recorded ROS 2 data, starts the stack with a predefined route, and opens the monitoring environment. This is a convenient way to explore the OpenADServices, data flow, and outputs without connecting a vehicle or simulator.

> [!IMPORTANT]
> Make sure that the general [OpenADS requirements](https://openads-project.github.io/start/start.html#requirements) are fulfilled.

## Demo Configurations

The demo provides two configurations corresponding to the processing paths shown in the [functional architecture](./functional-architecture.md).

### Demo without Perception

The default configuration focuses on the right-hand, planning-oriented side of the A-model. A detected object list is replayed from the recording and passed to the downstream prediction, planning, and optimization OpenADServices. This keeps the setup lightweight while exposing the central planning pipeline.

### Full Demo

The extended configuration also activates the left-hand perception side of the A-model. Instead of using the recorded object lists, it processes the recorded LiDAR point clouds through point-cloud fusion and point-cloud object detection before passing the resulting objects to the same downstream OpenADServices. This configuration requires a compatible NVIDIA GPU as described in the OpenADS requirements.

## Run the Demo

Clone the repository including all submodules and run all commands from the OpenADStack demo folder.

```bash
git clone --recurse-submodules git@github.com:openads-project/openadstack.git
cd openadstack/demo
```

Start the demo without perception:

```bash
export COMPOSE_FILE=docker-compose.demo.yml && docker compose up -d
```

Alternatively, start the full demo including perception:

```bash
export COMPOSE_FILE=docker-compose.demo-full.yml && docker compose up -d
```

Inspect the active Compose services:

```bash
docker compose ps
docker compose config --services
```

RViz starts as part of the monitoring Compose service and visualizes the replayed inputs and generated stack outputs. Each bag playback cycle runs for approximately three and a half minutes. The bag-replay Compose service then starts it again automatically.

Stop the selected demo configuration with:

```bash
docker compose down
```

## Recorded Demo Inputs

The demo recording supplies the external runtime data that would normally come from a vehicle or simulator:

- driver and sensor topics below `/drivers`, including the front-left and rear-right Ouster LiDAR point clouds used by the full demo
- ego-state and navigation data below `/localization/ego_state_estimation`
- the vehicle and sensor frame transforms on `/tf`
- a recorded point-cloud detected object list for the demo without perception
- simulated ROS time through the bag player's `/clock` output

The Lanelet2 map and visualization configuration are mounted from the `demo` folder rather than read from the bag. After the route-planning action becomes available, the demo also submits a predefined destination and intermediate destination. The setup is therefore deterministic and intended for inspection rather than closed-loop driving.

## Inspect ROS 2 Topics

Open a shell in a ROS 2-enabled stack container:

```bash
docker compose exec monitoring bash
```

List topics:

```bash
ros2 topic list
```

Inspect central data flow topics:

```bash
ros2 topic echo /localization/ego_state_estimation/ego_data
ros2 topic echo /understanding/lanelet2_object_list_prediction/object_list
ros2 topic echo /planning/trajectory_optimization/trajectory
ros2 topic echo /control/ackermann_trajectory_control/controls
```

Leave the container shell with:

```bash
exit
```

## Configuration

Most stack settings are already configured through environment variables in the OpenADService Compose files:

- namespace and node name
- input and output topic names
- parameter file paths
- `LOG_LEVEL`
- `USE_SIM_TIME`
- OpenADService-specific runtime options

For example, `planning/trajectory_optimization/docker-compose.yml` defines the ego-data input, predicted-object input, route input, reference trajectory input, and optimized trajectory output topic.

To customize a deployment composition, prefer a small Compose override file instead of editing generated OpenADService Compose files directly:

```yaml
services:
  trajectory-optimization:
    environment:
      EGO_DATA_TOPIC: /my_stack/ego_data
```

Start the stack with the override:

```bash
docker compose -f docker-compose.yml -f my-openadstack.override.yml up -d
```

## Development Process & Tools

For developing or modifying OpenADServices, follow the [OpenADSuite development workflow](https://openads-project.github.io/openadsuite/openadsuite.html). It describes the recommended template repositories, development containers, release workflow, and registry artifacts used by OpenADStack.

Additional helper tools are documented in the [OpenADSuite tools overview](https://openads-project.github.io/openadsuite/tools.html).
