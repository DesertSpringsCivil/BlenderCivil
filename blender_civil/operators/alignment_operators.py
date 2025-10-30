"""
Alignment Operations
Create and update alignment operators
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class BC_OT_create_native_alignment(bpy.types.Operator):
    """Create new native IFC alignment"""
    bl_idname = "bc.create_native_alignment"
    bl_label = "Create Native Alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    name: StringProperty(
        name="Name",
        default="Alignment",
        description="Alignment name"
    )
    
    def execute(self, context):
        ifc = NativeIfcManager.get_file()
        alignment = NativeIfcAlignment(ifc, self.name)
        
        # Create visualizer
        visualizer = AlignmentVisualizer(alignment)
        
        self.report({'INFO'}, f"Created alignment: {self.name}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



class BC_OT_update_pi_from_location(bpy.types.Operator):
    """Update PI in IFC from Blender location"""
    bl_idname = "bc.update_pi_from_location"
    bl_label = "Update from Location"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or "ifc_pi_id" not in obj:
            self.report({'ERROR'}, "Select a PI marker")
            return {'CANCELLED'}
        
        # Update IFC coordinates
        if "ifc_point_id" in obj:
            ifc = NativeIfcManager.get_file()
            point = ifc.by_id(obj["ifc_point_id"])
            point.Coordinates = [float(obj.location.x), float(obj.location.y)]
            
            # Regenerate alignment
            # Note: Full implementation needs to find parent alignment and regenerate
            self.report({'INFO'}, f"Updated PI {obj.name}")
            return {'FINISHED'}
        
        return {'CANCELLED'}




# Registration
classes = (
    BC_OT_create_native_alignment,
    BC_OT_update_pi_from_location,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
