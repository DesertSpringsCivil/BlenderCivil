# Sprint 1, Day 2 - Complete Blender Visualization System
# BlenderCivil Native IFC - Visualization Layer

import bpy
import math
import ifcopenshell
import ifcopenshell.guid
from mathutils import Vector

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

print("="*60)
print("SPRINT 1, DAY 2 - BLENDER VISUALIZATION LAYER")
print("="*60)

# ==================== NATIVE IFC MANAGER ====================
class NativeIfcManager:
    """Manages the IFC file and Blender object relationships"""
    
    file = None
    filepath = None
    project = None
    site = None
    
    @classmethod
    def new_file(cls, schema="IFC4X3"):
        """Create new IFC file with basic structure"""
        cls.file = ifcopenshell.file(schema=schema)
        
        # Create project
        cls.project = cls.file.create_entity("IfcProject",
            GlobalId=ifcopenshell.guid.new(),
            Name="BlenderCivil Sprint 1")
        
        # Create site
        cls.site = cls.file.create_entity("IfcSite",
            GlobalId=ifcopenshell.guid.new(),
            Name="Test Site")
        
        return cls.file
    
    @classmethod
    def get_file(cls):
        """Get active IFC file"""
        if cls.file is None:
            cls.new_file()
        return cls.file
    
    @classmethod
    def link_object(cls, blender_obj, ifc_entity):
        """Link Blender object to IFC entity"""
        blender_obj["ifc_definition_id"] = ifc_entity.id()
        blender_obj["ifc_class"] = ifc_entity.is_a()
        blender_obj["GlobalId"] = ifc_entity.GlobalId
    
    @classmethod
    def get_entity(cls, blender_obj):
        """Get IFC entity from Blender object"""
        if "ifc_definition_id" in blender_obj:
            return cls.file.by_id(blender_obj["ifc_definition_id"])
        return None

# ==================== SIMPLE VECTOR ====================
class SimpleVector:
    def __init__(self, x, y=0):
        if isinstance(x, (list, tuple)):
            self.x = float(x[0])
            self.y = float(x[1])
        else:
            self.x = float(x)
            self.y = float(y)
    
    def __sub__(self, other):
        return SimpleVector(self.x - other.x, self.y - other.y)
    
    def __add__(self, other):
        return SimpleVector(self.x + other.x, self.y + other.y)
    
    def __mul__(self, scalar):
        return SimpleVector(self.x * scalar, self.y * scalar)
    
    @property
    def length(self):
        return math.sqrt(self.x**2 + self.y**2)
    
    def normalized(self):
        l = self.length
        if l > 0:
            return SimpleVector(self.x / l, self.y / l)
        return SimpleVector(0, 0)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y

# ==================== NATIVE IFC ALIGNMENT ====================
class NativeIfcAlignment:
    """Native IFC alignment with PI-driven design"""
    
    def __init__(self, ifc_file, name="New Alignment"):
        self.ifc = ifc_file
        self.alignment = None
        self.horizontal = None
        self.pis = []
        self.segments = []
        
        self.create_alignment_structure(name)
    
    def create_alignment_structure(self, name):
        """Create IFC alignment hierarchy"""
        self.alignment = self.ifc.create_entity("IfcAlignment",
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            PredefinedType="USERDEFINED")
        
        self.horizontal = self.ifc.create_entity("IfcAlignmentHorizontal",
            GlobalId=ifcopenshell.guid.new())
        
        self.ifc.create_entity("IfcRelNests",
            GlobalId=ifcopenshell.guid.new(),
            Name="AlignmentToHorizontal",
            RelatingObject=self.alignment,
            RelatedObjects=[self.horizontal])
    
    def add_pi(self, x, y, radius=0.0):
        """Add PI to alignment"""
        pi_data = {
            'id': len(self.pis),
            'position': SimpleVector(x, y),
            'radius': radius,
            'ifc_point': self.ifc.create_entity("IfcCartesianPoint",
                Coordinates=[float(x), float(y)])
        }
        
        self.pis.append(pi_data)
        self.regenerate_segments()
        return pi_data
    
    def regenerate_segments(self):
        """Regenerate IFC segments from PIs"""
        self.segments = []
        
        if len(self.pis) < 2:
            return
        
        for i in range(len(self.pis) - 1):
            curr_pi = self.pis[i]
            next_pi = self.pis[i + 1]
            
            if i > 0 and curr_pi['radius'] > 0 and i < len(self.pis) - 1:
                prev_pi = self.pis[i - 1]
                curve_data = self._calculate_curve(
                    prev_pi['position'],
                    curr_pi['position'],
                    next_pi['position'],
                    curr_pi['radius']
                )
                
                if curve_data:
                    curve_seg = self._create_curve_segment(curve_data)
                    self.segments.append(curve_seg)
            
            if i == 0 or curr_pi['radius'] == 0:
                tangent_seg = self._create_tangent_segment(
                    curr_pi['position'],
                    next_pi['position']
                )
                self.segments.append(tangent_seg)
        
        self._update_ifc_nesting()
    
    def _create_tangent_segment(self, start_pos, end_pos):
        """Create IFC tangent segment"""
        direction = end_pos - start_pos
        length = direction.length
        angle = math.atan2(direction.y, direction.x)
        
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=f"Tangent_{len(self.segments)}",
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(start_pos.x), float(start_pos.y)]),
                StartDirection=float(angle),
                StartRadiusOfCurvature=0.0,
                EndRadiusOfCurvature=0.0,
                SegmentLength=float(length),
                PredefinedType="LINE"
            )
        )
        return segment
    
    def _create_curve_segment(self, curve_data):
        """Create IFC curve segment"""
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=f"Curve_{len(self.segments)}",
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(curve_data['bc'].x), float(curve_data['bc'].y)]),
                StartDirection=float(curve_data['start_direction']),
                StartRadiusOfCurvature=float(curve_data['radius']),
                EndRadiusOfCurvature=float(curve_data['radius']),
                SegmentLength=float(curve_data['arc_length']),
                PredefinedType="CIRCULARARC"
            )
        )
        return segment
    
    def _calculate_curve(self, prev_pi, curr_pi, next_pi, radius):
        """Calculate curve geometry from PIs"""
        t1 = (curr_pi - prev_pi).normalized()
        t2 = (next_pi - curr_pi).normalized()
        
        dot_product = max(-1, min(1, t1.dot(t2)))
        deflection = math.acos(dot_product)
        
        if deflection < 0.001:
            return None
        
        tangent_length = radius * math.tan(deflection / 2)
        bc = curr_pi - t1 * tangent_length
        ec = curr_pi + t2 * tangent_length
        arc_length = radius * deflection
        
        return {
            'bc': bc,
            'ec': ec,
            'radius': radius,
            'arc_length': arc_length,
            'deflection': deflection,
            'start_direction': math.atan2(t1.y, t1.x)
        }
    
    def _update_ifc_nesting(self):
        """Update IFC nesting relationships"""
        if self.segments:
            self.ifc.create_entity("IfcRelNests",
                GlobalId=ifcopenshell.guid.new(),
                Name="HorizontalToSegments",
                RelatingObject=self.horizontal,
                RelatedObjects=self.segments
            )

# ==================== ALIGNMENT VISUALIZER ====================
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

# ==================== CREATE TEST ALIGNMENT ====================
print("\n" + "="*60)
print("CREATING HIGHWAY 101 REALIGNMENT")
print("="*60)

# Create IFC file
ifc = NativeIfcManager.new_file()

# Create alignment
alignment = NativeIfcAlignment(ifc, "Highway 101 Realignment")

# Add PIs
print("\n🎯 Adding PIs...")
alignment.add_pi(0, 0, radius=0)         # Start
alignment.add_pi(100, 0, radius=150)     # Curve R=150m
alignment.add_pi(200, 100, radius=200)   # Curve R=200m
alignment.add_pi(300, 100, radius=0)     # End

# Stats
print(f"\n📊 Alignment Statistics:")
print(f"   Total PIs: {len(alignment.pis)}")
print(f"   Total Segments: {len(alignment.segments)}")

total_length = sum(seg.DesignParameters.SegmentLength for seg in alignment.segments)
print(f"   Total Length: {total_length:.2f} meters")

# Segment details
print(f"\n🛣️  Segment Details:")
station = 0.0
for i, seg in enumerate(alignment.segments):
    params = seg.DesignParameters
    print(f"   [{i}] Station {station:7.2f}: {params.PredefinedType:15s} {params.SegmentLength:7.2f}m", end="")
    if params.PredefinedType == "CIRCULARARC":
        print(f"  R={params.StartRadiusOfCurvature:.2f}m")
    else:
        print()
    station += params.SegmentLength

# Create visualization
print("\n" + "="*60)
print("CREATING BLENDER VISUALIZATION")
print("="*60)

visualizer = AlignmentVisualizer(alignment)
visualizer.visualize_all()

print("\n" + "="*60)
print("✅ SPRINT 1, DAY 2 - MORNING SESSION COMPLETE!")
print("="*60)
print(f"\nVisualization created in viewport:")
print(f"  • 4 PI markers (spheres)")
print(f"  • {len(alignment.segments)} alignment segments (curves)")
print(f"  • Green = tangent points, Orange = curve PIs")
print(f"  • Blue = tangent segments, Red = circular arcs")
print(f"\nLook in your 3D viewport to see the alignment!")
