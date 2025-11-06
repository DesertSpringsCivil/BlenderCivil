"""
Interactive PI Operations (Revised with Real-time Visualization)
PIs are pure tangent intersection points - NO radius property
Creates IFC entities and visualizations in real-time as user clicks
"""

import bpy
import gpu
import blf
import math
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty
from mathutils import Vector
from gpu_extras.batch import batch_for_shader


class BC_OT_add_pi_interactive(bpy.types.Operator):
    """Add PIs by clicking in the viewport - Pure intersection points with real-time visualization"""
    bl_idname = "bc.add_pi_interactive"
    bl_label = "Add PI (Click to Place)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Internal state
    _handle = None
    _alignment_obj = None  # NativeIfcAlignment instance
    _visualizer = None     # AlignmentVisualizer instance
    _last_mouse_pos = None
    
    def modal(self, context, event):
        context.area.tag_redraw()
        
        # Track mouse position for visual feedback
        if event.type == 'MOUSEMOVE':
            self._last_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            return {'RUNNING_MODAL'}
        
        # Left click - Place PI (immediate placement with visualization!)
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            # Get 3D location from mouse click
            location = self.get_3d_location_from_mouse(context, event)
            if location:
                # Add PI immediately with visualization
                self.add_pi_at_location(location)
            return {'RUNNING_MODAL'}
        
        # Right click or ENTER - Finish
        if event.type in {'RIGHTMOUSE', 'RET'} and event.value == 'PRESS':
            self.finish(context)
            return {'FINISHED'}
        
        # ESC - Cancel
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        # Validate prerequisites
        from . import NativeIfcManager
        from ..ui.alignment_properties import get_active_alignment_ifc, refresh_alignment_list
        from ..core.alignment_registry import get_or_create_alignment, get_or_create_visualizer
        
        # Check for IFC file
        ifc = NativeIfcManager.get_file()
        if not ifc:
            self.report({'ERROR'}, "No IFC file. Create an IFC file first.")
            return {'CANCELLED'}
        
        # Refresh alignment list
        refresh_alignment_list(context)
        
        # Check for active alignment
        active_alignment = get_active_alignment_ifc(context)
        if not active_alignment:
            # Try to get any alignment
            alignments = ifc.by_type("IfcAlignment")
            if not alignments:
                self.report({'ERROR'}, "No alignment found. Create an alignment first.")
                return {'CANCELLED'}
            
            # Set first alignment as active
            from ..ui.alignment_properties import set_active_alignment
            set_active_alignment(context, alignments[0])
            active_alignment = alignments[0]
            self.report({'INFO'}, f"Set {active_alignment.Name} as active alignment")
        
        # Get or create the Python alignment instance and visualizer
        self._alignment_obj, was_created = get_or_create_alignment(active_alignment)
        self._visualizer, vis_created = get_or_create_visualizer(self._alignment_obj)
        
        if was_created:
            print(f"[PI Tool] Created new alignment instance")
        if vis_created:
            print(f"[PI Tool] Created new visualizer")
        
        # Setup drawing handler for HUD
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        
        align_name = context.scene.bc_alignment.active_alignment_name
        self.report({'INFO'}, f"Interactive PI Mode [{align_name}] - Click to place, Enter/RMB to finish, ESC to cancel")
        return {'RUNNING_MODAL'}
    
    def get_3d_location_from_mouse(self, context, event):
        """Convert mouse position to 3D coordinates on XY plane (Z=0)"""
        region = context.region
        rv3d = context.region_data
        
        # Get mouse position in region coordinates
        coord = (event.mouse_region_x, event.mouse_region_y)
        
        # Use view3d_utils for proper 3D projection
        from bpy_extras import view3d_utils
        
        # Get ray from mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        
        # Intersect with Z=0 plane
        if abs(view_vector.z) > 0.0001:  # Avoid division by zero
            t = -ray_origin.z / view_vector.z
            if t >= 0:  # Only forward intersections
                intersection = ray_origin + t * view_vector
                return Vector((intersection.x, intersection.y, 0))
        
        return None
    
    def add_pi_at_location(self, location):
        """Add PI at location with immediate IFC creation and visualization"""
        
        if not self._alignment_obj or not self._visualizer:
            self.report({'ERROR'}, "Alignment or visualizer not initialized")
            return
        
        # Add PI to alignment (creates IFC entity)
        pi_data = self._alignment_obj.add_pi(location.x, location.y)
        
        # Create visual marker immediately
        pi_marker = self._visualizer.create_pi_object(pi_data)
        
        # Update tangent line visualization if we have 2+ PIs
        if len(self._alignment_obj.pis) >= 2:
            # Visualize the last created segment (should be the newest tangent)
            if self._alignment_obj.segments:
                last_segment = self._alignment_obj.segments[-1]
                self._visualizer.create_segment_curve(last_segment)
        
        pi_count = len(self._alignment_obj.pis)
        self.report({'INFO'}, f"✓ PI {pi_count} at ({location.x:.2f}, {location.y:.2f})")
        
        print(f"[PI Tool] Added PI {pi_count} at ({location.x:.2f}, {location.y:.2f})")
        print(f"[PI Tool] Total segments: {len(self._alignment_obj.segments)}")
    
    def draw_callback_px(self, operator, context):
        """Draw on-screen instructions and visual feedback"""
        
        font_id = 0
        
        # Draw instructions box
        blf.position(font_id, 15, 80, 0)
        blf.size(font_id, 22)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, "📍 Place Tangent Points (PIs)")
        
        blf.position(font_id, 15, 55, 0)
        blf.size(font_id, 14)
        blf.color(font_id, 0.9, 0.9, 0.9, 1.0)
        blf.draw(font_id, "🖱️  Left Click: Place PI (immediate!)")
        
        blf.position(font_id, 15, 38, 0)
        blf.draw(font_id, "✔ Enter / Right Click: Finish")
        
        blf.position(font_id, 15, 21, 0)
        blf.draw(font_id, "✖ ESC: Cancel")
        
        # Show point count if any points placed
        if self._alignment_obj and len(self._alignment_obj.pis) > 0:
            pi_count = len(self._alignment_obj.pis)
            blf.position(font_id, context.region.width - 180, 45, 0)
            blf.size(font_id, 18)
            blf.color(font_id, 0.3, 1.0, 0.4, 1.0)
            blf.draw(font_id, f"PIs Placed: {pi_count}")
            
            # Show last PI coordinates
            last_pi = self._alignment_obj.pis[-1]
            blf.position(font_id, context.region.width - 180, 25, 0)
            blf.size(font_id, 13)
            blf.color(font_id, 0.8, 0.8, 0.8, 1.0)
            blf.draw(font_id, f"Last: ({last_pi['position'].x:.1f}, {last_pi['position'].y:.1f})")
        
        # Draw crosshair cursor at mouse position
        if self._last_mouse_pos:
            x, y = self._last_mouse_pos
            
            # Create shader
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            shader.bind()
            shader.uniform_float("color", (0.3, 1.0, 0.4, 0.9))  # Green for PIs
            
            # Enable line smoothing
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(2.0)
            
            # Draw crosshair
            size = 15
            vertices = [
                (x - size, y), (x + size, y),  # Horizontal
                (x, y - size), (x, y + size)   # Vertical
            ]
            batch = batch_for_shader(shader, 'LINES', {"pos": vertices})
            batch.draw(shader)
            
            # Draw circle at cursor
            circle_segments = 24
            circle_vertices = []
            circle_radius = 8
            for i in range(circle_segments + 1):
                angle = 2 * math.pi * i / circle_segments
                circle_vertices.append((
                    x + circle_radius * math.cos(angle),
                    y + circle_radius * math.sin(angle)
                ))
            
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": circle_vertices})
            batch.draw(shader)
            
            gpu.state.blend_set('NONE')
    
    def finish(self, context):
        """Finish interactive mode - PIs and segments already in IFC!"""
        # Remove drawing handler
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        
        if self._alignment_obj:
            pi_count = len(self._alignment_obj.pis)
            segment_count = len(self._alignment_obj.segments)
            
            if pi_count > 0:
                self.report({'INFO'}, f"✅ Placed {pi_count} PIs, created {segment_count} tangent segments")
                print(f"[PI Tool] Finished: {pi_count} PIs, {segment_count} segments in IFC")
            else:
                self.report({'WARNING'}, "No PIs placed")
        
        context.area.tag_redraw()
    
    def cancel(self, context):
        """Cancel interactive mode"""
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        
        # TODO: Could implement undo here - remove PIs added during this session
        
        self.report({'INFO'}, "PI placement cancelled")
        context.area.tag_redraw()


# Keep original operator for backward compatibility
class BC_OT_add_native_pi(bpy.types.Operator):
    """Add PI at 3D cursor (classic method)"""
    bl_idname = "bc.add_native_pi"
    bl_label = "Add PI at Cursor"
    bl_options = {'REGISTER', 'UNDO'}
    
    # NO RADIUS PROPERTY!
    
    def execute(self, context):
        from . import NativeIfcManager
        from ..ui.alignment_properties import get_active_alignment_ifc
        from ..core.alignment_registry import get_or_create_alignment, get_or_create_visualizer
        
        cursor = context.scene.cursor.location
        
        # Get active alignment
        active_alignment = get_active_alignment_ifc(context)
        if not active_alignment:
            self.report({'ERROR'}, "No active alignment. Create an alignment first.")
            return {'CANCELLED'}
        
        # Get alignment instance
        alignment_obj, _ = get_or_create_alignment(active_alignment)
        visualizer, _ = get_or_create_visualizer(alignment_obj)
        
        # Add PI - no radius!
        pi_data = alignment_obj.add_pi(cursor.x, cursor.y)
        
        # Create visualization
        visualizer.create_pi_object(pi_data)
        
        # Update tangents if we have 2+ PIs
        if len(alignment_obj.pis) >= 2 and alignment_obj.segments:
            last_segment = alignment_obj.segments[-1]
            visualizer.create_segment_curve(last_segment)
        
        self.report({'INFO'}, f"Added PI at ({cursor.x:.2f}, {cursor.y:.2f})")
        return {'FINISHED'}


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
    BC_OT_add_pi_interactive,
    BC_OT_add_native_pi,
    BC_OT_delete_native_pi,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
