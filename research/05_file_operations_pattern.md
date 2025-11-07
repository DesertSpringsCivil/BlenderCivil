# File Operations Pattern - Save Means IFC

## 🎯 Core Discovery
"Save" in Bonsai primarily means writing the IFC file. The .blend file is secondary and just stores viewport state and the IFC file reference.

## 📍 Source Location
- **File:** `src/bonsai/bonsai/bim/module/project/operator.py`
- **Operations:** SaveProject, LoadProject

## 🔍 How Bonsai Handles Files

### Save Operation
```python
class SaveProject(Operator):
    """Save = Write IFC file"""
    
    def execute(self, context):
        # Primary action: Save IFC
        ifc = IfcStore.get_file()
        ifc.write(IfcStore.path)
        
        # Secondary: Save .blend (just viewport state)
        bpy.ops.wm.save_mainfile()
        
        return {'FINISHED'}
```

### Load Operation
```python
class LoadProject(Operator):
    """Load = Open IFC file"""
    
    def execute(self, context):
        # Clear existing
        IfcStore.file = None
        
        # Load IFC file
        IfcStore.file = ifcopenshell.open(self.filepath)
        IfcStore.path = self.filepath
        
        # Generate Blender objects from IFC
        for element in IfcStore.file.by_type("IfcElement"):
            create_object_from_ifc(element)
        
        return {'FINISHED'}
```

## 💡 Key Insights

### File Relationships
```
project.ifc     - THE DATA (complete project)
project.blend   - Just viewport (camera, UI state)
                - Stores path to .ifc
                - Can be regenerated from IFC
```

### What's Saved Where

**IFC File Contains:**
- All geometry
- All properties
- All relationships
- Complete project data

**Blend File Contains:**
- Camera position
- Viewport settings
- UI state
- Path to IFC file
- Cached visualization

## 🏗️ BlenderCivil Implementation
```python
class BC_OT_save_native_project(Operator):
    """Save BlenderCivil native IFC project"""
    bl_idname = "bc.save_native_project"
    bl_label = "Save Project"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        # Ensure .ifc extension
        if not self.filepath.endswith('.ifc'):
            self.filepath += '.ifc'
        
        # Save IFC (primary)
        ifc = NativeIfcManager.get_file()
        ifc.write(self.filepath)
        NativeIfcManager.filepath = self.filepath
        
        # Store IFC path in scene
        context.scene["ifc_filepath"] = self.filepath
        
        # Save .blend (secondary)
        blend_path = self.filepath.replace('.ifc', '.blend')
        bpy.ops.wm.save_as_mainfile(filepath=blend_path)
        
        self.report({'INFO'}, f"Saved: {self.filepath}")
        return {'FINISHED'}

class BC_OT_load_native_project(Operator):
    """Load BlenderCivil native IFC project"""
    bl_idname = "bc.load_native_project"
    bl_label = "Load Project"
    
    filepath: StringProperty(subtype='FILE_PATH')
    
    def execute(self, context):
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        # Load IFC file
        NativeIfcManager.open_file(self.filepath)
        ifc = NativeIfcManager.get_file()
        
        # Recreate Blender objects from IFC
        alignments = ifc.by_type("IfcAlignment")
        for alignment in alignments:
            create_alignment_visualization(alignment)
        
        # Store path
        context.scene["ifc_filepath"] = self.filepath
        
        self.report({'INFO'}, f"Loaded: {self.filepath}")
        return {'FINISHED'}
```

### Auto-save Strategy
```python
@persistent
def auto_save_ifc(scene):
    """Auto-save IFC file periodically"""
    if not NativeIfcManager.filepath:
        return
    
    # Save IFC every N changes
    if should_autosave():
        NativeIfcManager.save_file()
        print("Auto-saved IFC")

bpy.app.handlers.depsgraph_update_post.append(auto_save_ifc)
```

## 📁 Project Structure

### Recommended File Organization
```
MyRoadProject/
├── project.ifc          # THE PROJECT (all data)
├── project.blend        # Viewport state (optional)
├── backup/
│   ├── project_20250301.ifc
│   └── project_20250302.ifc
└── exports/
    ├── alignment.xml    # LandXML export
    └── model.dwg       # DWG export
```

## 🔄 Version Control

### What to Track in Git
```gitignore
# Track IFC (text-based, diffable!)
*.ifc

# Optional: track .blend
*.blend

# Ignore temp files
*.blend1
*.blend2
```

### Why IFC is Git-Friendly
```python
# IFC files are TEXT!
# You can diff them:
"""
- #123= IFCALIGNMENT('2xT$',$,'Alignment 1',$,$,$,$);
+ #123= IFCALIGNMENT('2xT$',$,'Main Street Alignment',$,$,$,$);
"""
```

## ⚠️ Critical Rules

1. **ALWAYS** save IFC file as primary
2. **OPTIONALLY** save .blend for convenience
3. **NEVER** rely on .blend for data
4. IFC file = complete project

## 📝 Implementation Checklist

- [ ] Create save operator (IFC primary)
- [ ] Create load operator (IFC → Blender)
- [ ] Add auto-save for IFC
- [ ] Store IFC path in scene
- [ ] Handle file extensions properly
- [ ] Create backup strategy