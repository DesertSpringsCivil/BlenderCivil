# BlenderCivil Native IFC - Developer Quick-Start Guide
**Version:** 1.0  
**Target Audience:** Python developers new to BlenderCivil  
**Prerequisites:** Basic Python, basic Blender knowledge

---

## ðŸš€ Quick Start

### 5-Minute Setup

```bash
# 1. Install IfcOpenShell in Blender's Python
cd /path/to/blender/python/bin
./python3 -m pip install ifcopenshell --break-system-packages

# 2. Clone BlenderCivil
git clone https://github.com/[your-repo]/blendercivil
cd blendercivil

# 3. Open Blender
blender

# 4. Load script in Blender Text Editor
# File → Text Editor → Open → native_ifc_manager.py

# 5. Run script (Alt+P)
```

**Done!** You're ready to create native IFC alignments.

---

## 🎯 Core Concepts

### 1. The IFC File is Everything

```python
import ifcopenshell

# This is NOT a helper file
# This IS your project data
ifc = ifcopenshell.file(schema="IFC4X3")
```

**Key Insight:** The IFC file isn't "output" - it's the project itself.

### 2. Blender Objects are "Views"

```python
# Blender object
curve = bpy.data.objects.new("Segment", curve_data)

# Stores only 3 things:
curve["ifc_definition_id"] = 42
curve["ifc_class"] = "IfcAlignmentSegment"  
curve["GlobalId"] = "2x3b5K..."

# Everything else comes from IFC!
```

### 3. Create IFC First, Blender Second

```python
# WRONG ORDER ❌
curve = bpy.data.objects.new(...)
ifc_seg = ifc.create_entity(...)

# CORRECT ORDER âœ…
ifc_seg = ifc.create_entity(...)  # IFC first
curve = bpy.data.objects.new(...)  # Blender second
NativeIfcManager.link_object(curve, ifc_seg)  # Link them
```

---

## 🔧 NativeIfcManager - Your Best Friend

### The Core API

```python
from native_ifc_manager import NativeIfcManager

# Create new IFC project
ifc = NativeIfcManager.new_file()

# Get current IFC file
ifc = NativeIfcManager.get_file()

# Save to disk
NativeIfcManager.save_file("/path/to/project.ifc")

# Load from disk
ifc = NativeIfcManager.open_file("/path/to/project.ifc")

# Link Blender object to IFC entity
NativeIfcManager.link_object(blender_obj, ifc_entity)

# Get IFC entity from Blender object
entity = NativeIfcManager.get_entity(blender_obj)

# Clear everything
NativeIfcManager.clear()
```

---

## 📝 Recipe: Create Your First Alignment

### Step-by-Step

```python
import bpy
import ifcopenshell
import ifcopenshell.guid
from native_ifc_manager import NativeIfcManager

# STEP 1: Get or create IFC file
ifc = NativeIfcManager.get_file()

# STEP 2: Create IfcAlignment entity
alignment = ifc.create_entity(
    "IfcAlignment",
    GlobalId=ifcopenshell.guid.new(),
    Name="My First Alignment",
    Description="Created in native IFC!"
)

# STEP 3: Create IfcAlignmentHorizontal
horizontal = ifc.create_entity(
    "IfcAlignmentHorizontal",
    GlobalId=ifcopenshell.guid.new()
)

# STEP 4: Create relationship
ifc.create_entity(
    "IfcRelNests",
    GlobalId=ifcopenshell.guid.new(),
    Name="AlignmentToHorizontal",
    RelatingObject=alignment,
    RelatedObjects=[horizontal]
)

# STEP 5: Create a LINE segment
segment = ifc.create_entity(
    "IfcAlignmentSegment",
    GlobalId=ifcopenshell.guid.new(),
    Name="Segment_001",
    DesignParameters=ifc.create_entity(
        "IfcAlignmentHorizontalSegment",
        StartPoint=ifc.create_entity(
            "IfcCartesianPoint",
            Coordinates=(0.0, 0.0)
        ),
        StartDirection=0.0,
        SegmentLength=100.0,
        PredefinedType="LINE"
    )
)

# STEP 6: Nest segment under horizontal
ifc.create_entity(
    "IfcRelNests",
    GlobalId=ifcopenshell.guid.new(),
    Name="HorizontalToSegment",
    RelatingObject=horizontal,
    RelatedObjects=[segment]
)

# STEP 7: Create Blender visualization
curve_data = bpy.data.curves.new("Alignment_001", 'CURVE')
curve_data.dimensions = '3D'

spline = curve_data.splines.new('POLY')
spline.points.add(1)
spline.points[0].co = (0, 0, 0, 1)
spline.points[1].co = (100, 0, 0, 1)

curve_obj = bpy.data.objects.new("Alignment_001", curve_data)

# STEP 8: Link to IFC
NativeIfcManager.link_object(curve_obj, alignment)

# STEP 9: Add to scene
bpy.context.collection.objects.link(curve_obj)

# STEP 10: Save
NativeIfcManager.save_file("/tmp/my_first_alignment.ifc")

print("âœ… Created native IFC alignment!")
```

**You just created a real IFC alignment!**

---

## 🎨 Pattern Library

### Pattern 1: Create LINE Segment

```python
def create_line_segment(ifc, start_x, start_y, direction, length):
    """Create a LINE segment in IFC"""
    
    segment = ifc.create_entity(
        "IfcAlignmentSegment",
        GlobalId=ifcopenshell.guid.new(),
        DesignParameters=ifc.create_entity(
            "IfcAlignmentHorizontalSegment",
            StartPoint=ifc.create_entity(
                "IfcCartesianPoint",
                Coordinates=(start_x, start_y)
            ),
            StartDirection=direction,
            SegmentLength=length,
            PredefinedType="LINE"
        )
    )
    
    return segment
```

### Pattern 2: Create CIRCULARARC Segment

```python
def create_arc_segment(ifc, start_x, start_y, direction, radius, length):
    """Create a CIRCULARARC segment in IFC"""
    
    segment = ifc.create_entity(
        "IfcAlignmentSegment",
        GlobalId=ifcopenshell.guid.new(),
        DesignParameters=ifc.create_entity(
            "IfcAlignmentHorizontalSegment",
            StartPoint=ifc.create_entity(
                "IfcCartesianPoint",
                Coordinates=(start_x, start_y)
            ),
            StartDirection=direction,
            StartRadiusOfCurvature=radius,
            EndRadiusOfCurvature=radius,
            SegmentLength=length,
            PredefinedType="CIRCULARARC"
        )
    )
    
    return segment
```

### Pattern 3: Read Segment Data

```python
def read_segment_info(blender_obj):
    """Read segment information from linked IFC entity"""
    
    # Get IFC entity
    entity = NativeIfcManager.get_entity(blender_obj)
    
    if not entity or not entity.is_a("IfcAlignmentSegment"):
        return None
    
    # Extract parameters
    params = entity.DesignParameters
    
    info = {
        'name': entity.Name,
        'global_id': entity.GlobalId,
        'type': params.PredefinedType,
        'start_point': params.StartPoint.Coordinates,
        'start_direction': params.StartDirection,
        'length': params.SegmentLength
    }
    
    # Add radius for curves
    if params.PredefinedType == "CIRCULARARC":
        info['radius'] = params.StartRadiusOfCurvature
    
    return info
```

### Pattern 4: Update Segment Data

```python
def update_segment_length(blender_obj, new_length):
    """Update segment length in IFC"""
    
    # Get IFC entity
    entity = NativeIfcManager.get_entity(blender_obj)
    
    if not entity:
        return False
    
    # Update IFC
    entity.DesignParameters.SegmentLength = new_length
    
    # Now update Blender visualization
    update_curve_geometry(blender_obj, entity)
    
    return True
```

---

## 🔄 Common Workflows

### Workflow 1: Create New Project

```python
# 1. Create new IFC file
ifc = NativeIfcManager.new_file()

# 2. Create alignment
alignment = create_alignment(ifc, "Project 2025")

# 3. Add segments
seg1 = create_line_segment(ifc, 0, 0, 0, 100)
seg2 = create_arc_segment(ifc, 100, 0, 0, 50, 78.54)
seg3 = create_line_segment(ifc, 150, 50, 1.57, 100)

# 4. Visualize in Blender
visualize_alignment(alignment, [seg1, seg2, seg3])

# 5. Save
NativeIfcManager.save_file("/path/to/project.ifc")
```

### Workflow 2: Load Existing Project

```python
# 1. Load IFC file
ifc = NativeIfcManager.open_file("/path/to/project.ifc")

# 2. Find alignments
alignments = ifc.by_type("IfcAlignment")

# 3. For each alignment, create visualization
for alignment in alignments:
    visualize_alignment_from_ifc(alignment)

# 4. Now user can interact in Blender
```

### Workflow 3: Modify and Save

```python
# 1. User selects object in Blender
obj = bpy.context.active_object

# 2. Get IFC entity
entity = NativeIfcManager.get_entity(obj)

# 3. Modify IFC data
entity.DesignParameters.SegmentLength = 150.0

# 4. Update visualization
update_curve_geometry(obj, entity)

# 5. Save changes
NativeIfcManager.save_file()
```

---

## 🐛 Debugging Tips

### Check if Object is Linked

```python
obj = bpy.context.active_object

if "ifc_definition_id" in obj:
    print(f"âœ… Linked to IFC entity ID: {obj['ifc_definition_id']}")
    entity = NativeIfcManager.get_entity(obj)
    print(f"   Entity type: {entity.is_a()}")
else:
    print("❌ Not linked to IFC")
```

### Validate IFC Structure

```python
ifc = NativeIfcManager.get_file()

# Count entities
projects = ifc.by_type("IfcProject")
sites = ifc.by_type("IfcSite")
alignments = ifc.by_type("IfcAlignment")

print(f"Projects: {len(projects)}")
print(f"Sites: {len(sites)}")
print(f"Alignments: {len(alignments)}")

# Check relationships
for alignment in alignments:
    print(f"\nAlignment: {alignment.Name}")
    # Find nested entities
    for rel in ifc.by_type("IfcRelNests"):
        if rel.RelatingObject == alignment:
            print(f"  Contains: {len(rel.RelatedObjects)} items")
```

### Print Entity Details

```python
def print_entity_tree(entity, indent=0):
    """Recursively print entity structure"""
    
    prefix = "  " * indent
    print(f"{prefix}{entity.is_a()}: {entity.Name or entity.GlobalId}")
    
    # Print key attributes
    if hasattr(entity, 'DesignParameters'):
        params = entity.DesignParameters
        print(f"{prefix}  Type: {params.PredefinedType}")
        print(f"{prefix}  Length: {params.SegmentLength}")
    
    # Find nested entities
    for rel in entity.wrapped_data.file.by_type("IfcRelNests"):
        if rel.RelatingObject == entity:
            for obj in rel.RelatedObjects:
                print_entity_tree(obj, indent + 1)
```

---

## âš ï¸ Common Mistakes

### Mistake 1: Creating Blender Object First

```python
# WRONG ❌
curve = bpy.data.objects.new("Segment", curve_data)
segment = ifc.create_entity("IfcAlignmentSegment", ...)

# CORRECT âœ…
segment = ifc.create_entity("IfcAlignmentSegment", ...)
curve = bpy.data.objects.new("Segment", curve_data)
NativeIfcManager.link_object(curve, segment)
```

### Mistake 2: Storing Data in Blender

```python
# WRONG ❌
obj["length"] = 100.0
obj["radius"] = 50.0

# CORRECT âœ…
entity = NativeIfcManager.get_entity(obj)
entity.DesignParameters.SegmentLength = 100.0
entity.DesignParameters.StartRadiusOfCurvature = 50.0
```

### Mistake 3: Forgetting to Save IFC

```python
# WRONG ❌
bpy.ops.wm.save_mainfile(filepath="project.blend")
# This only saves Blender file, not IFC data!

# CORRECT âœ…
NativeIfcManager.save_file("project.ifc")
# Optional: Also save .blend
bpy.ops.wm.save_mainfile(filepath="project.blend")
```

### Mistake 4: Not Linking Objects

```python
# WRONG ❌
segment = ifc.create_entity(...)
curve = bpy.data.objects.new(...)
# No link! Can't retrieve IFC data later

# CORRECT âœ…
segment = ifc.create_entity(...)
curve = bpy.data.objects.new(...)
NativeIfcManager.link_object(curve, segment)  # Link them!
```

---

## 🎯 Best Practices

### 1. Always Check if IFC File Exists

```python
ifc = NativeIfcManager.get_file()
if not ifc:
    ifc = NativeIfcManager.new_file()
```

### 2. Use Meaningful Names

```python
# GOOD âœ…
alignment = ifc.create_entity("IfcAlignment", Name="Main Street Alignment")
segment = ifc.create_entity("IfcAlignmentSegment", Name="Entry_Tangent")

# AVOID ❌
alignment = ifc.create_entity("IfcAlignment", Name="Alignment1")
segment = ifc.create_entity("IfcAlignmentSegment")  # No name
```

### 3. Handle Errors Gracefully

```python
try:
    entity = NativeIfcManager.get_entity(obj)
    if entity:
        length = entity.DesignParameters.SegmentLength
    else:
        print("Object not linked to IFC")
except Exception as e:
    print(f"Error: {e}")
```

### 4. Clean Up on Clear

```python
def clear_project():
    """Clean up everything"""
    
    # Clear IFC
    NativeIfcManager.clear()
    
    # Clear Blender objects
    for obj in bpy.data.objects:
        if "ifc_definition_id" in obj:
            bpy.data.objects.remove(obj)
    
    print("âœ… Project cleared")
```

---

## 📚 Resources

### Essential Reading
- IFC 4.3 Spec: https://ifc43-docs.standards.buildingsmart.org/
- IfcOpenShell Docs: https://docs.ifcopenshell.org/
- Architecture Document: `BlenderCivil_Native_IFC_Architecture.md`

### Example Code
- `native_ifc_manager.py` - Core system
- `blender_integration.py` - Full example
- `roundtrip_test.py` - Testing example

### Community
- OSArch Forum: https://community.osarch.org/
- GitHub Issues: [Your repo]/issues

---

## ðŸš€ Next Steps

### You're Ready When You Can:

- [ ] Create a new IFC file
- [ ] Create an IfcAlignment entity
- [ ] Add segments to alignment
- [ ] Link Blender objects to IFC entities
- [ ] Save and load IFC files
- [ ] Retrieve IFC data from Blender objects

### Want to Contribute?

**Start Here:**
1. Fix a bug from GitHub issues
2. Add a new segment type (CLOTHOID)
3. Improve visualization
4. Write tests
5. Create tutorials

---

## 🎉 Congratulations!

You now understand BlenderCivil's native IFC architecture!

**Remember:**
- IFC is the source of truth
- Blender is the visualization
- Create IFC first, Blender second
- Link objects with `ifc_definition_id`
- Save means write IFC file

**Now go build something amazing!** ðŸš€

---

**Document Version:** 1.0  
**Last Updated:** October 28, 2025  
**Questions?** Open an issue on GitHub or ask on OSArch forums!
