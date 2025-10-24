"""
BlenderCivil - Horizontal Alignment Operators

Operators for creating and managing horizontal roadway alignments:
- Add PI (Point of Intersection) points
- Create tangent lines between PIs
- Insert horizontal curves
- Add station markers
- Export alignment data
"""

import bpy
import math
import json
from mathutils import Vector
from bpy.types import Operator
from bpy.props import StringProperty

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_create_collection(name, parent=None):
    """Get existing collection or create new one"""
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    
    new_col = bpy.data.collections.new(name)
    
    if parent:
        parent.children.link(new_col)
    else:
        bpy.context.scene.collection.children.link(new_col)
    
    return new_col

def get_pi_objects():
    """Get all PI objects sorted by PI number"""
    pi_col = bpy.data.collections.get("PI_Points")
    if not pi_col:
        return []
    
    pi_objects = [obj for obj in pi_col.objects if "is_pi" in obj]
    return sorted(pi_objects, key=lambda x: x.get("pi_number", 0))

# ============================================================================
# PI POINT OPERATORS
# ============================================================================

class CIVIL_OT_AddPI(Operator):
    """Add a Point of Intersection at 3D cursor location"""
    bl_idname = "civil.add_pi"
    bl_label = "Add PI Point"
    bl_description = "Add a Point of Intersection at 3D cursor location"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        cursor_loc = context.scene.cursor.location.copy()
        props = context.scene.civil_alignment
        
        # Create collection hierarchy
        alignment_col = get_or_create_collection("Alignment")
        pi_col = get_or_create_collection("PI_Points", alignment_col)
        
        # Count existing PIs
        pi_count = len([obj for obj in pi_col.objects if obj.name.startswith("PI_")])
        
        # Create PI empty
        pi_name = f"PI_{pi_count + 1:03d}"
        bpy.ops.object.empty_add(type='SPHERE', location=cursor_loc)
        pi_obj = context.active_object
        pi_obj.name = pi_name
        pi_obj.empty_display_size = props.pi_size
        
        # Move to PI collection
        for col in pi_obj.users_collection:
            col.objects.unlink(pi_obj)
        pi_col.objects.link(pi_obj)
        
        # Store custom properties
        pi_obj["is_pi"] = True
        pi_obj["pi_number"] = pi_count + 1
        pi_obj["station"] = 0.0
        
        # Mark as IFC Referent if Bonsai is available
        try:
            pi_obj.civil_ifc.ifc_class = 'IFCREFERENT'
            pi_obj.civil_ifc.is_alignment_entity = True
        except:
            pass
        
        self.report({'INFO'}, f"Added {pi_name} at {cursor_loc}")
        return {'FINISHED'}

# ============================================================================
# TANGENT OPERATORS
# ============================================================================

class CIVIL_OT_CreateTangents(Operator):
    """Create tangent lines connecting PI points"""
    bl_idname = "civil.create_tangents"
    bl_label = "Create Tangents"
    bl_description = "Create tangent lines connecting PI points"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        pi_objects = get_pi_objects()
        
        if len(pi_objects) < 2:
            self.report({'WARNING'}, "Need at least 2 PI points")
            return {'CANCELLED'}
        
        # Create curve for tangents
        curve_data = bpy.data.curves.new(name="Alignment_Tangents", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.5
        
        # Create polyline
        polyline = curve_data.splines.new('POLY')
        polyline.points.add(len(pi_objects) - 1)
        
        for i, pi_obj in enumerate(pi_objects):
            polyline.points[i].co = (*pi_obj.location, 1.0)
        
        # Create object
        curve_obj = bpy.data.objects.new("Alignment_Tangents", curve_data)
        alignment_col = get_or_create_collection("Alignment")
        alignment_col.objects.link(curve_obj)
        
        # Mark as IFC Alignment
        try:
            curve_obj.civil_ifc.ifc_class = 'IFCALIGNMENTHORIZONTAL'
            curve_obj.civil_ifc.is_alignment_entity = True
        except:
            pass
        
        # Calculate stations
        cumulative_length = 0.0
        pi_objects[0]["station"] = 0.0
        
        for i in range(1, len(pi_objects)):
            segment_length = (pi_objects[i].location - pi_objects[i-1].location).length
            cumulative_length += segment_length
            pi_objects[i]["station"] = cumulative_length
        
        self.report({'INFO'}, f"Created tangent alignment through {len(pi_objects)} PIs")
        return {'FINISHED'}

# ============================================================================
# CURVE OPERATORS
# ============================================================================

class CIVIL_OT_InsertCurves(Operator):
    """Insert circular curves at PI points"""
    bl_idname = "civil.insert_curves"
    bl_label = "Insert Horizontal Curves"
    bl_description = "Insert circular curves at PI points with specified radius"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.civil_alignment
        radius = props.curve_radius
        
        pi_objects = get_pi_objects()
        
        if len(pi_objects) < 3:
            self.report({'WARNING'}, "Need at least 3 PIs to insert curves")
            return {'CANCELLED'}
        
        # Create curve
        curve_data = bpy.data.curves.new(name="Alignment_WithCurves", type='CURVE')
        curve_data.dimensions = '3D'
        curve_data.bevel_depth = 0.5
        
        spline = curve_data.splines.new('NURBS')
        all_points = []
        
        # Add first PI
        all_points.append(pi_objects[0].location)
        
        # Process middle PIs with curves
        for i in range(1, len(pi_objects) - 1):
            pi_prev = pi_objects[i - 1]
            pi_curr = pi_objects[i]
            pi_next = pi_objects[i + 1]
            
            # Calculate tangent vectors
            back_tan = (pi_curr.location - pi_prev.location).normalized()
            forward_tan = (pi_next.location - pi_curr.location).normalized()
            
            # Calculate deflection angle
            dot_product = max(-1.0, min(1.0, back_tan.dot(forward_tan)))
            delta = math.acos(dot_product)
            
            # Calculate tangent length
            tangent_length = radius * math.tan(delta / 2)
            
            # Calculate PC and PT
            pc = pi_curr.location - back_tan * tangent_length
            pt = pi_curr.location + forward_tan * tangent_length
            
            all_points.append(pc)
            
            # Calculate curve center
            pc_to_pi = (pi_curr.location - pc).normalized()
            perpendicular = Vector((-pc_to_pi.y, pc_to_pi.x, 0.0))
            
            cross = back_tan.cross(forward_tan)
            if cross.z < 0:
                perpendicular = -perpendicular
            
            center = pc + perpendicular * radius
            
            # Generate arc points
            num_curve_points = max(10, int(math.degrees(delta) / 5))
            for j in range(1, num_curve_points):
                t = j / num_curve_points
                angle = delta * t
                
                pc_vec = pc - center
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                
                rotated = Vector((
                    pc_vec.x * cos_a - pc_vec.y * sin_a,
                    pc_vec.x * sin_a + pc_vec.y * cos_a,
                    pc_vec.z
                ))
                
                all_points.append(center + rotated)
            
            all_points.append(pt)
            
            # Store curve data on PI
            pi_curr["curve_radius"] = radius
            pi_curr["curve_length"] = radius * delta
            pi_curr["tangent_length"] = tangent_length
        
        # Add last PI
        all_points.append(pi_objects[-1].location)
        
        # Apply points to spline
        spline.points.add(len(all_points) - 1)
        for i, pt in enumerate(all_points):
            spline.points[i].co = (*pt, 1.0)
        
        # Create object
        curve_obj = bpy.data.objects.new("Alignment_WithCurves", curve_data)
        alignment_col = get_or_create_collection("Alignment")
        alignment_col.objects.link(curve_obj)
        
        # Mark as IFC Alignment
        try:
            curve_obj.civil_ifc.ifc_class = 'IFCALIGNMENTHORIZONTAL'
            curve_obj.civil_ifc.is_alignment_entity = True
        except:
            pass
        
        self.report({'INFO'}, f"Inserted curves at {len(pi_objects)-2} PIs with R={radius:.1f}")
        return {'FINISHED'}

# ============================================================================
# STATION OPERATORS
# ============================================================================

class CIVIL_OT_AddStations(Operator):
    """Add station markers along the alignment"""
    bl_idname = "civil.add_stations"
    bl_label = "Add Station Markers"
    bl_description = "Add station markers along the alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.civil_alignment
        interval = props.station_interval
        
        # Get alignment curve
        alignment_obj = None
        for obj in bpy.data.objects:
            if obj.name in ["Alignment_WithCurves", "Alignment_Tangents"]:
                alignment_obj = obj
                break
        
        if not alignment_obj or alignment_obj.type != 'CURVE':
            self.report({'WARNING'}, "No alignment curve found")
            return {'CANCELLED'}
        
        # Create stations collection
        alignment_col = get_or_create_collection("Alignment")
        stations_col = get_or_create_collection("Stations", alignment_col)
        
        # Get curve data
        curve = alignment_obj.data
        if len(curve.splines) == 0:
            self.report({'WARNING'}, "Alignment curve has no splines")
            return {'CANCELLED'}
        
        spline = curve.splines[0]
        
        # Calculate total length
        total_length = 0.0
        for i in range(len(spline.points) - 1):
            p1 = Vector(spline.points[i].co[:3])
            p2 = Vector(spline.points[i + 1].co[:3])
            total_length += (p2 - p1).length
        
        # Place stations
        station = 0.0
        station_count = 0
        
        while station <= total_length:
            target_length = station
            cumulative = 0.0
            
            for i in range(len(spline.points) - 1):
                p1 = Vector(spline.points[i].co[:3])
                p2 = Vector(spline.points[i + 1].co[:3])
                segment_length = (p2 - p1).length
                
                if cumulative + segment_length >= target_length:
                    t = (target_length - cumulative) / segment_length if segment_length > 0 else 0
                    pos = p1.lerp(p2, t)
                    
                    # Create text object
                    station_text = f"{int(station/100):d}+{int(station%100):02d}"
                    bpy.ops.object.text_add(location=pos)
                    text_obj = context.active_object
                    text_obj.name = f"STA_{station_text}"
                    text_obj.data.body = station_text
                    text_obj.data.size = 5.0
                    text_obj.data.extrude = 0.1
                    
                    # Move to stations collection
                    for col in text_obj.users_collection:
                        col.objects.unlink(text_obj)
                    stations_col.objects.link(text_obj)
                    
                    station_count += 1
                    break
                
                cumulative += segment_length
            
            station += interval
        
        self.report({'INFO'}, f"Added {station_count} station markers")
        return {'FINISHED'}

# ============================================================================
# UTILITY OPERATORS
# ============================================================================

class CIVIL_OT_ClearAlignment(Operator):
    """Remove all alignment objects"""
    bl_idname = "civil.clear_alignment"
    bl_label = "Clear Alignment"
    bl_description = "Remove all alignment objects and start fresh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        collections_to_clear = ["Alignment", "PI_Points", "Stations"]
        
        for col_name in collections_to_clear:
            col = bpy.data.collections.get(col_name)
            if col:
                for obj in list(col.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.collections.remove(col)
        
        self.report({'INFO'}, "Alignment cleared")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

class CIVIL_OT_ExportAlignment(Operator):
    """Export alignment data to JSON"""
    bl_idname = "civil.export_alignment"
    bl_label = "Export Alignment Data"
    bl_description = "Export alignment PI and curve data to JSON"
    bl_options = {'REGISTER'}
    
    filepath: StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        pi_objects = get_pi_objects()
        
        if not pi_objects:
            self.report({'WARNING'}, "No PI points found")
            return {'CANCELLED'}
        
        # Get CRS data
        crs = context.scene.civil_crs
        
        # Build export data
        export_data = {
            "alignment_name": context.scene.civil_alignment.alignment_name,
            "units": crs.units if crs.has_crs else "meters",
            "coordinate_system": {
                "epsg_code": crs.epsg_code,
                "name": crs.coordinate_system_name,
                "datum": crs.datum,
                "projection": crs.projection,
            } if crs.has_crs else None,
            "pi_points": []
        }
        
        for pi in pi_objects:
            pi_data = {
                "number": pi.get("pi_number", 0),
                "station": pi.get("station", 0.0),
                "location": {
                    "x": pi.location.x,
                    "y": pi.location.y,
                    "z": pi.location.z
                }
            }
            
            if "curve_radius" in pi:
                pi_data["curve"] = {
                    "radius": pi["curve_radius"],
                    "length": pi.get("curve_length", 0.0),
                    "tangent_length": pi.get("tangent_length", 0.0)
                }
            
            export_data["pi_points"].append(pi_data)
        
        # Write to file
        with open(self.filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.report({'INFO'}, f"Exported alignment to {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# ============================================================================
# REGISTRATION
# ============================================================================

classes = (
    CIVIL_OT_AddPI,
    CIVIL_OT_CreateTangents,
    CIVIL_OT_InsertCurves,
    CIVIL_OT_AddStations,
    CIVIL_OT_ClearAlignment,
    CIVIL_OT_ExportAlignment,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
