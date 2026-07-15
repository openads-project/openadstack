# OpenAD**Stack**

<p align="center">
  <a href="https://github.com/openads-project"><img src="https://img.shields.io/badge/OpenADS-ffff00"/></a>
  <a href="https://www.ros.org"><img src="https://img.shields.io/badge/ROS 2-jazzy-22314e"/></a>
  <a href="https://github.com/openads-project/openadstack/releases/latest"><img src="https://img.shields.io/github/v/release/openads-project/openadstack"/></a>
  <a href="https://github.com/openads-project/openadstack/blob/main/LICENSE"><img src="https://img.shields.io/github/license/openads-project/openadstack"/></a>
</p>

**Baseline reference implementation for modular ROS 2 automated-driving stacks in OpenADS.**

OpenADStack bundles reusable OpenADS services into a Docker Compose based reference stack. It is designed for different integrations: from real-world automated-driving research with the [karl. research vehicle](https://karl.ac/) to lightweight and repeatable simulation tests in [OpenADSim](https://github.com/openads-project/openadsim).

**🚀 [Quick Start](#-quick-start)** | **🏗️ [Functional Overview & Architecture](#-functional-overview--architecture)** | **📝 [Documentation](#-documentation)** | **🙏 [Acknowledgements](#-acknowledgements)**

> [!NOTE]
> This repository is part of [***OpenADS***](https://github.com/openads-project), the *Open Automated Driving Systems* project. *OpenADS* and its modules have been initiated and are currently being maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/de/).

![OpenADStack running on the karl. research vehicle](./docs/assets/teaser-openadstack.gif)

## 🚀 Quick Start

> [!NOTE]
> For closed-loop simulation, scenario execution, maps, and simulator adapters, [OpenADSim](https://github.com/openads-project/openadsim) is the recommended entry point.

> [!IMPORTANT]
> Make sure that the general [OpenADS system requirements](https://openads-project.github.io/start/start.html#requirements) are fulfilled.

OpenADStack is usually part of an integration, for example with the [karl. research vehicle](https://karl.ac/) or in a simulation setup. For a first look at OpenADStack itself, a demo is provided in this repository. It runs the stack open-loop on recorded ROS 2 data, so you can inspect the stack behavior without starting additional simulation or vehicle modules.

- Two demos using different parts of OpenADStack are provided:
  - **Basic Demo:** Start a basic open-loop demo with planning components running on recorded detections:

    ```bash
    cd demo
    docker compose up -d
    ```

  - **Perception Demo:** Start the open-loop demo including perception modules running on recorded raw sensor data:

    ```bash
    cd demo
    docker compose -f docker-compose.perception.yml up -d
    ```

- **Stop** the demo with:

  ```bash
  docker compose down
  ```

## 🏗️ Functional Overview & Architecture

OpenADStack covers the complete automated driving processing chain from sensing & perception, environment modeling & prediction to planning & control, as well as, monitoring tools and other essentials. The detailed data flow is described in [Functional Architecture](./docs/functional-architecture.md).

OpenADStack is organized into functional domains:

- [**Esentials:**](./essentials/) base services, e.g. for traffic routing or model serving
- [**Localization:**](./localization/) map serving and vehicle dynamics state estimation
- [**Perception:**](./perception/) object detection & tracking, scene interpretation & environment modeling
- [**Understanding:**](./understanding/) environment prediction and scene enrichment
- [**Planning:**](./planning/) route & trajectory planning
- [**Control:**](./control/) trajectory optimization and vehicle dynamics control
- [**Monitoring:**](./monitoring/) inspection and runtime visualization
- [**Utilities:**](./utils/) helper functions

This structure keeps individual services replaceable while preserving stable interfaces between the stack domains.

![OpenADStack functional overview](./docs/assets/functional-overview.png)

The technical architecture is based on modular ROS 2 services, shared Docker Compose templates, generated service Compose files, and consistent OpenADS topics. The detailed service structure is described in [Technical Architecture](./docs/technical-architecture.md).

## 📝 Documentation

The documentation contains:

- [Usage](./docs/usage.md)
- [Functional Architecture](./docs/functional-architecture.md)
- [Technical Architecture](./docs/technical-architecture.md)
- [Service Integration](./docs/service-integration.md)

## 🙏 Acknowledgements

### Citation

We hope that OpenADStack can help your research. If this is the case, please cite it using the following metadata.

```
@misc{OpenADStack,
  author = {Institute for Automotive Engineering (ika), RWTH Aachen University},
  title = {{OpenADStack}},
  url = {https://github.com/openads-project/openadstack},
  year = {2026},
  doi = {TODO}
}
```

### Related Publications

<details>

<summary><strong>karl. - A Research Vehicle for Automated and Connected Driving, 2026</strong></summary>

> *([IEEEXplore](https://ieeexplore.ieee.org/document/10588502), [arXiv](http://arxiv.org/abs/2404.01836), [ResearchGate](https://www.researchgate.net/publication/379484629_CARLOS_An_Open_Modular_and_Scalable_Simulation_Framework_for_the_Development_and_Testing_of_Software_for_C-ITS))*  
>
> Jean-Pierre Busch, Lukas Ostendorf, Guido Linden, Lennart Reiher, Till Beemelmanns, Bastian Lampe, Timo Woopen, Lutz Eckstein
> [Institute for Automotive Engineering (ika), RWTH Aachen University](https://www.ika.rwth-aachen.de/en/)
>
> <sup>*Abstract* – As highly automated driving is transitioning from single-vehicle closed-access testing to commercial deployments of public ride-hailing in selected areas (e.g., Waymo), automated driving and connected cooperative intelligent transport systems (C-ITS) remain active fields of research. Even though simulation is omnipresent in the development and validation life cycle of automated and connected driving technology, the complex nature of public road traffic and software that masters it still requires real-world integration and testing with actual vehicles. Dedicated vehicles for research and development allow testing and validation of software and hardware components under real-world conditions early on. They also enable collecting and publishing real-world datasets that let others conduct research without vehicle access, and support early demonstration of futuristic use cases. In this paper, we present karl., our new research vehicle for automated and connected driving. Apart from major corporations, few institutions worldwide have access to their own L4-capable research vehicles, restricting their ability to carry out independent research. This paper aims to help bridge that gap by sharing the reasoning, design choices, and technical details that went into making karl. a flexible and powerful platform for research, engineering, and validation in the context of automated and connected driving. More impressions of karl. are available at [https://karl.ac/](https://karl.ac/).</sup>

</details>

### Licensing

The source code in this repository is licensed under Apache-2.0, see [LICENSE](https://github.com/openads-project/openadstack/blob/main/LICENSE). Container images provided by this repository may contain third-party software shipped with their own license terms.

### Funding

Development and maintenance of this repository are supported by the following projects. We acknowledge the funding of the respective institutions.

| Project | Funding Institution | Grant Number |
| --- | --- | --- |
| [6GEM+](https://6gem.de) | 🇩🇪 Federal Ministry for Research, Technology and Space (BMFTR) | 16KIS2409K |
| [AIGGREGATE](https://aiggregate.eu/) | 🇪🇺 European Union | 101202457 |
| [AIthena](https://aithena.eu/) | 🇪🇺 European Union | 101076754 |
| [autotech.agil](https://www.autotechagil.de/en/) | 🇩🇪 Federal Ministry for Research, Technology and Space (BMFTR) | 01IS22088A |

<p>
  <img src="https://www.drought.uni-freiburg.de/stressres/images/bmftr-logo/image" height=70>
  <img src="https://ec.europa.eu/regional_policy/images/information-sources/logo-download-center/eu_funded_en.jpg" height=70>
</p>

<sup><sub>Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Climate, Infrastructure and Environment Executive Agency (CINEA). Neither the European Union nor CINEA can be held responsible for them.</sup></sup>
