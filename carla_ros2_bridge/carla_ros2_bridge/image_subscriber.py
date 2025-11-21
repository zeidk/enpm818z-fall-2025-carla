#!/usr/bin/env python3
"""
CARLA Image Subscriber Node

Simple subscriber to display statistics about received images.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class CarlaImageSubscriber(Node):
    def __init__(self):
        super().__init__('carla_image_subscriber')
        
        self.declare_parameter('topic', '/carla/camera/image')
        topic = self.get_parameter('topic').value
        
        self.subscription = self.create_subscription(
            Image,
            topic,
            self.image_callback,
            10
        )
        
        self.frame_count = 0
        self.start_time = self.get_clock().now()
        self.last_report_time = self.start_time
        
        self.get_logger().info(f'Subscribed to: {topic}')
        self.get_logger().info('Waiting for images...')
    
    def image_callback(self, msg):
        self.frame_count += 1
        
        if self.frame_count == 1:
            self.get_logger().info('✓ Received first image!')
            self.get_logger().info(f'  Size: {msg.width}x{msg.height}')
            self.get_logger().info(f'  Encoding: {msg.encoding}')
        
        # Report every 30 frames
        if self.frame_count % 30 == 0:
            current_time = self.get_clock().now()
            elapsed = (current_time - self.last_report_time).nanoseconds / 1e9
            fps = 30.0 / elapsed if elapsed > 0 else 0
            
            self.get_logger().info(
                f'Frame {self.frame_count}: ~{fps:.1f} Hz'
            )
            
            self.last_report_time = current_time


def main(args=None):
    rclpy.init(args=args)
    
    node = CarlaImageSubscriber()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('\nShutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
