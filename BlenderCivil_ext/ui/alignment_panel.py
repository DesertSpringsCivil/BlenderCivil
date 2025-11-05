"""
Alignment Panel - REVISED
Separate PI and Curve tools following professional civil engineering practice
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty

# Import from parent ui module
from . import NativeIfcManager


class VIEW3D_PT_native_ifc_alignment(bpy.types.Panel):
    """Native IFC Alignment Tools"""
    bl_label = "Horizontal Alignment"
    bl_idname = "VIEW3D_PT_native_ifc_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "BlenderCivil"
    
    def draw(self, context):
        layout = self.layout
        
        # IFC File Status
        box = layout.box()
        box.label(text="IFC File", icon='FILE')
        
        ifc = NativeIfcManager.file
        if ifc:
            col = box.column(align=True)
            col.label(text=f"Schema: {ifc.schema}")
            
            # Count entities
            alignments = ifc.by_type("IfcAlignment")
            col.label(text=f"Alignments: {len(alignments)}")
        else:
            box.label(text="No IFC file loaded")
            box.operator("bc.new_ifc_file", text="Create New IFC")
        
        # Alignment Tools
        box = layout.box()
        box.label(text="Alignment", icon='CURVE_DATA')
        
        col = box.column(align=True)
        col.operator("bc.create_native_alignment", text="New Alignment", icon='ADD')
        
        # Active Alignment Info
        props = context.scene.bc_alignment
        if props.active_alignment_id:
            col.separator()
            
            # Active alignment indicator
            row = col.row()
            row.label(text=f"Active: {props.active_alignment_name}", icon='RADIOBUT_ON')
            
            # Refresh button
            row.operator("bc.refresh_alignment_list", text="", icon='FILE_REFRESH')
            
            # Show alignment stats if available
            active_item = None
            if props.active_alignment_index >= 0 and props.active_alignment_index < len(props.alignments):
                active_item = props.alignments[props.active_alignment_index]
            
            if active_item:
                sub = col.column(align=True)
                sub.scale_y = 0.8
                sub.label(text=f"  PIs: {active_item.pi_count}")
                sub.label(text=f"  Segments: {active_item.segment_count}")
                if active_item.total_length > 0:
                    sub.label(text=f"  Length: {active_item.total_length:.2f}m")
        else:
            col.separator()
            col.label(text="No active alignment", icon='ERROR')
        
        # Active object info (if selected)
        if context.active_object and "ifc_definition_id" in context.active_object:
            col.separator()
            col.label(text="Selected: " + context.active_object.name, icon='OBJECT_DATA')
            
            entity = NativeIfcManager.get_entity(context.active_object)
            if entity:
                col.label(text=f"Type: {entity.is_a()}")
                col.label(text=f"GlobalId: {entity.GlobalId[:8]}...")
        
        # ==================== PI TOOLS ====================
        box = layout.box()
        box.label(text="PI Tools (Tangent Points)", icon='EMPTY_DATA')
        
        col = box.column(align=True)
        
        # PRIMARY: Interactive PI placement
        row = col.row(align=True)
        row.scale_y = 1.3
        op = row.operator("bc.add_pi_interactive", text="📍 Click to Place PIs", icon='HAND')
        
        col.separator()
        
        # Secondary PI tools
        col.label(text="Edit PIs:", icon='PREFERENCES')
        row = col.row(align=True)
        row.operator("bc.add_native_pi", text="Add at Cursor", icon='CURSOR')
        row.operator("bc.delete_native_pi", text="Delete", icon='X')
        
        col.separator()
        col.operator("bc.update_pi_from_location", text="Update from Location", icon='FILE_REFRESH')
        
        # Display PI info if selected
        if context.active_object and "ifc_pi_id" in context.active_object:
            pi_box = box.box()
            obj = context.active_object
            
            col = pi_box.column(align=True)
            col.label(text=f"Selected: {obj.name}", icon='DECORATE_KEYFRAME')
            
            if "ifc_point_id" in obj:
                ifc = NativeIfcManager.get_file()
                if ifc:
                    point = ifc.by_id(obj["ifc_point_id"])
                    coords = point.Coordinates
                    col.label(text=f"Location: ({coords[0]:.2f}, {coords[1]:.2f})")
                    col.label(text=f"PI Index: {obj['ifc_pi_id']}")
        
        # ==================== CURVE TOOLS ====================
        box = layout.box()
        box.label(text="Curve Tools", icon='SPHERECURVE')
        
        col = box.column(align=True)
        
        # PRIMARY: Interactive curve insertion
        row = col.row(align=True)
        row.scale_y = 1.3
        op = row.operator("bc.add_curve_interactive", text="🔄 Add Curve", icon='HAND')
        
        col.separator()
        
        # Secondary curve tools
        col.label(text="Edit Curves:", icon='PREFERENCES')
        row = col.row(align=True)
        row.operator("bc.edit_curve_radius", text="Edit Radius", icon='DRIVER_DISTANCE')
        row.operator("bc.delete_curve", text="Delete", icon='X')
        
        # Display curve info if selected
        if context.active_object and context.active_object.type == 'CURVE':
            if "Curve" in context.active_object.name:
                curve_box = box.box()
                obj = context.active_object
                
                col = curve_box.column(align=True)
                col.label(text=f"Selected: {obj.name}", icon='CURVE_DATA')
                
                # Show curve parameters if available from IFC
                if "ifc_definition_id" in obj:
                    ifc = NativeIfcManager.get_file()
                    if ifc:
                        entity = ifc.by_id(obj["ifc_definition_id"])
                        if entity:
                            params = entity.DesignParameters
                            if params:
                                col.label(text=f"Radius: {abs(params.StartRadiusOfCurvature):.2f}m")
                                col.label(text=f"Length: {params.SegmentLength:.2f}m")
                                
                                # Determine turn direction
                                if params.StartRadiusOfCurvature > 0:
                                    col.label(text="Turn: LEFT (CCW)", icon='LOOP_BACK')
                                else:
                                    col.label(text="Turn: RIGHT (CW)", icon='LOOP_FORWARDS')


# Registration
classes = (
    VIEW3D_PT_native_ifc_alignment,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
