# CARLA ROS 2 Bridge

A clean ROS 2 package for interfacing with CARLA Simulator 0.9.16.

## Why This Package?

CARLA 0.9.16's native ROS 2 integration has a bug that creates invalid topic names with double slashes (`/carla//camera/image`), which are rejected by ROS 2 Jazzy's strict validation.

This package **bypasses CARLA's built-in ROS 2 bridge** and creates a clean, professional implementation that:
- ✅ Uses valid ROS 2 topic names
- ✅ Publishes camera images and calibration data  
- ✅ Publishes vehicle odometry
- ✅ Follows ROS 2 best practices
- ✅ Configurable via parameters and launch files

## Installation

### Prerequisites
- ROS 2 Jazzy
- CARLA 0.9.16
- Python packages: `carla`, `numpy`

```bash
pip install carla==0.9.16 numpy
```

### Build the Package

```bash
# Navigate to workspace
cd ~/carla_ros2_bridge_ws

# Build
colcon build

# Source
source install/setup.bash
```

## Usage

### Start CARLA Server
```bash
# In terminal 1
carla  # Or your CARLA startup command
```

### Run the Bridge

**Option 1: Using ros2 run**
```bash
# In terminal 2
source ~/carla_ros2_bridge_ws/install/setup.bash
ros2 run carla_ros2_bridge carla_camera_publisher
```

**Option 2: Using launch file**
```bash
source ~/carla_ros2_bridge_ws/install/setup.bash
ros2 launch carla_ros2_bridge carla_bridge.launch.py
```

### Subscribe to Topics

```bash
# List topics
ros2 topic list

# Echo images
ros2 topic echo /carla/camera/image --no-arr

# Check publishing rate
ros2 topic hz /carla/camera/image

# Visualize in RViz2
rviz2
```

### Run the Test Subscriber

```bash
ros2 run carla_ros2_bridge carla_image_subscriber
```

## Published Topics

| Topic | Type | Description |
|-------|------|-------------|
| `/carla/camera/image` | `sensor_msgs/Image` | Camera RGB image |
| `/carla/camera/camera_info` | `sensor_msgs/CameraInfo` | Camera calibration |
| `/carla/vehicle/odometry` | `nav_msgs/Odometry` | Vehicle pose and velocity |

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `carla_host` | string | `localhost` | CARLA server hostname |
| `carla_port` | int | `2000` | CARLA server port |
| `image_width` | int | `800` | Camera image width |
| `image_height` | int | `600` | Camera image height |
| `camera_fov` | float | `110.0` | Camera field of view (degrees) |
| `camera_x` | float | `1.6` | Camera X position relative to vehicle |
| `camera_z` | float | `1.2` | Camera Z position relative to vehicle |
| `spawn_vehicle` | bool | `true` | Spawn vehicle automatically |
| `autopilot` | bool | `true` | Enable autopilot |

### Example with Custom Parameters

```bash
ros2 run carla_ros2_bridge carla_camera_publisher \
    --ros-args \
    -p image_width:=1280 \
    -p image_height:=720 \
    -p camera_fov:=90.0 \
    -p autopilot:=false
```

## Architecture

```
CARLA Simulator
      ↓
  Python API (camera.listen())
      ↓
  ROS 2 Node (this package)
      ↓
  Clean ROS 2 Topics (/carla/camera/image)
      ↓
  Your ROS 2 Applications
```

**Key difference from CARLA's native implementation:**
- ❌ CARLA native: Uses `enable_for_ros()` → creates `/carla//camera/image` (broken)
- ✅ This package: Uses Python callbacks → creates `/carla/camera/image` (works!)

## For ENPM818Z Students

This is the recommended way to interface CARLA with ROS 2 for your assignments.

**Typical workflow:**
1. Start CARLA server
2. Run this bridge: `ros2 run carla_ros2_bridge carla_camera_publisher`
3. Write your own ROS 2 nodes that subscribe to `/carla/camera/image`
4. Process images, implement algorithms, publish control commands

## Development

### Project Structure
```
carla_ros2_bridge/
├── carla_ros2_bridge/
│   ├── __init__.py
│   ├── carla_bridge.py          # Main entry point
│   ├── camera_publisher.py       # Camera publisher node
│   └── image_subscriber.py       # Example subscriber
├── launch/
│   └── carla_bridge.launch.py   # Launch file
├── package.xml                   # Package metadata
├── setup.py                      # Python setup
└── README.md                     # This file
```

### Adding More Sensors

To add LIDAR, RADAR, or other sensors, follow the pattern in `camera_publisher.py`:
1. Spawn the sensor in CARLA
2. Use `.listen()` callback (not `enable_for_ros()`)
3. Convert CARLA data to ROS 2 messages
4. Publish to clean topic names

## Troubleshooting

### "Failed to connect to CARLA"
- Ensure CARLA is running: `docker ps` or check for CARLA window
- Check host/port parameters match your CARLA server

### "No spawn points available"
- CARLA world isn't loaded yet, wait a few seconds and retry

### "No messages received"
- Verify topics exist: `ros2 topic list`
- Check if node is running: `ros2 node list`
- Verify CARLA vehicle is spawned (visible in CARLA window)

## License

MIT

## Credits

Created as a workaround for CARLA 0.9.16 double-slash bug.  
Developed for ENPM818Z - On-Road Automated Vehicles course.
