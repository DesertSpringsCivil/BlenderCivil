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


class CIVIL_PT_alignment_v2(Panel):
    """Main panel for Professional Alignment Tools v2"""
    bl_label = "Professional Alignment (v0.3)"
    bl_idname = "CIVIL_PT_alignment_v2"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    
    def draw(self, context):
        layout = self.layout
        
        # Header with version
        box = layout.box()
        box.label(text="BlenderCivil v0.3.0", icon='OUTLINER_OB_CURVE')
        box.label(text="IFC-Compatible Separate Entities")
        
        layout.separator()
        
        # Instructions
        box = layout.box()
        box.label(text="Quick Start:", icon='INFO')
        col = box.column(align=True)
        col.label(text="1. Create PI points (Empties named PI_*)")
        col.label(text="2. Position PIs along desired route")
        col.label(text="3. Click 'Create Alignment'")
        col.label(text="4. Move PIs with G key (auto-updates!)")
        
        layout.separator()
        
        # Main operators
        box = layout.box()
        box.label(text="Alignment Creation:", icon='CURVE_BEZCURVE')
        
        # Create alignment operator with properties
        col = box.column(align=True)
        op = col.operator("civil.create_alignment_separate_v2", 
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
        col.operator("civil.update_alignment_v2",
                    text="Update from PIs (Manual)",
                    icon='FILE_REFRESH')
        
        col.operator("civil.analyze_alignment_v2",
                    text="Analyze Alignment",
                    icon='TEXT')
        
        layout.separator()
        
        # Auto-update status
        box = layout.box()
        box.label(text="Auto-Update Status:", icon='SETTINGS')
        
        # Find alignment roots in scene
        alignment_roots = [obj for obj in context.scene.objects
                          if obj.type == 'EMPTY' and hasattr(obj, 'alignment_root')
                          and obj.alignment_root.object_type == 'ALIGNMENT_ROOT']
        
        if alignment_roots:
            for root in alignment_roots:
                row = box.row()
                row.label(text=root.name)
                row.prop(root.alignment_root, "auto_update_enabled", 
                        text="Auto-Update" if root.alignment_root.auto_update_enabled else "Manual Only",
                        toggle=True)
        else:
            box.label(text="No alignments in scene", icon='INFO')
        
        layout.separator()
        
        # Status information
        box = layout.box()
        box.label(text="Scene Status:", icon='OUTLINER')
        
        # Count PIs
        pis = [obj for obj in context.scene.objects 
               if obj.type == 'EMPTY' and obj.name.startswith('PI_')]
        box.label(text=f"PI Points: {len(pis)}")
        box.label(text=f"Alignments: {len(alignment_roots)}")
        
        if alignment_roots:
            total_length = sum(root.alignment_root.total_length for root in alignment_roots)
            box.label(text=f"Total Length: {total_length:.2f}")


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
    CIVIL_PT_alignment_v2,
)


def register():
    """Register UI components"""
    register_properties()
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("✓ BlenderCivil v0.3.0: UI registered")


def unregister():
    """Unregister UI components"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    unregister_properties()


if __name__ == "__main__":
    register()
