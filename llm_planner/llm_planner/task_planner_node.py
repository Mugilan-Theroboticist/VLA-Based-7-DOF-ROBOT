import rclpy
from rclpy.node import Node
from franka_interfaces.srv import TaskCommand
import subprocess
import json
import os
import time
from google import genai


SYSTEM_PROMPT = """
You are a robotics task planner.

Convert user commands into JSON tasks.

Each task must be:
{
  "action": "pick_and_place",
  "color": "R" or "G" or "B",
  "destination": "bin" or "stack"
}

Return ONLY a JSON list.
NO explanation.
NO markdown.
"""


class TaskPlannerNode(Node):

    def __init__(self):
        super().__init__('task_planner_node')

        self.srv = self.create_service(
            TaskCommand,
            'task_command',
            self.callback
        )

        self.get_logger().info("LLM Planner Node Ready 🚀")

    # ================= SERVICE CALLBACK ================= #

    def callback(self, request, response):

        command = request.command
        self.get_logger().info(f"Received: {command}")

        try:
            tasks = self.call_llm(command)
        except Exception as e:
            self.get_logger().error(str(e))
            response.success = False
            response.message = str(e)
            response.executed_tasks = []
            return response

        executed = []

        self.get_logger().info(f"TOTAL TASKS RECEIVED: {len(tasks)}")

        # ================= SEQUENTIAL EXECUTION ================= #
        for i, task in enumerate(tasks):

            try:
                color = task.get("color", "").upper()
                dest = task.get("destination", "bin")

                # validate color
                if color not in ["R", "G", "B"]:
                    self.get_logger().warn(f"Skipping invalid task: {task}")
                    continue

                self.get_logger().info(
                    f"STEP {i+1}/{len(tasks)} → Executing {color} → {dest}"
                )

                result = subprocess.run([
                    "ros2", "run", "pymoveit2", "pick_and_place.py",
                    "--ros-args", "-p", f"target_color:={color}"
                ])

                if result.returncode != 0:
                    self.get_logger().error(f"Task failed for {color}")

                executed.append(f"{color}->{dest}")

                # IMPORTANT: allow robot to reset between tasks
                time.sleep(2)

            except Exception as e:
                self.get_logger().error(f"Task execution error: {e}")
                continue

        response.success = True
        response.message = f"Done {len(executed)} tasks"
        response.executed_tasks = executed

        return response

    # ================= LLM CALL (WITH RETRY) ================= #

    def call_llm(self, command):

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise Exception("GEMINI_API_KEY not set")

        client = genai.Client(api_key=api_key)

        model = "gemini-flash-latest"
        prompt = SYSTEM_PROMPT + "\nUser: " + command

        last_error = None

        # 🔁 RETRY LOGIC
        for attempt in range(3):

            try:
                self.get_logger().info(f"LLM attempt {attempt+1}/3")

                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                text = response.text.strip()

                self.get_logger().info(f"RAW LLM OUTPUT:\n{text}")

                # clean markdown
                text = text.replace("```json", "").replace("```", "").strip()

                tasks = json.loads(text)

                # validate output type
                if not isinstance(tasks, list):
                    raise Exception("LLM did not return a list")

                return tasks

            except Exception as e:
                last_error = e
                self.get_logger().warn(f"LLM failed attempt {attempt+1}: {e}")
                time.sleep(2)

        # ================= FALLBACK ================= #

        self.get_logger().error("LLM failed → using fallback plan")

        return [
            {"action": "pick_and_place", "color": "R", "destination": "bin"},
            {"action": "pick_and_place", "color": "G", "destination": "bin"}
        ]


# ================= MAIN ================= #

def main():
    rclpy.init()
    node = TaskPlannerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()