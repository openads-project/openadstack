#!/bin/bash

# Usage: ./tracing.sh {start|stop}

if [ $# -ne 1 ]; then
    echo "Usage: $0 {start|stop}"
    exit 1
fi

ACTION=$1
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# List of container name substrings to trace
# Default container substrings
DEFAULT_CONTAINER_SUBSTRINGS=(
    "perception.point-cloud-fusion"
    "perception.point-cloud-object-detection"
    "understanding.autoware-multi-object-tracker"
    "understanding.lanelet2-object-list-prediction"
    "planning.simple-planner"
    "planning.trajectory-optimization"
    "control.ackermann-trajectory-control"
)

# Allow additional container substrings via EXTRA_TRACING_CONTAINERS env var
# e.g. EXTRA_TRACING_CONTAINERS="my-container-1 my-other-container-1" ./tracing.sh start
EXTRA_SUBSTRINGS=()
if [ -n "$EXTRA_TRACING_CONTAINERS" ]; then
    IFS=' ' read -ra EXTRA_SUBSTRINGS <<< "$EXTRA_TRACING_CONTAINERS"
fi

CONTAINER_SUBSTRINGS=("${DEFAULT_CONTAINER_SUBSTRINGS[@]}" "${EXTRA_SUBSTRINGS[@]}")

DOCKER_USER="dockeruser"
TRACE_ROOT="/home/dockeruser/.ros/tracing"

format_target_label() {
    local target_type=$1
    local target_namespace=$2
    local target_name=$3

    if [ "$target_type" == "docker" ]; then
        echo "$target_name"
    else
        echo "$target_namespace/$target_name"
    fi
}

format_target_output_dir() {
    local target_type=$1
    local target_namespace=$2
    local target_name=$3

    if [ "$target_type" == "docker" ]; then
        echo "$target_name"
    else
        echo "k8s-${target_namespace}-${target_name}"
    fi
}

exec_in_target() {
    local target_type=$1
    local target_namespace=$2
    local target_name=$3
    local command=$4

    if [ "$target_type" == "docker" ]; then
        docker exec --user "$DOCKER_USER" "$target_name" bash -ic "$command"
    else
        kubectl exec -n "$target_namespace" "$target_name" -- bash -ic "$command"
    fi
}

copy_trace_from_target() {
    local target_type=$1
    local target_namespace=$2
    local target_name=$3
    local destination_dir=$4

    if [ "$target_type" == "docker" ]; then
        docker cp "$target_name:$TRACE_ROOT/trace" "$destination_dir"
    else
        kubectl cp "$target_namespace/$target_name:/root/.ros/tracing/trace" "$destination_dir"
    fi
}

# Arrays to track results
SUCCESS_TARGETS=()
FAILED_TARGETS=()
MISSING_TARGETS=()

# Validate action
if [ "$ACTION" != "start" ] && [ "$ACTION" != "stop" ]; then
    echo "Usage: $0 {start|stop}"
    exit 1
fi

mapfile -t RUNNING_CONTAINERS < <(docker ps --format '{{.Names}}' 2>/dev/null)
mapfile -t RUNNING_PODS < <(kubectl get pods -A --field-selector=status.phase=Running --no-headers -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name 2>/dev/null)

for substring in "${CONTAINER_SUBSTRINGS[@]}"; do
    MATCHED_TARGETS=()

    for container in "${RUNNING_CONTAINERS[@]}"; do
        if [[ "$container" == *"$substring"* ]]; then
            MATCHED_TARGETS+=("docker||$container")
        fi
    done

    for pod_entry in "${RUNNING_PODS[@]}"; do
        read -r namespace pod_name <<< "$pod_entry"
        if [[ "$pod_name" == *"$substring"* ]]; then
            MATCHED_TARGETS+=("k8s|$namespace|$pod_name")
        fi
    done

    if [ ${#MATCHED_TARGETS[@]} -eq 0 ]; then
        echo "Warning: No running target containing '$substring'."
        MISSING_TARGETS+=("$substring")
        continue
    fi

    for target in "${MATCHED_TARGETS[@]}"; do
        target_type=${target%%|*}
        target_remainder=${target#*|}
        target_namespace=${target_remainder%%|*}
        target_name=${target_remainder#*|}
        (
            TARGET_LABEL=$(format_target_label "$target_type" "$target_namespace" "$target_name")

            if [ "$ACTION" == "start" ]; then
                echo "Starting tracing in target: $TARGET_LABEL"

                TRACE_COMMAND="ros2 trace start trace --dual-session"
                exec_in_target "$target_type" "$target_namespace" "$target_name" "$TRACE_COMMAND"
                
                if [ $? -eq 0 ]; then
                    echo "$TARGET_LABEL" >> /tmp/tracing_success_$$
                else
                    echo "$TARGET_LABEL" >> /tmp/tracing_failed_$$
                fi

            elif [ "$ACTION" == "stop" ]; then
                echo "Stopping tracing in target: $TARGET_LABEL"
                STOP_COMMAND="ros2 trace stop trace --dual-session"
                exec_in_target "$target_type" "$target_namespace" "$target_name" "$STOP_COMMAND"
                
                STOP_STATUS=$?
                
                echo "Copy trace files from target: $TARGET_LABEL"
                TARGET_OUTPUT_DIR="$SCRIPT_DIR/trace/$TIMESTAMP/$(format_target_output_dir "$target_type" "$target_namespace" "$target_name")"
                mkdir -p "$TARGET_OUTPUT_DIR"
                copy_trace_from_target "$target_type" "$target_namespace" "$target_name" "$TARGET_OUTPUT_DIR"
                
                COPY_STATUS=$?

                echo "Removing trace files from target: $TARGET_LABEL"
                REMOVE_COMMAND="rm -rf $TRACE_ROOT"
                exec_in_target "$target_type" "$target_namespace" "$target_name" "$REMOVE_COMMAND"
                
                REMOVE_STATUS=$?
                
                if [ $STOP_STATUS -eq 0 ] && [ $COPY_STATUS -eq 0 ] && [ $REMOVE_STATUS -eq 0 ]; then
                    echo "$TARGET_LABEL" >> /tmp/tracing_success_$$
                else
                    echo "$TARGET_LABEL" >> /tmp/tracing_failed_$$
                fi
            fi
        ) &
    done
done

# Wait for all background jobs to complete
wait

# Read results from temporary files
if [ -f /tmp/tracing_success_$$ ]; then
    mapfile -t SUCCESS_TARGETS < /tmp/tracing_success_$$
    rm /tmp/tracing_success_$$
fi

if [ -f /tmp/tracing_failed_$$ ]; then
    mapfile -t FAILED_TARGETS < /tmp/tracing_failed_$$
    rm /tmp/tracing_failed_$$
fi

# Print summary
echo ""
echo "============================================"
echo "Summary - $ACTION operation:"
echo "============================================"

if [ ${#SUCCESS_TARGETS[@]} -gt 0 ]; then
    echo "✓ Successfully ${ACTION}ed tracing for ${#SUCCESS_TARGETS[@]} target(s):"
    for target in "${SUCCESS_TARGETS[@]}"; do
        echo "  - $target"
    done
else
    echo "✓ No targets ${ACTION}ed successfully"
fi

echo ""

if [ ${#FAILED_TARGETS[@]} -gt 0 ]; then
    echo "✗ Failed to $ACTION tracing for ${#FAILED_TARGETS[@]} target(s):"
    for target in "${FAILED_TARGETS[@]}"; do
        echo "  - $target"
    done
else
    echo "✗ No failures"
fi

echo ""

if [ ${#MISSING_TARGETS[@]} -gt 0 ]; then
    echo "⚠ Missing ${#MISSING_TARGETS[@]} target(s) (not running):"
    for substring in "${MISSING_TARGETS[@]}"; do
        echo "  - $substring"
    done
fi

echo "============================================="
