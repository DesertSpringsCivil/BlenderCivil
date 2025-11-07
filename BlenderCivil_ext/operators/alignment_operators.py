"""
Alignment Operations
Create and update alignment operators
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty

# Import from parent operators module (where classes are injected)
from . import NativeIfcManager, NativeIfcAlignment, AlignmentVisualizer


class BC_OT_create_native_alignment(bpy.types.Operator):
    """Create new native IFC alignment with automatic registration"""
    bl_idname = "bc.create_native_alignment"
    bl_label = "Create Native Alignment"
    bl_options = {'REGISTER', 'UNDO'}

    name: StringProperty(
        name="Name",
        default="Alignment",
        description="Alignment name"
    )

    def execute(self, context):
        from ..ui.alignment_properties import add_alignment_to_list, set_active_alignment
        from ..core.alignment_registry import register_alignment, register_visualizer

        # Ensure IFC file exists (create if needed)
        ifc = NativeIfcManager.get_file()
        if not ifc:
            # Create new IFC file with hierarchy if none exists
            result = NativeIfcManager.new_file()
            ifc = result['ifc_file']
            self.report({'INFO'}, "Created new IFC project")

        # Create alignment
        alignment = NativeIfcAlignment(ifc, self.name)

        # Register in property system
        add_alignment_to_list(context, alignment.alignment)
        set_active_alignment(context, alignment.alignment)

        # Register in instance registry
        register_alignment(alignment)

        # Create visualizer and store reference
        visualizer = AlignmentVisualizer(alignment)
        register_visualizer(visualizer, alignment.alignment.GlobalId)

        # CRITICAL: Store visualizer reference in alignment object for update system
        alignment.visualizer = visualizer

        self.report({'INFO'}, f"Created alignment: {self.name}")
        print(f"[Alignment] Created and registered: {self.name}")
        print(f"[Alignment] Visualizer attached for real-time updates")

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)



class BC_OT_update_pi_from_location(bpy.types.Operator):
    """Update PI in IFC from Blender location with registry integration"""
    bl_idname = "bc.update_pi_from_location"
    bl_label = "Update from Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        from ..ui.alignment_properties import get_active_alignment_ifc
        from ..core.alignment_registry import get_or_create_alignment, get_or_create_visualizer
        from ..core.native_ifc_alignment import SimpleVector

        obj = context.active_object

        if not obj or "ifc_pi_id" not in obj:
            self.report({'ERROR'}, "Select a PI marker")
            return {'CANCELLED'}

        # Get active alignment
        active_alignment_ifc = get_active_alignment_ifc(context)
        if not active_alignment_ifc:
            self.report({'ERROR'}, "No active alignment")
            return {'CANCELLED'}

        # Get or create alignment instance
        alignment_obj, _ = get_or_create_alignment(active_alignment_ifc)
        visualizer, _ = get_or_create_visualizer(alignment_obj)

        # Update IFC coordinates
        if "ifc_point_id" in obj:
            ifc = NativeIfcManager.get_file()
            point = ifc.by_id(obj["ifc_point_id"])
            point.Coordinates = [float(obj.location.x), float(obj.location.y)]

            # Update PI in alignment object
            pi_id = obj["ifc_pi_id"]
            if pi_id < len(alignment_obj.pis):
                alignment_obj.pis[pi_id]['position'] = SimpleVector(obj.location.x, obj.location.y)

            # Regenerate segments
            alignment_obj.regenerate_segments()

            # Update visualization
            visualizer.update_visualizations()

            self.report({'INFO'}, f"Updated PI {obj.name}")
            return {'FINISHED'}

        return {'CANCELLED'}




# Registration
classes = (
    BC_OT_create_native_alignment,
    BC_OT_update_pi_from_location,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
