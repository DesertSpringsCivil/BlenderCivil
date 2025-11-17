# ==============================================================================
# BlenderCivil - Civil Engineering Tools for Blender
# Copyright (c) 2024-2025 Michael Yoder / Desert Springs Civil Engineering PLLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Primary Author: Michael Yoder
# Company: Desert Springs Civil Engineering PLLC
# ==============================================================================

"""
File Operations
IFC file creation and management operators
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty

# Import from parent operators module
from . import NativeIfcManager


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
