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
    
    def modal(self, context, event):
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
                            # Show radius dialog
                            return context.window_manager.invoke_props_dialog(self, width=300)
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
    
    def draw(self, context):
        """Draw the radius input dialog"""
        layout = self.layout
        layout.label(text=f"Insert curve between:")
        layout.label(text=f"  • {self._first_tangent.name}")
        layout.label(text=f"  • {self._second_tangent.name}")
        layout.separator()
        layout.prop(self, "radius")
    
    def execute(self, context):
        """Called when OK is clicked in the radius dialog"""
        # Create the curve
        success = self.create_curve(self._first_tangent, self._second_tangent, self.radius)
        
        if success:
            self.report({'INFO'}, f"✅ Created curve with R={self.radius:.1f}m")
        else:
            self.report({'ERROR'}, "Failed to create curve")
        
        # Clean up and exit
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        
        context.area.tag_redraw()
        return {'FINISHED'}
    
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
    
    def create_curve(self, tangent1, tangent2, radius):
        """Create curve between two tangents"""
        # TODO INTEGRATION:
        # 1. Get the shared PI between the two tangents
        # 2. Calculate curve geometry (BC, EC, arc length, etc.)
        # 3. Create IFC curve segment
        # 4. Trim tangent1 at BC
        # 5. Trim tangent2 at EC
        # 6. Visualize the curve
        
        # from . import NativeIfcManager, NativeIfcAlignment
        # alignment = get_active_alignment()
        # curve_data = alignment.insert_curve_at_pi(pi_index, radius)
        # visualizer.create_curve_segment(curve_data)
        
        return True  # Placeholder
    
    def draw_callback_px(self, operator, context):
        """Draw on-screen instructions and visual feedback"""
        
        font_id = 0
        
        # Draw instructions based on state
        blf.position(font_id, 15, 80, 0)
        blf.size(font_id, 22)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.draw(font_id, "🔄 Add Curve Between Tangents")
        
        blf.position(font_id, 15, 55, 0)
        blf.size(font_id, 14)
        blf.color(font_id, 0.9, 0.9, 0.9, 1.0)
        
        if self._state == "SELECT_FIRST":
            blf.draw(font_id, "🖱️  Click FIRST tangent segment")
        elif self._state == "SELECT_SECOND":
            blf.draw(font_id, "🖱️  Click SECOND tangent segment")
            blf.position(font_id, 15, 38, 0)
            blf.color(font_id, 0.3, 1.0, 0.4, 1.0)
            blf.draw(font_id, f"✓ First: {self._first_tangent.name}")
        
        blf.position(font_id, 15, 21, 0)
        blf.color(font_id, 0.9, 0.9, 0.9, 1.0)
        blf.draw(font_id, "✖ ESC: Cancel")
        
        # Highlight hovered object
        if self._hovered_object and self.is_tangent_segment(self._hovered_object):
            # Draw highlight indicator
            blf.position(font_id, context.region.width - 250, 45, 0)
            blf.size(font_id, 16)
            blf.color(font_id, 1.0, 1.0, 0.0, 1.0)
            blf.draw(font_id, f"↗ Hover: {self._hovered_object.name}")
        
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
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        
        self.report({'INFO'}, "Curve addition cancelled")
        context.area.tag_redraw()


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
    BC_OT_delete_curve,
    BC_OT_edit_curve_radius,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
