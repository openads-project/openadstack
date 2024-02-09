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
        DeclareLaunchArgument(
            "image",
            default_value="~/image"
        ),
        DeclareLaunchArgument(
            "segmented_image",
            default_value="~/segmented_image"
        ),
        Node(
            package="image_segmentation",
            executable="image_segmentation",
            namespace="/perception",
            name="image_segmentation",
            parameters=[config],
            output="screen",
            remappings=[
                ("~/image", LaunchConfiguration("image")),
                ("~/segmented_image", LaunchConfiguration("segmented_image"))
            ]
        )
    ])
