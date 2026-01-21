# Trace Automated Driving Stack

Tracing lets you see how data and decisions flow through the automated driving stack over time. It helps you:

- Pinpoint latency bottlenecks and timing jitter.
- Correlate perception, planning, and control decisions with sensor inputs.
- Debug race conditions and missing messages across nodes.
- Validate performance regressions after changes.

## How to trace the automated driving stack

1. Set environment variable `ROS_TRACING="true"` (e.g. with `export ROS_TRACING="true"` or in `.env` file) to activate tracing in supported ROS nodes.
2. Runt the stack as usual. Trace data will be buffered but not written to disk.
3. Execute the script `tracing.sh start` to start capturing a trace snapshot on disk.
4. Once finished, stop capturing trace data with `tracing.sh stop`. This will write captured trace data into timestamped subfolders of this folder per container.
5. Start the Eclipse Trace Compass with ROS 2 Incubator plugin with `docker compose up`.
6. Select `File` --> `Import ...` --> Select root directory: `/trace` --> Chack the corresponding timestamped folders per container in the list --> `Finish`
7. Right-Click on `Traces` in the Project Explorer --> `Open As Experiment` --> `ROS 2 Expermient (Incubator)`
8. Extend `Experiments` in the Project Explorer --> `Experiment` --> `Views` --> `ROS 2 Messages` --> Right click on `Messages (incubator)` --> `Open`
9. Inspect the message flow, hold CTRL and scroll to zoom in, hold Shift to scroll left/right. Click an one of the bars in the message flow to follow, then click the *Follow this element* button above the graph to analyze the message flow.
10. Extend `Experiments` in the Project Explorer --> `Experiment` --> `Views` --> `ROS 2 Message Flow` --> Right click on `Message Flow (incubator)` --> `Open`
11. You should see the message flow.

### Tips

- Keep trace windows short to reduce file size.
- Restart the stack before capturing a new trace session to make sure that initialization data is captured, which is required for visualization in Eclipse Trace Compass.
- Make sure that traced ROS nodes are started as `dockeruser`. Otherwise, make sure that Eclipse Trace Compass has file permissions to read the trace data.
