from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import PathJoinSubstitution
from ament_index_python.packages import get_package_share_directory
import xacro
import os

def generate_launch_description():
    ns = 'robot1'
    package_name = 'differential_drive_description'
    package_share_dir = FindPackageShare(package_name)
    package_absolute = get_package_share_directory(package_name)
    gazebo_package = FindPackageShare('ros_gz_sim')
    urdf_file = os.path.join(package_absolute, 'description', 'urdfs', 'main.urdf')
    gz_launch_path = PathJoinSubstitution([gazebo_package, 'launch', 'gz_sim.launch.py'])
    robot_description = xacro.process_file(urdf_file).toxml().replace('ROBOT_NAME_PLACEHOLDER', ns)
    ekf_config_path = PathJoinSubstitution([package_share_dir, 'config', 'ekf.yaml'])

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        namespace=ns,
        parameters=[{
            'robot_description':robot_description,
            'use_sim_time':True,
            'frame_prefix':f'{ns}/',
        }]
    )

    spawner_node= Node(
        package='ros_gz_sim',
        executable='create',
        namespace=ns,
        arguments=[
            '-string', robot_description,
            '-name', ns,
            '-x', '0',
            '-y', '0',
            '-z', '0.1',
        ]
    )

    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            f'/model/{ns}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
            f'/model/{ns}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
            f'/model/{ns}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            f'/model/{ns}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
            f'/model/{ns}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V',
            f'/model/{ns}/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry'
        ],
        remappings=[
            (f'/model/{ns}/imu', f'/{ns}/imu'),
            (f'/model/{ns}/cmd_vel', f'/{ns}/cmd_vel'),
            (f'/model/{ns}/scan', f'/{ns}/scan'),
            (f'/model/{ns}/joint_states', f'/{ns}/joint_states'),
            (f'/model/{ns}/tf', f'/{ns}/tf'),
            (f'/model/{ns}/odom', f'/{ns}/wheel_odom'),
        ]
    )

    clock_node = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            ],
        )

    robot_localization = Node(
        package='robot_localization',
        executable='ekf_node',
        namespace=ns,
        name='ekf_filter_node',
        parameters=[ekf_config_path, {'use_sim_time':True}]
    )

    return LaunchDescription([
        IncludeLaunchDescription(gz_launch_path, launch_arguments={
            'gz_args': [PathJoinSubstitution([package_share_dir, 'description', 'models', 'my_world.world'])],
            'on_exit_shutdown':'True'
        }.items()),
        state_publisher,
        spawner_node,
        gz_bridge,
        robot_localization,
        clock_node,
    ])