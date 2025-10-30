"""
Alignment Visualizer
3D visualization of IFC alignments in Blender
"""

import bpy
import math
import ifcopenshell
import ifcopenshell.guid
from mathutils import Vector


class AlignmentVisualizer:
    """Create Blender visualization of IFC alignment"""
    
    def __init__(self, native_alignment):
        self.alignment = native_alignment
        self.collection = None
        self.pi_objects = []
        self.segment_objects = []
        
        self.setup_collection()
    
    def setup_collection(self):
        """Create collection for alignment"""
        name = self.alignment.alignment.Name or "Alignment"
        
        if name in bpy.data.collections:
            self.collection = bpy.data.collections[name]
        else:
            self.collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(self.collection)
        
        self.collection["ifc_definition_id"] = self.alignment.alignment.id()
        self.collection["ifc_class"] = "IfcAlignment"
    
    def create_pi_object(self, pi_data):
        """Create Blender Empty for PI"""
        obj = bpy.data.objects.new(f"PI_{pi_data['id']:03d}", None)
        obj.empty_display_type = 'SPHERE'
        obj.empty_display_size = 3.0
        obj.location = Vector((pi_data['position'].x, 
                              pi_data['position'].y, 0))
        
        # Link to IFC
        obj["ifc_pi_id"] = pi_data['id']
        obj["ifc_point_id"] = pi_data['ifc_point'].id()
        obj["radius"] = pi_data['radius']
        
        # Color code
        if pi_data['radius'] > 0:
            obj.color = (1.0, 0.5, 0.0, 1.0)  # Orange for curves
        else:
            obj.color = (0.0, 1.0, 0.0, 1.0)  # Green for tangent points
        
        self.collection.objects.link(obj)
        self.pi_objects.append(obj)
        return obj
    
    def create_segment_curve(self, ifc_segment):
        """Create Blender curve for IFC segment"""
        params = ifc_segment.DesignParameters
        
        # Create curve data
        curve_data = bpy.data.curves.new(
            name=ifc_segment.Name or "Segment",
            type='CURVE'
        )
        curve_data.dimensions = '3D'
        curve_data.resolution_u = 24
        
        # Create spline based on type
        if params.PredefinedType == "LINE":
            spline = curve_data.splines.new('POLY')
            spline.points.add(1)
            
            start = params.StartPoint.Coordinates
            length = params.SegmentLength
            angle = params.StartDirection
            
            spline.points[0].co = (start[0], start[1], 0, 1)
            end_x = start[0] + length * math.cos(angle)
            end_y = start[1] + length * math.sin(angle)
            spline.points[1].co = (end_x, end_y, 0, 1)
            
        elif params.PredefinedType == "CIRCULARARC":
            # Generate smooth arc
            spline = curve_data.splines.new('POLY')
            num_points = 32
            spline.points.add(num_points - 1)
            
            start = params.StartPoint.Coordinates
            start_dir = params.StartDirection
            radius = params.StartRadiusOfCurvature
            arc_length = params.SegmentLength
            angle_span = arc_length / radius
            
            # Calculate center
            center_offset_x = -radius * math.sin(start_dir)
            center_offset_y = radius * math.cos(start_dir)
            center_x = start[0] + center_offset_x
            center_y = start[1] + center_offset_y
            
            # Generate arc points
            for i in range(num_points):
                t = i / (num_points - 1)
                angle = start_dir + angle_span * t
                x = center_x + radius * math.cos(angle - math.pi/2)
                y = center_y + radius * math.sin(angle - math.pi/2)
                spline.points[i].co = (x, y, 0, 1)
        
        # Create object
        obj = bpy.data.objects.new(ifc_segment.Name, curve_data)
        
        # Link to IFC
        NativeIfcManager.link_object(obj, ifc_segment)
        
        # Visual properties
        curve_data.bevel_depth = 0.5
        
        # Color code
        if params.PredefinedType == "LINE":
            obj.color = (0.2, 0.6, 1.0, 1.0)  # Blue
        else:
            obj.color = (1.0, 0.3, 0.3, 1.0)  # Red
        
        self.collection.objects.link(obj)
        self.segment_objects.append(obj)
        return obj
    
    def visualize_all(self):
        """Create complete visualization"""
        print(f"\n📍 Creating {len(self.alignment.pis)} PI markers...")
        for pi_data in self.alignment.pis:
            self.create_pi_object(pi_data)
            print(f"  PI {pi_data['id']}: ({pi_data['position'].x:.2f}, {pi_data['position'].y:.2f}) R={pi_data['radius']:.2f}m")
        
        print(f"\n🛣️  Creating {len(self.alignment.segments)} segment curves...")
        for segment in self.alignment.segments:
            self.create_segment_curve(segment)
            params = segment.DesignParameters
            print(f"  {segment.Name}: {params.PredefinedType:15s} {params.SegmentLength:7.2f}m")
        
        print(f"\n✅ Visualization complete!")
        print(f"   Collection: {self.collection.name}")
        print(f"   PIs: {len(self.pi_objects)} objects")
        print(f"   Segments: {len(self.segment_objects)} curves")

