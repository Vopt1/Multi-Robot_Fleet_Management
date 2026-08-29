from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    bot_description = 'differential_drive_description'
    gz_world = 'AWS_world'

    bot_launch_description = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare(bot_description),
                'launch',
                'multi_bot_spawn.py'
            ])
        )
    )
    aws_world_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare(gz_world),
                'launch',
                'warehouse.launch.py'
            ])
        )
    )

    return LaunchDescription([
        aws_world_launch,
        bot_launch_description,
    ])
