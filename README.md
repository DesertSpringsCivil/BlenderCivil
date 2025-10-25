# BlenderCivil v0.3.0 - Professional Alignment System
## Phase 1: IFC-Compatible Separate Entity Architecture

**Status:** ✅ Phase 1 Complete - Ready for Testing  
**Date:** October 24, 2025  
**Architecture:** Separate Entities with Explicit Relationships

---

## 🎉 What's New in v0.3.0

### Revolutionary Changes:
- ✅ **Separate Entity Architecture** - Each tangent and curve is now an individual object
- ✅ **Explicit Object Relationships** - Using Blender's PointerProperty (not string-based!)
- ✅ **IFC-Compatible Structure** - Follows buildingSMART IFC Road standards
- ✅ **Enhanced PI Points** - Rich properties with explicit connections
- ✅ **Auto-Update System** - Depsgraph handler watches for PI movements
- ✅ **Professional Hierarchy** - Collections organize elements like Civil 3D/OpenRoads
- ✅ **Color Coding** - Red tangents, green curves for easy identification

### What This Means:
- ✅ Click to select individual tangents or curves
- ✅ Each element has its own properties and constraints
- ✅ Clean hierarchy in Outliner
- ✅ True professional workflow
- ✅ IFC export/import ready (Phase 4)

---

## 📦 Installation

### Method 1: Install as Blender Addon

1. **Prepare the addon folder:**
   ```
   BlenderCivil_v2/
   ├── __init__.py
   ├── properties_v2.py
   ├── alignment_objects_v2.py
   ├── operators_v2.py
   ├── handlers_v2.py
   └── ui_v2.py
   ```

2. **Zip the folder:**
   - On Windows: Right-click folder → Send to → Compressed folder
   - On Mac/Linux: `zip -r BlenderCivil_v2.zip BlenderCivil_v2/`

3. **Install in Blender:**
   - Open Blender
   - Edit → Preferences → Add-ons
   - Click "Install..."
   - Select the zip file
   - Enable "BlenderCivil v0.3.0"

4. **Verify installation:**
   - Check console for: `✓ BlenderCivil v0.3.0 ready!`
   - Open N-panel (press N) → Civil tab should appear

### Method 2: Development Mode (for testing/development)

1. **Copy files to Blender scripts folder:**
   - Windows: `C:\Users\<YourName>\AppData\Roaming\Blender Foundation\Blender\<version>\scripts\addons\`
   - Mac: `~/Library/Application Support/Blender/<version>/scripts/addons/`
   - Linux: `~/.config/blender/<version>/scripts/addons/`

2. **Restart Blender**

3. **Enable addon in Preferences**

---

## 🚀 Quick Start Guide

### Step 1: Create PI Points

**PI points are control points where tangents would intersect if extended.**

1. Add Empty objects (Shift+A → Empty → Arrows)
2. Name them `PI_001`, `PI_002`, `PI_003`, etc.
3. Position them along your desired alignment route

**Example PI layout:**
```
PI_001: (0, 0, 0)        - Start point
PI_002: (200, 100, 0)    - First turn
PI_003: (400, 250, 0)    - Second turn
PI_004: (600, 300, 0)    - Third turn
PI_005: (800, 200, 0)    - End point
```

### Step 2: Create Alignment

1. Open N-panel (press N in viewport)
2. Go to "Civil" tab
3. Set properties:
   - **Name:** "My_Alignment"
   - **Default Radius:** 500 (meters)
   - **Design Speed:** 35 (mph)
4. Click **"Create Professional Alignment"**

**What happens:**
- ✅ Creates alignment root (hierarchy container)
- ✅ Converts PIs to enhanced objects with properties
- ✅ Creates red tangent lines between PIs
- ✅ Creates green curves at intermediate PIs
- ✅ Sets up explicit relationships
- ✅ Calculates stations
- ✅ Enables auto-update (default)

### Step 3: Interactive Design

**Now comes the magic! Move PIs and watch the alignment update automatically!**

1. **Select any PI point** (click on it)
2. **Press G key** (grab/move)
3. **Move your mouse** to reposition the PI
4. **Left-click to confirm** the new position
5. ⚡ **Alignment updates automatically!**

**What updates automatically:**
- ✅ Tangent lines adjust to pass through new PI location
- ✅ Curves recalculate to maintain tangency
- ✅ Stations update along alignment
- ✅ Element lengths recalculate
- ✅ Geometric properties update

---

## 🎯 Using the UI Panel

### Main Panel: "Professional Alignment (v0.3)"

**Location:** N-panel → Civil tab

#### Alignment Creation Section:
- **Create Professional Alignment** - Main creation button
- **Name** - Alignment name (default: "Alignment_01")
- **Default Radius** - Curve radius at PIs (default: 500m)
- **Design Speed** - Design speed in mph (default: 35mph)

#### Alignment Management Section:
- **Update from PIs (Manual)** - Force manual update (if auto-update off)
- **Analyze Alignment** - Generate detailed report in console

#### Auto-Update Status Section:
- Shows all alignments in scene
- Toggle auto-update ON/OFF per alignment
- **Auto-Update ON:** Changes propagate automatically
- **Auto-Update OFF:** Must click "Update from PIs" manually

#### Scene Status Section:
- **PI Points:** Count of PI points in scene
- **Alignments:** Count of alignments
- **Total Length:** Sum of all alignment lengths

---

## 📊 Understanding the Structure

### Object Hierarchy (IFC-Compatible)

```
Alignment_01_Collection/
├── Alignment_01 (Empty - Root)
└── Alignment_01_Horizontal/
    ├── PI_001 (Empty with properties)
    ├── Tangent_001 (Curve - RED)
    ├── PI_002 (Empty with properties)
    ├── Curve_001 (Curve - GREEN)
    ├── Tangent_002 (Curve - RED)
    ├── PI_003 (Empty with properties)
    └── ...
```

### Object Types and Properties

#### 1. **PI Points** (Enhanced Empties)
**Properties:**
- `index` - Sequential PI number
- `station` - Station location
- `radius` - Curve radius at this PI
- `design_speed` - Design speed for segment
- `alignment_root` - PointerProperty to parent alignment
- `tangent_in` - PointerProperty to incoming tangent
- `tangent_out` - PointerProperty to outgoing tangent
- `curve` - PointerProperty to curve at this PI

#### 2. **Tangent Lines** (Curve Objects - RED)
**Properties:**
- `constraint` - FIXED, FLOATING, or FREE
- `length` - Tangent length
- `bearing` - Angle from north (+Y axis)
- `start_station` / `end_station`
- `pi_start` - PointerProperty to start PI
- `pi_end` - PointerProperty to end PI
- `previous_element` / `next_element` - Adjacent elements

#### 3. **Curves** (Curve Objects - GREEN)
**Properties:**
- `constraint` - FIXED, FLOATING, or FREE
- `radius` - Curve radius
- `delta_angle` - Central angle (radians)
- `length` - Arc length
- `tangent_length` - PC/PT to PI distance
- `start_station` / `end_station`
- `pi` - PointerProperty to associated PI
- `previous_element` / `next_element` - Adjacent elements

#### 4. **Alignment Root** (Empty - Container)
**Properties:**
- `alignment_name` - Human-readable name
- `alignment_type` - CENTERLINE, ROW, etc.
- `design_speed` - Design speed
- `total_length` - Total alignment length
- `auto_update_enabled` - Auto-update toggle

---

## 🔧 Operations

### Create Alignment
**Operator:** `civil.create_alignment_separate_v2`

**Requirements:**
- At least 2 PI points in scene (Empties named `PI_*`)

**Process:**
1. Finds all PI points
2. Creates alignment root and collections
3. Converts PIs to enhanced objects
4. Creates tangent lines between PIs
5. Creates curves at intermediate PIs
6. Sets up relationships (PointerProperty)
7. Calculates stations

**Output:**
- Prints detailed report to console
- Shows element count, lengths, geometry

### Update Alignment (Manual)
**Operator:** `civil.update_alignment_v2`

**When to use:**
- Auto-update is OFF
- After batch PI movements
- To force recalculation

**Process:**
1. Finds all alignments in scene
2. Updates tangent geometry
3. Updates curve geometry
4. Recalculates stations

### Analyze Alignment
**Operator:** `civil.analyze_alignment_v2`

**Output (to console):**
- General properties (type, speed, length)
- Element count (PIs, tangents, curves)
- PI details (index, location, radius)
- Element details (stations, lengths, geometry)

**Example Output:**
```
================================================================================
ALIGNMENT ANALYSIS: Test_Alignment
================================================================================

GENERAL PROPERTIES:
  Type: CENTERLINE
  Design Speed: 35.0 mph
  Total Length: 1247.35
  Auto-Update: ENABLED

ELEMENT COUNT:
  PIs: 5
  Tangents: 4
  Curves: 3
  Total Elements: 7

PI DETAILS:
--------------------------------------------------------------------------------
  PI_001     | Index:  1 | Location: (  0.00,   0.00,   0.00) | Radius:  500.0
  PI_002     | Index:  2 | Location: (200.00, 100.00,   0.00) | Radius:  500.0
  ...

ELEMENT DETAILS:
--------------------------------------------------------------------------------
  TANGENT  | Tangent_001     | Sta     0.00 -   223.61 | Length:   223.61
  CURVE    | Curve_001       | Sta   223.61 -   484.23 | L=  260.62 | R=500.0 | Δ=29.84°
  TANGENT  | Tangent_002     | Sta   484.23 -   765.19 | Length:   280.96
  ...
```

---

## 🎨 Visual Design

### Color Coding
- **RED** = Tangent lines (FIXED constraint)
- **GREEN** = Curves (FREE constraint)
- **Arrows** = PI points (enhanced empties)

### In the Outliner
- **Collections** organize elements
- **Parent-child** relationships visible
- **Select alignment root** to see all elements

### Selection
- **Click individual tangent** to select just that segment
- **Click individual curve** to select just that arc
- **Click PI** to select control point

---

## 🧪 Testing

### Automated Test Script

**File:** `test_alignment_v2.py`

**Run in Blender:**
1. Open Text Editor
2. Load `test_alignment_v2.py`
3. Press Alt+P to run

**Tests:**
- ✅ Alignment creation
- ✅ Manual update
- ✅ Analysis
- ✅ Auto-update (requires manual interaction)

### Manual Testing Checklist

- [ ] Create 5 PI points
- [ ] Create alignment from PIs
- [ ] Check console output
- [ ] Inspect Outliner hierarchy
- [ ] Select individual tangents/curves
- [ ] View object properties
- [ ] Move PI with G key
- [ ] Verify auto-update works
- [ ] Toggle auto-update OFF
- [ ] Move PI (should NOT update)
- [ ] Click "Update from PIs"
- [ ] Verify manual update works

---

## 🐛 Troubleshooting

### "Need at least 2 PI points"
**Solution:** Create Empty objects named `PI_001`, `PI_002`, etc.

### "No alignments found in scene"
**Solution:** Create an alignment first using the Create button

### Auto-update not working
**Check:**
1. Is auto-update enabled? (Check UI panel)
2. Are you moving PIs with G key? (Not Python scripts)
3. Is alignment root in scene?

**Fix:**
- Toggle auto-update OFF then ON
- Or use "Update from PIs" button

### Can't select individual elements
**This is the OLD system!** 
- Delete old single-entity alignment
- Create new v0.3 alignment
- New system has separate objects

---

## 📚 Technical Details

### Constraints (Phase 1)

**FIXED** - Tangent lines
- Both ends locked to specific PI locations
- When PI moves, tangent adjusts to connect

**FREE** - Curves
- Maintains tangency to both adjacent tangents
- Radius fixed, but position/angle adjusts automatically

**FLOATING** - Not yet implemented (Phase 2)
- Tangent to one element only
- Planned for future release

### Coordinate System
- **+Y** = North (0° bearing)
- **+X** = East (90° bearing)
- **+Z** = Up (elevation)

### Station System
- Cumulative distance along alignment
- Starts at 0.00 at first PI
- Increases through tangents and curves

### IFC Mapping (for Phase 4)

| BlenderCivil | IFC Entity |
|--------------|------------|
| Alignment Root | IfcAlignment |
| Horizontal Collection | IfcAlignmentHorizontal |
| PI Point | Implicit PI (calculated) |
| Tangent Line | IfcAlignmentSegment (LINE) |
| Curve | IfcAlignmentSegment (CIRCULARARC) |
| PointerProperty refs | IfcRelNests relationships |

---

## 🚦 Phase Roadmap

### ✅ Phase 1: Core Architecture (COMPLETE)
- Separate entity system
- Object pointer relationships
- Basic hierarchy
- Depsgraph auto-update
- Color coding
- Professional UI

### 🔄 Phase 2: Relationship System (Next - Week 2)
- Element neighbor tracking
- Constraint system refinement
- Relationship validation
- Element editing operators

### 📋 Phase 3: Interactive Editing (Week 3)
- Custom gizmos (Civil 3D-style grips)
- Visual feedback
- Element insertion/deletion
- Interactive radius adjustment

### 🌐 Phase 4: IFC Integration (Week 4)
- IFC export
- IFC import
- Material associations
- Full roundtrip capability

---

## 💡 Tips & Best Practices

### Creating Good Alignments
1. **Space PIs appropriately** - Not too close together
2. **Use consistent radius** - For uniform curves
3. **Design speed matters** - Affects minimum radius
4. **Name meaningfully** - "Main_Street_CL" not "Alignment_01"

### Working with Auto-Update
- **Leave it ON** for interactive design
- **Turn it OFF** for batch operations
- **Manual update** after multiple PI moves

### Performance
- Current system: Very fast (tested with 50+ PIs)
- Auto-update: Minimal overhead
- Only updates affected elements

---

## 🎓 Learning Resources

### Blender Concepts Used
- **Empty Objects** - Lightweight locators
- **Curve Objects** - Geometry with splines
- **Collections** - Organization hierarchy
- **PointerProperty** - Object references
- **Depsgraph** - Update notification system
- **Custom Properties** - Metadata storage

### Civil Engineering Concepts
- **PI (Point of Intersection)** - Control points
- **Tangent** - Straight line segment
- **Curve** - Circular arc transition
- **Station** - Distance along alignment
- **Bearing** - Direction angle
- **Delta Angle** - Central angle of curve

---

## 🤝 Contributing

### Reporting Issues
- Describe the problem clearly
- Include Blender version
- Attach .blend file if possible
- Copy console output

### Suggesting Features
- Check Phase roadmap first
- Explain use case
- Provide examples

---

## 📄 License

GPL v3

---

## 👏 Acknowledgments

- **buildingSMART International** - IFC standards
- **Blender Foundation** - Amazing 3D software
- **Civil 3D / OpenRoads** - Professional workflow inspiration

---

## 📞 Support

**Console Output:** All operations print detailed info to console (Window → Toggle System Console)

**Questions?** Check:
1. This README
2. Console output
3. Test script
4. Implementation Plan document

---

**BlenderCivil v0.3.0 - Built for Professional Civil Engineers** 🛣️✨

*"From Blender's flexibility + IFC standards = Professional civil design"*
