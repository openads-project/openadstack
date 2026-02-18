#!/bin/bash

# Usage: ./tracing.sh {start|stop}

if [ $# -ne 1 ]; then
    echo "Usage: $0 {start|stop}"
    exit 1
fi

ACTION=$1
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# List of container name suffixes to trace
# Default container suffixes
DEFAULT_CONTAINER_SUFFIXES=(
    "perception.point-cloud-fusion-1"
    "perception.point-cloud-object-detection.fused-1"
    "understanding.object-fusion-1"
    "understanding.lanelet2-object-list-prediction-1"
    "planning.simple-planner-1"
    "planning.planning-orchestrator-1"
    "planning.trajectory-optimization-1"
    "control.ackermann-trajectory-control-1"
)

# Allow additional container suffixes via EXTRA_TRACING_CONTAINERS env var
# e.g. EXTRA_TRACING_CONTAINERS="my-container-1 my-other-container-1" ./tracing.sh start
EXTRA_SUFFIXES=()
if [ -n "$EXTRA_TRACING_CONTAINERS" ]; then
    IFS=' ' read -ra EXTRA_SUFFIXES <<< "$EXTRA_TRACING_CONTAINERS"
fi

CONTAINER_SUFFIXES=("${DEFAULT_CONTAINER_SUFFIXES[@]}" "${EXTRA_SUFFIXES[@]}")

DOCKER_USER="dockeruser"

# Arrays to track results
SUCCESS_CONTAINERS=()
FAILED_CONTAINERS=()
MISSING_CONTAINERS=()

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
        echo "Warning: No running container containing '$substring'."
        MISSING_CONTAINERS+=("$substring")
        continue
    fi

    for container in "${MATCHED_CONTAINERS[@]}"; do
        (
            if [ "$ACTION" == "start" ]; then
                echo "Starting tracing in container: $container"

                TRACE_COMMAND="ros2 trace start trace --dual-session"
                docker exec --user "$DOCKER_USER" "$container" bash -ic "$TRACE_COMMAND"
                
                if [ $? -eq 0 ]; then
                    echo "$container" >> /tmp/tracing_success_$$
                else
                    echo "$container" >> /tmp/tracing_failed_$$
                fi

            elif [ "$ACTION" == "stop" ]; then
                echo "Stopping tracing in container: $container"
                STOP_COMMAND="ros2 trace stop trace --dual-session"
                docker exec --user "$DOCKER_USER" "$container" bash -ic "$STOP_COMMAND"
                
                STOP_STATUS=$?
                
                echo "Copy trace files from container: $container"
                mkdir -p "$SCRIPT_DIR/$TIMESTAMP/$container"
                docker cp $container:/home/dockeruser/.ros/tracing/trace "$SCRIPT_DIR/$TIMESTAMP/$container"
                
                COPY_STATUS=$?

                echo "Removing trace files from container: $container"
                REMOVE_COMMAND="rm -rf /home/dockeruser/.ros/tracing"
                docker exec --user "$DOCKER_USER" "$container" bash -ic "$REMOVE_COMMAND"
                
                REMOVE_STATUS=$?
                
                if [ $STOP_STATUS -eq 0 ] && [ $COPY_STATUS -eq 0 ] && [ $REMOVE_STATUS -eq 0 ]; then
                    echo "$container" >> /tmp/tracing_success_$$
                else
                    echo "$container" >> /tmp/tracing_failed_$$
                fi
            fi
        ) &
    done
done

# Wait for all background jobs to complete
wait

# Read results from temporary files
if [ -f /tmp/tracing_success_$$ ]; then
    mapfile -t SUCCESS_CONTAINERS < /tmp/tracing_success_$$
    rm /tmp/tracing_success_$$
fi

if [ -f /tmp/tracing_failed_$$ ]; then
    mapfile -t FAILED_CONTAINERS < /tmp/tracing_failed_$$
    rm /tmp/tracing_failed_$$
fi

# Print summary
echo ""
echo "============================================"
echo "Summary - $ACTION operation:"
echo "============================================"

if [ ${#SUCCESS_CONTAINERS[@]} -gt 0 ]; then
    echo "✓ Successfully ${ACTION}ed tracing for ${#SUCCESS_CONTAINERS[@]} container(s):"
    for container in "${SUCCESS_CONTAINERS[@]}"; do
        echo "  - $container"
    done
else
    echo "✓ No containers ${ACTION}ed successfully"
fi

echo ""

if [ ${#FAILED_CONTAINERS[@]} -gt 0 ]; then
    echo "✗ Failed to $ACTION tracing for ${#FAILED_CONTAINERS[@]} container(s):"
    for container in "${FAILED_CONTAINERS[@]}"; do
        echo "  - $container"
    done
else
    echo "✗ No failures"
fi

echo ""

if [ ${#MISSING_CONTAINERS[@]} -gt 0 ]; then
    echo "⚠ Missing ${#MISSING_CONTAINERS[@]} container(s) (not running):"
    for substring in "${MISSING_CONTAINERS[@]}"; do
        echo "  - $substring"
    done
fi

echo "============================================="
