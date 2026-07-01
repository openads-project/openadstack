# Functional Architecture

OpenADStack covers the complete automated-driving processing chain from ...

![Functional Architecture](./assets/functional-overview-teaser.svg)
-> hier besser A Modell nehmen

## Input Interfaces
- perception_interfaces
- planning_interfaces
- etsi_its_messages

## Functional Domains

| Domain | Default service | Role |
| ------ | --------------- | ---- |
| Localization | `lanelet2-map-server` | Loads and serves Lanelet2 map data and provides map context for downstream planning. |
| Environment Modeling and Prediction | `lanelet2-object-list-prediction` | Consumes tracked objects and publishes predicted objects for trajectory planning. |
| Planning | `lanelet2-route-planning` | Generates a route from ego-state and route-goal information on a Lanelet2 map. |
| Optimization | `trajectory-optimization` | Combines route, ego state, predicted objects, and reference trajectory input into an optimized trajectory. |
| Control | `ackermann-trajectory-control` | Tracks the optimized trajectory and publishes Ackermann-compatible control commands. |
| Monitoring | `monitoring` | Starts RViz with the repository-provided visualization configuration. |
