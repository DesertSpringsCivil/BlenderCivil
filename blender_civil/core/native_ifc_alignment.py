"""
Native IFC Alignment
PI-driven horizontal alignment with professional geometry
"""

import bpy
import math
import ifcopenshell
import ifcopenshell.guid
from mathutils import Vector


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

