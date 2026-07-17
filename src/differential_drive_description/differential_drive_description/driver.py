import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException

from geometry_msgs.msg import Twist

class Driver(Node):

    def __init__(self):

        super().__init__("driver")

        self.pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.speed = Twist()
        self.speed.linear.x = 1.0
        self.speed.angular.z = 0.5

        self.create_timer(0.2, self.publish_speed)

        self.get_logger().info(f"Started driver")

    def publish_speed(self):
        self.pub.publish(self.speed)

def main(args=None):

    rclpy.init(args=args)

    node = Driver()

    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        print("\nShutting down...")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == "__main__":
    main()