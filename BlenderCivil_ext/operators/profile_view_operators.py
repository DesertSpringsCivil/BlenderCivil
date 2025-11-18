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
BlenderCivil - Profile View Operators
======================================

Blender operators for profile view interaction.
Handles user actions: toggle, load data, edit PVIs, etc.

This follows BlenderCivil's architecture pattern:
- operators/ = User actions and workflows
- Imports from core/ for business logic

Author: BlenderCivil Development Team
Date: November 2025
License: GPL v3
"""

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, IntProperty, StringProperty

# Import core functionality
import sys
import os

# Note: Adjust import path based on actual installation
# from blendercivil.core.profile_view_overlay import (
#     get_profile_overlay,
#     load_from_sprint3_vertical,
#     sync_to_sprint3_vertical
# )


# ============================================================================
# OVERLAY CONTROL OPERATORS
# ============================================================================

class BC_OT_ProfileView_Toggle(Operator):
    """Toggle profile view overlay on/off"""
    bl_idname = "blendercivil.profile_view_toggle"
    bl_label = "Toggle Profile View"
    bl_description = "Show/hide the profile view overlay at bottom of viewport"
    bl_options = {'REGISTER'}

    def execute(self, context):
        # Import here to avoid circular dependencies
        from ..core.profile_view_overlay import get_profile_overlay

        overlay = get_profile_overlay()
        was_enabled = overlay.enabled
        overlay.toggle(context)

        # Start or stop the modal event handler
        if overlay.enabled and not was_enabled:
            # Start the modal event handler
            bpy.ops.blendercivil.profile_view_modal_handler('INVOKE_DEFAULT')
            self.report({'INFO'}, "Profile view enabled")
        else:
            self.report({'INFO'}, "Profile view disabled")
            # Modal handler will stop itself when overlay is disabled

        return {'FINISHED'}


class BC_OT_ProfileView_Enable(Operator):
    """Enable profile view overlay"""
    bl_idname = "blendercivil.profile_view_enable"
    bl_label = "Enable Profile View"
    bl_description = "Show the profile view overlay"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay

        overlay = get_profile_overlay()
        was_enabled = overlay.enabled
        overlay.enable(context)

        # Start the modal event handler if not already running
        if not was_enabled:
            bpy.ops.blendercivil.profile_view_modal_handler('INVOKE_DEFAULT')

        self.report({'INFO'}, "Profile view enabled")
        return {'FINISHED'}


class BC_OT_ProfileView_Disable(Operator):
    """Disable profile view overlay"""
    bl_idname = "blendercivil.profile_view_disable"
    bl_label = "Disable Profile View"
    bl_description = "Hide the profile view overlay"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        overlay.disable(context)
        self.report({'INFO'}, "Profile view disabled")
        return {'FINISHED'}


# ============================================================================
# DATA LOADING OPERATORS
# ============================================================================

class BC_OT_ProfileView_LoadFromSprint3(Operator):
    """Load vertical alignment from Sprint 3 data"""
    bl_idname = "blendercivil.profile_view_load_from_sprint3"
    bl_label = "Load from Sprint 3"
    bl_description = "Load vertical alignment data from Sprint 3 bc_vertical properties"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import (
            get_profile_overlay,
            load_from_sprint3_vertical
        )
        
        success = load_from_sprint3_vertical(context)
        
        if not success:
            self.report({'ERROR'}, "Sprint 3 vertical alignment not found")
            return {'CANCELLED'}
        
        overlay = get_profile_overlay()
        
        # Enable overlay if not already enabled
        if not overlay.enabled:
            overlay.enable(context)
        
        overlay.refresh(context)
        
        self.report({'INFO'}, 
                   f"Loaded {len(overlay.data.pvis)} PVIs from Sprint 3")
        return {'FINISHED'}


class BC_OT_ProfileView_SyncToSprint3(Operator):
    """Sync profile view changes back to Sprint 3"""
    bl_idname = "blendercivil.profile_view_sync_to_sprint3"
    bl_label = "Sync to Sprint 3"
    bl_description = "Write profile view changes back to Sprint 3 vertical alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import (
            get_profile_overlay,
            sync_to_sprint3_vertical
        )
        
        success = sync_to_sprint3_vertical(context)
        
        if not success:
            self.report({'ERROR'}, "Failed to sync to Sprint 3")
            return {'CANCELLED'}
        
        overlay = get_profile_overlay()
        overlay.refresh(context)
        
        self.report({'INFO'}, "Synced changes to Sprint 3")
        return {'FINISHED'}


class BC_OT_ProfileView_LoadTerrain(Operator):
    """Load terrain profile from selected mesh"""
    bl_idname = "blendercivil.profile_view_load_terrain"
    bl_label = "Load Terrain"
    bl_description = "Sample terrain elevations from selected mesh along alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        mesh_obj = context.active_object
        
        if not mesh_obj or mesh_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object (DTM/terrain)")
            return {'CANCELLED'}
        
        overlay = get_profile_overlay()
        
        # TODO: Implement terrain raycasting
        # For now, create placeholder data
        import numpy as np
        
        overlay.data.clear_terrain()
        
        stations = np.linspace(
            overlay.data.station_min,
            overlay.data.station_max,
            100
        )
        
        for station in stations:
            # Placeholder: sine wave terrain
            elevation = 50.0 + 20.0 * np.sin(station / 100.0)
            overlay.data.add_terrain_point(station, elevation)
        
        overlay.refresh(context)
        
        self.report({'INFO'}, 
                   f"Loaded {len(overlay.data.terrain_points)} terrain points")
        return {'FINISHED'}


# ============================================================================
# PVI EDITING OPERATORS
# ============================================================================

class BC_OT_ProfileView_AddPVI(Operator):
    """Add a new PVI at specified location"""
    bl_idname = "blendercivil.profile_view_add_pvi"
    bl_label = "Add PVI"
    bl_description = "Add a new Point of Vertical Intersection"
    bl_options = {'REGISTER', 'UNDO'}
    
    station: FloatProperty(
        name="Station",
        description="Station coordinate (m)",
        default=0.0,
        unit='LENGTH'
    )
    
    elevation: FloatProperty(
        name="Elevation",
        description="Elevation coordinate (m)",
        default=100.0,
        unit='LENGTH'
    )
    
    curve_length: FloatProperty(
        name="Curve Length",
        description="Vertical curve length (m)",
        default=100.0,
        min=0.0,
        unit='LENGTH'
    )
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        
        metadata = {'curve_length': self.curve_length}
        overlay.data.add_pvi(self.station, self.elevation, metadata)
        overlay.data.sort_pvis_by_station()
        overlay.refresh(context)
        
        self.report({'INFO'}, 
                   f"Added PVI at station {self.station:.2f}m, "
                   f"elevation {self.elevation:.2f}m")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class BC_OT_ProfileView_DeleteSelectedPVI(Operator):
    """Delete the currently selected PVI"""
    bl_idname = "blendercivil.profile_view_delete_selected_pvi"
    bl_label = "Delete PVI"
    bl_description = "Delete the currently selected PVI"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        
        if overlay.data.selected_pvi_index is None:
            self.report({'WARNING'}, "No PVI selected")
            return {'CANCELLED'}
        
        success = overlay.data.remove_pvi(overlay.data.selected_pvi_index)
        
        if success:
            overlay.refresh(context)
            self.report({'INFO'}, "Deleted PVI")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to delete PVI")
            return {'CANCELLED'}


class BC_OT_ProfileView_SelectPVI(Operator):
    """Select a PVI by index"""
    bl_idname = "blendercivil.profile_view_select_pvi"
    bl_label = "Select PVI"
    bl_description = "Select a PVI for editing"
    bl_options = {'REGISTER', 'UNDO'}
    
    pvi_index: IntProperty(
        name="PVI Index",
        description="Index of PVI to select",
        default=0,
        min=0
    )
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        
        success = overlay.data.select_pvi(self.pvi_index)
        
        if success:
            overlay.refresh(context)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Invalid PVI index")
            return {'CANCELLED'}


# ============================================================================
# VIEW CONTROL OPERATORS
# ============================================================================

class BC_OT_ProfileView_FitToData(Operator):
    """Automatically fit view extents to data"""
    bl_idname = "blendercivil.profile_view_fit_to_data"
    bl_label = "Fit to Data"
    bl_description = "Automatically adjust view extents to fit all data"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        overlay.data.update_view_extents()
        overlay.refresh(context)
        
        self.report({'INFO'}, "Fitted view to data")
        return {'FINISHED'}


class BC_OT_ProfileView_ClearData(Operator):
    """Clear all profile view data"""
    bl_idname = "blendercivil.profile_view_clear_data"
    bl_label = "Clear All Data"
    bl_description = "Clear all terrain, alignment, and PVI data"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from ..core.profile_view_overlay import get_profile_overlay
        
        overlay = get_profile_overlay()
        overlay.data.clear_all()
        overlay.refresh(context)
        
        self.report({'INFO'}, "Cleared all profile data")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class BC_OT_ProfileView_ModalHandler(Operator):
    """Modal event handler for profile view interaction (resize, etc.)"""
    bl_idname = "blendercivil.profile_view_modal_handler"
    bl_label = "Profile View Modal Handler"
    bl_description = "Handle mouse events for profile view resize and interaction"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        from ..core.profile_view_overlay import get_profile_overlay

        overlay = get_profile_overlay()

        # Stop modal handler if overlay is disabled
        if not overlay.enabled:
            # Restore cursor
            context.window.cursor_set('DEFAULT')
            return {'FINISHED'}

        # Handle mouse movement
        if event.type == 'MOUSEMOVE':
            overlay.handle_mouse_move(context, event)
            # Tag viewport for redraw if hovering or resizing
            if overlay.hover_resize_border or overlay.is_resizing:
                if context.area:
                    context.area.tag_redraw()

        # Handle mouse press
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if overlay.handle_mouse_press(context, event):
                return {'RUNNING_MODAL'}

        # Handle mouse release
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            if overlay.handle_mouse_release(context, event):
                if context.area:
                    context.area.tag_redraw()

        # Pass through other events
        if overlay.is_resizing:
            # Block other events while resizing
            return {'RUNNING_MODAL'}
        else:
            # Pass through when not resizing
            return {'PASS_THROUGH'}

    def invoke(self, context, event):
        # Add modal handler to window manager
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}


# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    BC_OT_ProfileView_Toggle,
    BC_OT_ProfileView_Enable,
    BC_OT_ProfileView_Disable,
    BC_OT_ProfileView_LoadFromSprint3,
    BC_OT_ProfileView_SyncToSprint3,
    BC_OT_ProfileView_LoadTerrain,
    BC_OT_ProfileView_AddPVI,
    BC_OT_ProfileView_DeleteSelectedPVI,
    BC_OT_ProfileView_SelectPVI,
    BC_OT_ProfileView_FitToData,
    BC_OT_ProfileView_ClearData,
    BC_OT_ProfileView_ModalHandler,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
