"""
BlenderCivil - Utility Operators

General utility operators for the addon
"""

import bpy
from bpy.types import Operator

class CIVIL_OT_OpenPreferences(Operator):
    """Open BlenderCivil preferences"""
    bl_idname = "civil.open_preferences"
    bl_label = "Open Preferences"
    bl_description = "Open BlenderCivil addon preferences"
    
    def execute(self, context):
        bpy.ops.preferences.addon_show(module=__package__.split('.')[0])
        return {'FINISHED'}

classes = (
    CIVIL_OT_OpenPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
