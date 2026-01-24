# Trace Automated Driving Stack

Tracing lets you see how data and decisions flow through the automated driving stack over time. It helps you:

- Pinpoint latency bottlenecks and timing jitter.
- Correlate perception, planning, and control decisions with sensor inputs.
- Debug race conditions and missing messages across nodes.
- Validate performance regressions after changes.

## How to trace the automated driving stack

1. Set the environment variable `ROS_TRACING="true"` for all relevant containers to activate tracing in supported ROS nodes.
2. Run the stack as usual. Trace data will be buffered but not written to disk.
3. Execute the script `tracing.sh start` to start capturing a trace snapshot on disk.
4. Once finished, stop capturing trace data with `tracing.sh stop`. This will write captured trace data into timestamped subfolders of this folder per container.
5. Start the ROS 2 Trace Analysis tools with `docker compose up`.

### Data Analysis with Eclipse Trace Compass

1. Select `File` --> `Import ...` --> Select root directory: `/trace` --> Chack the corresponding timestamped folders per container in the list --> `Finish`
2. Extend `Tracing` in the Project Explorer --> Right-Click on `Traces` in the Project Explorer --> `Open As Experiment` --> `ROS 2 Expermient (Incubator)`
3. Extend `Experiments` in the Project Explorer --> `Experiment` --> `Views` --> `ROS 2 Messages` --> Right click on `Messages (incubator)` --> `Open`
4. Inspect the message flow, hold CTRL and scroll to zoom in, hold Shift to scroll left/right. Click an one of the bars in the message flow to follow, then click the *Follow this element* button above the graph to analyze the message flow.
5. Extend `Experiments` in the Project Explorer --> `Experiment` --> `Views` --> `ROS 2 Message Flow` --> Right click on `Message Flow (incubator)` --> `Open`
6. You should see the message flow.

### Data Analysis with Jupyter Notebook

1. Connect to the JupyterLab server running ad [http://localhost:8888](http://localhost:8888).
2. Adapt the path in the first cell of the jupyter notebook to the container to be analyzed and run all cells to generate histograms of callback execution durations.

### Tips

- Keep trace windows short to reduce file size.
- Restart the stack before capturing a new trace session to make sure that initialization data is captured, which is required for visualization in Eclipse Trace Compass.
- Make sure that traced ROS nodes are started as `dockeruser`. Otherwise, make sure that Eclipse Trace Compass has file permissions to read the trace data.
