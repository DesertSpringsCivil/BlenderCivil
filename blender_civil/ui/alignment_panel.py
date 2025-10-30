"""
Alignment Panel
Main UI panel for IFC alignment operations
"""

import bpy
from bpy.props import StringProperty, FloatProperty, IntProperty, BoolProperty


class VIEW3D_PT_native_ifc_alignment(bpy.types.Panel):
    """Native IFC Alignment Tools"""
    bl_label = "Native IFC Alignment"
    bl_idname = "VIEW3D_PT_native_ifc_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Native IFC"
    
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
        col.operator("bc.create_native_alignment", text="New Alignment")
        
        # Active object info
        if context.active_object and "ifc_definition_id" in context.active_object:
            col.separator()
            col.label(text="Active: " + context.active_object.name)
            
            entity = NativeIfcManager.get_entity(context.active_object)
            if entity:
                col.label(text=f"Type: {entity.is_a()}")
                col.label(text=f"GlobalId: {entity.GlobalId[:8]}...")
        
        # PI Tools
        box = layout.box()
        box.label(text="PI Tools", icon='EMPTY_DATA')
        
        col = box.column(align=True)
        col.operator("bc.add_native_pi", text="Add PI")
        col.operator("bc.update_pi_from_location", text="Update from Location")
        col.operator("bc.delete_native_pi", text="Delete PI")
        
        # Display PI info if selected
        if context.active_object and "ifc_pi_id" in context.active_object:
            pi_box = box.box()
            obj = context.active_object
            
            col = pi_box.column(align=True)
            col.label(text=f"PI: {obj.name}")
            col.prop(obj, '["radius"]', text="Radius")
            
            if "ifc_point_id" in obj:
                ifc = NativeIfcManager.get_file()
                if ifc:
                    point = ifc.by_id(obj["ifc_point_id"])
                    coords = point.Coordinates
                    col.label(text=f"IFC: ({coords[0]:.3f}, {coords[1]:.3f})")




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
