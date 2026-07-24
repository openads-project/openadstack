from launch import LaunchDescription
from launch.actions import (
    EmitEvent,
    ExecuteProcess,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown

ROUTE_ACTION_NAME = "/planning/lanelet2_route_planning/plan_route"
ROUTE_ACTION_TYPE = "route_planning_msgs/action/PlanRoute"

# Route goal sent to the route planner once its action server is available.
ROUTE_GOAL = (
    "{"
        "destination: {"
            "header: {frame_id: 'map'}, "
            "point: {x: 305.2498474121094, y: 225.9604034423828, z: 0.03127288818359375}"
        "}, "
        "intermediate_destinations: ["
            "{"
                "header: {frame_id: 'map'}, "
                "point: {x: 247.24014282226562, y: 59.348243713378906, z: 1.3430328369140625}"
            "}"
        "]"
    "}"
)


def generate_launch_description():
    bag_play = ExecuteProcess(
        cmd=[
            "ros2", "bag", "play",
            "--input", "/data",
            "--clock"
        ],
        output="screen",
    )

    send_route_goal = ExecuteProcess(
        cmd=[
            "/bin/bash", "-c",
            "until ros2 action list | grep -Fxq -- \"$1\"; do sleep 1; done; "
            "exec ros2 action send_goal \"$1\" \"$2\" \"$3\" --feedback",
            "send-route-goal",
            ROUTE_ACTION_NAME,
            ROUTE_ACTION_TYPE,
            ROUTE_GOAL,
        ],
        output="screen",
    )

    # Shut the launch down (and let the container restart) once the bag finishes.
    shutdown_on_bag_end = RegisterEventHandler(
        OnProcessExit(
            target_action=bag_play,
            on_exit=[EmitEvent(event=Shutdown())],
        )
    )

    return LaunchDescription([
        send_route_goal,
        bag_play,
        shutdown_on_bag_end,
    ])
