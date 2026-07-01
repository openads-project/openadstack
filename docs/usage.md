# Usage

**❗ Important**

Make sure that the general [OpenADS requirements](https://openads-project.github.io/start/start.html#requirements) are fulfilled.


## Running OpenADStack Directly

Run all commands from the OpenADStack demo folder.

Pull the configured service images:

```bash
docker compose pull
```

Start the stack:

```bash
docker compose up -d
```

Inspect the active services:

```bash
docker compose ps
docker compose config --services
```

Stop the stack:

```bash
docker compose down
```

> [!NOTE]
> When started directly, OpenADStack will only become functionally active if the expected input topics are available.
>
> For a complete closed-loop experience, start OpenADStack through OpenADSim with the OpenADStack profiles enabled. OpenADSim provides simulation backend selection, maps and scenarios, ego-state and object-list inputs, adapter services, GUI-based configuration, and the OpenADStack services from this repository. See the [OpenADSim documentation](https://openads-project.github.io/openadsim/openadsim.html) for the full workflow.

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
ros2 topic echo /understanding/lanelet2_object_list_prediction/predicted_object_list
ros2 topic echo /planning/trajectory_optimization/trajectory
ros2 topic echo /control/ackermann_trajectory_control/controls
```

Leave the container shell with:

```bash
exit
```

## Configuration

Most stack settings are already configured through environment variables in the service Compose files:

- namespace and node name
- input and output topic names
- parameter file paths
- `LOG_LEVEL`
- `USE_SIM_TIME`
- module-specific runtime options

For example, `planning/trajectory_optimization/docker-compose.yml` defines the ego-data input, predicted-object input, route input, reference trajectory input, and optimized trajectory output topic.

To customize a deployment, prefer a small Compose override file instead of editing generated service files directly:

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

For developing new modules or modifying existing OpenADS services, follow the [OpenADSuite development workflow](https://openads-project.github.io/openadsuite/openadsuite.html). It describes the recommended template repositories, development containers, release workflow, and registry artifacts used by OpenADStack integrations.

Additional helper tools are documented in the [OpenADSuite tools overview](https://openads-project.github.io/openadsuite/tools.html).
