#!/usr/bin/env python3
"""
CARLA Camera Publisher Node

Connects to CARLA, spawns a vehicle with camera, and publishes
camera data to ROS 2 with clean topic names (no double-slash bug).

Topics published:
    /carla/camera/image (sensor_msgs/Image)
    /carla/camera/camera_info (sensor_msgs/CameraInfo)
    /carla/vehicle/odometry (nav_msgs/Odometry)
"""

import carla
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Header
import numpy as np
import weakref
from tf2_ros import TransformBroadcaster


class CarlaCameraPublisher(Node):
    def __init__(self):
        super().__init__('carla_camera_publisher')
        
        # Declare parameters
        self.declare_parameter('carla_host', 'localhost')
        self.declare_parameter('carla_port', 2000)
        self.declare_parameter('image_width', 800)
        self.declare_parameter('image_height', 600)
        self.declare_parameter('camera_fov', 110.0)
        self.declare_parameter('camera_x', 1.6)
        self.declare_parameter('camera_z', 1.2)
        self.declare_parameter('spawn_vehicle', True)
        self.declare_parameter('autopilot', True)
        
        # Get parameters
        self.carla_host = self.get_parameter('carla_host').value
        self.carla_port = self.get_parameter('carla_port').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        self.camera_fov = self.get_parameter('camera_fov').value
        self.camera_x = self.get_parameter('camera_x').value
        self.camera_z = self.get_parameter('camera_z').value
        self.spawn_vehicle = self.get_parameter('spawn_vehicle').value
        self.autopilot = self.get_parameter('autopilot').value
        
        # Create publishers
        self.image_pub = self.create_publisher(Image, '/carla/camera/image', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/carla/camera/camera_info', 10)
        self.odom_pub = self.create_publisher(Odometry, '/carla/vehicle/odometry', 10)
        
        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        self.get_logger().info('='*60)
        self.get_logger().info('CARLA Camera Publisher Node')
        self.get_logger().info('='*60)
        
        # Connect to CARLA
        self.carla_client = None
        self.carla_world = None
        self.vehicle = None
        self.camera = None
        self.frame_count = 0
        
        self.connect_to_carla()
        
        if self.spawn_vehicle:
            self.spawn_vehicle_and_camera()
        
        # Timer for publishing odometry
        self.create_timer(0.05, self.publish_odometry)  # 20 Hz
        
        self.get_logger().info('='*60)
        self.get_logger().info('Publishing to:')
        self.get_logger().info('  /carla/camera/image')
        self.get_logger().info('  /carla/camera/camera_info')
        self.get_logger().info('  /carla/vehicle/odometry')
        self.get_logger().info('='*60)
    
    def connect_to_carla(self):
        """Connect to CARLA server"""
        try:
            self.get_logger().info(f'Connecting to CARLA at {self.carla_host}:{self.carla_port}...')
            self.carla_client = carla.Client(self.carla_host, self.carla_port)
            self.carla_client.set_timeout(10.0)
            self.carla_world = self.carla_client.get_world()
            server_version = self.carla_client.get_server_version()
            self.get_logger().info(f'✓ Connected to CARLA {server_version}')
        except Exception as e:
            self.get_logger().error(f'Failed to connect to CARLA: {e}')
            raise
    
    def spawn_vehicle_and_camera(self):
        """Spawn vehicle and attach camera"""
        try:
            bp_lib = self.carla_world.get_blueprint_library()
            
            # Spawn vehicle
            vehicle_bp = bp_lib.filter('vehicle.tesla.model3')[0]
            spawn_points = self.carla_world.get_map().get_spawn_points()
            
            if not spawn_points:
                raise Exception("No spawn points available")
            
            self.vehicle = self.carla_world.spawn_actor(vehicle_bp, spawn_points[0])
            self.get_logger().info(f'✓ Spawned vehicle at {spawn_points[0].location}')
            
            if self.autopilot:
                self.vehicle.set_autopilot(True)
                self.get_logger().info('✓ Autopilot enabled')
            
            # Spawn camera
            camera_bp = bp_lib.find('sensor.camera.rgb')
            camera_bp.set_attribute('image_size_x', str(self.image_width))
            camera_bp.set_attribute('image_size_y', str(self.image_height))
            camera_bp.set_attribute('fov', str(self.camera_fov))
            
            # NOTE: We do NOT use ros_name or enable_for_ros() - we handle publishing ourselves!
            
            camera_transform = carla.Transform(
                carla.Location(x=self.camera_x, z=self.camera_z)
            )
            self.camera = self.carla_world.spawn_actor(
                camera_bp, camera_transform, attach_to=self.vehicle
            )
            self.get_logger().info('✓ Camera spawned and attached')
            
            # Listen to camera - use weak reference to avoid circular dependency
            weak_self = weakref.ref(self)
            self.camera.listen(lambda image: CarlaCameraPublisher._on_camera_update(weak_self, image))
            self.get_logger().info('✓ Camera listening')
            
            # Publish initial camera info
            self.publish_camera_info()
            
        except Exception as e:
            self.get_logger().error(f'Failed to spawn vehicle/camera: {e}')
            raise
    
    @staticmethod
    def _on_camera_update(weak_self, carla_image):
        """Callback for CARLA camera images"""
        self = weak_self()
        if not self:
            return
        
        self.publish_image(carla_image)
    
    def publish_image(self, carla_image):
        """Convert CARLA image to ROS 2 Image message and publish"""
        # Convert CARLA image to numpy array
        array = np.frombuffer(carla_image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (carla_image.height, carla_image.width, 4))
        array = array[:, :, :3]  # Remove alpha channel
        array = array[:, :, ::-1]  # BGR to RGB
        
        # Create ROS 2 Image message
        msg = Image()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.height = carla_image.height
        msg.width = carla_image.width
        msg.encoding = 'rgb8'
        msg.is_bigendian = 0
        msg.step = carla_image.width * 3
        msg.data = array.tobytes()
        
        # Publish
        self.image_pub.publish(msg)
        
        self.frame_count += 1
        if self.frame_count % 100 == 0:
            self.get_logger().info(f'Published {self.frame_count} frames')
    
    def publish_camera_info(self):
        """Publish camera calibration info"""
        msg = CameraInfo()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.height = self.image_height
        msg.width = self.image_width
        
        # Calculate camera matrix from FOV
        focal_length = self.image_width / (2.0 * np.tan(self.camera_fov * np.pi / 360.0))
        
        msg.k = [
            focal_length, 0.0, self.image_width / 2.0,
            0.0, focal_length, self.image_height / 2.0,
            0.0, 0.0, 1.0
        ]
        msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]  # No distortion
        msg.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        msg.p = [
            focal_length, 0.0, self.image_width / 2.0, 0.0,
            0.0, focal_length, self.image_height / 2.0, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        
        self.camera_info_pub.publish(msg)
    
    def publish_odometry(self):
        """Publish vehicle odometry"""
        if not self.vehicle or not self.vehicle.is_alive:
            return
        
        transform = self.vehicle.get_transform()
        velocity = self.vehicle.get_velocity()
        
        # Create Odometry message
        msg = Odometry()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.child_frame_id = 'base_link'
        
        # Position
        msg.pose.pose.position.x = transform.location.x
        msg.pose.pose.position.y = -transform.location.y  # CARLA uses left-handed, ROS uses right-handed
        msg.pose.pose.position.z = transform.location.z
        
        # Orientation (convert from Euler to Quaternion)
        roll = np.radians(transform.rotation.roll)
        pitch = -np.radians(transform.rotation.pitch)
        yaw = -np.radians(transform.rotation.yaw)
        
        cy = np.cos(yaw * 0.5)
        sy = np.sin(yaw * 0.5)
        cp = np.cos(pitch * 0.5)
        sp = np.sin(pitch * 0.5)
        cr = np.cos(roll * 0.5)
        sr = np.sin(roll * 0.5)
        
        msg.pose.pose.orientation.w = cr * cp * cy + sr * sp * sy
        msg.pose.pose.orientation.x = sr * cp * cy - cr * sp * sy
        msg.pose.pose.orientation.y = cr * sp * cy + sr * cp * sy
        msg.pose.pose.orientation.z = cr * cp * sy - sr * sp * cy
        
        # Velocity
        msg.twist.twist.linear.x = velocity.x
        msg.twist.twist.linear.y = -velocity.y
        msg.twist.twist.linear.z = velocity.z
        
        self.odom_pub.publish(msg)
    
    def destroy_actors(self):
        """Clean up CARLA actors"""
        self.get_logger().info('Destroying CARLA actors...')
        if self.camera:
            self.camera.destroy()
        if self.vehicle:
            self.vehicle.destroy()
        self.get_logger().info('✓ Actors destroyed')


def main(args=None):
    rclpy.init(args=args)
    
    node = None
    try:
        node = CarlaCameraPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\n\nShutting down...')
    except Exception as e:
        print(f'\nError: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if node:
            node.destroy_actors()
            node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
