"""
BlenderCivil v0.3.0 - User Interface Panel
Professional Alignment Tools UI

This module provides the UI panel for accessing alignment creation
and management tools in the 3D viewport sidebar.

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
from bpy.types import Panel


class CIVIL_PT_alignment(Panel):
    """Main panel for Professional Alignment Tools v2"""
    bl_label = "Professional Alignment (v0.3)"
    bl_idname = "CIVIL_PT_alignment"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    
    def draw(self, context):
        layout = self.layout
        
        # Main operators
        box = layout.box()
        box.label(text="Alignment Creation:", icon='CURVE_BEZCURVE')
        
        # Create alignment operator with properties
        col = box.column(align=True)
        op = col.operator("civil.create_alignment_separate", 
                         text="Create Professional Alignment",
                         icon='ADD')
        
        # Properties for create operator
        col = box.column(align=True)
        col.prop(context.scene, "civil_alignment_name")
        col.prop(context.scene, "civil_default_radius")
        col.prop(context.scene, "civil_design_speed")
        
        layout.separator()
        
        # Update and analysis operators
        box = layout.box()
        box.label(text="Alignment Management:", icon='FILE_REFRESH')
        
        col = box.column(align=True)
        col.operator("civil.update_alignment",
                    text="Update from PIs (Manual)",
                    icon='FILE_REFRESH')
        
        col.operator("civil.analyze_alignment",
                    text="Analyze Alignment",
                    icon='TEXT')
        
        layout.separator()
        
        # Curve Editing section
        box = layout.box()
        box.label(text="Curve Editing:", icon='CURVE_BEZCIRCLE')
        
        # Check if a curve is selected
        active_obj = context.active_object
        if (active_obj and active_obj.type == 'CURVE' and 
            hasattr(active_obj, 'alignment_curve') and
            active_obj.alignment_curve.object_type == 'ALIGNMENT_CURVE'):
            
            # Show current radius with proper units
            current_radius = active_obj.alignment_curve.radius
            col = box.column(align=True)
            col.label(text=f"Selected: {active_obj.name}")
            
            # Format radius with scene units
            unit_settings = context.scene.unit_settings
            if unit_settings.system == 'IMPERIAL':
                # Convert meters to feet
                radius_display = current_radius * 3.28084
                unit_label = "ft"
            elif unit_settings.system == 'METRIC':
                radius_display = current_radius
                unit_label = "m"
            else:  # NONE
                radius_display = current_radius
                unit_label = "units"
            
            col.label(text=f"Current Radius: {radius_display:.2f} {unit_label}")
            
            # Set radius operator
            col.operator("civil.set_curve_radius",
                        text="Set Radius",
                        icon='CURVE_BEZCIRCLE')
        else:
            box.label(text="Select a curve to edit radius", icon='INFO')
        
        layout.separator()
        
        # PI Editing operators
        box = layout.box()
        box.label(text="PI Editing:", icon='EDITMODE_HLT')
        
        col = box.column(align=True)
        col.operator("civil.insert_pi",
                    text="Insert PI",
                    icon='ADD')
        col.operator("civil.delete_pi",
                    text="Delete PI",
                    icon='REMOVE')
        
        # Instructions for PI editing
        col = box.column(align=True)
        col.scale_y = 0.8
        col.label(text="Insert: Select 2 consecutive PIs")
        col.label(text="Delete: Select 1 PI (not first/last)")


def register_properties():
    """Register scene properties for UI"""
    bpy.types.Scene.civil_alignment_name = bpy.props.StringProperty(
        name="Name",
        description="Name for the new alignment",
        default="Alignment_01"
    )
    
    bpy.types.Scene.civil_default_radius = bpy.props.FloatProperty(
        name="Default Radius",
        description="Default radius for curves",
        default=500.0,
        min=10.0,
        unit='LENGTH'
    )
    
    bpy.types.Scene.civil_design_speed = bpy.props.FloatProperty(
        name="Design Speed",
        description="Design speed in mph",
        default=35.0,
        min=5.0,
        max=120.0
    )


def unregister_properties():
    """Unregister scene properties"""
    del bpy.types.Scene.civil_alignment_name
    del bpy.types.Scene.civil_default_radius
    del bpy.types.Scene.civil_design_speed


# Registration
classes = (
    CIVIL_PT_alignment,
)


def register():
    """Register UI components"""
    register_properties()
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("âœ“ BlenderCivil v0.3.0: UI registered")


def unregister():
    """Unregister UI components"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    unregister_properties()


if __name__ == "__main__":
    register()
