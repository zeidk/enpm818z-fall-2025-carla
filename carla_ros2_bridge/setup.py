from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'carla_ros2_bridge'

setup(
    name=package_name,
    version='1.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='ROS 2 bridge for CARLA Simulator',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'carla_bridge = carla_ros2_bridge.carla_bridge:main',
            'carla_camera_publisher = carla_ros2_bridge.camera_publisher:main',
            'carla_camera_publisher_with_display = carla_ros2_bridge.camera_publisher_with_display:main',
            'carla_image_subscriber = carla_ros2_bridge.image_subscriber:main',
        ],
    },
)
