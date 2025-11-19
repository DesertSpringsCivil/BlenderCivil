# ==============================================================================
# BlenderCivil - Civil Engineering Tools for Blender
# Copyright (c) 2024-2025 Michael Yoder / Desert Springs Civil Engineering PLLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Primary Author: Michael Yoder
# Company: Desert Springs Civil Engineering PLLC
# ==============================================================================

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

        # Validate that alignments_parent still exists in Blender
        if alignments_parent:
            try:
                # Test if object is still valid
                _ = alignments_parent.name
            except ReferenceError:
                # Object was deleted, recreate the hierarchy
                print(f"[Visualizer] Alignments parent was deleted, recreating hierarchy")
                NativeIfcManager._create_blender_hierarchy()
                alignments_parent = NativeIfcManager.get_alignments_collection()

        if alignments_parent:
            # Check if alignment empty already exists and is valid
            alignment_empty_name = f"📐 {name}"
            if alignment_empty_name in bpy.data.objects:
                existing_empty = bpy.data.objects[alignment_empty_name]
                # Validate it's still valid
                try:
                    _ = existing_empty.name
                    self.alignment_empty = existing_empty
                except ReferenceError:
                    # Was deleted, will create new one below
                    self.alignment_empty = None
            else:
                self.alignment_empty = None

            if not self.alignment_empty:
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
        If collection was deleted (e.g., by undo), fall back to scene collection.

        This fixes the "StructRNA of type Collection has been removed" error
        that occurs when the update system tries to create objects after the
        collection was deleted.

        Returns:
            bool: True if valid collection exists, False otherwise
        """
        # Check if current collection is still valid
        try:
            if self.collection and self.collection.name in bpy.data.collections:
                # Collection is still valid
                return True
        except (ReferenceError, AttributeError):
            # Collection reference is dead
            pass

        # Collection is invalid - use scene collection (always valid)
        # Don't try to recreate hierarchy during visualization - that can cause issues
        print("[Visualizer] Collection was deleted (undo?), using scene collection")
        self.collection = bpy.context.scene.collection

        # Also clear alignment empty reference since hierarchy is gone
        self.alignment_empty = None

        return True

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

        # Parent to alignment empty for hierarchy organization FIRST
        # (must be done before linking to collection for proper Outliner hierarchy)
        if self.alignment_empty:
            try:
                _ = self.alignment_empty.name
                obj.parent = self.alignment_empty
            except (ReferenceError, AttributeError):
                # Alignment empty was deleted, skip parenting
                pass

        # Link to collection AFTER parenting (already validated by _ensure_valid_collection)
        self.collection.objects.link(obj)

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
            is_right_turn = params.StartRadiusOfCurvature < 0

            # Debug output
            turn_type = "RIGHT" if is_right_turn else "LEFT"
            print(f"[Visualizer] Curve {ifc_segment.Name}: {turn_type} turn, R={params.StartRadiusOfCurvature:.2f}, start=({start[0]:.2f},{start[1]:.2f})")

            if is_right_turn:
                # Right turn (clockwise)
                center_x = start[0] + radius * math.sin(start_dir)
                center_y = start[1] - radius * math.cos(start_dir)
                angle_span = -angle_span
            else:
                # Left turn (counterclockwise)
                center_x = start[0] - radius * math.sin(start_dir)
                center_y = start[1] + radius * math.cos(start_dir)

            # Generate arc points
            # CRITICAL: Tangent-to-radius conversion differs by turn direction!
            for i in range(num_points):
                t = i / (num_points - 1)
                angle = start_dir + angle_span * t

                # Convert tangent bearing to radial angle
                if is_right_turn:
                    # Right turn: radius is 90° CCW from tangent
                    radial_angle = angle + math.pi/2
                else:
                    # Left turn: radius is 90° CW from tangent
                    radial_angle = angle - math.pi/2

                x = center_x + radius * math.cos(radial_angle)
                y = center_y + radius * math.sin(radial_angle)
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

        # Parent to alignment empty for hierarchy organization FIRST
        # (must be done before linking to collection for proper Outliner hierarchy)
        if self.alignment_empty:
            try:
                _ = self.alignment_empty.name
                obj.parent = self.alignment_empty
            except (ReferenceError, AttributeError):
                # Alignment empty was deleted, skip parenting
                pass

        # Link to collection AFTER parenting (already validated by _ensure_valid_collection)
        self.collection.objects.link(obj)

        self.segment_objects.append(obj)

        print(f"[Visualizer] Created segment: {ifc_segment.Name} ({params.PredefinedType})")

        return obj
    
    def clear_visualizations(self):
        """Clear all existing visualizations"""
        # Remove all objects in tracked lists
        for obj in self.pi_objects + self.segment_objects:
            try:
                if obj and obj.name in bpy.data.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
            except (ReferenceError, AttributeError, RuntimeError):
                # Object already deleted or invalid - skip it
                pass

        self.pi_objects.clear()
        self.segment_objects.clear()

        # CRITICAL: Also remove any orphaned objects by name pattern
        # This handles the case where we're reloading and old objects exist
        # but aren't in our tracked lists
        if self.alignment_empty:
            try:
                # Remove all children of the alignment empty
                for child in list(self.alignment_empty.children):
                    try:
                        bpy.data.objects.remove(child, do_unlink=True)
                    except:
                        pass
            except (ReferenceError, AttributeError):
                pass

        print(f"[Visualizer] Cleared visualizations")
    
    def update_visualizations(self):
        """Update all visualizations from current alignment state"""
        # Clear existing
        self.clear_visualizations()

        # Recreate all PIs
        for pi_data in self.alignment.pis:
            try:
                self.create_pi_object(pi_data)
            except Exception as e:
                print(f"[Visualizer] Error creating PI {pi_data.get('id', '?')}: {e}")

        # Recreate all segments
        for segment in self.alignment.segments:
            try:
                self.create_segment_curve(segment)
            except Exception as e:
                print(f"[Visualizer] Error creating segment: {e}")

        print(f"[Visualizer] Updated: {len(self.pi_objects)} PIs, {len(self.segment_objects)} segments")

    def update_segments_in_place(self):
        """
        Update segment curves in-place without deleting/recreating objects.
        Safe to call during modal operations (like G for grab/move).
        Works alongside BlenderBIM without conflicts.
        """
        import math

        # Only update existing segments - don't delete/recreate
        for i, segment in enumerate(self.alignment.segments):
            if i >= len(self.segment_objects):
                # Need more segment objects - create them
                try:
                    self.create_segment_curve(segment)
                except Exception as e:
                    print(f"[Visualizer] Error creating new segment: {e}")
                continue

            # Get existing segment object
            seg_obj = self.segment_objects[i]

            # Safety check - if object was deleted (e.g., by undo), recreate it
            needs_recreation = False
            try:
                if not seg_obj or seg_obj.name not in bpy.data.objects:
                    needs_recreation = True
            except (ReferenceError, AttributeError):
                needs_recreation = True

            if needs_recreation:
                # Object was deleted, recreate it
                try:
                    # create_segment_curve appends to segment_objects, so we need to handle that
                    old_len = len(self.segment_objects)
                    new_obj = self.create_segment_curve(segment)

                    if new_obj:
                        # Remove from end where it was appended
                        if len(self.segment_objects) > old_len:
                            self.segment_objects.pop()

                        # Put it in the correct position
                        if i < len(self.segment_objects):
                            self.segment_objects[i] = new_obj
                        else:
                            # If list isn't long enough, append is correct
                            self.segment_objects.append(new_obj)

                        print(f"[Visualizer] Recreated segment {i} (was deleted)")
                except Exception as e:
                    print(f"[Visualizer] Error recreating segment {i}: {e}")
                continue

            # Update curve geometry data in-place
            try:
                params = segment.DesignParameters

                # CRITICAL: Update object name to match IFC segment name
                if seg_obj.name != segment.Name:
                    seg_obj.name = segment.Name

                # Also update color based on type
                if params.PredefinedType == "LINE":
                    seg_obj.color = (0.2, 0.6, 1.0, 1.0)  # Blue for tangents
                elif params.PredefinedType == "CIRCULARARC":
                    seg_obj.color = (1.0, 0.3, 0.3, 1.0)  # Red for curves

                curve_data = seg_obj.data

                # Clear existing splines
                curve_data.splines.clear()

                # Recreate geometry based on type
                if params.PredefinedType == "LINE":
                    # Tangent line
                    spline = curve_data.splines.new('POLY')
                    spline.points.add(1)  # Total 2 points

                    start = params.StartPoint.Coordinates
                    spline.points[0].co = (start[0], start[1], 0, 1)

                    length = params.SegmentLength
                    angle = params.StartDirection
                    end_x = start[0] + length * math.cos(angle)
                    end_y = start[1] + length * math.sin(angle)
                    spline.points[1].co = (end_x, end_y, 0, 1)

                elif params.PredefinedType == "CIRCULARARC":
                    # Circular arc
                    start = params.StartPoint.Coordinates
                    radius = abs(params.StartRadiusOfCurvature)  # FIXED: Use StartRadiusOfCurvature directly
                    angle_start = params.StartDirection
                    length = params.SegmentLength

                    # Calculate arc parameters
                    angle_subtended = length / radius
                    is_ccw = params.StartRadiusOfCurvature > 0  # FIXED: Use StartRadiusOfCurvature directly

                    if not is_ccw:
                        angle_subtended = -angle_subtended

                    # Center point
                    center_angle = angle_start + (math.pi / 2 if is_ccw else -math.pi / 2)
                    center_x = start[0] + radius * math.cos(center_angle)
                    center_y = start[1] + radius * math.sin(center_angle)

                    # Create arc points
                    num_points = max(8, int(abs(angle_subtended) * radius / 5))
                    spline = curve_data.splines.new('POLY')
                    spline.points.add(num_points - 1)

                    for j in range(num_points):
                        t = j / (num_points - 1)
                        angle = angle_start + t * angle_subtended - (math.pi / 2 if is_ccw else -math.pi / 2)
                        x = center_x + radius * math.cos(angle)
                        y = center_y + radius * math.sin(angle)
                        spline.points[j].co = (x, y, 0, 1)

            except Exception as e:
                print(f"[Visualizer] Error updating segment {i} geometry: {e}")

        # Remove extra segment objects if alignment has fewer segments now
        while len(self.segment_objects) > len(self.alignment.segments):
            extra_obj = self.segment_objects.pop()
            try:
                if extra_obj and extra_obj.name in bpy.data.objects:
                    bpy.data.objects.remove(extra_obj, do_unlink=True)
            except:
                pass

        print(f"[Visualizer] Updated {len(self.segment_objects)} segments in-place")

    def update_all(self):
        """Update entire visualization - Required by complete_update_system"""
        # FIRST: Ensure we have a valid collection for all operations
        # This prevents some objects going to hierarchy and others to scene root
        self._ensure_valid_collection()

        # Validate and recreate PI objects if they were deleted (e.g., by undo)
        for pi_data in self.alignment.pis:
            blender_obj = pi_data.get('blender_object')
            needs_recreation = False

            if blender_obj is not None:
                # Check if object still exists
                try:
                    _ = blender_obj.name
                    if blender_obj.name not in bpy.data.objects:
                        needs_recreation = True
                except (ReferenceError, AttributeError):
                    needs_recreation = True
            else:
                needs_recreation = True

            if needs_recreation:
                # Recreate PI object
                try:
                    self.create_pi_object(pi_data)
                    print(f"[Visualizer] Recreated PI {pi_data['id']} (was deleted)")
                except Exception as e:
                    print(f"[Visualizer] Error recreating PI {pi_data['id']}: {e}")

        # Use in-place updates to avoid conflicts with modal operators
        self.update_segments_in_place()

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
