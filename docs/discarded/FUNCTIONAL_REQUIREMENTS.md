# Functional Requirements & Product Specification

**Application Name:** StageReady Bodybuilding Posing & Symmetry Analyzer  
**Target Platform:** Android (Jetpack Compose, Kotlin, CameraX)  
**Document Version:** 1.0  

---

## 1. Product Overview
StageReady is an offline-capable Android application designed for competitive bodybuilders, physique athletes, and fitness coaches. It provides real-time pose symmetry analysis, customizable overlay guides, voice/sound-assisted pose practice timers, a posture guide reference library, and a progress photo comparison gallery.

### Core Value Proposition
- **Real-Time Symmetry Analysis:** Evaluates shoulder tilt, elbow alignment, and center-line balance during mandatory posing practice.
- **Stage Lighting Aesthetics:** Dark-themed UI tailored for high-contrast visibility under gym and stage lighting conditions.
- **Hands-Free Operation:** Voice/audio countdown timer allowing athletes to practice posing without holding or touching the phone.
- **Structured Reference:** Comprehensive guide covering mandatory bodybuilding and physique posing routines.

---

## 2. User Stories

### Epics & Features

#### Epic 1: Camera & Real-Time Pose Practice
- **US-1.1:** As an athlete, I want a live camera preview with customizable overlay guides (center line, grid, pose silhouette outline) so I can align my posture accurately.
- **US-1.2:** As an athlete, I want instant visual feedback on shoulder levelness and elbow symmetry so I can make real-time micro-adjustments.
- **US-1.3:** As an athlete, I want to capture high-resolution posing snapshots and save them directly to my posing gallery.
- **US-1.4:** As an athlete, I want a simulation mode with adjustable tilt/asymmetry sliders to practice analyzing sample posing routines when live camera hardware is unavailable.

#### Epic 2: Pose Practice Timer
- **US-2.1:** As a competitor, I want a hands-free pose practice timer with customizable hold durations (e.g., 5s, 10s, 15s) and interval sets.
- **US-2.2:** As a competitor, I want audible countdown cues and voice prompts so I know when to transition between poses without looking at the screen.
- **US-2.3:** As a competitor, I want pose routine presets (e.g., "Men's Open Mandatory 8", "Classic Physique Quarter Turns") that automatically cycle through required poses.

#### Epic 3: Pose Reference Guide
- **US-3.1:** As a beginner or coach, I want a reference guide of official bodybuilding and physique poses with execution cues and key symmetry checkpoints.
- **US-3.2:** As an athlete, I want to quickly launch the camera preview directly from any pose guide entry with that pose's silhouette pre-selected.

#### Epic 4: Posing Gallery & Progress Tracking
- **US-4.1:** As an athlete, I want to review my saved posing snapshots sorted by date and pose category.
- **US-4.2:** As an athlete, I want a side-by-side comparison tool to evaluate physique progress over time (e.g., Week 1 vs. Week 12 prep).
- **US-4.3:** As an athlete, I want to mark snapshots as favorites or delete non-ideal captures.

---

## 3. Navigation Architecture

The app employs a standard Bottom Navigation Bar architecture with four primary top-level destinations:

1. **Camera Posing Screen (`route_camera_posing`)**
   - Live / Simulated Camera Feed
   - Real-time Symmetry Overlay Canvas
   - Quick Controls Bar (Grid toggle, Silhouette toggle, Symmetry meters, Camera shutter, Front/Back camera flip)
   - Pose Selection Strip
   - Asymmetry adjustment dialog (for simulation mode)

2. **Pose Guide Screen (`route_pose_guide`)**
   - Filterable Pose Category Tabs (Mandatory, Quarter Turns, Classic, Physique)
   - Detailed Pose Cards with key cues and target symmetry rules
   - "Practice This Pose" quick launch button

3. **Practice Timer Screen (`route_timer`)**
   - Customizable Pose Hold Duration (5s - 30s)
   - Routine Preset Selector (Open Bodybuilding, Classic Physique, Men's Physique, Custom)
   - Big Display Countdown Timer
   - Audio Cues & Speech Synthesis options

4. **Gallery Screen (`route_gallery`)**
   - Date-grouped Grid of Posing Snapshots
   - Side-by-Side Comparison Mode
   - Detail View with symmetry metadata (symmetry score %, date, pose type)

---

## 4. Data Models & Technical Requirements

### Key Data Structures

#### `BodybuildingPose` (Enum / Model)
- `id`: String
- `name`: String (e.g., "Front Double Biceps")
- `category`: PoseCategory (MANDATORY, QUARTER_TURNS, CLASSIC, PHYSIQUE)
- `keyCues`: List<String>
- `targetSymmetryPoints`: List<SymmetryCheckpoint>

#### `SymmetryAssessment` (Data Class)
- `overallScore`: Int (0 - 100%)
- `shoulderTiltDeg`: Float
- `elbowDiffPx`: Float
- `isCenterBalanced`: Boolean
- `feedbackMessage`: String

#### `PosingSnapshot` (Entity / Model)
- `id`: String / Long
- `timestamp`: Long
- `poseId`: String
- `imageUri`: String
- `symmetryScore`: Int
- `isFavorite`: Boolean

---

## 5. Non-Functional Requirements

- **Performance:** Symmetry calculations and overlay rendering must maintain 30+ FPS on mid-range Android devices.
- **Offline First:** All core capabilities (posing simulation, guides, timer, local gallery) function without network connectivity.
- **Permissions:** Camera permission (`android.permission.CAMERA`) requested dynamically with fallback to simulation mode.
- **Orientation:** Optimized for Vertical Portrait mode during posing practice.
