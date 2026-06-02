#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import String
from threading import Thread

from pymoveit2 import MoveIt2, GripperInterface
from pymoveit2.robots import panda

import math


class PickAndPlace(Node):

    def __init__(self):
        super().__init__("pick_and_place")

        # ---------------- PARAMETERS ---------------- #
        self.declare_parameter("target_color", "R")
        self.target_color = self.get_parameter("target_color").value.upper()

        self.declare_parameter("approach_offset", 0.31)
        self.approach_offset = float(self.get_parameter("approach_offset").value)

        # ---------------- STATE FLAGS ---------------- #
        self.already_moved = False
        self.target_coords = None

        self.callback_group = ReentrantCallbackGroup()

        # ---------------- MOVEIT ---------------- #
        self.moveit2 = MoveIt2(
            node=self,
            joint_names=panda.joint_names(),
            base_link_name=panda.base_link_name(),
            end_effector_name=panda.end_effector_name(),
            group_name=panda.MOVE_GROUP_ARM,
            callback_group=self.callback_group,
        )

        self.moveit2.max_velocity = 0.1
        self.moveit2.max_acceleration = 0.1

        # ---------------- GRIPPER ---------------- #
        self.gripper = GripperInterface(
            node=self,
            gripper_joint_names=panda.gripper_joint_names(),
            open_gripper_joint_positions=panda.OPEN_GRIPPER_JOINT_POSITIONS,
            closed_gripper_joint_positions=panda.CLOSED_GRIPPER_JOINT_POSITIONS,
            gripper_group_name=panda.MOVE_GROUP_GRIPPER,
            callback_group=self.callback_group,
            gripper_command_action_name="gripper_action_controller/gripper_cmd",
        )

        # ---------------- SUBSCRIBER ---------------- #
        self.sub = self.create_subscription(
            String,
            "/color_coordinates",
            self.coords_callback,
            10
        )

        self.get_logger().info(
            f"Waiting for {self.target_color} from /color_coordinates..."
        )

        # ---------------- JOINT STATES ---------------- #
        self.start_joints = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, math.radians(-125)]
        self.home_joints  = [0.0, 0.0, 0.0, math.radians(-90), 0.0, math.radians(92), math.radians(50)]
        self.drop_joints  = [
            math.radians(-155), math.radians(30), math.radians(-20),
            math.radians(-124), math.radians(44), math.radians(163),
            math.radians(7)
        ]

        # Move to start position once
        self.moveit2.move_to_configuration(self.start_joints)
        self.moveit2.wait_until_executed()

    # ================= CALLBACK ================= #

    def coords_callback(self, msg):

        if self.already_moved:
            return

        try:
            color_id, x, y, z = msg.data.split(",")
            color_id = color_id.strip().upper()

            if color_id != self.target_color:
                return

            # Lock coordinates
            self.target_coords = [float(x), float(y), float(z)]
            self.already_moved = True

            self.get_logger().info(
                f"Locked {color_id} at {self.target_coords}"
            )

            # ---------------- PICK POSITION ---------------- #
            pick_position = [
                self.target_coords[0],
                self.target_coords[1],
                self.target_coords[2] - 0.60
            ]

            quat = [0.0, 1.0, 0.0, 0.0]

            # ================= PICK SEQUENCE ================= #

            self.moveit2.move_to_configuration(self.home_joints)
            self.moveit2.wait_until_executed()

            self.moveit2.move_to_pose(position=pick_position, quat_xyzw=quat)
            self.moveit2.wait_until_executed()

            self.gripper.open()
            self.gripper.wait_until_executed()

            approach_position = [
                pick_position[0],
                pick_position[1],
                pick_position[2] - self.approach_offset
            ]

            self.moveit2.move_to_pose(
                position=approach_position,
                quat_xyzw=quat,
                cartesian=True
            )
            self.moveit2.wait_until_executed()

            self.gripper.close()
            self.gripper.wait_until_executed()

            self.moveit2.move_to_configuration(self.home_joints)
            self.moveit2.wait_until_executed()

            self.moveit2.move_to_configuration(self.drop_joints)
            self.moveit2.wait_until_executed()

            self.gripper.open()
            self.gripper.wait_until_executed()

            self.moveit2.move_to_configuration(self.start_joints)
            self.moveit2.wait_until_executed()

            self.get_logger().info("Cycle complete ✔")

            # 🔥 RESET FOR NEXT TASK (IMPORTANT)
            self.already_moved = False
            self.target_coords = None

        except Exception as e:
            self.get_logger().error(f"Error: {e}")


# ================= MAIN ================= #

def main():
    rclpy.init()
    node = PickAndPlace()

    executor = rclpy.executors.MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()