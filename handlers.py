"""
BlenderCivil v0.3.0 - Depsgraph Handler for Auto-Updates
Automatic Alignment Updates on PI Movement

This module provides the depsgraph handler that monitors for PI movements
and automatically triggers alignment updates when auto-update is enabled.

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
from bpy.app.handlers import persistent

# Import our object update functions
try:
    from . import alignment_objects_v2 as align_obj
except ImportError:
    import alignment_objects_v2 as align_obj


# Store previous PI positions to detect actual movement
_pi_positions = {}


@persistent
def alignment_auto_update_handler(scene, depsgraph):
    """
    Depsgraph handler for automatic alignment updates.
    
    This handler is triggered whenever objects are transformed in the scene.
    It checks if any PI points have moved, and if auto-update is enabled,
    it automatically updates the affected alignments.
    
    Args:
        scene: Current Blender scene
        depsgraph: Dependency graph with update information
    """
    global _pi_positions
    
    # Find all alignment roots in scene
    alignment_roots = [obj for obj in scene.objects
                      if obj.type == 'EMPTY' and hasattr(obj, 'alignment_root')
                      and obj.alignment_root.object_type == 'ALIGNMENT_ROOT']
    
    if not alignment_roots:
        return
    
    # Track which alignments need updating
    alignments_to_update = set()
    
    # Check each alignment
    for alignment_root in alignment_roots:
        # Skip if auto-update is disabled
        if not alignment_root.alignment_root.auto_update_enabled:
            continue
        
        # Get horizontal layout collection
        h_layout_name = f"{alignment_root.name}_Horizontal"
        if h_layout_name not in bpy.data.collections:
            continue
        
        collection = bpy.data.collections[h_layout_name]
        
        # Check all PI points for movement
        pis = [obj for obj in collection.objects
              if hasattr(obj, 'alignment_pi')
              and obj.alignment_pi.object_type == 'ALIGNMENT_PI']
        
        for pi in pis:
            pi_id = pi.name
            current_loc = tuple(pi.location)
            
            # Check if this PI has moved
            if pi_id in _pi_positions:
                prev_loc = _pi_positions[pi_id]
                
                # Compare positions (with small tolerance for floating point)
                moved = any(abs(current_loc[i] - prev_loc[i]) > 0.0001 for i in range(3))
                
                if moved:
                    # PI has moved - mark this alignment for update
                    alignments_to_update.add(alignment_root)
                    print(f"  âš¡ PI moved: {pi.name} from {prev_loc} to {current_loc}")
            
            # Update stored position
            _pi_positions[pi_id] = current_loc
    
    # Update affected alignments
    for alignment_root in alignments_to_update:
        print(f"\nâš¡ AUTO-UPDATE: {alignment_root.name}")
        
        # Get horizontal layout collection
        h_layout_name = f"{alignment_root.name}_Horizontal"
        collection = bpy.data.collections[h_layout_name]
        
        # Update all tangents
        tangents = [obj for obj in collection.objects
                   if hasattr(obj, 'alignment_tangent')
                   and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT']
        
        for tangent in tangents:
            align_obj.update_tangent_geometry(tangent)
        
        # Update all curves
        curves = [obj for obj in collection.objects
                 if hasattr(obj, 'alignment_curve')
                 and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE']
        
        for curve in curves:
            align_obj.update_curve_geometry(curve)
        
        # Recalculate stations
        align_obj.update_stations(alignment_root)
        
        print(f"âœ“ Auto-updated {len(tangents)} tangents and {len(curves)} curves")


def clear_position_cache():
    """
    Clear the PI position cache.
    
    Useful when reloading files or resetting the system.
    """
    global _pi_positions
    _pi_positions = {}
    print("âœ“ Cleared PI position cache")


def register():
    """Register the depsgraph handler"""
    # Remove handler if already registered (avoid duplicates)
    if alignment_auto_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(alignment_auto_update_handler)
    
    # Register handler
    bpy.app.handlers.depsgraph_update_post.append(alignment_auto_update_handler)
    print("âœ“ BlenderCivil v0.3.0: Auto-update handler registered")


def unregister():
    """Unregister the depsgraph handler"""
    if alignment_auto_update_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(alignment_auto_update_handler)
    
    clear_position_cache()
    print("âœ“ BlenderCivil v0.3.0: Auto-update handler unregistered")


if __name__ == "__main__":
    print("BlenderCivil v0.3.0 - Depsgraph Handler")
    print("This module is meant to be imported, not run directly.")
