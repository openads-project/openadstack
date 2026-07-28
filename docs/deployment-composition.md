# Deployment Composition

> [!NOTE]
> 🚧 This section is currently under construction.

OpenADStack provides reusable blueprint compositions for a full reference stack. A custom deployment composition combines all or selected parts of OpenADStack with platform-specific overrides and additional services. There are different deployment compositions that actively use OpenADStack:

- the [demo](https://github.com/openads-project/openadstack/tree/main/demo) adds recorded inputs, maps, and monitoring to create an open-loop setup;
- the [karl. research vehicle](https://karl.ac/) adds sensor drivers, remote interfaces, and actuator interfaces;
- [OpenADSim](https://openads-project.github.io/openadsim/openadsim.html) provides simulator adapters and scenario-based testing.

## Customized Deployment Composition

> [!NOTE]
> This section guides you through the process of integrating OpenADStack into a custom vehicle or simulation deployment composition.

Add OpenADStack to the vehicle or simulation repository as a Git submodule:

```bash
git submodule add https://github.com/openads-project/openadstack.git openadstack
git submodule update --init --recursive
```

A deployment can then integrate OpenADStack blueprint compositions in one of two ways.

### Include and Override

Use `include` to import several services while keeping their original service names. As in the repository demo, the consuming Compose file can include the required blueprints and then override selected services:

```yaml
include:
  - ./openadstack/localization/lanelet2_map_server/docker-compose.yml
  - ./openadstack/perception/point_cloud_object_detection/docker-compose.yml
  - ./openadstack/understanding/lanelet2_object_list_prediction/docker-compose.yml

services:
  lanelet2-map-server:
    environment:
      PARAMS: /params.yml
    volumes:
      - ./config/map-server.yml:/params.yml

  point-cloud-object-detection:
    profiles:
      - enable-perception
```

This pattern is especially useful when the imported blueprints require only minor modifications.

### Extend and Override

Use `extends` to select and customize OpenADServices individually, for example to assign deployment-specific service names and profiles:

```yaml
services:
  planning.trajectory-optimization:
    profiles:
      - planning
    extends:
      file: ./openadstack/planning/trajectory_optimization/docker-compose.yml
      service: trajectory-optimization
    environment:
      PARAMS: /params.yml
    volumes:
      - ./config/trajectory-optimization.yml:/params.yml:ro
```

> [!NOTE]
> Make sure to integrate all relevant blueprint compositions. The demo's [docker-compose.yml](https://github.com/openads-project/openadstack/blob/main/demo/docker-compose.yml) provides an overview of the minimal reference composition.

## Add Platform Services

Drivers, simulator adapters, localization sources, and actuator gateways belong to the custom deployment composition rather than OpenADStack. They can be declared directly or imported from additional Compose files:

```yaml
include:
  - ./drivers/docker-compose.yml
  - ./actuators/docker-compose.yml
```

These services provide the ROS 2 interfaces expected by OpenADStack. For example, drivers publish sensor and vehicle-state data, while an actuator gateway translates the OpenADStack control output into commands for the vehicle interface.

> [!IMPORTANT]
> Planning to integrate OpenADStack into your own vehicle? We would be happy to support your project. Get in touch through [OpenADS Support](https://openads-project.github.io/support/support.html) to discuss your platform, interfaces, and deployment architecture.
