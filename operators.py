"""
BlenderCivil Operators - Civil Engineering Actions
Integrates with OASYS cloud platform for coordinate system extraction
and provides tools for horizontal alignment design and IFC export.
"""

import bpy
from bpy.types import Operator
from bpy.props import (
    StringProperty, 
    FloatProperty, 
    IntProperty, 
    BoolProperty,
    EnumProperty,
    FloatVectorProperty
)
import mathutils
import math
import json
import os
import tempfile

# Try to import optional dependencies
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  requests not available - OASYS API features disabled")

try:
    import ifcopenshell
    import ifcopenshell.api
    from ifcopenshell.util.placement import get_local_placement
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    print("⚠️  ifcopenshell not available - IFC export disabled")


# =============================================================================
# OASYS Integration Operators
# =============================================================================

class CIVIL_OT_connect_oasys(Operator):
    """Connect to OASYS API and check status"""
    bl_idname = "civil.connect_oasys"
    bl_label = "Connect to OASYS"
    bl_description = "Test connection to OASYS cloud service"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests library not available. Install via pip.")
            return {'CANCELLED'}
        
        props = context.scene.civil_properties
        api_url = props.oasys_api_url
        
        if not api_url:
            self.report({'ERROR'}, "OASYS API URL not set in preferences")
            return {'CANCELLED'}
        
        try:
            response = requests.get(f"{api_url}/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.report({'INFO'}, f"✓ Connected to OASYS: {data.get('message', 'OK')}")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"OASYS returned status {response.status_code}")
                return {'CANCELLED'}
        except requests.exceptions.RequestException as e:
            self.report({'ERROR'}, f"Connection failed: {str(e)}")
            return {'CANCELLED'}


class CIVIL_OT_list_crs_files(Operator):
    """List available coordinate system files from OASYS"""
    bl_idname = "civil.list_crs_files"
    bl_label = "List CRS Files"
    bl_description = "Retrieve list of processed coordinate system files from OASYS"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests library not available")
            return {'CANCELLED'}
        
        props = context.scene.civil_properties
        api_url = props.oasys_api_url
        
        try:
            response = requests.get(f"{api_url}/list-crs", timeout=10)
            if response.status_code == 200:
                data = response.json()
                files = data.get('files', [])
                self.report({'INFO'}, f"Found {len(files)} CRS files")
                
                # Store in scene property for UI display
                props.available_crs_files = json.dumps(files)
                
                # Print to console for debugging
                print(f"\n{'='*60}")
                print(f"Available CRS Files from OASYS:")
                print(f"{'='*60}")
                for i, file_info in enumerate(files, 1):
                    print(f"{i}. {file_info.get('key', 'unknown')}")
                    print(f"   Size: {file_info.get('size', 0)} bytes")
                    print(f"   Modified: {file_info.get('last_modified', 'unknown')}")
                print(f"{'='*60}\n")
                
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Failed to retrieve CRS list: {response.status_code}")
                return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}


class CIVIL_OT_set_coordinate_system(Operator):
    """Set scene coordinate system from OASYS CRS data"""
    bl_idname = "civil.set_coordinate_system"
    bl_label = "Set Coordinate System"
    bl_description = "Apply coordinate system from OASYS to current scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    crs_file_key: StringProperty(
        name="CRS File Key",
        description="S3 key of the coordinate system file"
    )
    
    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests library not available")
            return {'CANCELLED'}
        
        props = context.scene.civil_properties
        api_url = props.oasys_api_url
        
        # Use provided key or get from properties
        file_key = self.crs_file_key if self.crs_file_key else props.selected_crs_file
        
        if not file_key:
            self.report({'ERROR'}, "No CRS file selected")
            return {'CANCELLED'}
        
        try:
            # Retrieve CRS data from OASYS
            response = requests.get(f"{api_url}/get-crs/{file_key}", timeout=10)
            if response.status_code != 200:
                self.report({'ERROR'}, f"Failed to retrieve CRS data: {response.status_code}")
                return {'CANCELLED'}
            
            crs_data = response.json()
            
            # Extract coordinate system information
            coord_sys = crs_data.get('coordinate_system', {})
            epsg_code = coord_sys.get('epsg_code', '')
            crs_name = coord_sys.get('coordinate_system_name', 'Unknown')
            scale_factor = crs_data.get('blender_setup', {}).get('scale_factor', 1.0)
            units = coord_sys.get('units', 'meters')
            
            # Store in scene properties
            context.scene['EPSG_Code'] = epsg_code
            context.scene['CoordinateSystemName'] = crs_name
            context.scene['ScaleFactor'] = scale_factor
            context.scene['Units'] = units
            context.scene['OASYS_CRS_Data'] = json.dumps(crs_data)
            
            # Update scene unit scale if needed
            if 'feet' in units.lower() or 'foot' in units.lower():
                context.scene.unit_settings.length_unit = 'FEET'
            else:
                context.scene.unit_settings.length_unit = 'METERS'
            
            self.report({'INFO'}, f"✓ Set coordinate system: {crs_name} (EPSG:{epsg_code})")
            
            # Print detailed info
            print(f"\n{'='*60}")
            print(f"Coordinate System Applied:")
            print(f"{'='*60}")
            print(f"Name: {crs_name}")
            print(f"EPSG: {epsg_code}")
            print(f"Units: {units}")
            print(f"Scale Factor: {scale_factor}")
            print(f"Datum: {coord_sys.get('datum', 'Unknown')}")
            print(f"{'='*60}\n")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}


class CIVIL_OT_upload_plan_pdf(Operator):
    """Upload a plan PDF to OASYS for processing"""
    bl_idname = "civil.upload_plan_pdf"
    bl_label = "Upload Plan PDF"
    bl_description = "Upload a roadway plan PDF to OASYS for coordinate system extraction"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.pdf", options={'HIDDEN'})
    
    def execute(self, context):
        if not REQUESTS_AVAILABLE:
            self.report({'ERROR'}, "requests library not available")
            return {'CANCELLED'}
        
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}
        
        props = context.scene.civil_properties
        api_url = props.oasys_api_url
        
        try:
            # Request presigned URL from OASYS
            filename = os.path.basename(self.filepath)
            response = requests.post(
                f"{api_url}/submit-plan",
                json={"filename": filename},
                timeout=10
            )
            
            if response.status_code != 200:
                self.report({'ERROR'}, f"Failed to get upload URL: {response.status_code}")
                return {'CANCELLED'}
            
            data = response.json()
            upload_url = data.get('upload_url')
            s3_key = data.get('s3_key')
            
            # Upload file to S3
            with open(self.filepath, 'rb') as f:
                upload_response = requests.put(upload_url, data=f, timeout=60)
            
            if upload_response.status_code == 200:
                self.report({'INFO'}, f"✓ Uploaded {filename} to OASYS for processing")
                print(f"S3 Key: {s3_key}")
                print("Processing will take 10-30 seconds. Use 'List CRS Files' to check status.")
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, f"Upload failed: {upload_response.status_code}")
                return {'CANCELLED'}
                
        except Exception as e:
            self.report({'ERROR'}, f"Error: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# =============================================================================
# Alignment Design Operators
# =============================================================================

class CIVIL_OT_add_pi_point(Operator):
    """Add a Point of Intersection (PI) for alignment design"""
    bl_idname = "civil.add_pi_point"
    bl_label = "Add PI Point"
    bl_description = "Add a Point of Intersection at 3D cursor location"
    bl_options = {'REGISTER', 'UNDO'}
    
    station: FloatProperty(
        name="Station",
        default=0.0,
        description="Station value for this PI"
    )
    
    def execute(self, context):
        # Count existing PI points
        pi_count = len([o for o in bpy.data.objects if o.name.startswith('PI_')])
        
        # Add empty at cursor location
        bpy.ops.object.empty_add(type='SPHERE', location=context.scene.cursor.location)
        empty = context.active_object
        empty.name = f"PI_{pi_count + 1:03d}"
        empty.empty_display_size = 10.0
        
        # Store station as custom property
        empty['station'] = self.station
        
        self.report({'INFO'}, f"Added {empty.name} at station {self.station}")
        return {'FINISHED'}


class CIVIL_OT_create_alignment_tangents(Operator):
    """Create alignment from PI points (tangents only, no curves)"""
    bl_idname = "civil.create_alignment_tangents"
    bl_label = "Create Alignment (Tangents)"
    bl_description = "Create straight-line alignment connecting PI points"
    bl_options = {'REGISTER', 'UNDO'}
    
    alignment_name: StringProperty(
        name="Alignment Name",
        default="Alignment_Tangents"
    )
    
    def execute(self, context):
        # Get all PI points sorted by name
        pi_points = sorted(
            [o for o in bpy.data.objects if o.name.startswith('PI_')],
            key=lambda x: x.name
        )
        
        if len(pi_points) < 2:
            self.report({'ERROR'}, "Need at least 2 PI points")
            return {'CANCELLED'}
        
        # Create curve object
        curve_data = bpy.data.curves.new(self.alignment_name, type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create spline (polyline)
        spline = curve_data.splines.new('POLY')
        spline.points.add(len(pi_points) - 1)
        
        for i, pi in enumerate(pi_points):
            spline.points[i].co = (*pi.location, 1.0)
        
        # Create object
        curve_obj = bpy.data.objects.new(self.alignment_name, curve_data)
        context.collection.objects.link(curve_obj)
        
        # Select the new alignment
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj
        
        self.report({'INFO'}, f"Created alignment with {len(pi_points)} PI points")
        return {'FINISHED'}


class CIVIL_OT_create_alignment_curves(Operator):
    """Create alignment with horizontal curves between PI points"""
    bl_idname = "civil.create_alignment_curves"
    bl_label = "Create Alignment (With Curves)"
    bl_description = "Create alignment with horizontal curves (requires curve radii)"
    bl_options = {'REGISTER', 'UNDO'}
    
    alignment_name: StringProperty(
        name="Alignment Name",
        default="Alignment_WithCurves"
    )
    
    default_radius: FloatProperty(
        name="Default Radius",
        default=500.0,
        min=50.0,
        description="Default curve radius for PIs without specified radius"
    )
    
    def execute(self, context):
        # Get all PI points sorted by name
        pi_points = sorted(
            [o for o in bpy.data.objects if o.name.startswith('PI_')],
            key=lambda x: x.name
        )
        
        if len(pi_points) < 3:
            self.report({'ERROR'}, "Need at least 3 PI points for curves")
            return {'CANCELLED'}
        
        # Create curve object
        curve_data = bpy.data.curves.new(self.alignment_name, type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 24  # Smooth curves
        
        # Create bezier spline
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(len(pi_points) - 1)
        
        for i, pi in enumerate(pi_points):
            point = spline.bezier_points[i]
            point.co = pi.location
            point.handle_left_type = 'AUTO'
            point.handle_right_type = 'AUTO'
        
        # Create object
        curve_obj = bpy.data.objects.new(self.alignment_name, curve_data)
        context.collection.objects.link(curve_obj)
        
        # Select the new alignment
        bpy.ops.object.select_all(action='DESELECT')
        curve_obj.select_set(True)
        context.view_layer.objects.active = curve_obj
        
        self.report({'INFO'}, f"Created curved alignment with {len(pi_points)} PI points")
        return {'FINISHED'}


class CIVIL_OT_apply_station_labels(Operator):
    """Apply station labels along selected alignment curve"""
    bl_idname = "civil.apply_station_labels"
    bl_label = "Apply Station Labels"
    bl_description = "Create station labels at regular intervals along alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    interval: FloatProperty(
        name="Station Interval",
        default=100.0,
        min=1.0,
        description="Distance between station labels"
    )
    
    start_station: FloatProperty(
        name="Start Station",
        default=0.0,
        description="Starting station value"
    )
    
    text_size: FloatProperty(
        name="Text Size",
        default=10.0,
        min=0.1,
        description="Size of station labels"
    )
    
    def execute(self, context):
        # Get active object (must be a curve)
        obj = context.active_object
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "Select a curve alignment first")
            return {'CANCELLED'}
        
        curve = obj.data
        
        # Calculate total length (simplified - use curve evaluation in production)
        num_samples = 100
        total_length = 0
        prev_point = None
        
        # Sample points along curve
        for spline in curve.splines:
            if spline.type == 'BEZIER':
                for i in range(len(spline.bezier_points) - 1):
                    p1 = obj.matrix_world @ spline.bezier_points[i].co
                    p2 = obj.matrix_world @ spline.bezier_points[i+1].co
                    total_length += (p2 - p1).length
            elif spline.type == 'POLY':
                for i in range(len(spline.points) - 1):
                    p1 = obj.matrix_world @ mathutils.Vector(spline.points[i].co[:3])
                    p2 = obj.matrix_world @ mathutils.Vector(spline.points[i+1].co[:3])
                    total_length += (p2 - p1).length
        
        # Create station labels
        if total_length > 0:
            num_stations = int(total_length / self.interval) + 1
            
            for i in range(num_stations):
                station = self.start_station + (i * self.interval)
                
                # Create text object (positioned along curve - simplified here)
                bpy.ops.object.text_add()
                text_obj = context.active_object
                text_obj.name = f"STA_{int(station/100)}+{int(station%100):02d}"
                text_obj.data.body = f"STA {int(station/100)}+{int(station%100):02d}"
                text_obj.data.size = self.text_size
                
                # Position along alignment (simplified - should evaluate curve at t)
                t = (i * self.interval) / total_length
                if curve.splines:
                    if curve.splines[0].type == 'BEZIER' and len(curve.splines[0].bezier_points) > 0:
                        idx = min(int(t * (len(curve.splines[0].bezier_points) - 1)), 
                                len(curve.splines[0].bezier_points) - 1)
                        text_obj.location = obj.matrix_world @ curve.splines[0].bezier_points[idx].co
            
            self.report({'INFO'}, f"Created {num_stations} station labels")
        else:
            self.report({'WARNING'}, "Could not calculate alignment length")
        
        return {'FINISHED'}


class CIVIL_OT_import_landxml(Operator):
    """Import alignment from LandXML file"""
    bl_idname = "civil.import_landxml"
    bl_label = "Import LandXML"
    bl_description = "Import horizontal and vertical alignments from LandXML"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.xml", options={'HIDDEN'})
    
    def execute(self, context):
        if not os.path.exists(self.filepath):
            self.report({'ERROR'}, "File not found")
            return {'CANCELLED'}
        
        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(self.filepath)
            root = tree.getroot()
            
            # This is a placeholder - full LandXML parsing is complex
            self.report({'INFO'}, f"Imported {os.path.basename(self.filepath)}")
            print("⚠️  LandXML parsing not fully implemented yet")
            print("    Full implementation would parse <Alignment> elements")
            print("    and create curve objects from coordinate geometry")
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error parsing LandXML: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# =============================================================================
# IFC Export Operators
# =============================================================================

class CIVIL_OT_export_ifc_alignment(Operator):
    """Export alignment to IFC file with IfcAlignment entity"""
    bl_idname = "civil.export_ifc_alignment"
    bl_label = "Export IFC Alignment"
    bl_description = "Export selected alignment as georeferenced IFC file"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ifc", options={'HIDDEN'})
    
    include_terrain: BoolProperty(
        name="Include Terrain",
        default=False,
        description="Include terrain mesh in IFC export"
    )
    
    def execute(self, context):
        if not IFC_AVAILABLE:
            self.report({'ERROR'}, "IfcOpenShell not installed. Install via pip.")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "Select a curve alignment to export")
            return {'CANCELLED'}
        
        try:
            # Create IFC file
            ifc_file = ifcopenshell.api.run("project.create_file")
            project = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                          ifc_class="IfcProject", name="Civil Project")
            
            # Set coordinate system if available
            if 'EPSG_Code' in context.scene:
                epsg = context.scene['EPSG_Code']
                crs_name = context.scene.get('CoordinateSystemName', 'Unknown')
                print(f"Adding EPSG:{epsg} ({crs_name}) to IFC file")
                
                # Create map conversion (simplified - full implementation needs proper transformation)
                # This is where you'd add IfcMapConversion and IfcProjectedCRS
            
            # Create site
            site = ifcopenshell.api.run("root.create_entity", ifc_file, 
                                       ifc_class="IfcSite", name="Site")
            ifcopenshell.api.run("aggregate.assign_object", ifc_file, 
                               product=site, relating_object=project)
            
            # Create IfcAlignment (IFC 4.1+ feature)
            # Note: Full IfcAlignment implementation is complex and requires:
            # - IfcAlignment entity
            # - IfcAlignmentHorizontal with segments
            # - IfcAlignmentVertical with segments
            # This is a placeholder showing the structure
            
            print("⚠️  IfcAlignment entity creation not fully implemented")
            print("    Full implementation requires IFC 4.1+ schema and")
            print("    proper alignment segment definitions")
            
            # Write file
            ifc_file.write(self.filepath)
            
            self.report({'INFO'}, f"✓ Exported IFC to {os.path.basename(self.filepath)}")
            print(f"Saved to: {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"IFC export failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        self.filepath = "alignment.ifc"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# =============================================================================
# Utility Operators
# =============================================================================

class CIVIL_OT_calculate_curve_data(Operator):
    """Calculate curve data for selected PI points"""
    bl_idname = "civil.calculate_curve_data"
    bl_label = "Calculate Curve Data"
    bl_description = "Calculate tangent lengths, curve lengths, and deflection angles"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        pi_points = sorted(
            [o for o in bpy.data.objects if o.name.startswith('PI_') and o.select_get()],
            key=lambda x: x.name
        )
        
        if len(pi_points) < 3:
            self.report({'ERROR'}, "Select at least 3 PI points")
            return {'CANCELLED'}
        
        print(f"\n{'='*60}")
        print("Curve Data Calculation")
        print(f"{'='*60}")
        
        total_tangent = 0
        total_curve = 0
        
        for i in range(1, len(pi_points) - 1):
            prev_pi = pi_points[i-1]
            curr_pi = pi_points[i]
            next_pi = pi_points[i+1]
            
            # Calculate vectors
            v1 = prev_pi.location - curr_pi.location
            v2 = next_pi.location - curr_pi.location
            
            # Calculate deflection angle
            angle = v1.angle(v2)
            angle_deg = math.degrees(angle)
            
            # Get or estimate radius
            radius = curr_pi.get('radius', 500.0)
            
            # Calculate curve properties
            tangent_length = radius * math.tan(angle / 2) if angle > 0 else 0
            curve_length = radius * angle if angle > 0 else 0
            external_distance = radius * (1 / math.cos(angle / 2) - 1) if angle > 0 else 0
            
            total_tangent += tangent_length * 2  # Both sides of curve
            total_curve += curve_length
            
            print(f"\n{curr_pi.name}:")
            print(f"  Deflection Angle: {angle_deg:.2f}° ({angle:.4f} rad)")
            print(f"  Radius: {radius:.2f}")
            print(f"  Tangent Length: {tangent_length:.2f}")
            print(f"  Curve Length: {curve_length:.2f}")
            print(f"  External Distance: {external_distance:.2f}")
            print(f"  Chord Length: {2 * radius * math.sin(angle / 2):.2f}")
        
        # Calculate total alignment length
        total_straight = 0
        for i in range(len(pi_points) - 1):
            total_straight += (pi_points[i+1].location - pi_points[i].location).length
        
        print(f"\n{'='*60}")
        print(f"Alignment Summary:")
        print(f"  Number of curves: {len(pi_points) - 2}")
        print(f"  Total PI-to-PI length: {total_straight:.2f}")
        print(f"  Total tangent length: {total_tangent:.2f}")
        print(f"  Total curve length: {total_curve:.2f}")
        print(f"  Estimated true length: {total_straight - total_tangent + total_curve:.2f}")
        print(f"{'='*60}\n")
        
        self.report({'INFO'}, f"Calculated curve data for {len(pi_points)-2} curves")
        return {'FINISHED'}


class CIVIL_OT_clear_pi_points(Operator):
    """Clear all PI points from scene"""
    bl_idname = "civil.clear_pi_points"
    bl_label = "Clear PI Points"
    bl_description = "Delete all PI point empties from the scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        pi_points = [o for o in bpy.data.objects if o.name.startswith('PI_')]
        
        if not pi_points:
            self.report({'INFO'}, "No PI points found")
            return {'CANCELLED'}
        
        count = len(pi_points)
        
        # Delete all PI points
        bpy.ops.object.select_all(action='DESELECT')
        for pi in pi_points:
            pi.select_set(True)
        bpy.ops.object.delete()
        
        self.report({'INFO'}, f"Deleted {count} PI points")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


# =============================================================================
# Registration
# =============================================================================

classes = (
    # OASYS Integration
    CIVIL_OT_connect_oasys,
    CIVIL_OT_list_crs_files,
    CIVIL_OT_set_coordinate_system,
    CIVIL_OT_upload_plan_pdf,
    
    # Alignment Design
    CIVIL_OT_add_pi_point,
    CIVIL_OT_create_alignment_tangents,
    CIVIL_OT_create_alignment_curves,
    CIVIL_OT_apply_station_labels,
    CIVIL_OT_import_landxml,
    
    # IFC Export
    CIVIL_OT_export_ifc_alignment,
    
    # Utilities
    CIVIL_OT_calculate_curve_data,
    CIVIL_OT_clear_pi_points,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("BlenderCivil operators registered")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
