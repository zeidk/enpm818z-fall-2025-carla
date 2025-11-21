#!/bin/bash
# CARLA ROS 2 Setup Script
# For CARLA 0.9.16 with ROS 2 humble on Ubuntu 22.04

carla_setup() {
    # Configuration
    CARLA_WS="/home/zeid/carla_ws" # change this path
    
    echo "🔧 Setting up CARLA ROS 2 environment..."
    
    # 1. Setup Host Environment Variables
    export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
    export ROS_DOMAIN_ID=0
    unset ROS_LOCALHOST_ONLY  # Unset the deprecated variable
    unset FASTRTPS_DEFAULT_PROFILES_FILE  # Don't use XML for ROS 2 nodes
    
    # 2. Source ROS 2 (detect shell and source appropriate file)
    local SHELL_NAME=$(basename "$SHELL")
    if [ "$SHELL_NAME" = "zsh" ]; then
        if [ -f "/opt/ros/humble/setup.zsh" ]; then
            source /opt/ros/humble/setup.zsh
        else
            echo "❌ Error: ROS 2 humble setup.zsh not found"
            return 1
        fi
    elif [ "$SHELL_NAME" = "bash" ]; then
        if [ -f "/opt/ros/humble/setup.bash" ]; then
            source /opt/ros/humble/setup.bash
        else
            echo "❌ Error: ROS 2 humble setup.bash not found"
            return 1
        fi
    else
        # Fallback: try bash first, then zsh
        if [ -f "/opt/ros/humble/setup.bash" ]; then
            source /opt/ros/humble/setup.bash
        elif [ -f "/opt/ros/humble/setup.zsh" ]; then
            source /opt/ros/humble/setup.zsh
        else
            echo "❌ Error: ROS 2 humble not found"
            return 1
        fi
    fi
    
    # 3. Source CARLA workspace if it exists
    if [ -d "$CARLA_WS" ]; then
        if [ "$SHELL_NAME" = "zsh" ]; then
            if [ -f "$CARLA_WS/install/setup.zsh" ]; then
                source "$CARLA_WS/install/setup.zsh"
                echo "✅ Sourced CARLA workspace (zsh)"
            else
                echo "⚠️  Warning: CARLA workspace not built yet"
                echo "   Run: cd $CARLA_WS && colcon build"
            fi
        else
            if [ -f "$CARLA_WS/install/setup.bash" ]; then
                source "$CARLA_WS/install/setup.bash"
                echo "✅ Sourced CARLA workspace (bash)"
            else
                echo "⚠️  Warning: CARLA workspace not built yet"
                echo "   Run: cd $CARLA_WS && colcon build"
            fi
        fi
    else
        echo "⚠️  Warning: CARLA workspace not found at $CARLA_WS"
    fi
    
    # 4. Reset ROS 2 Daemon
    echo "🔄 Restarting ROS 2 daemon..."
    ros2 daemon stop > /dev/null 2>&1
    sleep 1
    ros2 daemon start > /dev/null 2>&1
    
    echo "✅ CARLA Setup Complete!"
    echo ""
    echo "📋 Usage:"
    echo "   1. Start CARLA (native installation):"
    echo "      cd ~/CARLA_0.9.16"
    echo "      ./CarlaUE4.sh -quality-level=Low"
    echo ""
    echo "   2. Run ROS 2 bridge:"
    echo "      ros2 run carla_ros2_bridge carla_camera_publisher"
    echo ""
    echo "   3. Or run with pygame display:"
    echo "      python3 camera_publisher_with_display.py"
    echo ""
    echo "🔍 Environment Variables Set:"
    echo "   ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
    echo "   RMW_IMPLEMENTATION=$RMW_IMPLEMENTATION"
    echo "   CARLA_WS=$CARLA_WS"
    
    cd "${CARLA_WS}"
}

# Run setup automatically when script is sourced
carla_setup