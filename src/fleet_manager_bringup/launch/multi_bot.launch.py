from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_path
import yaml

def generate_launch_description():
    bot_description = 'differential_drive_description'
    gz_world = 'AWS_world'
    robots_config = get_package_share_path('fleet_manager_bringup') / 'config' / 'warehouse.yaml'
    navigation_pkg = 'multi_bot_navigation'

    map_yaml = PathJoinSubstitution([FindPackageShare(gz_world), 'maps', '005', 'map.yaml'])

    ld = LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare(gz_world),
                    'launch',
                    'warehouse.launch.py'
                ])
            )
        ),
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            parameters=[{
                'use_sim_time': True,
                'yaml_filename': map_yaml,
            }]
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager',
            parameters=[{
                'use_sim_time': True,
                'autostart': True,
                'node_names': ['map_server']
            }]
        )
    ]) 

    with open(robots_config, 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file)
        robot_list = config.get('robots', [])

    for robot in robot_list:
        args = {
            'namespace': robot['name'],
            'x': str(robot['x']),'y': str(robot['y']),'z': str(robot['z']),
            'use_sim_time': 'true',
        }

        #Spawn Robot action
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare(bot_description),
                        'launch',
                        'single_bot.launch.py',
                    ]),
                ),
                launch_arguments=args.items()
            )
        )
        #AMCL server action
        ld.add_action(
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution([
                        FindPackageShare(navigation_pkg),
                        'launch',
                        'amcl.launch.py',
                    ])
                ),
                launch_arguments=args.items(),
            )
        )

    return ld
