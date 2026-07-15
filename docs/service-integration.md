# OpenADService Integration

This guide describes how a validated OpenADService is incorporated into OpenADStack as a reusable reference component. Inclusion assumes that the module has been tested and benchmarked, its role and interfaces have been agreed, and it is intended to become a maintained part of the stack.

OpenADService development itself follows the [OpenADSuite Development](https://openads-project.github.io/openadsuite/openadsuite.html) workflow. Experimental evaluation and use-case-specific configuration belong in a deployment composition, such as [OpenADSim](https://github.com/openads-project/openadsim). The workflow below assumes an existing OpenADService, including a published container image and an OCI Compose artifact.

## Integration Scope

An OpenADService integration must define the module's functional role and interfaces. This includes its subscribed and published ROS 2 topics, namespace, parameters, middleware assumptions, and runtime requirements such as GPU or X11 access. Existing OpenADS interfaces and development guidelines should be preserved wherever possible. The current data flow is documented in the [Functional Architecture](./functional-architecture.md).

The change must also state whether the module replaces an existing function or runs in parallel. A replacement must preserve the downstream contract or update all affected consumers. A parallel service must use distinct outputs and must not alter the default data flow unintentionally. This rationale and the affected interfaces belong in the pull request developed on a dedicated feature branch.

## Repository Representation

Place the new OpenADService within its its functional namespace. Each used OpenADService has a maintained stack override and an automatically generated Compose file:

```text
<domain>/<service>/
├── .docker-compose.oci-overrides.yml
└── docker-compose.yml
```

The two files describe the same OpenADService integration. The override is the source of truth. The generated file provides the resolved representation used by deployment compositions. Their detailed role within OpenADStack is described in the [Technical Architecture](./technical-architecture.md).

## Stack Override

The `.docker-compose.oci-overrides.yml` file references the published OpenADService artifact and adds only stack-specific configuration: the functional namespace, stable input and output topics, connecting services within the OpenADStack, parameter defaults, and the appropriate Compose service template.

```yaml
include:
  - oci://ghcr.io/openads-project/my_openadservice:compose-v1.0.0

services:
  my-openadservice:
    extends:
      file: ../../utils/compose/docker-compose.template.yml
      service: ros2-service
    environment:
      NAMESPACE: /planning
      EGO_DATA_TOPIC: /localization/ego_state_estimation/ego_data
```

Most headless modules extend `ros2-service`. GPU or X11 variants are available as well and documented in the [Technical Architecture](./technical-architecture.md#compose-service-templates).

## Generated Compose File

Run the renderer after changing a stack override:

```bash
python3 utils/scripts/render_compose_sources.py
```

The renderer combines the OCI Compose artifact with the stack override and writes the adjacent `docker-compose.yml`. Both files are version-controlled, but only `.docker-compose.oci-overrides.yml` is edited manually. CI verifies that generated files remain up-to-date.

## Deployment Composition

The generated module definition is consumed by a deployment composition, such as a vehicle setup, OpenADSim, or this repository demo:

```yaml
include:
  - ./openadstack/planning/my_service/docker-compose.yml
```

Default, profile-based, or replacement inclusion is defined by the deployment composition. Add the module to the repository demo only when it contributes to the demonstrated reference data flow. Keep composition-specific parameters and mounts in the consuming deployment composition.
