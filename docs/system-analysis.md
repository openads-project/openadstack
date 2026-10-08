# System Analysis

OpenADStack is a distributed system: its modules run as separate ROS 2 nodes in individual containers and exchange data via topics. This makes it hard to tell, from the outside, how long a message takes to travel from sensor input to control output, or where time is lost along the way. This page describes how to record runtime traces of the stack with [ros2_tracing](https://github.com/ros2/ros2_tracing) and how to analyze them, so you can inspect timing and message flow across all modules of the automated driving stack.

## Why Trace the Message Flow?

Tracing records when callbacks run and when messages are published and received, across all traced nodes and over time. It helps you to:

- Pinpoint latency bottlenecks and timing jitter.
- Correlate perception, planning, and control decisions with their sensor inputs.
- Debug race conditions and missing messages across nodes.
- Detect performance regressions after changes.

## How to Trace the Automated Driving Stack

1. Start the stack with tracing enabled by setting the `ROS_TRACING` environment variable:

    ```bash
    export ROS_TRACING=true
    docker compose up -d
    ```

    Tracing is disabled by default (`ROS_TRACING=false`).

2. Use OpenADStack as usual. Trace data is continuously recorded into an in-memory ring buffer, but not yet written to disk.

3. Start capturing a trace snapshot to disk:

    ```bash
    utils/tracing/tracing.sh start
    ```

4. Once you have captured the situation of interest, stop capturing:

    ```bash
    utils/tracing/tracing.sh stop
    ```

    The trace data of each container is copied to `utils/tracing/trace/<timestamp>/<container>/` and removed from the containers.

5. Start the ROS 2 trace analysis tools:

    ```bash
    docker compose -f utils/tracing/docker-compose.yml up
    ```

    The `utils/tracing/trace/` folder is mounted into the analysis container at `/trace`.

### Traced Services

By default, `tracing.sh` traces all running containers (Docker) or pods (Kubernetes) whose name contains one of the following:

- `perception.point-cloud-fusion`
- `perception.point-cloud-object-detection`
- `understanding.autoware-multi-object-tracker`
- `understanding.lanelet2-object-list-prediction`
- `planning.simple-planner`
- `planning.trajectory-optimization`
- `control.ackermann-trajectory-control`

Additional containers can be traced by passing their (partial) names via `EXTRA_TRACING_CONTAINERS`:

```bash
EXTRA_TRACING_CONTAINERS="my-container-1 my-other-container-1" utils/tracing/tracing.sh start
```

> [!NOTE]
> Additional containers must support tracing themselves, i.e., their nodes must be launched with tracing enabled.

## How to Analyze Trace Data

The analysis container provides [Eclipse Trace Compass](https://eclipse.dev/tracecompass/) and Jupyter Notebooks for evaluating the recorded traces. See [ros2-tracing-analysis](https://gitlab.ika.rwth-aachen.de/fb-fi/misc/ros2-tracing-analysis) for usage details.
