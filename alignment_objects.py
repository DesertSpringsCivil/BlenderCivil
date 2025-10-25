"""
BlenderCivil v0.3.0 - Object Creation Functions
IFC-Compatible Alignment Object Creation

This module provides functions to create alignment objects (PIs, tangents, curves)
with proper properties, relationships, and IFC-compliant structure.

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
import math
from mathutils import Vector


def create_alignment_root(name="Alignment_01", alignment_type='CENTERLINE', design_speed=35.0):
    """
    Create root container for alignment hierarchy.
    
    Creates an Empty object that serves as the parent for all alignment elements,
    following IFC structure principles (IfcAlignment).
    
    Args:
        name: Name for the alignment
        alignment_type: Type of alignment (CENTERLINE, ROW, etc.)
        design_speed: Design speed in mph
    
    Returns:
        Root Empty object with alignment_root properties
    """
    # Create empty object for root
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 10.0
    
    # Set properties
    props = root.alignment_root
    props.alignment_name = name
    props.alignment_type = alignment_type
    props.design_speed = design_speed
    props.auto_update_enabled = True
    
    # Create collection structure (IFC-style hierarchy)
    collection_name = f"{name}_Collection"
    if collection_name not in bpy.data.collections:
        align_col = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(align_col)
    else:
        align_col = bpy.data.collections[collection_name]
    
    # Create Horizontal_Layout collection
    h_layout_name = f"{name}_Horizontal"
    if h_layout_name not in bpy.data.collections:
        h_layout = bpy.data.collections.new(h_layout_name)
        align_col.children.link(h_layout)
    
    # Link root to main alignment collection
    align_col.objects.link(root)
    
    print(f"✓ Created alignment root: {name}")
    return root


def create_pi_point(name, location, index, alignment_root, radius=500.0, design_speed=35.0):
    """
    Create a PI (Point of Intersection) object.
    
    Creates an Enhanced Empty that serves as a control point for the alignment.
    PIs define where tangents would intersect if extended.
    
    Args:
        name: Name for the PI (e.g., "PI_001")
        location: Vector or tuple (x, y, z) for PI location
        index: Sequential PI number
        alignment_root: Reference to parent alignment object
        radius: Default radius for curve at this PI
        design_speed: Design speed for this segment
    
    Returns:
        Empty object with alignment_pi properties
    """
    # Create empty for PI
    empty = bpy.data.objects.new(name, None)
    empty.empty_display_type = 'ARROWS'
    empty.empty_display_size = 5.0
    empty.location = location
    
    # Set parent to alignment root
    empty.parent = alignment_root
    
    # Set properties
    props = empty.alignment_pi
    props.index = index
    props.radius = radius
    props.design_speed = design_speed
    props.alignment_root = alignment_root
    
    # Add to horizontal layout collection
    h_layout_name = f"{alignment_root.name}_Horizontal"
    if h_layout_name in bpy.data.collections:
        collection = bpy.data.collections[h_layout_name]
        collection.objects.link(empty)
    else:
        # Fallback to scene collection
        bpy.context.scene.collection.objects.link(empty)
    
    print(f"✓ Created PI: {name} at index {index}")
    return empty


def create_tangent_line(name, pi_start, pi_end, alignment_root):
    """
    Create a tangent line object between two PIs.
    
    Creates a Curve object representing a straight line segment (tangent)
    connecting two PI points. This corresponds to a LINE segment in IFC.
    
    Args:
        name: Name for the tangent (e.g., "Tangent_001")
        pi_start: PI object at start of tangent
        pi_end: PI object at end of tangent
        alignment_root: Reference to parent alignment object
    
    Returns:
        Curve object with alignment_tangent properties
    """
    # Create curve data
    curve_data = bpy.data.curves.new(name, 'CURVE')
    curve_data.dimensions = '3D'
    
    # Create spline with 2 points (straight line)
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)  # Total 2 points
    
    # Set points to PI locations
    spline.points[0].co = (*pi_start.location, 1)
    spline.points[1].co = (*pi_end.location, 1)
    
    # Create object
    obj = bpy.data.objects.new(name, curve_data)
    obj.parent = alignment_root
    
    # Visual properties
    curve_data.bevel_depth = 0.5
    curve_data.fill_mode = 'FULL'
    
    # Material - RED for tangents
    mat = bpy.data.materials.get('Tangent_Material')
    if not mat:
        mat = bpy.data.materials.new('Tangent_Material')
        mat.diffuse_color = (0.8, 0.2, 0.2, 1.0)  # Red
    
    if len(curve_data.materials) == 0:
        curve_data.materials.append(mat)
    else:
        curve_data.materials[0] = mat
    
    # Calculate geometric properties
    vec = Vector(pi_end.location) - Vector(pi_start.location)
    length = vec.length
    
    # Calculate bearing (angle from +Y axis, clockwise positive)
    dx = pi_end.location.x - pi_start.location.x
    dy = pi_end.location.y - pi_start.location.y
    bearing = math.atan2(dx, dy)  # atan2(x, y) for angle from +Y
    
    # Set properties
    props = obj.alignment_tangent
    props.constraint = 'FIXED'
    props.alignment_root = alignment_root
    props.pi_start = pi_start
    props.pi_end = pi_end
    props.length = length
    props.bearing = bearing
    
    # Update PI references
    if pi_start:
        pi_start.alignment_pi.tangent_out = obj
    if pi_end:
        pi_end.alignment_pi.tangent_in = obj
    
    # Add to horizontal layout collection
    h_layout_name = f"{alignment_root.name}_Horizontal"
    if h_layout_name in bpy.data.collections:
        collection = bpy.data.collections[h_layout_name]
        collection.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    
    print(f"✓ Created tangent: {name}, length={length:.2f}, bearing={math.degrees(bearing):.2f}°")
    return obj


def create_curve(name, pi, pi_prev, pi_next, radius, alignment_root, sample_interval=5.0):
    """
    Create a circular curve object at a PI.
    
    Creates a Curve object representing a circular arc that maintains tangency
    to the incoming and outgoing tangent lines. This corresponds to a
    CIRCULARARC segment in IFC.
    
    Args:
        name: Name for the curve (e.g., "Curve_001")
        pi: PI object where curve is located
        pi_prev: Previous PI (for calculating incoming tangent direction)
        pi_next: Next PI (for calculating outgoing tangent direction)
        radius: Radius of the circular curve
        alignment_root: Reference to parent alignment object
        sample_interval: Distance between points along curve (for visualization)
    
    Returns:
        Curve object with alignment_curve properties, or None if no curve needed
    """
    # Calculate tangent directions
    v_in = (Vector(pi.location) - Vector(pi_prev.location)).normalized()
    v_out = (Vector(pi_next.location) - Vector(pi.location)).normalized()
    
    # Calculate deflection angle (change in direction)
    # Using 2D cross product for sign and dot product for magnitude
    cross = v_in.x * v_out.y - v_in.y * v_out.x
    dot = v_in.dot(v_out)
    deflection = math.atan2(cross, dot)
    
    # If deflection is too small, no curve needed (straight line)
    if abs(deflection) < 0.001:  # ~0.06 degrees
        print(f"  ⚠ Skipping curve at {name}: deflection too small ({math.degrees(deflection):.3f}°)")
        return None
    
    # Calculate tangent length
    tangent_length = radius * math.tan(abs(deflection) / 2)
    
    # Calculate curve center
    # Perpendicular to incoming tangent, offset by radius
    angle_in = math.atan2(v_in.y, v_in.x)
    offset_angle = angle_in + math.pi/2 if deflection > 0 else angle_in - math.pi/2
    
    center = Vector(pi.location) - Vector((
        tangent_length * v_in.x,
        tangent_length * v_in.y,
        0
    )) + Vector((
        radius * math.cos(offset_angle),
        radius * math.sin(offset_angle),
        0
    ))
    
    # Create curve data
    curve_data = bpy.data.curves.new(name, 'CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    
    # Calculate arc length and number of sample points
    arc_length = abs(radius * deflection)
    num_points = max(10, int(arc_length / sample_interval))
    
    spline.points.add(num_points - 1)  # Add remaining points
    
    # Calculate PC (Point of Curvature) location
    pc = Vector(pi.location) - tangent_length * v_in
    
    # Generate curve points
    start_angle = math.atan2(pc.y - center.y, pc.x - center.x)
    
    for i in range(num_points):
        t = i / (num_points - 1)
        angle = start_angle + t * deflection
        
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        z = pi.location.z  # Keep same elevation for now
        
        spline.points[i].co = (x, y, z, 1)
    
    # Create object
    obj = bpy.data.objects.new(name, curve_data)
    obj.parent = alignment_root
    
    # Visual properties
    curve_data.bevel_depth = 0.5
    curve_data.fill_mode = 'FULL'
    
    # Material - GREEN for curves
    mat = bpy.data.materials.get('Curve_Material')
    if not mat:
        mat = bpy.data.materials.new('Curve_Material')
        mat.diffuse_color = (0.2, 0.8, 0.2, 1.0)  # Green
    
    if len(curve_data.materials) == 0:
        curve_data.materials.append(mat)
    else:
        curve_data.materials[0] = mat
    
    # Set properties
    props = obj.alignment_curve
    props.constraint = 'FREE'
    props.alignment_root = alignment_root
    props.pi = pi
    props.radius = radius
    props.delta_angle = deflection
    props.length = arc_length
    props.tangent_length = tangent_length
    
    # Update PI reference
    if pi:
        pi.alignment_pi.curve = obj
    
    # Add to horizontal layout collection
    h_layout_name = f"{alignment_root.name}_Horizontal"
    if h_layout_name in bpy.data.collections:
        collection = bpy.data.collections[h_layout_name]
        collection.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    
    print(f"✓ Created curve: {name}, R={radius:.2f}, Δ={math.degrees(deflection):.2f}°, L={arc_length:.2f}")
    return obj


def update_tangent_geometry(tangent_obj):
    """
    Update the geometry of a tangent line based on its PI references.
    
    When a PI moves, this function recalculates the tangent line to connect
    the updated PI locations.
    
    Args:
        tangent_obj: Tangent object to update
    """
    props = tangent_obj.alignment_tangent
    
    if not props.pi_start or not props.pi_end:
        print(f"  ⚠ Cannot update {tangent_obj.name}: missing PI references")
        return
    
    # Get curve data
    curve_data = tangent_obj.data
    if not curve_data or not curve_data.splines:
        return
    
    spline = curve_data.splines[0]
    
    # Update point locations
    spline.points[0].co = (*props.pi_start.location, 1)
    spline.points[1].co = (*props.pi_end.location, 1)
    
    # Recalculate geometric properties
    vec = Vector(props.pi_end.location) - Vector(props.pi_start.location)
    props.length = vec.length
    
    dx = props.pi_end.location.x - props.pi_start.location.x
    dy = props.pi_end.location.y - props.pi_start.location.y
    props.bearing = math.atan2(dx, dy)
    
    print(f"  ✓ Updated tangent: {tangent_obj.name}, new length={props.length:.2f}")


def update_curve_geometry(curve_obj):
    """
    Update the geometry of a curve based on its PI and adjacent tangent references.
    
    When a PI or adjacent tangent moves, this function recalculates the curve
    to maintain tangency.
    
    Args:
        curve_obj: Curve object to update
    """
    props = curve_obj.alignment_curve
    
    if not props.pi:
        print(f"  ⚠ Cannot update {curve_obj.name}: missing PI reference")
        return
    
    # Get adjacent PI objects from tangents
    pi = props.pi
    tangent_in = pi.alignment_pi.tangent_in
    tangent_out = pi.alignment_pi.tangent_out
    
    if not tangent_in or not tangent_out:
        print(f"  ⚠ Cannot update {curve_obj.name}: missing tangent references")
        return
    
    pi_prev = tangent_in.alignment_tangent.pi_start
    pi_next = tangent_out.alignment_tangent.pi_end
    
    if not pi_prev or not pi_next:
        print(f"  ⚠ Cannot update {curve_obj.name}: missing adjacent PIs")
        return
    
    # Recalculate curve using same logic as create_curve
    v_in = (Vector(pi.location) - Vector(pi_prev.location)).normalized()
    v_out = (Vector(pi_next.location) - Vector(pi.location)).normalized()
    
    cross = v_in.x * v_out.y - v_in.y * v_out.x
    dot = v_in.dot(v_out)
    deflection = math.atan2(cross, dot)
    
    if abs(deflection) < 0.001:
        # No curve needed anymore - could delete it
        print(f"  ⚠ {curve_obj.name}: deflection now too small, consider removing")
        return
    
    radius = props.radius
    tangent_length = radius * math.tan(abs(deflection) / 2)
    
    # Calculate curve center
    angle_in = math.atan2(v_in.y, v_in.x)
    offset_angle = angle_in + math.pi/2 if deflection > 0 else angle_in - math.pi/2
    
    center = Vector(pi.location) - Vector((
        tangent_length * v_in.x,
        tangent_length * v_in.y,
        0
    )) + Vector((
        radius * math.cos(offset_angle),
        radius * math.sin(offset_angle),
        0
    ))
    
    # Update curve geometry
    curve_data = curve_obj.data
    if not curve_data or not curve_data.splines:
        return
    
    spline = curve_data.splines[0]
    
    # Calculate PC location and generate points
    pc = Vector(pi.location) - tangent_length * v_in
    start_angle = math.atan2(pc.y - center.y, pc.x - center.x)
    
    num_points = len(spline.points)
    for i in range(num_points):
        t = i / (num_points - 1)
        angle = start_angle + t * deflection
        
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        z = pi.location.z
        
        spline.points[i].co = (x, y, z, 1)
    
    # Update properties
    arc_length = abs(radius * deflection)
    props.delta_angle = deflection
    props.length = arc_length
    props.tangent_length = tangent_length
    
    print(f"  ✓ Updated curve: {curve_obj.name}, new Δ={math.degrees(deflection):.2f}°, L={arc_length:.2f}")


def update_stations(alignment_root):
    """
    Recalculate stations for all elements in an alignment.
    
    Walks through the alignment elements in order and updates their
    start/end station values based on cumulative length.
    
    Args:
        alignment_root: Root alignment object
    """
    # Get horizontal layout collection
    h_layout_name = f"{alignment_root.name}_Horizontal"
    if h_layout_name not in bpy.data.collections:
        return
    
    collection = bpy.data.collections[h_layout_name]
    
    # Find all tangents and curves, sort by their PI indices
    elements = []
    for obj in collection.objects:
        if hasattr(obj, 'alignment_tangent') and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT':
            elements.append(('tangent', obj))
        elif hasattr(obj, 'alignment_curve') and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE':
            elements.append(('curve', obj))
    
    # Sort elements by start PI index
    def get_start_index(elem):
        elem_type, obj = elem
        if elem_type == 'tangent':
            pi = obj.alignment_tangent.pi_start
            return pi.alignment_pi.index if pi else 999
        else:  # curve
            pi = obj.alignment_curve.pi
            return pi.alignment_pi.index if pi else 999
    
    elements.sort(key=get_start_index)
    
    # Calculate cumulative stations
    current_station = 0.0
    
    for elem_type, obj in elements:
        if elem_type == 'tangent':
            props = obj.alignment_tangent
            props.start_station = current_station
            props.end_station = current_station + props.length
            current_station += props.length
        else:  # curve
            props = obj.alignment_curve
            props.start_station = current_station
            props.end_station = current_station + props.length
            current_station += props.length
    
    # Update total length on root
    alignment_root.alignment_root.total_length = current_station
    
    print(f"  ✓ Updated stations: total length = {current_station:.2f}")


# Test function
if __name__ == "__main__":
    print("BlenderCivil v0.3.0 - Object Creation Functions")
    print("This module is meant to be imported, not run directly.")
