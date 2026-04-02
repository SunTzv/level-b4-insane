## Game Design Document: Level B4 Insane

---

### **1. Game Overview**

* **Project Title:** Level B4 Insane
* **Genre:** Management Simulator / Psychological Horror
* **Engine:** Python (Pygame)
* **Camera & Perspective:** 2.5D Isometric (Pseudo-3D). The environment is built on a diamond grid, with 2D sprites layered and Y-sorted to create the illusion of depth.
* **Core Theme:** Repressed guilt, isolation, and the subversion of mundane, repetitive tasks. 

> *"Just keep track of the plates, kid. Don't worry about the noise from the lower levels; it's just the ventilation settling." — The Boss*

---

### **2. Visual & Audio Direction**

**2.5D Visual Style**
* **Perspective:** True isometric projection (dimetric angle, roughly 30 degrees). Walls and pillars are drawn as vertical extrusions.
* **Color Palette:** Monochromatic and washed out. Harsh, pale yellows for the flickering fluorescent lights, surrounded by deep, oppressive charcoal blacks for unlit areas.
* **Lighting Engine (Pygame Custom):** Using Pygame's `pygame.Surface` with `BLEND_RGBA_MULT` to create a dynamic darkness overlay. The player and working headlights act as "cutouts" in the darkness.
* **UI Design:** Diegetic and clunky. The logbook resembles a pixelated, late-90s MS-DOS terminal interface. 

**Audio Design**
* **Atmosphere:** Heavy, low-frequency hums. The sound of distant water dripping. 
* **Mechanics:** Loud, echoing footsteps. Heavy, mechanical clunks when the entry/exit barriers open.
* **Horror Elements:** Audio distortion tied to the Paranoia meter. Subtle whispers hidden beneath the sound of idling car engines.

---

### **3. Core Gameplay Mechanics**

The game operates on a dual-loop system: the primary management loop, which slowly degrades, and the secondary survival/horror loop, which takes over.

**Primary Loop: The Job**
1.  **Admit/Exit:** Monitor the entrance barrier. Note the license plate and vehicle type.
2.  **Valet (Days 2+):** Enter vehicles and drive them to highlighted isometric grid coordinates. 
3.  **Log:** Enter data into the terminal. Accurate logs earn "tips," which are meaningless but feed into the illusion of a standard game loop.

**Secondary Loop: The Descent**
1.  **Paranoia Management:** Standing in unlit areas slowly increases a hidden `paranoia_float` variable. High paranoia triggers auditory hallucinations and UI glitches.
2.  **Anomaly Investigation:** Interacting with abnormal entities (the autonomous car, the black sedan) without lingering too long.
3.  **Spatial Navigation:** Surviving as the physical geometry of the parking lot begins to defy logic (endless corridors, looping exits).

---

### **4. Control Scheme**

A tank-control scheme for driving enhances the feeling of weight and claustrophobia in tight parking spaces, while standard movement applies to walking.

| Action | Keybinding | Context |
| :--- | :--- | :--- |
| **Move / Accelerate** | `W` / `Up Arrow` | Player (Walk) / Car (Gas) |
| **Reverse / Back Up** | `S` / `Down Arrow` | Player (Walk) / Car (Brake/Reverse) |
| **Turn Left/Right** | `A` / `D` | Player (Strafe) / Car (Steering) |
| **Interact / Enter Car** | `E` | Terminals, Barriers, Car Doors |
| **Toggle Flashlight** | `F` | Only available from Day 3 onwards |
| **Open Logbook** | `TAB` | Pauses game on Day 1; real-time on Day 3+ |

---

### **5. Progression & Lore (The 5-Day Shift)**

| Day | Duration | The Job | The Horror Escalation |
| :--- | :--- | :--- | :--- |
| **1** | 3 mins | Let cars in/out. Use terminal. | **The Discrepancy:** Log shows 1 missing car. Player finds a damaged, plateless black sedan in the dark. |
| **2** | 5 mins | Valet parking introduced. | **The Autonomous Car:** Tinted windows, doors lock on approach. Moves only when the player's back is turned. |
| **3** | 7 mins | Level B2 opens. Elevator use required. | **The Glitch:** Logbook text scrambles. Distant sounds of a violent car crash. The black sedan blocks key paths. |
| **4** | 10 mins | Re-organize parked cars. No new entries. | **The Isolation:** Exit barrier jams. Pygame alpha-channel shadows stretch aggressively. Cars flash high-beams when walked past. |
| **5** | ∞ | Survive. | **The Labyrinth:** Map geometry loops infinitely. All cars are the black sedan. Driving mechanics invert. Forced fatal crash ending. |

---

### **6. Technical Architecture (Pygame Implementation)**

**Entity Management & Y-Sorting**
To maintain the 2.5D illusion, all game objects (player, cars, pillars) must be stored in a dynamic list and sorted by their Y-coordinate every frame before rendering.
* **Logic:** `render_list.sort(key=lambda obj: obj.rect.bottom)`
* Objects with a lower bottom Y-coordinate are drawn first (behind), while objects with a higher Y-coordinate are drawn last (in front).

**Collision Detection**
Due to the isometric perspective, standard rectangular hitboxes (`pygame.Rect`) will feel inaccurate. 
* **Solution:** Use polygonal hitboxes mapped to the diamond grid footprint of the sprites, utilizing `pygame.math.Vector2` for precise point-in-polygon collision checking during driving sequences.

**State Machine**
The game will rely on a robust state machine to handle the shifting reality of the garage.
* `GameState.NORMAL`: Standard collision and logic.
* `GameState.DECAY`: Introduces RNG-based audio cues and shadow manipulation.
* `GameState.NIGHTMARE`: Disables map boundaries, triggering screen-wrap math (`if player.x > screen_width: player.x = 0`) to create the endless labyrinth effect on Day 5.