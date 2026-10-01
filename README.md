# 🍉 Fruit Ninja 

An advanced **AI-powered Fruit Ninja** game featuring real-time **hand gesture recognition**, **high-resolution fruit textures**, **Chaikin curve blade smoothing**, and a modern **glassmorphic UI/UX design**. Built with Python, Pygame-CE, OpenCV, and MediaPipe.

---

## ✨ Key Highlights & Features

### 🖐️ Computer Vision & Tracking
- **MediaPipe 1.0+ & Legacy API Support**: Auto-downloads and initializes `hand_landmarker.task` for MediaPipe Tasks API.
- **Enhanced Accuracy & Jitter Reduction**: Confidence thresholds tuned to `0.75` for detection and tracking.
- **Moving Average Coordinate Filtering**: 5-frame moving average buffer on index fingertip coordinates to eliminate jitter.
- **Chaikin Corner-Cutting Blade Smoothing**: Iterative curve subdivision algorithm transforms raw tracking points into a continuous, silky smooth glowing blade trail.
- **Closest-Point Line Segment Collision**: Vector projection line-segment vs circle intersection algorithm ($P_{closest} = P_1 + t \cdot (P_2 - P_1)$ with $t \in [0, 1]$) guarantees sub-pixel accuracy even on ultra-fast swipes.

### 🎨 Visual & Graphics Enhancements
- **Pre-Rendered Transparent Fruit Textures**: Real fruit PNG textures (`apple.png`, `banana.png`, `orange.png`, `watermelon.png`, `pineapple.png`, `golden.png`) in `data/`.
- **Aligned Physics Hitboxes**: Pre-scaled to exact diameter (`radius * 2`), rotated and centered dynamically on `(x, y)` physics coordinates.
- **Sliced Fruit Splitting**: Real-time half-sprite surface clipping, rotational divergence, and alpha fading.

### 💎 Glassmorphic UI/UX Design System
- **Glassmorphic In-Game HUD**: Translucent header bar with cyan glowing borders, glowing score counters, and high-score badge.
- **Level Progress Bar**: Live progress bar indicating progress to the next level right on the HUD header.
- **Animated Heart Lives**: Multi-layered glowing vector heart indicators for active lives.
- **Performance Ranks**: Performance grading (`👑 S-RANK`, `💎 A-RANK`, `⚔️ B-RANK`, `🍉 C-RANK`) calculated on the Game Over screen based on score and slicing accuracy.
- **Modern Menus & Cards**: Glassmorphic title plate, hover neon borders, 2x2 Mode Select grid, and achievement badges.

### 🎮 Gameplay Modes & Mechanics
- **4 Game Modes**: Classic (3 lives, bombs), Arcade (60s blitz), Zen (no bombs), Survival (1 life).
- **Power-ups**: Freeze Time, Fire Blade, Double Score, Slow Motion with active countdown badges.
- **Boss Battles**: Mega Watermelon Boss fights with health bar every 10 levels.
- **Achievements & Persistence**: High scores and 9 unlockable achievements saved to JSON.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ (Supports Python 3.14 via `pygame-ce`)
- Webcam (optional — mouse fallback mode available)

### Installation
```bash
pip install -r requirements.txt
```

### Run
```bash
python main.py
```

### Controls
| Input | Action |
|---|---|
| **Index finger** | Blade / Slice |
| **Open palm** | Pause Game |
| **Mouse (left click + drag)** | Blade (Fallback) |
| **TAB** | Toggle Mouse / Hand Tracking mode |
| **SPACE / ESC** | Pause / Resume |
| **R** | Replay (Game Over screen) |
| **M** | Return to Main Menu |

---

## 📁 Project Architecture

```
fruit ninja/
├── main.py                    # Main game loop, state manager & rendering
├── config.py                  # Colors, tuning constants & difficulty tiers
├── requirements.txt           # Dependencies (pygame-ce, opencv-python, mediapipe, numpy)
├── hand_landmarker.task       # MediaPipe HandLandmarker model file
├── README.md
│
├── vision/                    # Computer Vision pipeline
│   ├── camera.py              # OpenCV camera stream handler
│   ├── hand_detector.py       # MediaPipe 21-landmark detector & smoothing filter
│   ├── gesture_recognizer.py  # Semantic gesture classification
│   └── motion_analyzer.py     # Velocity, acceleration, and trail analyzer
│
├── entities/                  # Game objects & renderers
│   ├── fruit.py               # PNG fruit entity, rotation & half-slice rendering
│   ├── bomb.py                # Bomb entity & fuse sparkle animation
│   ├── powerup.py             # Collectible power-ups
│   ├── blade.py               # Chaikin smooth curve blade trail renderer
│   └── particle.py            # Juice splash particles & score popups
│
├── systems/                   # Gameplay logic systems
│   ├── fruit_spawner.py       # Wave & difficulty spawner
│   ├── scoring.py             # Score, accuracy & high score manager
│   ├── combo.py               # Multiplier & combo manager
│   ├── lives.py               # Health management
│   ├── powerup_system.py      # Active power-up timers
│   ├── level_system.py        # XP level progression
│   └── achievement_system.py  # Achievement tracking & popup queue
│
├── core/                      # Engine math & physics
│   └── collision.py           # Closest-point line segment vs circle intersection
│
├── effects/                   # Screen effects
│   └── screen_effects.py      # Screen shake & flash overlays
│
├── ui/                        # User Interface
│   └── hud.py                 # Modern glassmorphic HUD overlay
│
└── data/                      # Asset storage & saved data
    ├── apple.png, banana.png...# Fruit PNG sprite graphics
    ├── scores.json            # High scores
    └── achievements.json      # Unlocked achievements
```

---
## 🔬 Mathematical & Algorithm Specifications

### 1. Chaikin's Corner-Cutting Curve Smoothing
Given ordered trail control points $P_0, P_1, \dots, P_n$:
For each segment $(P_i, P_{i+1})$, generate two refined vertices:
$$Q_i = 0.75 P_i + 0.25 P_{i+1}$$
$$R_i = 0.25 P_i + 0.75 P_{i+1}$$
Iterated over 2 passes to yield an aesthetically smooth $C^1$ continuous curved blade path.

### 2. Closest-Point Vector Line-Segment Collision
To determine if blade segment $P_1 \to P_2$ hits entity circle $(C, r)$:
$$t = \text{clamp}\left(\frac{(C - P_1) \cdot (P_2 - P_1)}{|P_2 - P_1|^2}, 0, 1\right)$$
$$P_{closest} = P_1 + t \cdot (P_2 - P_1)$$
$$\text{Hit} \iff |P_{closest} - C|^2 \le r^2$$

---

## 📜 License
MIT — Built for educational and portfolio demonstration.
