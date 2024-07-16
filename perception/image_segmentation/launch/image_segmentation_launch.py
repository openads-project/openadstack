import os
from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():

    config = os.path.join(
        get_package_share_directory("image_segmentation"),
        "config",
        "params.yaml"
    )

    return LaunchDescription([
        DeclareLaunchArgument("namespace", default_value=""),
        DeclareLaunchArgument("name", default_value="image_segmentation"),
        DeclareLaunchArgument("image", default_value="~/image"),
        DeclareLaunchArgument("segmentation",default_value="~/segmentation"),
        Node(
            package="image_segmentation",
            executable="image_segmentation",
            namespace=LaunchConfiguration("namespace"),
            name=LaunchConfiguration("name"),
            parameters=[config],
            output="screen",
            remappings=[
                ("~/image", LaunchConfiguration("image")),
                ("~/segmentation", LaunchConfiguration("segmentation"))
            ]
        )
    ])
