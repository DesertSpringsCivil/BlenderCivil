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
        """Regenerate IFC segments from PIs - PROFESSIONAL METHOD
        
        Creates proper tangent-curve-tangent sequences per professional standards:
        - Tangent segments connect consecutive PIs  
        - Curves are inserted AT intermediate PIs (not at first/last)
        - All elements properly connected: Tangent → Curve → Tangent → Curve → Tangent
        
        Example: For 4 PIs, creates 5 elements:
        - Tangent from PI_0 to BC of curve at PI_1
        - Curve at PI_1
        - Tangent from EC of PI_1 curve to BC of curve at PI_2  
        - Curve at PI_2
        - Tangent from EC of PI_2 curve to PI_3
        """
        self.segments = []
        
        if len(self.pis) < 2:
            return
        
        # Process each pair of consecutive PIs
        for i in range(len(self.pis) - 1):
            curr_pi = self.pis[i]
            next_pi = self.pis[i + 1]
            
            # Determine tangent start position
            if i == 0:
                # First tangent starts at first PI
                start_pos = curr_pi['position']
            else:
                # Check if current PI has a curve
                if curr_pi['radius'] > 0:
                    # Start at EC of curve at current PI
                    prev_pi = self.pis[i - 1]
                    curve_data = self._calculate_curve(
                        prev_pi['position'],
                        curr_pi['position'],
                        next_pi['position'],
                        curr_pi['radius']
                    )
                    if curve_data:
                        start_pos = curve_data['ec']
                    else:
                        start_pos = curr_pi['position']
                else:
                    # No curve, start at current PI
                    start_pos = curr_pi['position']
            
            # Determine tangent end position
            if i + 1 < len(self.pis) - 1 and next_pi['radius'] > 0:
                # Next PI has a curve, tangent ends at BC
                next_next_pi = self.pis[i + 2]
                curve_data = self._calculate_curve(
                    curr_pi['position'],
                    next_pi['position'],
                    next_next_pi['position'],
                    next_pi['radius']
                )
                if curve_data:
                    end_pos = curve_data['bc']
                else:
                    end_pos = next_pi['position']
            else:
                # No curve at next PI, tangent goes to next PI
                end_pos = next_pi['position']
            
            # Create tangent segment
            tangent_seg = self._create_tangent_segment(start_pos, end_pos)
            self.segments.append(tangent_seg)
            
            # Add curve at next PI if applicable (not for last PI)
            print(f"  DEBUG: i={i}, next_PI_id={next_pi['id']}, radius={next_pi['radius']}, check: {i + 1 < len(self.pis) - 1}")
            if i + 1 < len(self.pis) - 1 and next_pi['radius'] > 0:
                print(f"    → Creating curve at PI_{next_pi['id']}")
                next_next_pi = self.pis[i + 2]
                curve_data = self._calculate_curve(
                    curr_pi['position'],
                    next_pi['position'],
                    next_next_pi['position'],
                    next_pi['radius']
                )
                if curve_data:
                    curve_seg = self._create_curve_segment(curve_data, next_pi['id'])
                    self.segments.append(curve_seg)
        
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
    
    def _create_curve_segment(self, curve_data, pi_id=None):
        """Create IFC curve segment with SIGNED radius for turn direction
        
        Per IFC convention:
        - Positive radius = LEFT turn (counterclockwise)
        - Negative radius = RIGHT turn (clockwise)
        """
        name = f"Curve_{pi_id}" if pi_id is not None else f"Curve_{len(self.segments)}"
        
        # Use signed radius based on deflection angle
        signed_radius = curve_data['radius'] if curve_data['deflection'] > 0 else -curve_data['radius']
        # DEBUG OUTPUT
        print(f"  _create_curve_segment: deflection={curve_data['deflection']:.4f} rad ({math.degrees(curve_data['deflection']):.2f}°), radius={curve_data['radius']}, signed_radius={signed_radius}")
        
        segment = self.ifc.create_entity("IfcAlignmentSegment",
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            DesignParameters=self.ifc.create_entity(
                "IfcAlignmentHorizontalSegment",
                StartPoint=self.ifc.create_entity("IfcCartesianPoint",
                    Coordinates=[float(curve_data['bc'].x), float(curve_data['bc'].y)]),
                StartDirection=float(curve_data['start_direction']),
                StartRadiusOfCurvature=float(signed_radius),
                EndRadiusOfCurvature=float(signed_radius),
                SegmentLength=float(curve_data['arc_length']),
                PredefinedType="CIRCULARARC"
            )
        )
        return segment
    
    def _calculate_curve(self, prev_pi, curr_pi, next_pi, radius):
        """Calculate curve geometry from PIs with SIGNED deflection angle
        
        Positive deflection = LEFT turn (counterclockwise)
        Negative deflection = RIGHT turn (clockwise)
        """
        t1 = (curr_pi - prev_pi).normalized()
        t2 = (next_pi - curr_pi).normalized()
        
        # Calculate SIGNED deflection angle using atan2
        # This preserves turn direction information
        angle1 = math.atan2(t1.y, t1.x)
        angle2 = math.atan2(t2.y, t2.x)
        
        # Calculate signed deflection
        deflection = angle2 - angle1
        
        # Normalize to [-π, π]
        if deflection > math.pi:
            deflection -= 2 * math.pi
        elif deflection < -math.pi:
            deflection += 2 * math.pi
        
        # Check if deflection is too small (nearly straight)
        if abs(deflection) < 0.001:
            return None
        
        # Calculate curve geometry
        # Use absolute deflection for tangent length calculation
        tangent_length = radius * math.tan(abs(deflection) / 2)
        bc = curr_pi - t1 * tangent_length
        ec = curr_pi + t2 * tangent_length
        arc_length = radius * abs(deflection)
        
        return {
            'bc': bc,
            'ec': ec,
            'radius': radius,
            'arc_length': arc_length,
            'deflection': deflection,  # SIGNED deflection (+ = left, - = right)
            'start_direction': angle1,
            'turn_direction': 'LEFT' if deflection > 0 else 'RIGHT'
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

