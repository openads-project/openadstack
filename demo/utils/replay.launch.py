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
EGO_DATA_TOPIC = "/localization/ego_state_estimation/ego_data"

# Route goal sent once per replay cycle after the action server and ego data are available.
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
    wait_for_route_action = ExecuteProcess(
        cmd=[
            "/bin/bash", "-c",
            "until ros2 action list | grep -Fxq -- \"$1\"; do sleep 1; done",
            "wait-for-route-action",
            ROUTE_ACTION_NAME,
        ],
        output="screen",
    )

    bag_play = ExecuteProcess(
        cmd=[
            "ros2", "bag", "play",
            "--input", "/data",
            "--clock",
            "--remap", "/perception/point_cloud_object_detection_ouster/object_list:=/perception/point_cloud_object_detection/object_list"
        ],
        output="screen",
    )

    wait_for_ego_data = ExecuteProcess(
        cmd=[
            "/bin/bash", "-c",
            "until ros2 topic echo \"$1\" --once >/dev/null 2>&1; do sleep 1; done",
            "wait-for-ego-data",
            EGO_DATA_TOPIC,
        ],
        output="screen",
    )

    send_route_goal = ExecuteProcess(
        cmd=[
            "ros2", "action", "send_goal",
            ROUTE_ACTION_NAME,
            ROUTE_ACTION_TYPE,
            ROUTE_GOAL,
            "--feedback",
        ],
        output="screen",
    )

    # Start the ego-data waiter before playback so the first message cannot be missed.
    start_demo_when_ready = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_for_route_action,
            on_exit=[wait_for_ego_data, bag_play],
        )
    )

    send_route_goal_on_first_ego_data = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_for_ego_data,
            on_exit=[send_route_goal],
        )
    )

    # Shut the launch down (and let the container restart) once the bag finishes.
    shutdown_on_bag_end = RegisterEventHandler(
        OnProcessExit(
            target_action=bag_play,
            on_exit=[EmitEvent(event=Shutdown())],
        )
    )

    return LaunchDescription([
        shutdown_on_bag_end,
        send_route_goal_on_first_ego_data,
        start_demo_when_ready,
        wait_for_route_action,
    ])
