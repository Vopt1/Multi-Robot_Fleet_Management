# Multi-Robot Fleet Management — Project Notes

> Agent-facing reference document. Updated: 2026-10-12.

---

## Overview

A **ROS 2** workspace that simulates and manages a fleet of differential-drive robots inside an **AWS RoboMaker small warehouse** world rendered in **Gazebo (gz-sim)**. Each robot is independently localized with **AMCL** and fused with an **EKF** node. The fleet size and spawn positions are controlled entirely by a single YAML config file — no code changes needed to add/remove robots.

---

## Workspace Layout

```
Multi-Robot_Fleet_Management/
├── src/
│   ├── AWS_world/                     # Gazebo world package (warehouse environment)
│   ├── differential_drive_description/ # Robot URDF, launch files, EKF & driver node
│   ├── fleet_manager_bringup/          # Top-level bringup: spins up the whole fleet
│   └── multi_bot_navigation/          # Per-robot AMCL localization & Nav2 config
├── build/                             # colcon build artifacts (gitignored)
└── PROJECT_NOTES.md                   # This file
```

---

## ROS 2 Packages

### 1. `AWS_world`
| Item | Detail |
|------|--------|
| **Purpose** | Provides the Gazebo simulation world (small warehouse) |
| **Worlds** | `small_warehouse.world`, `no_roof_small_warehouse.world` |
| **Models** | AWS RoboMaker warehouse assets: shelves, lamps, walls, floor tiles, pallet jacks, etc. |
| **Key files** | `worlds/`, `models/` |

---

### 2. `differential_drive_description`
| Item | Detail |
|------|--------|
| **Purpose** | Robot definition, spawning, sensor bridging, and EKF localization |
| **URDF** | `description/urdfs/main.urdf` — uses `ROBOT_NAME_PLACEHOLDER` which is substituted at launch time per-namespace |
| **Driver node** | `differential_drive_description/driver.py` — simple test node, publishes `Twist` on `cmd_vel` at 5 Hz (`linear.x=1.0`, `angular.z=0.5`) |
| **EKF config** | `config/ekf.yaml` — fuses `wheel_odom` (vx, wz) + `imu` (yaw, wz with `imu0_relative: true`) at 30 Hz, 2D mode |
| **Maintainer** | vatsalya-brahmatmaj (vatsalyabrahmatmaj@gmail.com) |

#### Launch Files
| File | What it does |
|------|-------------|
| `single_bot.launch.py` | Spawns **one** robot: robot_state_publisher → gz spawner → ros_gz_bridge → EKF node. Takes `namespace`, `x`, `y`, `z` args. |
| `multi_bot_spawn.py`   | Reads `config/warehouse.yaml` and spawns all listed robots in one call (older approach). |
| `gz_sim.launch.py`     | Starts Gazebo sim world only. |
| `one_bot.launch.py`    | Convenience launcher for a single robot (standalone). |

#### ROS ↔ Gazebo Bridge Topics (per robot, namespace = `<ns>`)
| Gazebo topic | ROS topic | Direction | Type |
|---|---|---|---|
| `/model/<ns>/imu` | `/<ns>/imu` | Gz → ROS | `sensor_msgs/Imu` |
| `/model/<ns>/cmd_vel` | `/<ns>/cmd_vel` | ROS → Gz | `geometry_msgs/Twist` |
| `/model/<ns>/scan` | `/<ns>/scan` | Gz → ROS | `sensor_msgs/LaserScan` |
| `/model/<ns>/joint_states` | `/<ns>/joint_states` | Gz → ROS | `sensor_msgs/JointState` |
| `/model/<ns>/odom` | `/<ns>/wheel_odom` | Gz → ROS | `nav_msgs/Odometry` |

---

### 3. `fleet_manager_bringup`
| Item | Detail |
|------|--------|
| **Purpose** | Orchestrates the entire system — world + map server + all robots |
| **Config** | `config/warehouse.yaml` — list of robots with name, namespace, x, y, z |
| **Entry point** | `launch/multi_bot.launch.py` |

#### `multi_bot.launch.py` Sequence
1. Launches `AWS_world/launch/warehouse.launch.py` (Gazebo world)
2. Starts `nav2_map_server` with `maps/005/map.yaml` (shared map, `use_sim_time=True`)
3. Starts `nav2_lifecycle_manager` to manage the map server
4. For **each robot** in `warehouse.yaml`:
   - Includes `single_bot.launch.py` (spawn + bridge + EKF)
   - Includes `amcl.launch.py` (AMCL + lifecycle manager)

---

### 4. `multi_bot_navigation`
| Item | Detail |
|------|--------|
| **Purpose** | Per-robot AMCL localization node, namespaced correctly |
| **AMCL launch** | `launch/amcl.launch.py` — uses `RewrittenYaml` to inject namespace into the AMCL params |
| **AMCL config** | `config/amcl.yaml` — `DifferentialMotionModel`, likelihood field laser model, 500–2000 particles |
| **Nav2 config** | `config/nav2.yaml` — full Nav2 stack config (MPPI controller, NavFn planner, costmaps, behaviors, waypoint follower, docking server, etc.) |

#### AMCL per-robot param rewrites
| Parameter | Rewritten to |
|---|---|
| `base_frame_id` | `<namespace>/base_link` |
| `odom_frame_id` | `<namespace>/odom` |
| `global_frame_id` | `map` (shared) |
| `scan_topic` | `/<namespace>/scan` |
| Initial pose | x, y, z from `warehouse.yaml` |

---

## Robot Fleet Configuration

Edit [`src/fleet_manager_bringup/config/warehouse.yaml`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/fleet_manager_bringup/config/warehouse.yaml) to add/remove robots:

```yaml
robots:
  - name: "robot1"
    namespace: "robot1"
    x: 0.0
    y: 1.0
    z: 0.1
  - name: "robot2"
    namespace: "robot2"
    x: 0.0
    y: -1.0
    z: 0.1
  - name: "robot3"
    namespace: "robot3"
    x: 2.0
    y: 0.0
    z: 0.1
```

> [!NOTE]
> `name` and `namespace` are kept identical. `z: 0.1` spawns the robot slightly above the ground plane to avoid collision with the floor mesh on spawn.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `ROBOT_NAME_PLACEHOLDER` in URDF | Allows one URDF to serve all robots; replaced at launch time per namespace |
| Shared `/map` topic | Single `map_server` serves all robots; each robot's AMCL subscribes via remapping `('map', '/map')` |
| Namespaced TF frames (`<ns>/base_link`, `<ns>/odom`) | Prevents TF tree collisions across robots |
| EKF fuses wheel odometry + IMU | Improves odometry accuracy before AMCL takes over for global localization |
| `RewrittenYaml` in AMCL launch | Injects per-robot namespace into a single YAML config file — no per-robot YAML needed |
| MPPI controller | Model Predictive Path Integral — smooth, obstacle-aware local planning for differential drive |

---

## System Architecture Diagram

```
                        ┌─────────────────────────┐
                        │   Gazebo Simulation       │
                        │   (AWS Warehouse World)   │
                        └────────────┬────────────┘
                                     │ ros_gz_bridge
              ┌──────────────────────┼─────────────────────┐
              │                      │                      │
        ┌─────▼──────┐        ┌──────▼─────┐        ┌──────▼─────┐
        │  robot1    │        │  robot2    │        │  robot3    │
        │  namespace │        │  namespace │        │  namespace │
        │            │        │            │        │            │
        │ RSP        │        │ RSP        │        │ RSP        │
        │ EKF node   │        │ EKF node   │        │ EKF node   │
        │ AMCL       │        │ AMCL       │        │ AMCL       │
        └────────────┘        └────────────┘        └────────────┘
                                     │
                               ┌─────▼──────┐
                               │ map_server │
                               │ (shared)   │
                               └────────────┘
```

---

## Build & Run

```bash
# Build
cd Multi-Robot_Fleet_Management
colcon build --symlink-install

# Source
source install/setup.bash

# Launch the full fleet
ros2 launch fleet_manager_bringup multi_bot.launch.py

# Launch a single robot (for testing)
ros2 launch differential_drive_description single_bot.launch.py namespace:=robot1 x:=0.0 y:=0.0 z:=0.1
```

---

## Dependencies (Key)

| Package | Role |
|---|---|
| `ros_gz_sim` / `ros_gz_bridge` | Gazebo ↔ ROS 2 integration |
| `robot_state_publisher` | Publishes TF from URDF |
| `robot_localization` (`ekf_node`) | Sensor fusion (wheel odom + IMU) |
| `nav2_amcl` | Adaptive Monte Carlo Localization |
| `nav2_map_server` | Loads and serves the pre-built map |
| `nav2_lifecycle_manager` | Manages Nav2 node lifecycle |
| `nav2_mppi_controller` | Local path following (MPPI) |
| `nav2_navfn_planner` | Global path planning (Dijkstra/A*) |
| `xacro` | URDF preprocessing |
| `ament_python` | Build system for all packages |

---

## Files To Know First

| File | Why |
|---|---|
| [`fleet_manager_bringup/config/warehouse.yaml`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/fleet_manager_bringup/config/warehouse.yaml) | Add/remove robots here |
| [`fleet_manager_bringup/launch/multi_bot.launch.py`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/fleet_manager_bringup/launch/multi_bot.launch.py) | System entry point |
| [`differential_drive_description/launch/single_bot.launch.py`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/differential_drive_description/launch/single_bot.launch.py) | Per-robot spawn logic |
| [`multi_bot_navigation/launch/amcl.launch.py`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/multi_bot_navigation/launch/amcl.launch.py) | Per-robot AMCL setup |
| [`differential_drive_description/config/ekf.yaml`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/differential_drive_description/config/ekf.yaml) | Sensor fusion config |
| [`multi_bot_navigation/config/nav2.yaml`](file:///home/vatsalya/Desktop/Multi-Robot_Fleet_Management/src/multi_bot_navigation/config/nav2.yaml) | Full Nav2 stack params |
