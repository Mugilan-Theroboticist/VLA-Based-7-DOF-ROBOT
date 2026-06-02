import rclpy
from rclpy.node import Node
import subprocess

class VoiceNode(Node):

    def __init__(self):
        super().__init__('voice_node')
        self.get_logger().info("Type command (blue/red/green):")

        while True:
            text = input("Command >> ")

            self.handle_command(text.lower())

    def handle_command(self, text):

        if "blue" in text:
            color = "B"
        elif "red" in text:
            color = "R"
        elif "green" in text:
            color = "G"
        else:
            self.get_logger().info("Unknown command")
            return

        subprocess.Popen([
            "ros2","run","pymoveit2",
            "pick_and_place.py",
            "--ros-args",
            "-p",f"target_color:={color}"
        ])

def main():
    rclpy.init()
    node = VoiceNode()
    rclpy.spin(node)

if __name__ == "__main__":
    main()