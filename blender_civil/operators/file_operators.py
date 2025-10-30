"""
File Operations
IFC file creation and management operators
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class BC_OT_new_ifc_file(bpy.types.Operator):
    """Create new IFC file"""
    bl_idname = "bc.new_ifc_file"
    bl_label = "New IFC File"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        ifc = NativeIfcManager.new_file()
        self.report({'INFO'}, f"Created new IFC file: {ifc.schema}")
        return {'FINISHED'}




# Registration
classes = (
    BC_OT_new_ifc_file,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
