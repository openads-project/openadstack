#!/usr/bin/env python

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import LaunchConfigurationNotEquals
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import LifecycleNode, SetParameter


def generate_launch_description():

    params_arg = DeclareLaunchArgument('params', default_value='params.yml')
    config = PathJoinSubstitution([
        get_package_share_directory("lanelet2_route_planning"), "config",
        LaunchConfiguration('params')
    ])

    node_name_default = 'global_planner'
    node_name_arg = DeclareLaunchArgument('node_name',
                                          default_value=node_name_default)

    use_sim_time_arg = DeclareLaunchArgument('use_sim_time_arg', default_value='False')

    node = LifecycleNode(
        package="lanelet2_route_planning",
        executable="global_planner_node",
        name=LaunchConfiguration('node_name'),
        namespace="",
        output="screen",
        emulate_tty=True,
        parameters=[config],
        remappings=[
            ("/carla_its_adapter/ego_data", "/ego_state_estimation_node/ego_state"),
        ]
    )

    node_group = GroupAction(actions=[
        SetParameter(name='use_sim_time',
                     value=LaunchConfiguration('use_sim_time_arg'),
                     condition=LaunchConfigurationNotEquals(
                         'use_sim_time_arg', "None")), node
    ])

    return LaunchDescription([
        params_arg,
        node_name_arg,
        use_sim_time_arg,
        node_group
    ])
