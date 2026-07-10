# Service Integration

This guide focuses on integrating a new OpenADService into the default OpenADStack setup after the module has already been tested and considered useful for the stack. It is about making a component part of OpenADStack itself, not about trying out a new component for the first time.

For source-level module development, use the [OpenADSuite Development](https://openads-project.github.io/openadsuite/openadsuite.html) guide. For early testing of a new component, integrate it directly in [OpenADSim](https://github.com/openads-project/openadsim) or another use-case-specific setup first. The steps below assume that the service already exists as a ROS 2 module with a Docker image and, ideally, a published Compose artifact.

> [!NOTE]
> Applying OpenADStack to a new use case is a different task. Vehicle setups, simulator demos, recorded-data demos, component experiments, and project-specific parameter mounts usually belong to an integration or deployment repository around OpenADStack. Move a component into OpenADStack only when it should become part of the reusable default stack.

## 1. Work on a Feature Branch

Add new services on a dedicated feature branch. This keeps the stack reviewable and makes it clear which files belong to the new module integration.

```bash
git switch -c integrate/my-openadservice
```

The final change should be submitted as a pull request. In that pull request, make the intended role explicit:

- Does the service replace an existing module?
- Does it run in parallel to an existing module?
- Is it optional, experimental, or part of the default stack?
- Which upstream and downstream topics define its boundary?
- Why is this integration better or necessary compared to the current stack behavior?

## 2. Define the Service Boundary

Before adding files, define the service contract. The boundary must match the surrounding stack.

Check:

- subscribed topics and message types
- published topics and message types
- namespace and node name
- required parameters and configuration files
- whether `USE_SIM_TIME` is needed
- middleware assumptions
- whether the service needs GPU, X11, or special host access

Prefer existing OpenADS interface packages and topic conventions. A service is easier to integrate when it preserves the expected input and output contracts of the domain it belongs to.

The default OpenADStack service chain currently uses these central topics:

| Topic | Role |
| ----- | ---- |
| `/localization/ego_state_estimation/ego_data` | ego-state input for planning and control |
| `/localization/ego_state_estimation/nav_sat_fix` | GNSS input for map server context |
| `/understanding/simple_object_tracking/object_list` | object-list input for prediction |
| `/understanding/lanelet2_object_list_prediction/object_list` | predicted-object input for trajectory optimization |
| `/planning/lanelet2_route_planning/route` | route input for trajectory optimization |
| `/planning/simple_planner/trajectory` | optional reference trajectory input |
| `/planning/trajectory_optimization/trajectory` | optimized trajectory output |
| `/control/ackermann_trajectory_control/controls` | control-command output |

## 3. Choose Replacement or Parallel Integration

Decide whether the new service replaces an existing service or runs next to the current stack.

Use a replacement when:

- the new module provides the same functional role as an existing service
- the output contract stays compatible for downstream services
- the old service should no longer run in the selected configuration

Use a parallel integration when:

- the module provides diagnostics, monitoring, validation, or an optional alternative output
- the existing default stack should continue to run unchanged
- the service is experimental and should not affect downstream behavior yet

If the replacement changes topic names or message types, update downstream services at the same time and document the changed boundary in the pull request.

## 4. Add the Folder Structure

Follow the existing domain layout and add the service below the matching domain, for example:

```text
planning/my_service/
```

Each service folder contains the stack override and the generated Compose file:

```text
<domain>/<service>/
├── .docker-compose.oci-overrides.yml
└── docker-compose.yml
```

Use existing service folders as templates and keep names consistent with the service image, ROS 2 package, and node name.

## 5. Add the Stack Override

The `.docker-compose.oci-overrides.yml` file connects the service-level artifact to OpenADStack. It should set stack-specific defaults such as namespaces, topic names, parameters, and template usage.

Example:

```yaml
include:
  - oci://ghcr.io/openads-project/my_openadservice:compose-v1.0.0

services:
  my-openadservice:
    environment:
      # --- name ------
      NAMESPACE: /planning
      # --- inputs ----
      EGO_DATA_TOPIC: /localization/ego_state_estimation/ego_data
      ROUTE_TOPIC: /planning/lanelet2_route_planning/route
      # --- other -----
      PARAMS: /params.yml
    extends:
      file: ../../docker-compose-essentials/docker-compose.template.yml
      service: ros2-service
```

Choose a shared template according to the service requirements:

| Template | Use when |
| -------- | -------- |
| `ros2-service` | Standard headless ROS 2 service |
| `ros2-gpu-service` | Service needs GPU access but no GUI |
| `ros2-gpu-x11-service` | Service needs GPU and X11, for example visualization |

## 6. Generate the Resolved Compose File

OpenADStack keeps generated `docker-compose.yml` files next to the override files. Regenerate them after adding or changing `.docker-compose.oci-overrides.yml`:

```bash
python3 scripts/render_compose_sources.py
```

Commit both files:

- `<domain>/<service>/.docker-compose.oci-overrides.yml`
- `<domain>/<service>/docker-compose.yml`

## 7. Include the Service in the Stack

Add the new service Compose file to the top-level `docker-compose.yml` under the matching domain.

Example:

```yaml
include:
  # planning
  - planning/lanelet2_route_planning/docker-compose.yml
  - planning/trajectory_optimization/docker-compose.yml
  - planning/my_openadservice/docker-compose.yml
```

If the service is optional, use Compose profiles or document why it should not start by default.

## 8. Validate the Integration

Inspect the effective service list:

```bash
docker compose config --services
```

Start the stack or the relevant profile:

```bash
docker compose up -d
```

Check logs:

```bash
docker compose logs -f my-openadservice
```

Inspect ROS 2 topics and node connectivity:

```bash
docker compose exec monitoring bash
ros2 topic list
ros2 node list
ros2 node info /planning/my_openadservice
```

For replacements, verify that downstream services still receive the expected topics. For parallel integrations, verify that the new service does not accidentally shadow or remap existing default topics.

## 9. Document the Change

Update the documentation when the new service changes the stack structure or data flow:

- [Functional Architecture](./functional-architecture.md): functional role, inputs, outputs, and domain placement
- [Technical Architecture](./technical-architecture.md): service composition or integration-level changes
- [Usage](./usage.md): only if users need a new command, profile, or runtime option
