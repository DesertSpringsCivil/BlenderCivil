"""
BlenderCivil - Cross-Section Operators
Sprint 1 Day 2: Template Management Operators
"""

import bpy
from bpy.types import Operator


def get_templates_module():
    """Safely import the templates module"""
    import sys
    import os
    
    # Get the addon root path
    current_dir = os.path.dirname(__file__)
    addon_path = os.path.dirname(current_dir)
    
    if addon_path not in sys.path:
        sys.path.insert(0, addon_path)
    
    # Import and reload if needed
    import importlib
    if 'templates' in sys.modules:
        importlib.reload(sys.modules['templates'])
    
    import templates
    return templates


class BLENDERCIVIL_OT_create_standard_template(Operator):
    """Create a standard cross-section template"""
    bl_idname = "blendercivil.create_standard_template"
    bl_label = "Create Standard Template"
    bl_options = {'REGISTER', 'UNDO'}
    
    template_type: bpy.props.EnumProperty(
        name="Template Type",
        items=[
            ('RURAL_2LANE', 'Rural 2-Lane', 'Standard rural 2-lane highway'),
            ('URBAN_4LANE', 'Urban 4-Lane Arterial', 'Urban arterial with curb & gutter'),
            ('HIGHWAY_DIVIDED', 'Highway Divided 4-Lane', 'Divided highway with median'),
            ('LOCAL_PARKING', 'Local Street with Parking', 'Residential street with parking'),
            ('BIKE_LANE', 'Complete Street with Bike Lanes', 'Urban street with bike lanes'),
        ],
        default='RURAL_2LANE'
    )
    
    def execute(self, context):
        templates = get_templates_module()
        scene = context.scene
        
        # Create the requested template
        if self.template_type == 'RURAL_2LANE':
            template = templates.create_rural_2lane_template(scene)
        elif self.template_type == 'URBAN_4LANE':
            template = templates.create_urban_4lane_arterial_template(scene)
        elif self.template_type == 'HIGHWAY_DIVIDED':
            template = templates.create_highway_divided_template(scene)
        elif self.template_type == 'LOCAL_PARKING':
            template = templates.create_local_street_parking_template(scene)
        elif self.template_type == 'BIKE_LANE':
            template = templates.create_bike_lane_template(scene)
        
        self.report({'INFO'}, f"Created template: {template.name}")
        return {'FINISHED'}


class BLENDERCIVIL_OT_create_all_templates(Operator):
    """Create all 5 standard templates at once"""
    bl_idname = "blendercivil.create_all_templates"
    bl_label = "Create All Standard Templates"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        templates = get_templates_module()
        scene = context.scene
        created = templates.create_all_standard_templates(scene)
        
        self.report({'INFO'}, f"Created {len(created)} standard templates")
        return {'FINISHED'}


class BLENDERCIVIL_OT_delete_template(Operator):
    """Delete a cross-section template"""
    bl_idname = "blendercivil.delete_template"
    bl_label = "Delete Template"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        scene = context.scene
        
        if 0 <= self.index < len(scene.cross_section_templates):
            template_name = scene.cross_section_templates[self.index].name
            scene.cross_section_templates.remove(self.index)
            self.report({'INFO'}, f"Deleted template: {template_name}")
        else:
            self.report({'ERROR'}, "Invalid template index")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BLENDERCIVIL_OT_duplicate_template(Operator):
    """Duplicate a cross-section template"""
    bl_idname = "blendercivil.duplicate_template"
    bl_label = "Duplicate Template"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        scene = context.scene
        
        if 0 <= self.index < len(scene.cross_section_templates):
            source = scene.cross_section_templates[self.index]
            new_template = scene.cross_section_templates.add()
            
            # Copy properties
            new_template.name = source.name + " Copy"
            new_template.template_type = source.template_type
            new_template.description = source.description
            new_template.symmetrical = source.symmetrical
            new_template.crown_type = source.crown_type
            new_template.start_station = source.start_station
            new_template.end_station = source.end_station
            
            # Copy lanes
            new_template.lanes_left.count = source.lanes_left.count
            new_template.lanes_left.width = source.lanes_left.width
            new_template.lanes_left.cross_slope = source.lanes_left.cross_slope
            new_template.lanes_right.count = source.lanes_right.count
            new_template.lanes_right.width = source.lanes_right.width
            new_template.lanes_right.cross_slope = source.lanes_right.cross_slope
            
            # Copy shoulders
            new_template.shoulder_left.width = source.shoulder_left.width
            new_template.shoulder_left.slope = source.shoulder_left.slope
            new_template.shoulder_left.type = source.shoulder_left.type
            new_template.shoulder_right.width = source.shoulder_right.width
            new_template.shoulder_right.slope = source.shoulder_right.slope
            new_template.shoulder_right.type = source.shoulder_right.type
            
            # Copy median
            new_template.has_median = source.has_median
            if source.has_median:
                new_template.median.width = source.median.width
                new_template.median.type = source.median.type
                new_template.median.left_slope = source.median.left_slope
                new_template.median.right_slope = source.median.right_slope
            
            self.report({'INFO'}, f"Duplicated template: {source.name}")
        else:
            self.report({'ERROR'}, "Invalid template index")
            return {'CANCELLED'}
        
        return {'FINISHED'}




class BLENDERCIVIL_OT_export_templates(Operator):
    """Export all templates to a JSON file"""
    bl_idname = "blendercivil.export_templates"
    bl_label = "Export Template Library"
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filename: bpy.props.StringProperty(default="BlenderCivil_Templates.json")
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        import sys
        import os
        addon_path = os.path.dirname(os.path.dirname(__file__))
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        import importlib
        if 'persistence' in sys.modules:
            importlib.reload(sys.modules['persistence'])
        import persistence
        
        scene = context.scene
        
        if len(scene.cross_section_templates) == 0:
            self.report({'ERROR'}, "No templates to export")
            return {'CANCELLED'}
        
        try:
            persistence.export_scene_templates(scene, self.filepath)
            count = len(scene.cross_section_templates)
            self.report({'INFO'}, f"Exported {count} templates to {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BLENDERCIVIL_OT_import_templates(Operator):
    """Import templates from a JSON file"""
    bl_idname = "blendercivil.import_templates"
    bl_label = "Import Template Library"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    replace: bpy.props.BoolProperty(
        name="Replace Existing",
        description="Replace all existing templates",
        default=False
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        import sys
        import os
        addon_path = os.path.dirname(os.path.dirname(__file__))
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        import importlib
        if 'persistence' in sys.modules:
            importlib.reload(sys.modules['persistence'])
        import persistence
        
        scene = context.scene
        
        try:
            loaded = persistence.import_templates_to_scene(scene, self.filepath, self.replace)
            action = "Replaced with" if self.replace else "Imported"
            self.report({'INFO'}, f"{action} {len(loaded)} templates")
        except Exception as e:
            self.report({'ERROR'}, f"Import failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BLENDERCIVIL_OT_save_template(Operator):
    """Save the current template to a JSON file"""
    bl_idname = "blendercivil.save_template"
    bl_label = "Save Template"
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    
    def invoke(self, context, event):
        scene = context.scene
        if 0 <= scene.active_cross_section_index < len(scene.cross_section_templates):
            template = scene.cross_section_templates[scene.active_cross_section_index]
            
            # Set default filename
            import sys
            import os
            addon_path = os.path.dirname(os.path.dirname(__file__))
            if addon_path not in sys.path:
                sys.path.insert(0, addon_path)
            import persistence
            
            self.filepath = persistence.get_template_filepath(template.name)
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        import sys
        import os
        addon_path = os.path.dirname(os.path.dirname(__file__))
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        import importlib
        if 'persistence' in sys.modules:
            importlib.reload(sys.modules['persistence'])
        import persistence
        
        scene = context.scene
        
        if scene.active_cross_section_index < 0 or scene.active_cross_section_index >= len(scene.cross_section_templates):
            self.report({'ERROR'}, "No template selected")
            return {'CANCELLED'}
        
        template = scene.cross_section_templates[scene.active_cross_section_index]
        
        try:
            persistence.save_template_to_file(template, self.filepath)
            self.report({'INFO'}, f"Saved template: {template.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Save failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class BLENDERCIVIL_OT_load_template(Operator):
    """Load a template from a JSON file"""
    bl_idname = "blendercivil.load_template"
    bl_label = "Load Template"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        import sys
        import os
        addon_path = os.path.dirname(os.path.dirname(__file__))
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        import importlib
        if 'persistence' in sys.modules:
            importlib.reload(sys.modules['persistence'])
        import persistence
        
        scene = context.scene
        
        try:
            template = persistence.load_template_from_file(self.filepath, scene)
            self.report({'INFO'}, f"Loaded template: {template.name}")
        except Exception as e:
            self.report({'ERROR'}, f"Load failed: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}




class BLENDERCIVIL_OT_add_section_assignment(Operator):
    """Add a cross-section assignment to the selected alignment"""
    bl_idname = "blendercivil.add_section_assignment"
    bl_label = "Add Section Assignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    template_index: bpy.props.IntProperty(
        name="Template",
        description="Index of template to assign",
        default=0,
        min=0
    )
    
    start_station: bpy.props.FloatProperty(
        name="Start Station",
        description="Starting station",
        default=0.0,
        unit='LENGTH'
    )
    
    end_station: bpy.props.FloatProperty(
        name="End Station",
        description="Ending station",
        default=1000.0,
        unit='LENGTH'
    )
    
    @classmethod
    def poll(cls, context):
        """Only active if alignment object selected"""
        obj = context.active_object
        return obj and hasattr(obj, 'alignment_root') and obj.alignment_root
    
    def invoke(self, context, event):
        """Show dialog before executing"""
        scene = context.scene
        obj = context.active_object
        
        # Use currently selected template from scene
        if hasattr(scene, 'active_cross_section_index'):
            self.template_index = scene.active_cross_section_index
        
        # Set defaults based on existing assignments
        if obj and hasattr(obj, 'section_assignments'):
            assignments = obj.section_assignments
            if len(assignments) > 0:
                # Start where last assignment ended
                last = assignments[-1]
                self.start_station = last.end_station
                self.end_station = last.end_station + 1000.0
        
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        """Add section assignment"""
        obj = context.active_object
        
        # Validate stations
        if self.end_station <= self.start_station:
            self.report({'ERROR'}, "End station must be greater than start station")
            return {'CANCELLED'}
        
        # Check template exists
        templates = context.scene.cross_section_templates
        if self.template_index >= len(templates):
            self.report({'ERROR'}, "Invalid template index")
            return {'CANCELLED'}
        
        # Add new assignment
        assignment = obj.section_assignments.add()
        assignment.template_index = self.template_index
        assignment.start_station = self.start_station
        assignment.end_station = self.end_station
        assignment.description = f"{templates[self.template_index].name}: {self.start_station:.2f} - {self.end_station:.2f}"
        
        self.report({'INFO'}, f"Added section assignment: Station {self.start_station:.2f} to {self.end_station:.2f}")
        return {'FINISHED'}


class BLENDERCIVIL_OT_remove_section_assignment(Operator):
    """Remove a cross-section assignment"""
    bl_idname = "blendercivil.remove_section_assignment"
    bl_label = "Remove Section Assignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    index: bpy.props.IntProperty(
        name="Index",
        description="Index of assignment to remove",
        default=0,
        min=0
    )
    
    @classmethod
    def poll(cls, context):
        """Only active if alignment object selected with assignments"""
        obj = context.active_object
        return (obj and hasattr(obj, 'section_assignments') and 
                len(obj.section_assignments) > 0)
    
    def execute(self, context):
        """Remove section assignment"""
        obj = context.active_object
        
        if self.index < 0 or self.index >= len(obj.section_assignments):
            self.report({'ERROR'}, "Invalid assignment index")
            return {'CANCELLED'}
        
        obj.section_assignments.remove(self.index)
        self.report({'INFO'}, f"Removed section assignment at index {self.index}")
        return {'FINISHED'}


# Registration
classes = (
    BLENDERCIVIL_OT_create_standard_template,
    BLENDERCIVIL_OT_create_all_templates,
    BLENDERCIVIL_OT_delete_template,
    BLENDERCIVIL_OT_duplicate_template,
    BLENDERCIVIL_OT_export_templates,
    BLENDERCIVIL_OT_import_templates,
    BLENDERCIVIL_OT_save_template,
    BLENDERCIVIL_OT_load_template,
    BLENDERCIVIL_OT_add_section_assignment,
    BLENDERCIVIL_OT_remove_section_assignment,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("✅ Cross-section operators registered")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
