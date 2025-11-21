#!/usr/bin/env python3
"""
CARLA Camera Publisher with Pygame Visualization

Publishes to ROS 2 AND shows pygame window
"""

import carla
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from nav_msgs.msg import Odometry
from std_msgs.msg import Header
import numpy as np
import pygame
import weakref


class CarlaCameraPublisherWithDisplay(Node):
    def __init__(self):
        super().__init__('carla_camera_publisher_display')
        
        # Declare parameters
        self.declare_parameter('carla_host', 'localhost')
        self.declare_parameter('carla_port', 2000)
        self.declare_parameter('image_width', 800)
        self.declare_parameter('image_height', 600)
        self.declare_parameter('camera_fov', 110.0)
        self.declare_parameter('camera_x', 1.6)
        self.declare_parameter('camera_z', 1.2)
        
        # Get parameters
        self.carla_host = self.get_parameter('carla_host').value
        self.carla_port = self.get_parameter('carla_port').value
        self.image_width = self.get_parameter('image_width').value
        self.image_height = self.get_parameter('image_height').value
        self.camera_fov = self.get_parameter('camera_fov').value
        self.camera_x = self.get_parameter('camera_x').value
        self.camera_z = self.get_parameter('camera_z').value
        
        # Initialize Pygame
        pygame.init()
        self.display = pygame.display.set_mode(
            (self.image_width, self.image_height),
            pygame.HWSURFACE | pygame.DOUBLEBUF
        )
        pygame.display.set_caption("CARLA ROS 2 Bridge")
        self.font = pygame.font.SysFont('monospace', 18, bold=True)
        self.clock = pygame.time.Clock()
        
        # Create ROS 2 publishers
        self.image_pub = self.create_publisher(Image, '/carla/camera/image', 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, '/carla/camera/camera_info', 10)
        self.odom_pub = self.create_publisher(Odometry, '/carla/vehicle/odometry', 10)
        
        self.get_logger().info('='*60)
        self.get_logger().info('CARLA Camera Publisher with Display')
        self.get_logger().info('='*60)
        
        # Connect to CARLA
        self.carla_client = None
        self.carla_world = None
        self.vehicle = None
        self.camera = None
        self.spectator = None
        self.frame_count = 0
        self.latest_image = None
        
        self.connect_to_carla()
        self.spawn_vehicle_and_camera()
        
        # Timer for pygame updates and odometry
        self.create_timer(0.016, self.update_pygame)  # ~60 Hz
        self.create_timer(0.05, self.publish_odometry)  # 20 Hz
        
        self.get_logger().info('='*60)
        self.get_logger().info('✓ Publishing to:')
        self.get_logger().info('  /carla/camera/image')
        self.get_logger().info('  /carla/camera/camera_info')
        self.get_logger().info('  /carla/vehicle/odometry')
        self.get_logger().info('')
        self.get_logger().info('✓ Pygame window open')
        self.get_logger().info('  Press ESC to exit')
        self.get_logger().info('='*60)
    
    def connect_to_carla(self):
        """Connect to CARLA server"""
        try:
            self.get_logger().info(f'Connecting to CARLA at {self.carla_host}:{self.carla_port}...')
            self.carla_client = carla.Client(self.carla_host, self.carla_port)
            self.carla_client.set_timeout(10.0)
            self.carla_world = self.carla_client.get_world()
            self.spectator = self.carla_world.get_spectator()
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
            self.get_logger().info('✓ Vehicle spawned')
            
            self.vehicle.set_autopilot(True)
            self.get_logger().info('✓ Autopilot enabled')
            
            # Spawn camera
            camera_bp = bp_lib.find('sensor.camera.rgb')
            camera_bp.set_attribute('image_size_x', str(self.image_width))
            camera_bp.set_attribute('image_size_y', str(self.image_height))
            camera_bp.set_attribute('fov', str(self.camera_fov))
            
            camera_transform = carla.Transform(
                carla.Location(x=self.camera_x, z=self.camera_z)
            )
            self.camera = self.carla_world.spawn_actor(
                camera_bp, camera_transform, attach_to=self.vehicle
            )
            self.get_logger().info('✓ Camera spawned')
            
            # Listen to camera
            weak_self = weakref.ref(self)
            self.camera.listen(
                lambda image: CarlaCameraPublisherWithDisplay._on_camera_update(weak_self, image)
            )
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
        
        # Store for pygame display
        self.latest_image = carla_image
        
        # Publish to ROS 2
        self.publish_image(carla_image)
    
    def publish_image(self, carla_image):
        """Convert and publish image to ROS 2"""
        # Convert CARLA image to numpy
        array = np.frombuffer(carla_image.raw_data, dtype=np.uint8)
        array = np.reshape(array, (carla_image.height, carla_image.width, 4))
        array = array[:, :, :3]  # Remove alpha
        array = array[:, :, ::-1]  # BGR to RGB
        
        # Create ROS 2 message
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
        
        self.image_pub.publish(msg)
        
        self.frame_count += 1
        if self.frame_count % 100 == 0:
            self.get_logger().info(f'Published {self.frame_count} frames')
    
    def publish_camera_info(self):
        """Publish camera calibration"""
        msg = CameraInfo()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera_link'
        msg.height = self.image_height
        msg.width = self.image_width
        
        focal_length = self.image_width / (2.0 * np.tan(self.camera_fov * np.pi / 360.0))
        
        msg.k = [
            focal_length, 0.0, self.image_width / 2.0,
            0.0, focal_length, self.image_height / 2.0,
            0.0, 0.0, 1.0
        ]
        msg.d = [0.0, 0.0, 0.0, 0.0, 0.0]
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
        
        msg = Odometry()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.child_frame_id = 'base_link'
        
        # Position
        msg.pose.pose.position.x = transform.location.x
        msg.pose.pose.position.y = -transform.location.y
        msg.pose.pose.position.z = transform.location.z
        
        # Orientation
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
    
    def update_pygame(self):
        """Update pygame display"""
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.get_logger().info('Pygame window closed')
                rclpy.shutdown()
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.get_logger().info('ESC pressed, shutting down')
                    rclpy.shutdown()
                    return
        
        # Display latest image
        if self.latest_image:
            array = np.frombuffer(self.latest_image.raw_data, dtype=np.uint8)
            array = np.reshape(array, (self.latest_image.height, self.latest_image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
            self.display.blit(surface, (0, 0))
        
        # Update spectator (chase camera)
        if self.vehicle and self.vehicle.is_alive:
            vehicle_transform = self.vehicle.get_transform()
            spectator_loc = vehicle_transform.location - 10 * vehicle_transform.get_forward_vector()
            spectator_loc.z += 5
            spectator_rot = vehicle_transform.rotation
            spectator_rot.pitch = -15
            self.spectator.set_transform(carla.Transform(spectator_loc, spectator_rot))
        
        # Draw FPS overlay
        client_fps = self.clock.get_fps()
        snapshot = self.carla_world.get_snapshot()
        server_fps = 1.0 / snapshot.timestamp.delta_seconds if snapshot.timestamp.delta_seconds > 0 else 0
        
        pygame.draw.rect(self.display, (0, 0, 0), (0, 0, 250, 85))
        
        lbl_client = self.font.render(f'Client FPS: {client_fps:.1f}', True, (0, 255, 0))
        lbl_server = self.font.render(f'Server FPS: {server_fps:.1f}', True, (255, 100, 100))
        lbl_ros = self.font.render(f'ROS2: {self.frame_count} frames', True, (100, 255, 100))
        
        self.display.blit(lbl_client, (10, 10))
        self.display.blit(lbl_server, (10, 35))
        self.display.blit(lbl_ros, (10, 60))
        
        pygame.display.flip()
        self.clock.tick(60)
    
    def destroy_actors(self):
        """Clean up CARLA actors"""
        self.get_logger().info('Destroying CARLA actors...')
        if self.camera:
            self.camera.destroy()
        if self.vehicle:
            self.vehicle.destroy()
        pygame.quit()
        self.get_logger().info('✓ Cleanup complete')


def main(args=None):
    rclpy.init(args=args)
    
    node = None
    try:
        node = CarlaCameraPublisherWithDisplay()
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
