# Hardware-Agnostic Automated Driving Stack

As a composition of ITS modules, this repository defines a software stack for automated driving. The AD stack architecture is designed to be agnostic to hardware, i.e., it can be run on different vehicles equipped with different sensing and actuation capabilities. This flexibility also allows to run the AD stack in simulation. See [Platforms](#platforms) for a list of vehicle / simulation platforms with AD stack integration. See [Integration](#integration) for instructions on how to integrate the AD stack into a new platform.


## Architecture

![stack](assets/stack.png)


## Integration

This repository only defines the blueprint for a flexible AD stack. Integration into vehicles or simulation takes place in dedicated platform repositories. As an example, integrating the AD stack into the [cc-platform](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform) for the VW Passat CC research vehicle involves the following steps.

1. Define services for platform-specific [hardware drivers](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform/-/tree/main/drivers?ref_type=heads) (*Sensing*) and/or *Actuation* and include them in the top-level [`docker-compose.yml`](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform/-/blob/main/docker-compose.yml?ref_type=heads).
1. Add the `automated-driving-stack` as a Git submodule.
1. Pick services or groups of services (e.g., *Planning*) defined in the AD stack and include them in the top-level [`docker-compose.yml`](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform/-/blob/main/docker-compose.yml?ref_type=heads).
1. If AD stack services need to be configured with platform-specific parameters, [extend AD stack services instead of inclusion](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform/-/blob/main/perception/image-segmentation/docker-compose.yml?ref_type=heads) or [pass arguments to AD stack services using environment variables](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform/-/blob/main/perception/point-cloud-object-detection/docker-compose.yml?ref_type=heads).


## Platforms

### Vehicles

- [cc-platform](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/cc-platform)

### Simulation

- [simulation-platform](https://gitlab.ika.rwth-aachen.de/fb-fi/its-compositions/simulation-platform)
