# OpenAD**Stack**

<p align="center">
  <a href="https://openads-project.github.io"><img src="https://img.shields.io/badge/OpenADS-45ccc6"/></a>
  <a href="https://www.ros.org"><img src="https://img.shields.io/badge/ROS 2-jazzy-22314e"/></a>
  <a href="https://github.com/openads-project/openadstack/releases/latest"><img src="https://img.shields.io/github/v/release/openads-project/openadstack"/></a>
  <a href="https://github.com/openads-project/openadstack/blob/main/LICENSE"><img src="https://img.shields.io/github/license/openads-project/openadstack"/></a>
</p>

**Baseline reference implementation for modular ROS 2 automated-driving stacks in OpenADS.**

OpenADStack bundles reusable OpenADServices into a Docker Compose based reference stack. It supports different deployment compositions, from real-world automated-driving research with the [karl. research vehicle](https://karl.ac/) to lightweight and repeatable simulation tests in [OpenADSim](https://openads-project.github.io/openadsim/openadsim.html).

**🚀 [Quick Start](#-quick-start)** | **📐 [Architecture](#-architecture)** | **📝 [Documentation](#-documentation)** | **🙏 [Acknowledgements](#-acknowledgements)**

> [!NOTE]
> This repository is part of [***OpenADS***](https://github.com/openads-project), the *Open Automated Driving Systems* project. *OpenADS* and its modules have been initiated and are currently being maintained by the [**Institute for Automotive Engineering (ika) at RWTH Aachen University**](https://www.ika.rwth-aachen.de/de/).

<div align="center">
  <video controls autoplay width="720" style="max-width: 100%;" src="https://github.com/user-attachments/assets/af4f9095-960a-43c5-a959-af4afa81243c"></video>
  <br>
  <em>Watch the preview above or <a href="https://www.youtube.com/watch?v=B0Lnu-1w9KE">open the full video on YouTube</a>.</em>
</div>

## 🚀 Quick Start

> [!NOTE]
> For closed-loop simulation, scenario execution, maps, and simulator adapters, [OpenADSim](https://openads-project.github.io/openadsim/openadsim.html) is the recommended entry point.

> [!IMPORTANT]
> Make sure that the general [OpenADS system requirements](https://openads-project.github.io/start/start.html#requirements) are fulfilled. Graphical applications require access to a local X11 server.

OpenADStack is usually part of a larger deployment composition, for example with the [karl. research vehicle](https://karl.ac/) or in an [OpenADSim simulation setup](https://openads-project.github.io/openadsim/openadsim.html). For a first look at OpenADStack itself, a demo is provided in this repository. It runs the stack open-loop on recorded ROS 2 data, so you can inspect the stack behavior without starting additional simulation or vehicle components.

- Two demos using different parts of OpenADStack are provided:
  - **Basic Demo** without Perception: Start the open-loop demo using recorded detections:

    ```bash
    cd demo
    xhost +local:
    docker compose up -d
    ```

  - **Extended Demo:** Start the open-loop demo including perception OpenADServices running on recorded raw sensor data:

    ```bash
    cd demo
    xhost +local:
    export COMPOSE_PROFILES=demo-extended && docker compose up -d
    ```

> [!NOTE]
> The extended demo requires an NVIDIA GPU with compute capability 8.0 or higher, and additional disk
> space of 14GB for its larger bag files.

- **Stop** the demo with:

  ```bash
  docker compose down
  ```

## 📐 Architecture

OpenADStack is an L4 automated driving software stack built on ROS 2. It aims to enable suitably equipped vehicles to operate in traffic without human intervention.

The system is composed of services that primarily communicate through ROS messages. Each service uses a Docker image containing one or more ROS nodes. The services are composed and deployed using Docker Compose.

The modular architecture is organized into domains such as localization, perception, planning, and control.

The architecture is documented from three complementary perspectives:

- The [**Functional Architecture**](./docs/functional-architecture.md) describes the system's functional modules, their responsibilities, and the interfaces between them.
- The [**Integration Architecture**](./docs/integration-architecture.md) explains how released OpenADServices are assembled into the reference stack.
- The [**Deployment Composition**](./docs/deployment-composition.md) describes how the stack or selected parts can be embedded in custom vehicle and simulation setups.

The following image shows the so-called *A Model*, a functional reference architecture for automated driving systems originally developed in the [UNICARagil project](http://www.unicaragil.de/en/). The left side of the A describes the world modeling while the right side describes planning and actuation. The horizontal bar describes safety fallbacks, e.g. to perform a minimum risk maneuver in case of a degradation in the higher levels. The on-board system is supported by remote operations, e.g. for technical supervision.

<div align="center" style="text-align: center;">

![OpenADStack functional architecture](./docs/assets/A-Model.svg)

</div>

The OpenADStack architecture follows a [*Doer/Checker/Fallback* pattern](https://www.the-autonomous.com/wp-content/uploads/2023/12/wg-safetyarchitecture-full-report-a4.pdf), which continually evolves from a rule-based architecture into a hybrid architecture that combines a white-box safety *Checker* with an MLOps-driven end-to-end driving model. For more details, take a look at our proposed [architecture for learning-based behavior planning](https://arxiv.org/abs/2608.12198) and our proposed [MLOps architecture](https://arxiv.org/abs/2605.12719).

![OpenADStack architecture roadmap](./docs/assets/openadstack-architecture.svg)

In the initial release in **Phase I**, OpenADStack consists of lidar-based learned perception and a rule-based planner module, which initially acts as both *Doer* and *Checker*. The planned motion is converted into actuation signals by a model-based controller.

In **Phase II** (until the end of 2026), the architecture is planned to be extended with a learned planning module acting as *Doer* while keeping the rule-based planner as *Checker*. This enables a data-driven MLOps process for continual improvement. In addition, camera- and radar-based perception, remote operations, and minimum-risk maneuvers are planned.

As the collected database grows, **Phase III** (until the end of 2027) plans to replace the learned planner with an end-to-end driving model acting as *Doer*, while keeping the learned perception and rule-based planning path as *Checker*.

## 📝 Documentation

The documentation contains:

- [Getting Started](./docs/getting-started.md)
- [Functional Architecture](./docs/functional-architecture.md)
- [Integration Architecture](./docs/integration-architecture.md)
- [Deployment Composition](./docs/deployment-composition.md)
- [System Analysis](./docs/system-analysis.md)

## 🙏 Acknowledgements

### Citation

We hope that OpenADStack can help your research. If this is the case, please cite it using the metadata specified in [CITATION.cff](https://github.com/openads-project/openadstack/blob/main/CITATION.cff), or click on Cite this repository in GitHub's About section on the top right.

### Related Publications

<details>

<summary><strong>karl. – A Research Vehicle for Automated and Connected Driving, 2026</strong></summary>

> *([IEEEXplore](https://ieeexplore.ieee.org/document/11625211), [arXiv](https://arxiv.org/abs/2602.08842), [ResearchGate](https://www.researchgate.net/publication/400622171_karl_-_A_Research_Vehicle_for_Automated_and_Connected_Driving))*  
>
> Jean-Pierre Busch, Lukas Ostendorf, Guido Linden, Lennart Reiher, Till Beemelmanns, Bastian Lampe, Timo Woopen, Lutz Eckstein
> [Institute for Automotive Engineering (ika), RWTH Aachen University](https://www.ika.rwth-aachen.de/en/)
>
> <sup>*Abstract* – As highly automated driving is transitioning from single-vehicle closed-access testing to commercial deployments of public ride-hailing in selected areas (e.g., Waymo), automated driving and connected cooperative intelligent transport systems (C-ITS) remain active fields of research. Even though simulation is omnipresent in the development and validation life cycle of automated and connected driving technology, the complex nature of public road traffic and software that masters it still requires real-world integration and testing with actual vehicles. Dedicated vehicles for research and development allow testing and validation of software and hardware components under real-world conditions early on. They also enable collecting and publishing real-world datasets that let others conduct research without vehicle access, and support early demonstration of futuristic use cases. In this paper, we present karl., our new research vehicle for automated and connected driving. Apart from major corporations, few institutions worldwide have access to their own L4-capable research vehicles, restricting their ability to carry out independent research. This paper aims to help bridge that gap by sharing the reasoning, design choices, and technical details that went into making karl. a flexible and powerful platform for research, engineering, and validation in the context of automated and connected driving. More impressions of karl. are available at [https://karl.ac/](https://karl.ac/).</sup>

</details>

<details>

<summary><strong>Learning-Based Behavior Planning for Automated Driving: Real-World Integration and Deployment, 2026</strong></summary>

> *([arXiv](https://arxiv.org/abs/2608.12198), [ResearchGate](https://www.researchgate.net/publication/412211767_Learning-Based_Behavior_Planning_for_Automated_Driving_Real-World_Integration_and_Deployment))*  
>
> Jean-Pierre Busch, Guido Linden, Jan Bergmann, Lutz Eckstein
> [Institute for Automotive Engineering (ika), RWTH Aachen University](https://www.ika.rwth-aachen.de/en/)
>
> <sup>*Abstract* – Recent research in machine and deep learning has shown the potential of learningbased motion planning approaches to improve the driving behavior of automated vehicles, especially in complex environments. However, their complex nature and lack of transparency can hinder explainability and trustworthiness and complicate safety assurance. Motivated by these challenges, we propose a hybrid planning architecture that combines the advantages of machine learning with the verifiability and the determinism of classical approaches. Specifically, we developed a deep neural network to interpret complex traffic scenes and propose driving behavior, while an optimization-based supervision layer validates this proposal and enforces explicit drivability and safety constraints. We evaluate the learned planner's driving behavior in open-loop studies on real-world urban data, discuss system integration aspects for stable closed-loop operation, and report results from real-world deployment on our research vehicle karl.. </sup>

</details>

### Licensing

The source code in this repository is licensed under Apache-2.0, see [LICENSE](https://github.com/openads-project/openadstack/blob/main/LICENSE). Container images provided by this repository may contain third-party software shipped with their own license terms.

### Funding

Development and maintenance of this repository are supported by the following projects. We acknowledge the funding of the respective institutions.

| Project                                          | Funding Institution                                           | Grant Number |
| ------------------------------------------------ | ------------------------------------------------------------- | ------------ |
| [6GEM+](https://6gem.de)                         | 🇩🇪 Federal Ministry for Research, Technology and Space (BMFTR) | 16KIS2409K   |
| [AIGGREGATE](https://aiggregate.eu/)             | 🇪🇺 European Union                                              | 101202457    |
| [AIthena](https://aithena.eu/)                   | 🇪🇺 European Union                                              | 101076754    |
| [autotech.agil](https://www.autotechagil.de/en/) | 🇩🇪 Federal Ministry for Research, Technology and Space (BMFTR) | 01IS22088A   |

<p>
  <img src="https://www.drought.uni-freiburg.de/stressres/images/bmftr-logo/image" height=70>
  <img src="https://ec.europa.eu/regional_policy/images/information-sources/logo-download-center/eu_funded_en.jpg" height=70>
</p>

<sup><sub>Funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Climate, Infrastructure and Environment Executive Agency (CINEA). Neither the European Union nor CINEA can be held responsible for them.</sup></sup>
