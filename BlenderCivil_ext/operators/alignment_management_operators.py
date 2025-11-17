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
Alignment Management Operators
Helper operators for managing alignments, active alignment, and alignment list
"""

import bpy
from bpy.props import StringProperty, IntProperty


class BC_OT_refresh_alignment_list(bpy.types.Operator):
    """Refresh the alignment list from IFC file"""
    bl_idname = "bc.refresh_alignment_list"
    bl_label = "Refresh Alignment List"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        from ..ui.alignment_properties import refresh_alignment_list
        
        refresh_alignment_list(context)
        
        props = context.scene.bc_alignment
        self.report({'INFO'}, props.status_message)
        
        return {'FINISHED'}


class BC_OT_set_active_alignment(bpy.types.Operator):
    """Set the active alignment by index"""
    bl_idname = "bc.set_active_alignment"
    bl_label = "Set Active Alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    alignment_index: IntProperty(
        name="Alignment Index",
        description="Index of alignment to set as active",
        default=0
    )
    
    def execute(self, context):
        from . import NativeIfcManager
        from ..ui.alignment_properties import set_active_alignment, refresh_alignment_list
        
        # Refresh list first
        refresh_alignment_list(context)
        
        props = context.scene.bc_alignment
        
        if self.alignment_index < 0 or self.alignment_index >= len(props.alignments):
            self.report({'ERROR'}, f"Invalid alignment index: {self.alignment_index}")
            return {'CANCELLED'}
        
        # Get alignment item
        item = props.alignments[self.alignment_index]
        
        # Get IFC entity
        ifc = NativeIfcManager.get_file()
        if not ifc:
            self.report({'ERROR'}, "No IFC file")
            return {'CANCELLED'}
        
        alignment = ifc.by_id(item.ifc_entity_id)
        if not alignment:
            self.report({'ERROR'}, "Alignment not found in IFC")
            return {'CANCELLED'}
        
        # Set as active
        set_active_alignment(context, alignment)
        
        self.report({'INFO'}, f"Active alignment: {item.name}")
        return {'FINISHED'}


class BC_OT_select_active_alignment_collection(bpy.types.Operator):
    """Select the active alignment's collection"""
    bl_idname = "bc.select_active_alignment_collection"
    bl_label = "Select Active Alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..ui.alignment_properties import get_active_alignment_item
        
        item = get_active_alignment_item(context)
        if not item:
            self.report({'ERROR'}, "No active alignment")
            return {'CANCELLED'}
        
        if not item.collection_name:
            self.report({'ERROR'}, "Alignment collection not found")
            return {'CANCELLED'}
        
        # Find and select collection
        collection = bpy.data.collections.get(item.collection_name)
        if not collection:
            self.report({'ERROR'}, f"Collection '{item.collection_name}' not found")
            return {'CANCELLED'}
        
        # Select all objects in collection
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        
        self.report({'INFO'}, f"Selected {len(collection.objects)} objects from {item.name}")
        return {'FINISHED'}


# Registration
classes = (
    BC_OT_refresh_alignment_list,
    BC_OT_set_active_alignment,
    BC_OT_select_active_alignment_collection,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
