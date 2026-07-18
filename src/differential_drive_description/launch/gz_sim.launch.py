from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
import xacro
import yaml
import os

def generate_launch_description():
    package_name = "differential_drive_description"
    ros_gz_sim_pkg_path = get_package_share_directory('ros_gz_sim')
    example_pkg_path = FindPackageShare(package_name)
    pkg_path = get_package_share_directory(package_name)
    gz_launch_path = PathJoinSubstitution([ros_gz_sim_pkg_path, 'launch', 'gz_sim.launch.py'])
    urdf_file = os.path.join(pkg_path, 'description','urdfs', 'main.urdf')
    description_raw = xacro.process_file(urdf_file).toxml()
    config_file_path = os.path.join(pkg_path, 'config/warehouse.yaml')

    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            robots_list = config.get('robots', [])
    except Exception as e:
        print(f"Unable to load config file because {e}")
        robots_list=[]

    ld = LaunchDescription([
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
    ])

    for robot in robots_list:
        ns = robot['namespace']
        entity_name = robot['name']
        description_processed = description_raw.replace('ROBOT_NAME_PLACEHOLDER', entity_name)

        robot_state_publisher = Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            namespace=ns,
            parameters=[{
                'robot_description':description_processed,
                'use_sim_time':True,
                'frame_prefix':f'{ns}/'
            }]
            
        )

        spawner_node= Node(
            package='ros_gz_sim',
            executable='create',
            namespace=entity_name,
            arguments=[
                '-string', description_processed,
                '-name', entity_name,
                '-x', str(robot['x']),
                '-y', str(robot['y']),
                '-z', str(robot['z']),
            ]
        )

        gz_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                f'/model/{entity_name}/imu@sensor_msgs/msg/Imu[gz.msgs.IMU',
                f'/model/{entity_name}/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                f'/model/{entity_name}/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
                f'/model/{entity_name}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model',
                f'/model/{entity_name}/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'
            ],
            remappings=[
                (f'/model/{entity_name}/imu', f'/{ns}/imu'),
                (f'/model/{entity_name}/cmd_vel', f'/{ns}/cmd_vel'),
                (f'/model/{entity_name}/scan', f'/{ns}/scan'),
                (f'/model/{entity_name}/joint_states', f'/{ns}/joint_states'),
                (f'/model/{entity_name}/tf', f'/{ns}/tf'),
            ]
        )

        ld.add_action(spawner_node)
        ld.add_action(robot_state_publisher)
        ld.add_action(gz_bridge)

    clock_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
        ],
    )

    ld.add_action(clock_node)

    return ld
 