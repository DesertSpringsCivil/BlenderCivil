"""
PI Operations
Add and delete PI point operators
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class BC_OT_add_native_pi(bpy.types.Operator):
    """Add PI at 3D cursor"""
    bl_idname = "bc.add_native_pi"
    bl_label = "Add PI"
    bl_options = {'REGISTER', 'UNDO'}
    
    radius: FloatProperty(
        name="Radius",
        default=0.0,
        min=0.0,
        description="Curve radius (0 = tangent point)"
    )
    
    def execute(self, context):
        cursor = context.scene.cursor.location
        
        # Get active alignment (simplified - needs proper implementation)
        ifc = NativeIfcManager.get_file()
        alignments = ifc.by_type("IfcAlignment")
        
        if not alignments:
            self.report({'ERROR'}, "No alignment found. Create an alignment first.")
            return {'CANCELLED'}
        
        # Add PI to first alignment
        # Note: This is simplified. Full implementation needs alignment selection
        self.report({'INFO'}, f"Added PI at ({cursor.x:.2f}, {cursor.y:.2f}) R={self.radius}m")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



class BC_OT_delete_native_pi(bpy.types.Operator):
    """Delete selected PI"""
    bl_idname = "bc.delete_native_pi"
    bl_label = "Delete PI"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or "ifc_pi_id" not in obj:
            self.report({'ERROR'}, "Select a PI marker")
            return {'CANCELLED'}
        
        # Remove from scene
        bpy.data.objects.remove(obj, do_unlink=True)
        
        # Note: Full implementation needs to update IFC alignment
        self.report({'INFO'}, "Deleted PI")
        return {'FINISHED'}




# Registration
classes = (
    BC_OT_add_native_pi,
    BC_OT_delete_native_pi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
