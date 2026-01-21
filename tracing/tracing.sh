#!/bin/bash

# Usage: ./tracing.sh {start|stop}

if [ $# -ne 1 ]; then
    echo "Usage: $0 {start|stop}"
    exit 1
fi

ACTION=$1
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)

# List of container name suffixes to trace
CONTAINER_SUFFIXES=(
    "perception.point-cloud-fusion-1"
    "perception.point-cloud-object-detection.fused-1"
)

DOCKER_USER="dockeruser"

# Validate action
if [ "$ACTION" != "start" ] && [ "$ACTION" != "stop" ]; then
    echo "Usage: $0 {start|stop}"
    exit 1
fi

mapfile -t RUNNING_CONTAINERS < <(docker ps --format '{{.Names}}')

for suffix in "${CONTAINER_SUFFIXES[@]}"; do
    MATCHED_CONTAINERS=()
    for container in "${RUNNING_CONTAINERS[@]}"; do
        if [[ "$container" == *"$suffix" ]]; then
            MATCHED_CONTAINERS+=("$container")
        fi
    done

    if [ ${#MATCHED_CONTAINERS[@]} -eq 0 ]; then
        echo "Warning: No running container ending with '$suffix'."
        continue
    fi

    for container in "${MATCHED_CONTAINERS[@]}"; do
        if [ "$ACTION" == "start" ]; then
            echo "Starting tracing in container: $container"

            # Start tracing with timestamped path
            TRACE_COMMAND="ros2 trace start trace --dual-session"
            docker exec --user "$DOCKER_USER" "$container" bash -ic "$TRACE_COMMAND"

        elif [ "$ACTION" == "stop" ]; then
            echo "Stopping tracing in container: $container"
            STOP_COMMAND="ros2 trace stop trace --dual-session && mv ~/.ros/tracing/trace /trace/$TIMESTAMP"
            docker exec --user "$DOCKER_USER" "$container" bash -ic "$STOP_COMMAND"
        fi
    done
done
