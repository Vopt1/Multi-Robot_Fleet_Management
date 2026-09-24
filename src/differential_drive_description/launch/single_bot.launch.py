import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro


def launch_setup(context, *args, **kwargs):
    # Perform evaluation to get real Python strings
    ns_str = context.perform_substitution(LaunchConfiguration('namespace'))
    x = context.perform_substitution(LaunchConfiguration('x'))
    y = context.perform_substitution(LaunchConfiguration('y'))
    z = context.perform_substitution(LaunchConfiguration('z'))
    
    package_name = 'differential_drive_description'
    package_dir = get_package_share_directory(package_name)
    urdf_file = os.path.join(package_dir, 'description', 'urdfs', 'main.urdf')
    
    # Process xacro/urdf and replace placeholder safely
    robot_description = xacro.process_file(urdf_file).toxml().replace('ROBOT_NAME_PLACEHOLDER', ns_str)
    ekf_config_path = os.path.join(package_dir, 'config', 'ekf.yaml')

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=ns_str,
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': True,
            'frame_prefix': f'{ns_str}/',
        }]
    )

    spawner_node = Node(
        package='ros_gz_sim',
        executable='create',
        namespace=ns_str,
        arguments=[
            '-string', robot_description,
            '-name', ns_str,
            '-x', x,
            '-y', y,
            '-z', z,
        ]
    )

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        namespace=ns_str,
        arguments=[
            f'/model/{ns_str}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            f'/model/{ns_str}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'/model/{ns_str}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            f'/model/{ns_str}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            f'/model/{ns_str}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            f'/model/{ns_str}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry'
        ],
        remappings=[
            (f'/model/{ns_str}/imu', f'/{ns_str}/imu'),
            (f'/model/{ns_str}/cmd_vel', f'/{ns_str}/cmd_vel'),
            (f'/model/{ns_str}/scan', f'/{ns_str}/scan'),
            (f'/model/{ns_str}/joint_states', f'/{ns_str}/joint_states'),
            (f'/model/{ns_str}/tf', f'/tf'),
            (f'/model/{ns_str}/odom', f'/{ns_str}/wheel_odom'),
        ]
    )

    robot_localization = Node(
        package='robot_localization',
        executable='ekf_node',
        namespace=ns_str,
        name='ekf_filter_node',
        parameters=[ekf_config_path, {'use_sim_time': True}]
    )

    return [
        state_publisher,
        spawner_node,
        gz_bridge,
        robot_localization,
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='robot1',
            description='Namespace value of the bot to be spawned'
        ),
        DeclareLaunchArgument(
            'x',
            default_value='0.0',
            description='The initial x position of the bot'
        ),
        DeclareLaunchArgument(
            'y',
            default_value='0.0',
            description='The initial y position of the bot'
        ),
        DeclareLaunchArgument(
            'z',
            default_value='0.1',
            description='The initial z position of the bot'
        ),
        OpaqueFunction(function=launch_setup),
    ])
