"""
BlenderCivil v0.3.0 - User Interface Panels
Professional Alignment & Cross-Section Tools UI

Author: BlenderCivil Development Team
Sprint 1 Day 3: Cross-Section UI Panel
Date: October 27, 2025
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


class CIVIL_PT_cross_sections(Panel):
    """Panel for Cross-Section Template Management - Sprint 1 Day 3"""
    bl_label = "Cross Sections"
    bl_idname = "CIVIL_PT_cross_sections"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # Template Selection Section
        box = layout.box()
        box.label(text="Template Library:", icon='PRESET')
        
        # Template dropdown - show available templates
        templates = scene.cross_section_templates
        if len(templates) > 0:
            col = box.column(align=True)
            
            # Template selector
            col.prop(scene, "active_cross_section_index", text="Template")
            
            # Get the active template
            if 0 <= scene.active_cross_section_index < len(templates):
                template = templates[scene.active_cross_section_index]
                
                # Show template name
                col.label(text=f"Selected: {template.name}", icon='CHECKMARK')
                
                layout.separator()
                
                # Template Properties Section
                box = layout.box()
                box.label(text="Template Properties:", icon='PROPERTIES')
                
                # Template type and name
                col = box.column(align=True)
                col.prop(template, "template_type", text="Type")
                col.prop(template, "name", text="Name")
                
                layout.separator()
                
                # Lanes Section
                box = layout.box()
                box.label(text="◯ Lanes", icon='MESH_GRID')
                
                row = box.row(align=True)
                col = row.column(align=True)
                col.label(text="Left:")
                col.prop(template.lanes_left, "count", text="Count")
                col.prop(template.lanes_left, "width", text="Width")
                
                col = row.column(align=True)
                col.label(text="Right:")
                col.prop(template.lanes_right, "count", text="Count")
                col.prop(template.lanes_right, "width", text="Width")
                
                layout.separator()
                
                # Shoulders Section
                box = layout.box()
                box.label(text="◯ Shoulders", icon='MOD_ARRAY')
                
                row = box.row(align=True)
                col = row.column(align=True)
                col.label(text="Left:")
                col.prop(template.shoulder_left, "width", text="Width")
                col.prop(template.shoulder_left, "slope", text="Slope", slider=True)
                # Show slope as percentage
                slope_pct = template.shoulder_left.slope * 100
                col.label(text=f"({slope_pct:.1f}%)")
                
                col = row.column(align=True)
                col.label(text="Right:")
                col.prop(template.shoulder_right, "width", text="Width")
                col.prop(template.shoulder_right, "slope", text="Slope", slider=True)
                slope_pct = template.shoulder_right.slope * 100
                col.label(text=f"({slope_pct:.1f}%)")
                
                layout.separator()
                
                # Crown/Cross Slope Section
                box = layout.box()
                box.label(text="◯ Crown/Cross Slope", icon='DRIVER_ROTATIONAL_DIFFERENCE')
                
                col = box.column(align=True)
                col.prop(template, "crown_type", text="Type")
                col.prop(template, "crown_rate", text="Rate", slider=True)
                crown_pct = template.crown_rate * 100
                col.label(text=f"({crown_pct:.1f}%)")
                
                layout.separator()
                
                # Median Section (if applicable)
                box = layout.box()
                row = box.row()
                row.prop(template, "has_median", text="Has Median")
                
                if template.has_median:
                    col = box.column(align=True)
                    col.prop(template.median, "width", text="Width")
                    col.prop(template.median, "type", text="Type")
                
                layout.separator()
                
                # Station Range Section
                box = layout.box()
                box.label(text="Station Range:", icon='TRACKING')
                col = box.column(align=True)
                col.prop(template, "start_station", text="Start")
                col.prop(template, "end_station", text="End")
                
                layout.separator()
                
                # Action Buttons
                box = layout.box()
                col = box.column(align=True)
                col.scale_y = 1.2
                
                # Save modifications
                col.operator("blendercivil.save_template_changes",
                           text="Save Changes",
                           icon='FILE_TICK')
                
                # Duplicate template
                col.operator("blendercivil.duplicate_template",
                           text="Duplicate Template",
                           icon='DUPLICATE')
                
                # Delete template
                col.operator("blendercivil.delete_template",
                           text="Delete Template",
                           icon='TRASH')
                
        else:
            # No templates available
            col = box.column(align=True)
            col.label(text="No templates available", icon='INFO')
            col.label(text="Create standard templates below")
        
        layout.separator()
        
        # Template Creation Section
        box = layout.box()
        box.label(text="Create Templates:", icon='ADD')
        
        col = box.column(align=True)
        
        # Quick create all standard templates
        col.operator("blendercivil.create_all_templates",
                    text="Create All Standard Templates",
                    icon='PRESET')
        
        col.separator()
        
        # Individual template creation
        col.label(text="Or create individual:")
        col.operator("blendercivil.create_standard_template",
                    text="Rural 2-Lane",
                    icon='ADD').template_type = 'RURAL_2LANE'
        col.operator("blendercivil.create_standard_template",
                    text="Urban 4-Lane Arterial",
                    icon='ADD').template_type = 'URBAN_4LANE'
        col.operator("blendercivil.create_standard_template",
                    text="Highway Divided",
                    icon='ADD').template_type = 'HIGHWAY_DIVIDED'
        col.operator("blendercivil.create_standard_template",
                    text="Local Street + Parking",
                    icon='ADD').template_type = 'LOCAL_PARKING'
        col.operator("blendercivil.create_standard_template",
                    text="Complete Street + Bike",
                    icon='ADD').template_type = 'BIKE_LANE'
        
        layout.separator()
        
        layout.separator()
        
        # Section Assignments - Day 4
        box = layout.box()
        box.label(text="Section Assignments:", icon='SORTSIZE')
        
        obj = context.active_object
        if obj and hasattr(obj, 'section_assignments') and hasattr(obj, 'alignment_root'):
            if obj.alignment_root:
                # Show assignments for this alignment
                assignments = obj.section_assignments
                
                if len(assignments) > 0:
                    # List existing assignments
                    col = box.column(align=True)
                    for idx, assignment in enumerate(assignments):
                        row = col.row(align=True)
                        
                        # Show assignment info
                        template_name = "Unknown"
                        if assignment.template_index < len(scene.cross_section_templates):
                            template_name = scene.cross_section_templates[assignment.template_index].name
                        
                        row.label(text=f"#{idx+1}: {template_name}", icon='MESH_DATA')
                        row.label(text=f"Sta {assignment.start_station:.1f}-{assignment.end_station:.1f}")
                        
                        # Remove button
                        op = row.operator("blendercivil.remove_section_assignment", 
                                        text="", icon='X')
                        op.index = idx
                    
                    layout.separator()
                
                # Add new assignment
                col = box.column(align=True)
                col.label(text="Add New Section:", icon='ADD')
                
                # Template selector for assignment
                row = col.row(align=True)
                row.prop(scene, "active_cross_section_index", text="Template")
                
                # Add button
                op = col.operator("blendercivil.add_section_assignment",
                                text="Add Section Assignment",
                                icon='LINKED')
                op.template_index = scene.active_cross_section_index
                
            else:
                col = box.column()
                col.label(text="Select an alignment object", icon='INFO')
        else:
            col = box.column()
            col.label(text="Select an alignment object", icon='INFO')



def draw_template_selector(layout, scene):
    """Helper function to draw template selector dropdown"""
    templates = scene.cross_section_templates
    
    if len(templates) == 0:
        layout.label(text="No templates", icon='INFO')
        return None
    
    # Create a dropdown-style selector
    items = [(str(i), t.name, f"{t.template_type}: {t.name}") 
             for i, t in enumerate(templates)]
    
    layout.prop(scene, "active_cross_section_index", text="")
    
    if 0 <= scene.active_cross_section_index < len(templates):
        return templates[scene.active_cross_section_index]
    
    return None


def register_properties():
    """Register scene properties for UI"""
    # Alignment properties
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
    
    # Cross-section properties
    bpy.types.Scene.active_cross_section_index = bpy.props.IntProperty(
        name="Active Template",
        description="Currently selected cross-section template",
        default=0,
        min=0
    )


def unregister_properties():
    """Unregister scene properties"""
    del bpy.types.Scene.civil_alignment_name
    del bpy.types.Scene.civil_default_radius
    del bpy.types.Scene.civil_design_speed
    del bpy.types.Scene.active_cross_section_index


# ============================================================================
# GEOREFERENCING PANEL
# ============================================================================

class CIVIL_PT_Georeferencing(bpy.types.Panel):
    """Panel for managing georeferencing"""
    bl_label = "Georeferencing"
    bl_idname = "CIVIL_PT_georeferencing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Civil'
    bl_order = 2  # After Alignment panel
    
    def draw(self, context):
        layout = self.layout
        georef = context.scene.bc_georeferencing
        
        # Status indicator
        if georef.is_georeferenced:
            box = layout.box()
            box.label(text="[X] Georeferenced", icon='WORLD')
            
            col = box.column(align=True)
            col.label(text=f"CRS: {georef.crs_name}")
            col.label(text=f"EPSG: {georef.epsg_code}")
            
            col.separator()
            col.label(text="False Origin:")
            col.label(text=f"  E: {georef.false_easting:,.0f}m")
            col.label(text=f"  N: {georef.false_northing:,.0f}m")
            col.label(text=f"  El: {georef.false_elevation:,.0f}m")
            
            # Precision info
            if georef.max_distance_from_origin > 0:
                ok, prec_mm, warning = self._verify_precision_display(georef.max_distance_from_origin)
                col.separator()
                if ok:
                    col.label(text=f"[X] Precision: {prec_mm:.4f}mm", icon='CHECKMARK')
                else:
                    col.label(text=f"[!] Precision: {prec_mm:.2f}mm", icon='ERROR')
        else:
            box = layout.box()
            box.label(text="Not Georeferenced", icon='QUESTION')
            box.label(text="Setup georeferencing to work")
            box.label(text="with real-world coordinates")
        
        # Setup button
        layout.separator()
        row = layout.row()
        row.scale_y = 1.5
        if georef.is_georeferenced:
            row.operator("civil.setup_georeferencing", text="Update Georeferencing", icon='FILE_REFRESH')
        else:
            row.operator("civil.setup_georeferencing", text="Setup Georeferencing", icon='WORLD_DATA')
        
        # Tools
        if georef.is_georeferenced:
            layout.separator()
            col = layout.column(align=True)
            col.label(text="Tools:")
            col.operator("civil.auto_calculate_false_origin", icon='PIVOT_MEDIAN')
            col.operator("civil.verify_precision", icon='CHECKMARK')
            
            # Import/Export
            col.separator()
            col.label(text="Import/Export:")
            col.operator("civil.import_landxml", text="Import LandXML", icon='IMPORT')
            col.operator("civil.export_landxml", text="Export LandXML", icon='EXPORT')
            
            if context.active_object:
                col.operator("civil.show_coordinate_info", icon='INFO')
            
            col.separator()
            col.operator("civil.clear_georeferencing", icon='X')
    
    def _verify_precision_display(self, max_dist):
        """Helper to verify precision for display"""
        import sys
        import os
        addon_path = os.path.dirname(__file__)
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        from core.georeferencing import GeoreferencingUtils
        return GeoreferencingUtils.verify_precision(max_dist)



# Registration



classes = (
    CIVIL_PT_Georeferencing,
    CIVIL_PT_alignment,
    CIVIL_PT_cross_sections,
)


def register():
    """Register UI components"""
    register_properties()
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("✓ BlenderCivil v0.3.0: UI registered (with Cross Sections panel)")


def unregister():
    """Unregister UI components"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    unregister_properties()


if __name__ == "__main__":
    register()