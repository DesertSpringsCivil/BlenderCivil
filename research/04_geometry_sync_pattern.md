# Geometry Synchronization Pattern

## 🎯 Core Discovery
Geometry flows ONE WAY: IFC → Blender. When IFC changes, update Blender visualization. Never the reverse.

## 📍 Source Location
- **File:** `src/bonsai/bonsai/tool/geometry.py`
- **File:** `src/bonsai/bonsai/bim/module/geometry/operator.py`

## 🔍 How Bonsai Syncs Geometry

### The Update Cycle
```python
# 1. User action (e.g., move object)
def on_object_moved(obj):
    # 2. Get IFC entity
    element = get_ifc_entity(obj)
    
    # 3. Update IFC with new position
    element.ObjectPlacement = create_ifc_placement(
        obj.location,
        obj.rotation_euler)
    
    # 4. IFC is now the truth
    # 5. Other objects reading this element will get new position
```

### Mesh Generation from IFC
```python
def regenerate_mesh_from_ifc(obj):
    """Regenerate Blender mesh from IFC geometry"""
    element = get_ifc_entity(obj)
    if not element:
        return
    
    # Get IFC shape
    shape = ifcopenshell.geom.create_shape(settings, element)
    
    # Convert to Blender mesh
    mesh = shape_to_mesh(shape)
    
    # Replace object's mesh
    old_mesh = obj.data
    obj.data = mesh
    bpy.data.meshes.remove(old_mesh)
```

## 💡 Key Insights

### Traditional CAD Sync
```
Blender Geometry ←→ Internal Format ←→ IFC Export
(Bidirectional, complex, lossy)
```

### Native IFC Sync
```
IFC Geometry (truth) → Blender Display
(Unidirectional, simple, lossless)
```

## 🏗️ BlenderCivil Implementation

### For Alignment Updates
```python
class AlignmentGeometrySync:
    """Sync IFC alignment to Blender curves"""
    
    @staticmethod
    def update_from_ifc(alignment_obj):
        """Regenerate Blender curve from IFC segments"""
        ifc = NativeIfcManager.get_file()
        alignment = get_ifc_entity(alignment_obj)
        
        if not alignment:
            return
        
        # Get horizontal alignment
        horizontal = get_horizontal_alignment(alignment)
        segments = get_alignment_segments(horizontal)
        
        # Create new curve data
        curve_data = bpy.data.curves.new(name="Alignment", type='CURVE')
        curve_data.dimensions = '3D'
        
        for segment in segments:
            add_segment_to_curve(curve_data, segment)
        
        # Update object
        alignment_obj.data = curve_data
    
    @staticmethod
    def on_pi_moved(pi_obj):
        """When PI moves, update IFC then sync"""
        # 1. Get IFC point
        ifc_point = get_ifc_entity(pi_obj)
        
        # 2. Update IFC coordinates
        ifc_point.Coordinates = (
            pi_obj.location.x,
            pi_obj.location.y
        )
        
        # 3. Regenerate alignment segments in IFC
        alignment = get_parent_alignment(pi_obj)
        regenerate_ifc_segments(alignment)
        
        # 4. Update Blender visualization
        update_alignment_curve(alignment)
```

### Depsgraph Handler
```python
@persistent
def on_depsgraph_update(scene):
    """Handle object updates"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            
            # Check if it's an IFC object
            if "ifc_definition_id" not in obj:
                continue
            
            # Check if transform changed
            if update.is_updated_transform:
                sync_transform_to_ifc(obj)
            
            # Check if geometry changed
            if update.is_updated_geometry:
                sync_geometry_to_ifc(obj)

# Register handler
bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)
```

## 🔄 The Sync Rules

### When to Sync IFC → Blender
1. After IFC file loaded
2. After IFC entity created
3. After IFC property changed
4. After IFC geometry updated

### When to Update IFC
1. User moves object
2. User edits properties
3. User modifies geometry
4. User adds/removes elements

### What NOT to Do
```python
# ❌ NEVER derive IFC from Blender
ifc_geom = mesh_to_ifc(obj.data)  # WRONG!

# ✅ ALWAYS update IFC first, then sync
update_ifc_geometry(element, new_params)
sync_to_blender(element, obj)  # RIGHT!
```

## ⚠️ Critical Rules

1. IFC is ALWAYS the source of truth
2. Blender is ALWAYS just visualization
3. Updates go: User → IFC → Blender
4. Never go: Blender → IFC

## 📝 Implementation Checklist

- [ ] Create sync functions for alignments
- [ ] Add depsgraph handlers
- [ ] Update IFC before Blender
- [ ] Regenerate curves from IFC segments
- [ ] Handle PI movement updates