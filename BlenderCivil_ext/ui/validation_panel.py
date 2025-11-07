"""
Validation Panel
UI panel for validation and debugging tools
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class VIEW3D_PT_native_ifc_validation(bpy.types.Panel):
    """Native IFC Validation Tools"""
    bl_label = "Validation"
    bl_idname = "VIEW3D_PT_native_ifc_validation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderCivil"
    
    def draw(self, context):
        layout = self.layout
        
        # Validation Tools
        box = layout.box()
        box.label(text="Validation", icon='CHECKMARK')
        
        col = box.column(align=True)
        col.operator("bc.validate_ifc_alignment", text="Validate IFC")
        col.operator("bc.list_all_ifc_objects", text="List All Objects")
        
        # Segment Info
        if context.active_object and "ifc_definition_id" in context.active_object:
            box = layout.box()
            box.label(text="Selected Segment", icon='INFO')
            box.operator("bc.show_segment_info", text="Show Details")




# Registration
classes = (
    VIEW3D_PT_native_ifc_validation,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
