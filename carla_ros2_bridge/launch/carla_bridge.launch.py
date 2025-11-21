#!/usr/bin/env python3
"""
Launch file for CARLA ROS 2 Bridge
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        # Declare arguments
        DeclareLaunchArgument(
            'carla_host',
            default_value='localhost',
            description='CARLA server host'
        ),
        DeclareLaunchArgument(
            'carla_port',
            default_value='2000',
            description='CARLA server port'
        ),
        DeclareLaunchArgument(
            'image_width',
            default_value='800',
            description='Camera image width'
        ),
        DeclareLaunchArgument(
            'image_height',
            default_value='600',
            description='Camera image height'
        ),
        DeclareLaunchArgument(
            'camera_fov',
            default_value='110.0',
            description='Camera field of view'
        ),
        
        # Camera publisher node
        Node(
            package='carla_ros2_bridge',
            executable='carla_camera_publisher',
            name='carla_camera_publisher',
            output='screen',
            parameters=[{
                'carla_host': LaunchConfiguration('carla_host'),
                'carla_port': LaunchConfiguration('carla_port'),
                'image_width': LaunchConfiguration('image_width'),
                'image_height': LaunchConfiguration('image_height'),
                'camera_fov': LaunchConfiguration('camera_fov'),
            }]
        ),
    ])
