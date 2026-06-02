
# 🤖 Franka Emika Panda 7 DOF Robot — Vision-Language-Action System

A **ROS 2 Humble-based autonomous robotic manipulation system** using the **Franka Emika Panda robotic arm**, integrating **computer vision, MoveIt 2 motion planning, and Large Language Models (LLM)** to enable natural language driven pick-and-place tasks in Gazebo simulation.

The system converts **human language commands into structured robot actions using Gemini LLM**, and executes them using a vision-guided manipulation pipeline.

---

## ✨ Features

* 🦾 **Motion Planning**: Trajectory execution using MoveIt 2
* 🧠 **LLM Task Planning**: Natural language → structured JSON tasks using Gemini API
* 🎯 **Autonomous Manipulation**: Fully automated pick-and-place execution
* 🎨 **Vision-Based Detection**: OpenCV-based red, green, blue object detection
* 📍 **TF2-Based Localization**: Converts camera coordinates into robot base frame
* 🔄 **Sequential Task Execution**: Executes multiple tasks one by one
* 📊 **RViz + Gazebo Visualization**: Real-time simulation and robot monitoring

---

## 📦 Packages

* **franka_description** → Robot URDF/Xacro, meshes, Gazebo model
* **franka_bringup** → Launch files for simulation, controllers, and robot startup
* **franka_moveit** → MoveIt 2 configuration for motion planning
* **franka_interfaces** → Custom ROS2 service definitions (`TaskCommand.srv`)
* **llm_planner** → LLM-based task planning node (Gemini integration)
* **pymoveit2** → Pick-and-place execution logic with MoveIt 2
* **color_detector (franka_vision)** → OpenCV-based perception node

---

## 🏗️ Installation

### 1. Create Workspace

```bash
mkdir -p ~/franka_ws/src
cd ~/franka_ws/src
git clone <your-repo-url>
```

### 2. Install Dependencies

```bash
cd ~/franka_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 3. Build Workspace

```bash
colcon build
source install/setup.bash
```

---

## 🚀 Running the System

You must open **two terminals inside Docker/Ubuntu environment**.

---

### 🖥️ Terminal 1 — Launch Robot Simulation

```bash
source ~/franka_ws/install/setup.bash
ros2 launch franka_bringup pick_and_place.launch.py
```

This starts:

* Gazebo simulation with Franka Panda
* MoveIt 2 motion planning
* RViz visualization
* Camera + perception pipeline
* Controllers and TF tree

---

### 🧠 Terminal 2 — Start LLM Planner Node

```bash
source ~/franka_ws/install/setup.bash
ros2 run llm_planner task_planner_node
```

This node:

* Receives natural language commands
* Sends them to Gemini API
* Converts them into structured JSON tasks
* Sends tasks to robot execution layer

---

### 🤖 Send Natural Language Command

```bash
ros2 service call /task_command franka_interfaces/srv/TaskCommand \
"{command: 'pick red object and stack green one'}"
```

---

## 🔄 System Architecture

```text
User Command (Natural Language)
        ↓
ROS2 Service (/task_command)
        ↓
LLM Planner Node (Gemini API)
        ↓
JSON Task Generation
        ↓
Sequential Task Executor
        ↓
MoveIt2 Pick & Place Controller
        ↓
Franka Panda Robot Execution


Parallel Perception Path:
Camera Feed → OpenCV Detection → TF2 Transformation → /color_coordinates → Robot
```

---

## 🔍 Useful ROS 2 Commands

```bash
ros2 node list
ros2 topic list
ros2 service list
ros2 topic echo /color_coordinates
ros2 topic echo /joint_states
ros2 run rqt_graph rqt_graph
ros2 run rqt_image_view rqt_image_view
```

---

## 🧠 LLM Integration

* Provider: **Google Gemini API**
* Model: `gemini-flash-latest` (or available flash models)
* Library: `google-genai`
* Function: Converts natural language → structured robot task JSON

Example output:

```json
[
  {
    "action": "pick_and_place",
    "color": "R",
    "destination": "bin"
  }
]
```

---

## 📚 Project Summary

This project demonstrates a complete **Vision-Language-Action robotic system** where a Franka Panda robot performs autonomous manipulation by combining:

* Computer Vision (object detection)
* LLM-based reasoning (task planning)
* Motion planning (MoveIt2)
* ROS2 communication (services/topics)
* Simulation (Gazebo + RViz)

It enables the robot to understand commands like:

> “pick red object and stack green one”

and execute them autonomously in simulation.

