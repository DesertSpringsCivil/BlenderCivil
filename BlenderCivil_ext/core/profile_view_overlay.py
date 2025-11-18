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
BlenderCivil - Profile View Overlay Manager (Core)
===================================================

Manages the viewport overlay system for profile view visualization.
Handles draw handler registration and coordinates with renderer.

This follows BlenderCivil's architecture pattern:
- Core logic for overlay management
- Minimal Blender dependencies

Author: BlenderCivil Development Team
Date: November 2025
License: GPL v3
"""

import bpy

from .profile_view_data import ProfileViewData
from .profile_view_renderer import ProfileViewRenderer


class ProfileViewOverlay:
    """
    Manages the profile view as an overlay at the bottom of the 3D viewport.
    
    Responsibilities:
        - Register/unregister draw handlers
        - Coordinate rendering with Blender's refresh cycle
        - Manage overlay state (enabled/disabled)
        - Define overlay dimensions
    
    This is the "glue" between the core rendering system and Blender's viewport.
    """
    
    def __init__(self):
        """Initialize overlay manager"""
        self.data = ProfileViewData()
        self.renderer = ProfileViewRenderer()
        self.draw_handle = None
        self.enabled = False
        
        # Overlay dimensions
        self.overlay_height = 200  # pixels (fixed at bottom of viewport)
    
    def enable(self, context):
        """
        Enable the profile view overlay.
        
        Args:
            context: Blender context
        """
        if not self.enabled:
            # Register draw handler for 3D viewport
            # This will be called every time the viewport refreshes
            self.draw_handle = bpy.types.SpaceView3D.draw_handler_add(
                self._draw_callback,
                (context,),
                'WINDOW',
                'POST_PIXEL'
            )
            self.enabled = True
            
            # Force viewport redraw
            if context.area:
                context.area.tag_redraw()
    
    def disable(self, context):
        """
        Disable the profile view overlay.
        
        Args:
            context: Blender context
        """
        if self.enabled and self.draw_handle:
            # Unregister draw handler
            bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle, 'WINDOW')
            self.draw_handle = None
            self.enabled = False
            
            # Force viewport redraw
            if context.area:
                context.area.tag_redraw()
    
    def toggle(self, context):
        """
        Toggle overlay on/off.
        
        Args:
            context: Blender context
        """
        if self.enabled:
            self.disable(context)
        else:
            self.enable(context)
    
    def _draw_callback(self, context):
        """
        Draw callback - invoked by Blender every frame.
        
        Args:
            context: Blender context
        
        Note:
            This is called automatically by Blender's draw handler system.
            Do not call directly.
        """
        if not self.enabled:
            return
        
        # Get viewport dimensions
        area = context.area
        region = context.region
        
        if not region or not area:
            return
        
        # Set renderer region (bottom strip of viewport)
        x = 0
        y = 0
        width = region.width
        height = self.overlay_height
        
        self.renderer.set_view_region(x, y, width, height)
        
        # Render profile view
        self.renderer.render(self.data)
    
    def refresh(self, context):
        """
        Force a viewport refresh.
        
        Args:
            context: Blender context
        """
        if context.area:
            context.area.tag_redraw()
    
    def get_status(self) -> str:
        """
        Get overlay status as string.
        
        Returns:
            Status description
        """
        if self.enabled:
            return f"ENABLED - {len(self.data.pvis)} PVIs, " \
                   f"{len(self.data.terrain_points)} terrain pts"
        else:
            return "DISABLED"


# ============================================================================
# GLOBAL OVERLAY INSTANCE
# ============================================================================

# Singleton pattern - one overlay per Blender session
_profile_overlay_instance = None


def get_profile_overlay() -> ProfileViewOverlay:
    """
    Get or create the global profile overlay instance (singleton).
    
    Returns:
        ProfileViewOverlay instance
    
    Note:
        This ensures only one overlay exists at a time.
        Operators and UI can access this to interact with the overlay.
    """
    global _profile_overlay_instance
    
    if _profile_overlay_instance is None:
        _profile_overlay_instance = ProfileViewOverlay()
    
    return _profile_overlay_instance


def reset_profile_overlay():
    """
    Reset the global profile overlay instance.
    
    Note:
        Call this when Blender restarts or when you want to clear all data.
    """
    global _profile_overlay_instance
    
    # Disable if currently enabled
    if _profile_overlay_instance and _profile_overlay_instance.enabled:
        import bpy
        _profile_overlay_instance.disable(bpy.context)
    
    _profile_overlay_instance = None


# ============================================================================
# INTEGRATION HELPERS
# ============================================================================

def load_from_sprint3_vertical(context) -> bool:
    """
    Load profile data from Sprint 3 vertical alignment properties.
    
    Args:
        context: Blender context
        
    Returns:
        True if loaded successfully, False otherwise
    """
    overlay = get_profile_overlay()
    
    # Check if Sprint 3 vertical alignment exists
    if not hasattr(context.scene, 'bc_vertical'):
        return False
    
    v_props = context.scene.bc_vertical
    
    # Clear existing data
    overlay.data.clear_alignment()
    
    # Load PVIs from Sprint 3
    for pvi_prop in v_props.pvis:
        metadata = {
            'curve_length': pvi_prop.curve_length,
            'incoming_grade': pvi_prop.incoming_grade,
            'outgoing_grade': pvi_prop.outgoing_grade,
        }
        
        if hasattr(pvi_prop, 'k_value'):
            metadata['k_value'] = pvi_prop.k_value
        
        overlay.data.add_pvi(
            pvi_prop.station,
            pvi_prop.elevation,
            metadata
        )
    
    # Load segments to create smooth alignment profile
    for segment_prop in v_props.segments:
        # Sample points along segment for smooth display
        import numpy as np
        
        num_points = 20 if segment_prop.segment_type == 'CURVE' else 2
        stations = np.linspace(
            segment_prop.start_station,
            segment_prop.end_station,
            num_points
        )
        
        for station in stations:
            # Linear interpolation (Sprint 3 has better elevation calculator)
            t = (station - segment_prop.start_station) / segment_prop.length
            elevation = (
                segment_prop.start_elevation * (1 - t) +
                segment_prop.end_elevation * t
            )
            
            overlay.data.add_alignment_point(station, elevation)
    
    # Update view extents
    overlay.data.update_view_extents()
    
    return True


def sync_to_sprint3_vertical(context) -> bool:
    """
    Write profile data back to Sprint 3 vertical alignment properties.
    
    Args:
        context: Blender context
        
    Returns:
        True if synced successfully, False otherwise
    """
    overlay = get_profile_overlay()
    
    # Check if Sprint 3 vertical alignment exists
    if not hasattr(context.scene, 'bc_vertical'):
        return False
    
    v_props = context.scene.bc_vertical
    
    # Clear existing PVIs
    v_props.pvis.clear()
    
    # Add updated PVIs
    for pvi in overlay.data.pvis:
        pvi_prop = v_props.pvis.add()
        pvi_prop.station = pvi.station
        pvi_prop.elevation = pvi.elevation
        
        # Transfer metadata
        if 'curve_length' in pvi.metadata:
            pvi_prop.curve_length = pvi.metadata['curve_length']
        
        # Note: incoming/outgoing grades will be recalculated by Sprint 3
    
    # Trigger Sprint 3 segment regeneration
    # (This operator should exist from Sprint 3)
    if hasattr(bpy.ops.blendercivil, 'generate_vertical_segments'):
        bpy.ops.blendercivil.generate_vertical_segments()
    
    return True


if __name__ == "__main__":
    print("ProfileViewOverlay - Core overlay manager")
    print("Use from within Blender for testing.")
