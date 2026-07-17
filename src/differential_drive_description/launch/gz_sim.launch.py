from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import xacro
import os

def generate_launch_description():
    package_name = "differential_drive_description"
    ros_gz_sim_pkg_path = get_package_share_directory('ros_gz_sim')
    example_pkg_path = FindPackageShare(package_name)  # Replace with your own package name
    gz_launch_path = PathJoinSubstitution([ros_gz_sim_pkg_path, 'launch', 'gz_sim.launch.py'])
    urdf_file = os.path.join(get_package_share_directory(package_name), 'description','urdfs', 'main.urdf')
    description_raw = xacro.process_file(urdf_file).toxml()

    spawner_node = Node(
        package='ros_gz_sim',
        executable='create',
        output = 'screen',
        arguments=[
            '-string', description_raw,
            '-name', 'differential_drive_bot',
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.0'
        ]
    )
    state_publisher = Node(
        executable='robot_state_publisher',
        package='robot_state_publisher',
        parameters=[{
            'robot_description':description_raw,
            'use_sim_time':True
        }]
    )

    return LaunchDescription([
        SetEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            PathJoinSubstitution([example_pkg_path, 'description', 'models'])
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(gz_launch_path),
            launch_arguments={
                'gz_args': [PathJoinSubstitution([example_pkg_path, 'description/models/my_world.world'])],
                'on_exit_shutdown': 'True'
            }.items(),
        ),

        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/imu@sensor_msgs/msg/Imu@gz.msgs.IMU',
                '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                '/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                '/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
                '/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
            ],
            remappings=[('/imu', '/imu_ros2'),],
            output='screen',
        ),
        spawner_node,
        state_publisher,
    ])
 