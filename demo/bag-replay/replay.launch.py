from launch import LaunchDescription
from launch.actions import (
    EmitEvent,
    ExecuteProcess,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown

# Route goal sent to the route planner once its action server is available.
# `ros2 action send_goal` blocks until the server is up, so no explicit
# wait/poll loop is needed.
ROUTE_GOAL = (
    "{"
        "destination: {"
            "header: {frame_id: 'map'}, "
            "point: {x: 303.0938415527344, y: 235.60919189453125, z: 0.03127288818359375}"
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
            "--start-offset", "20",
            "--playback-duration", "200",
            "--input", "/data",
            "--clock",
            "--regex",
            "/drivers.*|/localization/ego_state_estimation.*|"
            "/perception/point_cloud_object_detection_ouster/object_list|/tf",
        ],
        output="screen",
    )

    send_route_goal = ExecuteProcess(
        cmd=[
            "ros2", "action", "send_goal",
            "/planning/lanelet2_route_planning/plan_route",
            "route_planning_msgs/action/PlanRoute",
            ROUTE_GOAL,
            "--feedback",
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
