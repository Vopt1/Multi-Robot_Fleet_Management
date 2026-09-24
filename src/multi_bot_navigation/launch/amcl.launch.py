import os
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node, PushROSNamespace
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from nav2_common.launch import RewrittenYaml

def generate_launch_description():
    pkg = get_package_share_directory('multi_bot_navigation')

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    x, y, z = (LaunchConfiguration('x'),
               LaunchConfiguration('y'),
               LaunchConfiguration('z'))

    params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites={
            'use_sim_time': use_sim_time,
            'base_frame_id': [namespace, '/base_link'],
            'odom_frame_id': [namespace, '/odom'],
            'global_frame_id': 'map',
            'scan_topic': ['/', namespace, '/scan'],
        },
        convert_types=True,
    )

    return LaunchDescription([
        DeclareLaunchArgument('namespace'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('params_file',
            default_value=os.path.join(pkg, 'config', 'amcl.yaml')),
        DeclareLaunchArgument('x',   default_value='0.0'),
        DeclareLaunchArgument('y',   default_value='0.0'),
        DeclareLaunchArgument('z',   default_value='0.0'),

        GroupAction([
            PushROSNamespace(namespace),

            Node(
                package='nav2_amcl', executable='amcl', name='amcl',
                output='screen',
                parameters=[params, {
                    'set_initial_pose': True,
                    'initial_pose.x': x,
                    'initial_pose.y': y,
                    'initial_pose.z': z,
                    'use_sim_time': True,
                }],
                remappings=[('map', '/map')],
            ),
            Node(
                package='nav2_lifecycle_manager', executable='lifecycle_manager',
                name='lifecycle_manager_localization', output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'autostart': True,
                    'node_names': ['amcl'],
                }],
            ),
        ]),
    ])
