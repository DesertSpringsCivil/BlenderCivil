# Object-to-IFC Linking Pattern

## 🎯 Core Discovery
Blender objects are "dumb shells" that only know their IFC entity's ID. All data lives in IFC.

## 📍 Source Locations
- **File:** `src/bonsai/bonsai/bim/module/root/operator.py`
- **Property:** `BIMObjectProperties.ifc_definition_id`

## 🔍 How Bonsai Links Objects

### Creating a Linked Object
```python
# Step 1: Create IFC entity FIRST
ifc = IfcStore.get_file()
ifc_wall = ifcopenshell.api.run("root.create_entity", 
    ifc, 
    ifc_class="IfcWall",
    name="Wall.001")

# Step 2: Create Blender object (just visualization)
mesh = bpy.data.meshes.new(name="Wall")
obj = bpy.data.objects.new("Wall.001", mesh)

# Step 3: Link them with ONLY the ID
obj.BIMObjectProperties.ifc_definition_id = ifc_wall.id()

# That's it! The link is just an integer!
```

### Retrieving the IFC Entity
```python
# Given a Blender object, get its IFC data
def get_ifc_entity(blender_obj):
    ifc = IfcStore.get_file()
    ifc_id = blender_obj.BIMObjectProperties.ifc_definition_id
    if ifc_id:
        return ifc.by_id(ifc_id)
    return None
```

## 💡 Key Insights

### What's Stored in Blender
```python
# ONLY these IFC references:
obj.BIMObjectProperties.ifc_definition_id = 12345  # The IFC entity ID
obj.BIMObjectProperties.ifc_guid = "2xGh3..."      # Optional: Global ID
```

### What's NOT Stored in Blender
```python
# NONE of this:
obj["wall_height"] = 3.0        # ❌ Data is in IFC
obj["material"] = "Concrete"    # ❌ Data is in IFC  
obj["fire_rating"] = "2HR"      # ❌ Data is in IFC
```

## 🏗️ BlenderCivil Implementation
```python
# For alignments and PIs
def link_object_to_ifc(blender_obj, ifc_entity):
    """Link Blender object to IFC entity"""
    blender_obj["ifc_definition_id"] = ifc_entity.id()
    blender_obj["ifc_global_id"] = ifc_entity.GlobalId
    # That's ALL we store in Blender!

def get_ifc_entity(blender_obj):
    """Get IFC entity from Blender object"""
    if "ifc_definition_id" not in blender_obj:
        return None
    
    ifc = NativeIfcManager.get_file()
    return ifc.by_id(blender_obj["ifc_definition_id"])

# Example: Creating a PI
def create_native_pi(x, y, radius):
    ifc = NativeIfcManager.get_file()
    
    # 1. Create IFC entity FIRST
    ifc_point = ifc.create_entity("IfcCartesianPoint",
        Coordinates=(x, y))
    
    # 2. Create Blender visualization
    empty = bpy.data.objects.new("PI_001", None)
    empty.empty_display_type = 'SPHERE'
    empty.location = (x, y, 0)
    
    # 3. Link them
    link_object_to_ifc(empty, ifc_point)
    
    # 4. Store radius in IFC (not Blender!)
    # Would create property set in IFC...
    
    return empty
```

## 🔄 The Data Flow
```
User moves PI in viewport
    ↓
Get IFC entity via ifc_definition_id
    ↓
Update IFC entity coordinates
    ↓
IFC is now updated (source of truth)
    ↓
Optionally update other dependent objects
```

## ⚠️ Critical Rules

1. **ALWAYS** create IFC entity before Blender object
2. **ONLY** store IFC ID in Blender
3. **NEVER** store design data in Blender properties
4. When user edits, update IFC first

## 📝 Implementation Checklist

- [ ] Add ifc_definition_id to all created objects
- [ ] Create helper functions for linking
- [ ] Remove all data storage from Blender objects
- [ ] Update all getters to read from IFC
- [ ] Update all setters to write to IFC