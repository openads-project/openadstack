# System Analysis

intro paragraph

## Trace Message Flow

Tracing lets you see how data and decisions flow through the automated driving stack over time. It helps you:

- Pinpoint latency bottlenecks and timing jitter.
- Correlate perception, planning, and control decisions with sensor inputs.
- Debug race conditions and missing messages across nodes.
- Validate performance regressions after changes.

## How to trace the automated driving stack

1. Set the environment variable `ROS_TRACING="true"` befor running `docker compose up -d` to activate tracing in supported ROS nodes.
2. Run the stack as usual. Trace data will be buffered but not written to disk.
3. Execute the script `utils/tracing/tracing.sh start` to start capturing a trace snapshot on disk.
4. Once finished, stop capturing trace data with `utils/tracing/tracing.sh stop`. This will write captured trace data into timestamped subfolders of this folder per container.
5. Start the ROS 2 Trace Analysis tools with `docker compose -f utils/tracing/docker-compose.yml up`.

### How to analyze trace data using Eclipse Trace Compass and Jupyter Notebooks

See [ros2-tracing-analysis](https://gitlab.ika.rwth-aachen.de/fb-fi/misc/ros2-tracing-analysis).
