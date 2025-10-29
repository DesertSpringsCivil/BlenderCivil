"""
BlenderCivil - Georeferencing Operators

Operators for managing georeferencing:
- Setup and configure georeferencing
- Auto-calculate false origin
- Verify precision
- Display coordinate information
- Import/Export LandXML

Author: BlenderCivil Development Team
Date: October 28, 2025
"""

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, StringProperty, IntProperty, BoolProperty
from mathutils import Vector
import sys
import os

# Import georeferencing utilities
addon_path = os.path.dirname(os.path.dirname(__file__))
if addon_path not in sys.path:
    sys.path.insert(0, addon_path)

from core.georeferencing import GeoreferencingUtils


# ============================================================================
# SETUP OPERATORS
# ============================================================================

class CIVIL_OT_SetupGeoreferencing(Operator):
    """Setup georeferencing for the project"""
    bl_idname = "civil.setup_georeferencing"
    bl_label = "Setup Georeferencing"
    bl_description = "Configure coordinate reference system and false origin"
    bl_options = {'REGISTER', 'UNDO'}
    
    crs_name: StringProperty(
        name="CRS Name",
        default="NAD83 / UTM zone 10N",
        description="Coordinate reference system name"
    )
    
    epsg_code: IntProperty(
        name="EPSG Code",
        default=26910,
        min=0,
        description="EPSG code (e.g., 26910 for NAD83 UTM 10N)"
    )
    
    auto_calculate: BoolProperty(
        name="Auto-Calculate False Origin",
        default=True,
        description="Automatically calculate false origin from scene objects"
    )
    
    false_easting: FloatProperty(
        name="False Easting",
        default=500000.0,
        precision=3,
        description="False origin easting (meters)"
    )
    
    false_northing: FloatProperty(
        name="False Northing",
        default=4000000.0,
        precision=3,
        description="False origin northing (meters)"
    )
    
    false_elevation: FloatProperty(
        name="False Elevation",
        default=0.0,
        precision=3,
        description="False origin elevation (meters)"
    )
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        
        # Set CRS properties
        georef.crs_name = self.crs_name
        georef.epsg_code = self.epsg_code
        georef.scale_factor = 1.0
        georef.rotation_angle = 0.0
        
        # Handle false origin
        if self.auto_calculate:
            # Collect all object locations
            locations = []
            for obj in context.scene.objects:
                if obj.type in {'MESH', 'CURVE', 'EMPTY'}:
                    locations.append(Vector(obj.location))
            
            if locations:
                # Calculate optimal false origin
                false_origin = GeoreferencingUtils.calculate_optimal_false_origin(locations)
                georef.false_easting = false_origin.x
                georef.false_northing = false_origin.y
                georef.false_elevation = false_origin.z
                
                self.report({'INFO'}, 
                    f"Georeferencing setup with auto-calculated false origin: "
                    f"E:{false_origin.x:.0f}, N:{false_origin.y:.0f}")
            else:
                # No objects, use manual values
                georef.false_easting = self.false_easting
                georef.false_northing = self.false_northing
                georef.false_elevation = self.false_elevation
                
                self.report({'WARNING'}, 
                    "No objects found for auto-calculation. Using manual values.")
        else:
            # Use manual values
            georef.false_easting = self.false_easting
            georef.false_northing = self.false_northing
            georef.false_elevation = self.false_elevation
            
            self.report({'INFO'}, 
                f"Georeferencing setup: {self.crs_name} (EPSG:{self.epsg_code})")
        
        georef.is_georeferenced = True
        
        # Update rotation components
        georef.update_rotation_components()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        georef = context.scene.bc_georeferencing
        
        # Pre-fill with existing values if already set
        if georef.is_georeferenced:
            self.crs_name = georef.crs_name
            self.epsg_code = georef.epsg_code
            self.false_easting = georef.false_easting
            self.false_northing = georef.false_northing
            self.false_elevation = georef.false_elevation
            self.auto_calculate = False  # Default to manual when updating
        else:
            # Check if we have objects to auto-calculate from
            has_objects = any(obj.type in {'MESH', 'CURVE', 'EMPTY'} 
                            for obj in context.scene.objects)
            self.auto_calculate = has_objects  # Auto-enable if objects exist
        
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        """Custom dialog layout"""
        layout = self.layout
        
        # CRS Section
        box = layout.box()
        box.label(text="Coordinate Reference System:", icon='WORLD')
        box.prop(self, "crs_name")
        box.prop(self, "epsg_code")
        
        # False Origin Section
        box = layout.box()
        box.label(text="False Origin:", icon='EMPTY_AXIS')
        
        # Auto-calculate checkbox
        row = box.row()
        row.prop(self, "auto_calculate")
        
        # Show count of objects if auto-calculate enabled
        if self.auto_calculate:
            obj_count = sum(1 for obj in context.scene.objects 
                          if obj.type in {'MESH', 'CURVE', 'EMPTY'})
            row = box.row()
            row.label(text=f"Will calculate from {obj_count} objects", icon='INFO')
        
        # Manual entry fields (disabled if auto-calculate)
        col = box.column()
        col.enabled = not self.auto_calculate
        col.prop(self, "false_easting")
        col.prop(self, "false_northing")
        col.prop(self, "false_elevation")
        
        if not self.auto_calculate:
            row = box.row()
            row.label(text="Enter coordinates manually", icon='HAND')


class CIVIL_OT_AutoCalculateFalseOrigin(Operator):
    """Automatically calculate optimal false origin from scene objects"""
    bl_idname = "civil.auto_calculate_false_origin"
    bl_label = "Auto-Calculate False Origin"
    bl_description = "Calculate optimal false origin from all objects in scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        
        # Collect all object locations
        locations = []
        for obj in context.scene.objects:
            if obj.type in {'MESH', 'CURVE', 'EMPTY'}:
                locations.append(Vector(obj.location))
        
        if not locations:
            self.report({'WARNING'}, "No objects in scene to calculate from")
            return {'CANCELLED'}
        
        # Calculate optimal false origin
        false_origin = GeoreferencingUtils.calculate_optimal_false_origin(locations)
        
        # Apply
        georef.false_easting = false_origin.x
        georef.false_northing = false_origin.y
        georef.false_elevation = false_origin.z
        georef.is_georeferenced = True
        
        self.report({'INFO'}, 
            f"False origin set to E:{false_origin.x:.0f}, N:{false_origin.y:.0f}")
        return {'FINISHED'}


class CIVIL_OT_VerifyPrecision(Operator):
    """Verify coordinate precision at current distance from origin"""
    bl_idname = "civil.verify_precision"
    bl_label = "Verify Precision"
    bl_description = "Check if precision requirements are met"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        
        # Find maximum distance from origin
        max_dist = 0.0
        for obj in context.scene.objects:
            dist = Vector(obj.location).length
            max_dist = max(max_dist, dist)
        
        # Update stored value
        georef.max_distance_from_origin = max_dist
        
        # Verify precision
        ok, precision_mm, warning = GeoreferencingUtils.verify_precision(max_dist)
        
        if ok:
            self.report({'INFO'}, 
                f"✓ Precision OK: {precision_mm:.4f}mm at {max_dist:.1f}m")
        else:
            self.report({'WARNING'}, warning)
        
        return {'FINISHED'}


class CIVIL_OT_ClearGeoreferencing(Operator):
    """Clear all georeferencing data"""
    bl_idname = "civil.clear_georeferencing"
    bl_label = "Clear Georeferencing"
    bl_description = "Reset all georeferencing data"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        georef = context.scene.bc_georeferencing
        
        # Reset all values
        georef.crs_name = ""
        georef.epsg_code = 0
        georef.false_easting = 0.0
        georef.false_northing = 0.0
        georef.false_elevation = 0.0
        georef.scale_factor = 1.0
        georef.rotation_angle = 0.0
        georef.is_georeferenced = False
        
        self.report({'INFO'}, "Georeferencing data cleared")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class CIVIL_OT_ShowCoordinateInfo(Operator):
    """Show coordinate information for selected object"""
    bl_idname = "civil.show_coordinate_info"
    bl_label = "Show Coordinate Info"
    bl_description = "Display local and map coordinates for selected object"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
        
        georef = context.scene.bc_georeferencing
        local_coord = Vector(obj.location)
        
        if georef.is_georeferenced:
            map_coord = GeoreferencingUtils.local_to_map(local_coord, georef)
            self.report({'INFO'}, 
                f"Local: ({local_coord.x:.3f}, {local_coord.y:.3f}, {local_coord.z:.3f}) | "
                f"Map: (E:{map_coord.x:.3f}, N:{map_coord.y:.3f}, El:{map_coord.z:.3f})")
        else:
            self.report({'INFO'}, 
                f"Local: ({local_coord.x:.3f}, {local_coord.y:.3f}, {local_coord.z:.3f}) "
                f"(No georeferencing set)")
        
        return {'FINISHED'}


# ============================================================================
# LANDXML IMPORT OPERATOR
# ============================================================================

class CIVIL_OT_ImportLandXML(Operator):
    """Import LandXML file with georeferencing support"""
    bl_idname = "civil.import_landxml"
    bl_label = "Import LandXML"
    bl_description = "Import alignment and survey data from LandXML file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="File Path",
        description="Path to LandXML file",
        subtype='FILE_PATH'
    )
    
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'}
    )
    
    auto_georef: BoolProperty(
        name="Auto Georeferencing",
        default=True,
        description="Automatically setup georeferencing from file"
    )
    
    import_alignments: BoolProperty(
        name="Import Alignments",
        default=True,
        description="Import horizontal alignments"
    )
    
    create_curve_objects: BoolProperty(
        name="Create Curve Objects",
        default=True,
        description="Create curve objects for visualization"
    )
    
    def execute(self, context):
        from file_io.landxml import parse_landxml_file
        
        # Parse LandXML file
        self.report({'INFO'}, f"Parsing {os.path.basename(self.filepath)}...")
        data = parse_landxml_file(self.filepath)
        
        if not data['success']:
            self.report({'ERROR'}, f"Failed to parse: {data['error']}")
            return {'CANCELLED'}
        
        # Report what we found
        self.report({'INFO'}, 
            f"Found {len(data['alignments'])} alignment(s), "
            f"{len(data['all_coordinates'])} points"
        )
        
        # Setup georeferencing if requested
        georef = context.scene.bc_georeferencing
        
        if self.auto_georef and data['all_coordinates']:
            # Calculate optimal false origin
            false_origin = GeoreferencingUtils.calculate_optimal_false_origin(
                data['all_coordinates']
            )
            
            # Setup georeferencing
            georef.false_easting = false_origin.x
            georef.false_northing = false_origin.y
            georef.false_elevation = false_origin.z
            georef.scale_factor = 1.0
            georef.rotation_angle = 0.0
            
            # Set CRS if found
            if data['crs']['found']:
                georef.crs_name = data['crs']['name']
                if data['crs']['epsg_code']:
                    georef.epsg_code = data['crs']['epsg_code']
            
            georef.is_georeferenced = True
            georef.update_rotation_components()
            
            self.report({'INFO'}, 
                f"Georeferencing setup: E={false_origin.x:.0f}, N={false_origin.y:.0f}"
            )
        
        # Import alignments
        if self.import_alignments and data['alignments']:
            for align_data in data['alignments']:
                self._import_alignment(context, align_data, georef)
        
        self.report({'INFO'}, "LandXML import complete!")
        return {'FINISHED'}
    
    def _import_alignment(self, context, align_data, georef):
        """Import a single alignment"""
        align_name = align_data['name']
        
        # Create parent empty for alignment
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        parent_obj = context.active_object
        parent_obj.name = f"Alignment_{align_name}"
        parent_obj.empty_display_size = 5.0
        
        # Store alignment metadata
        parent_obj['bc_alignment'] = True
        parent_obj['bc_start_station'] = align_data['start_station']
        parent_obj['bc_end_station'] = align_data['end_station']
        parent_obj['bc_length'] = align_data['length']
        
        # If we have coordinate list, create polyline
        if align_data['coordinates']:
            self._create_alignment_polyline(
                context, align_data['coordinates'], georef, parent_obj
            )
    
    def _create_alignment_polyline(self, context, coordinates, georef, parent):
        """Create a polyline from coordinate list"""
        if len(coordinates) < 2:
            return
        
        # Transform all coordinates to local
        local_coords = [GeoreferencingUtils.map_to_local(c, georef) for c in coordinates]
        
        # Create curve
        curve_data = bpy.data.curves.new(f"{parent.name}_Path", type='CURVE')
        curve_data.dimensions = '3D'
        
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(len(local_coords) - 1)
        
        for i, coord in enumerate(local_coords):
            polyline.points[i].co = (*coord, 1)
        
        curve_obj = bpy.data.objects.new(f"{parent.name}_Path", curve_data)
        context.collection.objects.link(curve_obj)
        curve_obj.parent = parent
        
        # Style
        curve_data.bevel_depth = 0.1
        curve_data.bevel_resolution = 2
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# ============================================================================
# REGISTRATION
# ============================================================================



# ============================================================================
# LANDXML EXPORT OPERATOR
# ============================================================================

class CIVIL_OT_ExportLandXML(Operator):
    """Export alignments to LandXML file"""
    bl_idname = "civil.export_landxml"
    bl_label = "Export LandXML"
    bl_description = "Export alignment data to LandXML file with georeferencing"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(
        name="File Path",
        description="Path to save LandXML file",
        subtype='FILE_PATH'
    )
    
    filter_glob: StringProperty(
        default="*.xml",
        options={'HIDDEN'}
    )
    
    filename_ext = ".xml"
    
    export_selected_only: BoolProperty(
        name="Selected Only",
        default=False,
        description="Export only selected alignments"
    )
    
    def execute(self, context):
        from file_io.landxml import generate_landxml
        from mathutils import Vector
        
        georef = context.scene.bc_georeferencing
        
        # Check if georeferenced
        if not georef.is_georeferenced:
            self.report({'ERROR'}, "Project not georeferenced. Setup georeferencing first.")
            return {'CANCELLED'}
        
        # Gather alignment data from scene
        alignments_data = []
        
        # Find alignment objects
        objects_to_export = context.selected_objects if self.export_selected_only else context.scene.objects
        
        for obj in objects_to_export:
            # Check if it's an alignment parent
            if 'bc_alignment' in obj and obj.get('bc_alignment'):
                # This is an alignment parent
                align_data = self._gather_alignment_data(obj)
                if align_data:
                    alignments_data.append(align_data)
        
        if not alignments_data:
            self.report({'WARNING'}, "No alignments found to export")
            return {'CANCELLED'}
        
        # Prepare georeferencing data
        georef_data = {
            'crs_name': georef.crs_name,
            'epsg_code': georef.epsg_code,
            'false_easting': georef.false_easting,
            'false_northing': georef.false_northing,
            'false_elevation': georef.false_elevation,
            'scale_factor': georef.scale_factor,
            'rotation_angle': georef.rotation_angle,
        }
        
        # Generate LandXML
        self.report({'INFO'}, f"Exporting {len(alignments_data)} alignment(s)...")
        
        success = generate_landxml(alignments_data, georef_data, self.filepath)
        
        if success:
            self.report({'INFO'}, f"Successfully exported to {os.path.basename(self.filepath)}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "Failed to generate LandXML file")
            return {'CANCELLED'}
    
    def _gather_alignment_data(self, parent_obj):
        """Gather alignment data from parent and child objects."""
        from mathutils import Vector
        
        align_data = {
            'name': parent_obj.name.replace('Alignment_', ''),
            'length': parent_obj.get('bc_length', 0.0),
            'start_station': parent_obj.get('bc_start_station', 0.0),
            'end_station': parent_obj.get('bc_end_station', 0.0),
            'coordinates': []
        }
        
        # Find child curve objects
        for child in parent_obj.children:
            if child.type == 'CURVE' and child.data:
                # Extract points from curve
                curve_data = child.data
                
                for spline in curve_data.splines:
                    if spline.type == 'POLY':
                        # Polyline - extract points
                        for point in spline.points:
                            # Convert to world space
                            local_co = Vector((point.co[0], point.co[1], point.co[2]))
                            world_co = child.matrix_world @ local_co
                            align_data['coordinates'].append(world_co)
                    
                    elif spline.type == 'BEZIER':
                        # Bezier curve - sample points
                        for point in spline.bezier_points:
                            world_co = child.matrix_world @ point.co
                            align_data['coordinates'].append(world_co)
                    
                    elif spline.type == 'NURBS':
                        # NURBS - sample points
                        for point in spline.points:
                            local_co = Vector((point.co[0], point.co[1], point.co[2]))
                            world_co = child.matrix_world @ local_co
                            align_data['coordinates'].append(world_co)
        
        # If no coordinates found, return None
        if not align_data['coordinates']:
            return None
        
        return align_data
    
    def invoke(self, context, event):
        # Set default filename
        if not self.filepath:
            self.filepath = "alignment_export.xml"
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


classes = (
    CIVIL_OT_SetupGeoreferencing,
    CIVIL_OT_AutoCalculateFalseOrigin,
    CIVIL_OT_VerifyPrecision,
    CIVIL_OT_ClearGeoreferencing,
    CIVIL_OT_ShowCoordinateInfo,
    CIVIL_OT_ImportLandXML,
    CIVIL_OT_ExportLandXML)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("✅ Georeferencing operators registered")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
