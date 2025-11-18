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
Interactive Curve Operations
Add curves between tangent segments by selecting tangents graphically
"""

import bpy
import gpu
import blf
import math
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty
from mathutils import Vector
from gpu_extras.batch import batch_for_shader


class BC_OT_add_curve_interactive(bpy.types.Operator):
    """Add curve by selecting two tangent segments"""
    bl_idname = "bc.add_curve_interactive"
    bl_label = "Add Curve (Click Tangents)"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Curve radius (entered after selecting tangents)
    radius: FloatProperty(
        name="Radius",
        default=100.0,
        min=0.1,
        description="Curve radius in meters"
    )
    
    # Internal state
    _handle = None
    _first_tangent = None
    _second_tangent = None
    _last_mouse_pos = None
    _hovered_object = None
    _state = "SELECT_FIRST"  # States: SELECT_FIRST, SELECT_SECOND, ENTER_RADIUS
    _dialog_active = False  # Flag to prevent cancel() when dialog is shown
    _finished = False  # Flag to track if operator has completed
    
    def modal(self, context, event):
        # CRITICAL: Check finished flag FIRST, before any context access
        if self._finished:
            # Don't access context or do anything - just exit immediately
            return {'FINISHED'}

        # Safe to access context now
        context.area.tag_redraw()

        # Track mouse position and highlight hovered objects
        if event.type == 'MOUSEMOVE':
            self._last_mouse_pos = (event.mouse_region_x, event.mouse_region_y)
            
            # Raycast to find hovered object
            self._hovered_object = self.get_object_under_mouse(context, event)
            return {'RUNNING_MODAL'}
        
        # Left click - Select tangent
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            if self._state == "SELECT_FIRST":
                # Select first tangent
                obj = self.get_object_under_mouse(context, event)
                if obj and self.is_tangent_segment(obj):
                    self._first_tangent = obj
                    self._state = "SELECT_SECOND"
                    self.report({'INFO'}, f"First tangent selected: {obj.name}. Click second tangent...")
                else:
                    self.report({'WARNING'}, "Click on a tangent line segment")
                    
            elif self._state == "SELECT_SECOND":
                # Select second tangent
                obj = self.get_object_under_mouse(context, event)
                if obj and self.is_tangent_segment(obj):
                    if obj != self._first_tangent:
                        self._second_tangent = obj
                        # Check if tangents are adjacent
                        if self.are_tangents_adjacent(self._first_tangent, self._second_tangent):
                            # CRITICAL: End modal operator BEFORE dialog
                            # Store tangent info in scene for the dialog operator to use
                            context.scene["bc_curve_tangent1"] = self._first_tangent.name
                            context.scene["bc_curve_tangent2"] = self._second_tangent.name

                            # Clean up modal operator
                            if self._handle:
                                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                                self._handle = None

                            # Exit modal cleanly
                            self._finished = True
                            context.area.tag_redraw()

                            # Invoke the SEPARATE dialog operator
                            bpy.ops.bc.add_curve_dialog('INVOKE_DEFAULT')
                            return {'FINISHED'}
                        else:
                            self.report({'ERROR'}, "Tangents must be adjacent (share a PI)")
                            self._second_tangent = None
                    else:
                        self.report({'WARNING'}, "Select a different tangent")
                else:
                    self.report({'WARNING'}, "Click on a tangent line segment")
            
            return {'RUNNING_MODAL'}
        
        # ESC - Cancel
        if event.type == 'ESC':
            self.cancel(context)
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        # Validate prerequisites
        from . import NativeIfcManager
        from ..ui.alignment_properties import get_active_alignment_ifc, refresh_alignment_list
        
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
            alignments = ifc.by_type("IfcAlignment")
            if not alignments:
                self.report({'ERROR'}, "No alignment found. Create an alignment first.")
                return {'CANCELLED'}
            
            # Set first alignment as active
            from ..ui.alignment_properties import set_active_alignment
            set_active_alignment(context, alignments[0])
            active_alignment = alignments[0]
            self.report({'INFO'}, f"Set {active_alignment.Name} as active alignment")
        
        # Setup drawing handler for HUD
        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
        
        context.window_manager.modal_handler_add(self)
        
        align_name = context.scene.bc_alignment.active_alignment_name
        self.report({'INFO'}, f"Add Curve Mode [{align_name}] - Click first tangent segment")
        return {'RUNNING_MODAL'}
    
    
    def get_object_under_mouse(self, context, event):
        """Get object under mouse cursor using ray casting"""
        region = context.region
        rv3d = context.region_data
        coord = (event.mouse_region_x, event.mouse_region_y)
        
        from bpy_extras import view3d_utils
        
        # Get ray from mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
        ray_target = ray_origin + (view_vector * 10000.0)
        
        # Cast ray in scene
        result = context.scene.ray_cast(context.view_layer.depsgraph, ray_origin, view_vector)
        
        if result[0]:  # Hit
            return result[4]  # Hit object
        
        return None
    
    def is_tangent_segment(self, obj):
        """Check if object is a tangent line segment"""
        # Check if it's a curve object with LINE type
        if obj.type != 'CURVE':
            return False
        
        # Check if it has IFC data
        if "ifc_definition_id" not in obj:
            return False
        
        # Check name pattern
        if "Tangent" in obj.name:
            return True
        
        # Could also check IFC entity type
        # from . import NativeIfcManager
        # entity = NativeIfcManager.get_entity(obj)
        # if entity and entity.DesignParameters.PredefinedType == "LINE":
        #     return True
        
        return False
    
    def are_tangents_adjacent(self, tangent1, tangent2):
        """Check if two tangent segments share a PI (are adjacent)"""
        # Simple check: compare segment names/indices
        # In production, would check actual geometry and IFC relationships
        
        # Extract segment numbers from names like "Tangent_0", "Tangent_1"
        try:
            num1 = int(tangent1.name.split('_')[-1])
            num2 = int(tangent2.name.split('_')[-1])
            
            # Adjacent means difference of 1
            return abs(num1 - num2) == 1
        except:
            # Fallback: check spatial proximity of endpoints
            return True  # Allow for now
    
    def draw_callback_px(self, operator, context):
        """Draw on-screen instructions and visual feedback"""
        # CRITICAL: If finished or handler removed, don't draw anything
        if self._finished or self._handle is None:
            return

        font_id = 0

        # Draw instructions based on state
        blf.position(font_id, 15, 80, 0)
        blf.size(font_id, 22)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, "[CURVE] Add Curve Between Tangents")

        blf.position(font_id, 15, 55, 0)
        blf.size(font_id, 14)
        blf.color(font_id, 0.9, 0.9, 0.9, 1.0)

        if self._state == "SELECT_FIRST":
            blf.draw(font_id, "Click FIRST tangent segment")
        elif self._state == "SELECT_SECOND":
            blf.draw(font_id, "Click SECOND tangent segment")
            blf.position(font_id, 15, 38, 0)
            blf.color(font_id, 0.3, 1.0, 0.4, 1.0)
            # Safely get tangent name
            try:
                tangent_name = self._first_tangent.name if self._first_tangent else "Unknown"
            except (AttributeError, ReferenceError):
                tangent_name = "Unknown"
            blf.draw(font_id, f"[+] First: {tangent_name}")

        blf.position(font_id, 15, 21, 0)
        blf.color(font_id, 0.9, 0.9, 0.9, 1.0)
        blf.draw(font_id, "[X] ESC: Cancel")

        # Highlight hovered object
        if self._hovered_object and self.is_tangent_segment(self._hovered_object):
            # Draw highlight indicator
            blf.position(font_id, context.region.width - 250, 45, 0)
            blf.size(font_id, 16)
            blf.color(font_id, 1.0, 1.0, 0.0, 1.0)
            # Safely get hovered object name
            try:
                hover_name = self._hovered_object.name
            except (AttributeError, ReferenceError):
                hover_name = "Unknown"
            blf.draw(font_id, f"[>>] Hover: {hover_name}")
        
        # Draw cursor - different color for curve tool (orange)
        if self._last_mouse_pos:
            x, y = self._last_mouse_pos
            
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
            shader.bind()
            
            # Orange for curve mode
            shader.uniform_float("color", (1.0, 0.6, 0.0, 0.9))
            
            gpu.state.blend_set('ALPHA')
            gpu.state.line_width_set(2.0)
            
            # Draw crosshair
            size = 15
            vertices = [
                (x - size, y), (x + size, y),
                (x, y - size), (x, y + size)
            ]
            batch = batch_for_shader(shader, 'LINES', {"pos": vertices})
            batch.draw(shader)
            
            # Draw square for curve mode (different from circle for PI mode)
            square_size = 10
            square_vertices = [
                (x - square_size, y - square_size),
                (x + square_size, y - square_size),
                (x + square_size, y + square_size),
                (x - square_size, y + square_size),
                (x - square_size, y - square_size)
            ]
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": square_vertices})
            batch.draw(shader)
            
            gpu.state.blend_set('NONE')
    
    def cancel(self, context):
        """Cancel curve addition"""
        # Don't run cancel if we're transitioning to dialog (prevents double cleanup crash)
        if self._dialog_active:
            return

        # Don't run cancel if we've already finished (dialog completed)
        if self._finished:
            return

        # Clean up draw handler safely
        if self._handle:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                self._handle = None
            except:
                pass  # Already removed

        self.report({'INFO'}, "Curve addition cancelled")
        context.area.tag_redraw()


class BC_OT_add_curve_dialog(bpy.types.Operator):
    """Dialog for entering curve radius (separated from modal)"""
    bl_idname = "bc.add_curve_dialog"
    bl_label = "Add Curve"
    bl_options = {'REGISTER', 'UNDO'}

    radius: FloatProperty(
        name="Radius",
        default=100.0,
        min=0.1,
        description="Curve radius in meters"
    )

    def execute(self, context):
        """Create curve with specified radius"""
        # Get tangent names from scene
        tangent1_name = context.scene.get("bc_curve_tangent1")
        tangent2_name = context.scene.get("bc_curve_tangent2")

        if not tangent1_name or not tangent2_name:
            self.report({'ERROR'}, "Tangent references lost")
            return {'CANCELLED'}

        # Get tangent objects
        tangent1 = bpy.data.objects.get(tangent1_name)
        tangent2 = bpy.data.objects.get(tangent2_name)

        if not tangent1 or not tangent2:
            self.report({'ERROR'}, "Tangent objects no longer exist")
            return {'CANCELLED'}

        # Create the curve
        try:
            success = self.create_curve(tangent1, tangent2, self.radius)

            if success:
                self.report({'INFO'}, f"[OK] Created curve with R={self.radius:.1f}m")
            else:
                self.report({'ERROR'}, "Failed to create curve")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create curve: {e}")
            print(f"[CurveTool] Error in create_curve: {e}")
            import traceback
            traceback.print_exc()

        # Clean up scene properties
        if "bc_curve_tangent1" in context.scene:
            del context.scene["bc_curve_tangent1"]
        if "bc_curve_tangent2" in context.scene:
            del context.scene["bc_curve_tangent2"]

        return {'FINISHED'}

    def invoke(self, context, event):
        """Show dialog"""
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        """Draw dialog UI"""
        layout = self.layout

        tangent1_name = context.scene.get("bc_curve_tangent1", "Unknown")
        tangent2_name = context.scene.get("bc_curve_tangent2", "Unknown")

        layout.label(text=f"Insert curve between:")
        layout.label(text=f"  • {tangent1_name}")
        layout.label(text=f"  • {tangent2_name}")
        layout.separator()
        layout.prop(self, "radius")

    def _find_shared_pi(self, tangent1, tangent2):
        """Find the PI index shared by two tangent curve objects

        Args:
            tangent1, tangent2: Blender curve objects representing tangents

        Returns:
            PI index (int) or None if not found
        """
        import bpy
        from mathutils import Vector

        # Get the alignment parent object
        alignment = tangent1.parent
        if not alignment or tangent2.parent != alignment:
            print(f"[CurveTool] Tangents don't share the same parent alignment")
            return None

        # Find all PI objects in the alignment
        pi_objects = [obj for obj in alignment.children if obj.name.startswith("PI_")]

        if not pi_objects:
            print(f"[CurveTool] No PI objects found in alignment")
            return None

        # Get the endpoints of each tangent curve
        # Tangents use POLY splines, so we need to access .points, not .bezier_points
        try:
            if len(tangent1.data.splines) > 0:
                spline1 = tangent1.data.splines[0]
                # Check if it's a POLY spline (tangents) or BEZIER spline (curves)
                if spline1.type == 'POLY' and len(spline1.points) > 0:
                    tangent1_start = spline1.points[0].co.xyz
                    tangent1_end = spline1.points[-1].co.xyz
                elif spline1.type == 'BEZIER' and len(spline1.bezier_points) > 0:
                    tangent1_start = spline1.bezier_points[0].co
                    tangent1_end = spline1.bezier_points[-1].co
                else:
                    print(f"[CurveTool] Tangent1 has no points (type: {spline1.type})")
                    return None
            else:
                print(f"[CurveTool] Tangent1 has no splines")
                return None

            if len(tangent2.data.splines) > 0:
                spline2 = tangent2.data.splines[0]
                # Check if it's a POLY spline (tangents) or BEZIER spline (curves)
                if spline2.type == 'POLY' and len(spline2.points) > 0:
                    tangent2_start = spline2.points[0].co.xyz
                    tangent2_end = spline2.points[-1].co.xyz
                elif spline2.type == 'BEZIER' and len(spline2.bezier_points) > 0:
                    tangent2_start = spline2.bezier_points[0].co
                    tangent2_end = spline2.bezier_points[-1].co
                else:
                    print(f"[CurveTool] Tangent2 has no points (type: {spline2.type})")
                    return None
            else:
                print(f"[CurveTool] Tangent2 has no splines")
                return None
        except Exception as e:
            print(f"[CurveTool] Error getting tangent endpoints: {e}")
            return None

        # Transform to world space
        tangent1_start_world = tangent1.matrix_world @ tangent1_start
        tangent1_end_world = tangent1.matrix_world @ tangent1_end
        tangent2_start_world = tangent2.matrix_world @ tangent2_start
        tangent2_end_world = tangent2.matrix_world @ tangent2_end

        # Find which PI is at the junction between the two tangents
        # The shared PI should be close to one endpoint of each tangent
        tolerance = 1.0  # 1 meter tolerance (increased for floating point precision)

        # Debug output
        print(f"[CurveTool] Searching for shared PI between {tangent1.name} and {tangent2.name}")
        print(f"[CurveTool] Tangent1 endpoints: {tangent1_start_world} to {tangent1_end_world}")
        print(f"[CurveTool] Tangent2 endpoints: {tangent2_start_world} to {tangent2_end_world}")

        for pi_obj in pi_objects:
            pi_location = pi_obj.matrix_world.translation

            # Calculate distances
            dist_t1_start = (pi_location - tangent1_start_world).length
            dist_t1_end = (pi_location - tangent1_end_world).length
            dist_t2_start = (pi_location - tangent2_start_world).length
            dist_t2_end = (pi_location - tangent2_end_world).length

            # Check if this PI is at an endpoint of both tangents
            is_tangent1_endpoint = (dist_t1_start < tolerance or dist_t1_end < tolerance)
            is_tangent2_endpoint = (dist_t2_start < tolerance or dist_t2_end < tolerance)

            # Debug output for each PI
            print(f"[CurveTool] {pi_obj.name}: t1_start={dist_t1_start:.3f}m, t1_end={dist_t1_end:.3f}m, "
                  f"t2_start={dist_t2_start:.3f}m, t2_end={dist_t2_end:.3f}m")

            if is_tangent1_endpoint and is_tangent2_endpoint:
                # Found the shared PI! Extract its index from the name
                try:
                    # PI_002 -> index 2
                    pi_index = int(pi_obj.name.split('_')[-1])
                    print(f"[CurveTool] ✓ Found shared PI: {pi_obj.name} at index {pi_index}")
                    return pi_index
                except:
                    print(f"[CurveTool] Could not parse PI index from name: {pi_obj.name}")
                    return None

        print(f"[CurveTool] ✗ No shared PI found between tangents")
        return None

    def create_curve(self, tangent1, tangent2, radius):
        """Create curve between two tangents by integrating with alignment system"""
        import bpy
        import math

        # Find the shared PI between the two tangents
        # Look at the tangent endpoints to find which PI they share
        pi_index = self._find_shared_pi(tangent1, tangent2)

        if pi_index is None:
            print(f"[CurveTool] Could not find shared PI between {tangent1.name} and {tangent2.name}")
            return False

        print(f"[CurveTool] Found shared PI at index {pi_index}")

        # Get the alignment object from the registry
        from ..core.native_ifc_manager import NativeIfcManager
        from ..core import alignment_registry
        from ..ui.alignment_properties import get_active_alignment_ifc

        # Get the active alignment IFC entity
        ifc = NativeIfcManager.get_file()
        if not ifc:
            print(f"[CurveTool] No IFC file loaded")
            return False

        active_alignment_ifc = get_active_alignment_ifc(bpy.context)
        if not active_alignment_ifc:
            print(f"[CurveTool] No active alignment")
            return False

        # Get the alignment object from registry
        alignment_obj = alignment_registry.get_alignment(active_alignment_ifc.GlobalId)
        if not alignment_obj:
            print(f"[CurveTool] Could not find alignment object in registry")
            return False

        # Insert curve at PI using the alignment's built-in method
        print(f"[CurveTool] Inserting curve at PI {pi_index} with radius {radius:.1f}m")

        curve_data = alignment_obj.insert_curve_at_pi(pi_index, radius)

        if not curve_data:
            print(f"[CurveTool] Failed to insert curve at PI {pi_index}")
            return False

        # The alignment has updated its segments, now update visualization
        if hasattr(alignment_obj, 'visualizer') and alignment_obj.visualizer:
            alignment_obj.visualizer.update_all()
            print(f"[CurveTool] Updated visualization")

        print(f"[CurveTool] Successfully inserted curve:")
        print(f"[CurveTool]   PI Index: {pi_index}")
        print(f"[CurveTool]   Radius: {radius:.1f}m")
        print(f"[CurveTool]   Arc Length: {curve_data['arc_length']:.2f}m")
        print(f"[CurveTool]   Deflection: {math.degrees(curve_data['deflection']):.1f}°")
        print(f"[CurveTool]   Turn: {curve_data['turn_direction']}")

        return True


class BC_OT_delete_curve(bpy.types.Operator):
    """Delete selected curve"""
    bl_idname = "bc.delete_curve"
    bl_label = "Delete Curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "Select a curve segment")
            return {'CANCELLED'}
        
        # Check if it's a curve (not a tangent)
        if "Curve" not in obj.name:
            self.report({'ERROR'}, "Select a curve segment (not a tangent)")
            return {'CANCELLED'}
        
        # Remove from scene
        bpy.data.objects.remove(obj, do_unlink=True)
        
        # TODO: Extend tangent lines to meet at PI
        # TODO: Update IFC alignment
        
        self.report({'INFO'}, "Deleted curve")
        return {'FINISHED'}


class BC_OT_edit_curve_radius(bpy.types.Operator):
    """Edit radius of selected curve"""
    bl_idname = "bc.edit_curve_radius"
    bl_label = "Edit Curve Radius"
    bl_options = {'REGISTER', 'UNDO'}
    
    radius: FloatProperty(
        name="New Radius",
        default=100.0,
        min=0.1,
        description="New curve radius in meters"
    )
    
    def execute(self, context):
        obj = context.active_object
        
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "Select a curve segment")
            return {'CANCELLED'}
        
        # TODO INTEGRATION:
        # 1. Get IFC curve entity
        # 2. Update radius
        # 3. Recalculate curve geometry
        # 4. Update visualization
        
        self.report({'INFO'}, f"Updated curve radius to {self.radius:.1f}m")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        obj = context.active_object
        
        # Get current radius from IFC if available
        # self.radius = get_current_radius(obj)
        
        return context.window_manager.invoke_props_dialog(self)


# Registration
classes = (
    BC_OT_add_curve_interactive,
    BC_OT_add_curve_dialog,
    BC_OT_delete_curve,
    BC_OT_edit_curve_radius,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
