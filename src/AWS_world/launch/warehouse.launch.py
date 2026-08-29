from launch import LaunchDescription
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, AppendEnvironmentVariable
)


def generate_launch_description():
    pkg_name = "AWS_world"

    default_world = PathJoinSubstitution([
        FindPackageShare(pkg_name),
        'worlds', 'no_roof_small_warehouse', 'no_roof_small_warehouse.world'
    ])

    world = DeclareLaunchArgument(
        'world', default_value=default_world,
        description="World file for gz to launch"
    )

    gz_resource_path = AppendEnvironmentVariable(
        name="GZ_SIM_RESOURCE_PATH",
        value=PathJoinSubstitution([FindPackageShare(pkg_name), 'models'])
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            ])
        ),
        launch_arguments={
            'gz_args': [LaunchConfiguration('world')],
            'on_exit_shutdown': 'true',
        }.items()
    )

    clk_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="clock_bridge",
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']
    )

    return LaunchDescription([world, gz_resource_path, gazebo, clk_bridge])