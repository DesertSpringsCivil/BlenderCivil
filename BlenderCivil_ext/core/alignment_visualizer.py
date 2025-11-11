"""
Alignment Visualizer (Updated)
3D visualization of IFC alignments in Blender
PIs have NO radius - always green markers!
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
        self.collection = None  # Will use project collection
        self.alignment_empty = None  # Main alignment empty
        self.pi_objects = []
        self.segment_objects = []

        self.setup_hierarchy()

    def setup_hierarchy(self):
        """Create alignment empty in IFC hierarchy (no separate collection)"""
        from .native_ifc_manager import NativeIfcManager

        name = self.alignment.alignment.Name or "Alignment"

        # Use the project collection for all objects (no separate collection)
        self.collection = NativeIfcManager.get_project_collection()
        if not self.collection:
            # Fallback to scene collection
            self.collection = bpy.context.scene.collection

        # Create alignment empty and parent to Alignments organizational empty
        alignments_parent = NativeIfcManager.get_alignments_collection()
        if alignments_parent:
            # Check if alignment empty already exists
            alignment_empty_name = f"📐 {name}"
            if alignment_empty_name in bpy.data.objects:
                self.alignment_empty = bpy.data.objects[alignment_empty_name]
            else:
                # Create new alignment empty
                self.alignment_empty = bpy.data.objects.new(alignment_empty_name, None)
                self.alignment_empty.empty_display_type = 'ARROWS'
                self.alignment_empty.empty_display_size = 2.0
                self.alignment_empty.parent = alignments_parent

                # Link to IFC
                self.alignment_empty["ifc_definition_id"] = self.alignment.alignment.id()
                self.alignment_empty["ifc_class"] = "IfcAlignment"

                # Add to project collection
                self.collection.objects.link(self.alignment_empty)
                print(f"[Visualizer] Created alignment empty: {alignment_empty_name}")
        else:
            print(f"[Visualizer] Warning: No Alignments parent found")

    def _ensure_valid_collection(self):
        """
        Ensure visualizer has a valid collection reference.
        If collection was deleted, get a new one.

        This fixes the "StructRNA of type Collection has been removed" error
        that occurs when the update system tries to create objects after the
        collection was deleted.

        Returns:
            bool: True if valid collection exists, False otherwise
        """
        from .native_ifc_manager import NativeIfcManager

        # Check if current collection is still valid
        try:
            if self.collection and self.collection.name in bpy.data.collections:
                # Collection is still valid
                return True
        except (ReferenceError, AttributeError):
            # Collection reference is dead
            pass

        # Collection is invalid or missing - get a new one
        print("[Visualizer] Collection reference invalid, refreshing...")

        self.collection = NativeIfcManager.get_project_collection()
        if not self.collection:
            # Fallback to scene collection
            self.collection = bpy.context.scene.collection
            print("[Visualizer] Using scene collection as fallback")
        else:
            print(f"[Visualizer] Refreshed to collection: {self.collection.name}")

        return self.collection is not None

    def create_pi_object(self, pi_data):
        """Create Blender Empty for PI - Always GREEN (no radius!)"""

        # CRITICAL: Ensure valid collection before creating objects!
        if not self._ensure_valid_collection():
            print("[Visualizer] ERROR: No valid collection available!")
            return None

        obj = bpy.data.objects.new(f"PI_{pi_data['id']:03d}", None)
        obj.empty_display_type = 'SPHERE'
        obj.empty_display_size = 3.0
        obj.location = Vector((pi_data['position'].x,
                              pi_data['position'].y, 0))

        # Link to IFC
        obj["ifc_pi_id"] = pi_data['id']
        obj["ifc_point_id"] = pi_data['ifc_point'].id()
        # NO RADIUS PROPERTY!

        # CRITICAL: Add these for update system!
        obj['bc_pi_id'] = pi_data['id']
        obj['bc_alignment_id'] = str(id(self.alignment))  # Store as string (Python int too large for C int)

        # CRITICAL: Store reference!
        pi_data['blender_object'] = obj

        # Always GREEN for PIs (they're just intersection points)
        obj.color = (0.0, 1.0, 0.0, 1.0)

        # Link to project collection
        self.collection.objects.link(obj)

        # Parent to alignment empty for hierarchy organization
        if self.alignment_empty:
            obj.parent = self.alignment_empty

        self.pi_objects.append(obj)

        print(f"[Visualizer] Created PI marker: PI_{pi_data['id']:03d}")

        return obj
    
    def create_segment_curve(self, ifc_segment):
        """Create Blender curve for IFC segment"""
        from .native_ifc_manager import NativeIfcManager

        # CRITICAL: Ensure valid collection before creating objects!
        if not self._ensure_valid_collection():
            print("[Visualizer] ERROR: No valid collection available!")
            return None

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
            # Generate smooth arc with PROPER turn direction handling
            spline = curve_data.splines.new('POLY')
            num_points = 32
            spline.points.add(num_points - 1)
            
            start = params.StartPoint.Coordinates
            start_dir = params.StartDirection
            radius = abs(params.StartRadiusOfCurvature)
            arc_length = params.SegmentLength
            angle_span = arc_length / radius
            
            # Determine turn direction from sign of radius
            if params.StartRadiusOfCurvature < 0:
                # Right turn (clockwise)
                center_x = start[0] + radius * math.sin(start_dir)
                center_y = start[1] - radius * math.cos(start_dir)
                angle_span = -angle_span
            else:
                # Left turn (counterclockwise)
                center_x = start[0] - radius * math.sin(start_dir)
                center_y = start[1] + radius * math.cos(start_dir)
            
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
            obj.color = (0.2, 0.6, 1.0, 1.0)  # Blue for tangents
        else:
            obj.color = (1.0, 0.3, 0.3, 1.0)  # Red for curves

        # Link to project collection
        self.collection.objects.link(obj)

        # Parent to alignment empty for hierarchy organization
        if self.alignment_empty:
            obj.parent = self.alignment_empty

        self.segment_objects.append(obj)

        print(f"[Visualizer] Created segment: {ifc_segment.Name} ({params.PredefinedType})")

        return obj
    
    def clear_visualizations(self):
        """Clear all existing visualizations"""
        # Remove all objects in collection
        for obj in self.pi_objects + self.segment_objects:
            if obj and obj.name in bpy.data.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
        
        self.pi_objects.clear()
        self.segment_objects.clear()
        
        print(f"[Visualizer] Cleared visualizations")
    
    def update_visualizations(self):
        """Update all visualizations from current alignment state"""
        # Clear existing
        self.clear_visualizations()
        
        # Recreate all PIs
        for pi_data in self.alignment.pis:
            self.create_pi_object(pi_data)
        
        # Recreate all segments
        for segment in self.alignment.segments:
            self.create_segment_curve(segment)
        
        print(f"[Visualizer] Updated: {len(self.pi_objects)} PIs, {len(self.segment_objects)} segments")

    def update_all(self):
        """Update entire visualization - Required by complete_update_system"""
        self.update_visualizations()

    def visualize_all(self):
        """Create complete visualization - Legacy method for compatibility"""
        print(f"\n[*] Creating {len(self.alignment.pis)} PI markers...")
        for pi_data in self.alignment.pis:
            self.create_pi_object(pi_data)
            print(f"  PI {pi_data['id']}: ({pi_data['position'].x:.2f}, {pi_data['position'].y:.2f})")

        print(f"\n[*] Creating {len(self.alignment.segments)} segment curves...")
        for segment in self.alignment.segments:
            self.create_segment_curve(segment)
            params = segment.DesignParameters
            print(f"  {segment.Name}: {params.PredefinedType:15s} {params.SegmentLength:7.2f}m")

        print(f"\n[+] Visualization complete!")
        print(f"   Collection: {self.collection.name}")
        print(f"   PIs: {len(self.pi_objects)} objects")
        print(f"   Segments: {len(self.segment_objects)} curves")
