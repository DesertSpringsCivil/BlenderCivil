"""
BlenderCivil v0.3.0 - Operators for Separate Entity Architecture
IFC-Compatible Alignment Creation and Management

This module provides operators for creating and managing alignments
using the separate entity architecture with explicit object relationships.

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, StringProperty
import math

# Import our object creation functions
try:
    from . import alignment_objects_v2 as align_obj
except ImportError:
    import alignment_objects_v2 as align_obj


class CIVIL_OT_create_alignment_separate_v2(Operator):
    """
    Create a professional PI-driven alignment with separate entity architecture.
    
    This operator creates an alignment from existing PI points (Empties) in the scene,
    generating separate tangent and curve objects with proper IFC-compliant relationships.
    
    IFC Mapping: Creates IfcAlignment structure with segments
    """
    bl_idname = "civil.create_alignment_separate_v2"
    bl_label = "Create Professional Alignment (v2)"
    bl_description = "Create alignment from PIs with separate entities and IFC structure"
    bl_options = {'REGISTER', 'UNDO'}
    
    alignment_name: StringProperty(
        name="Alignment Name",
        default="Alignment_01",
        description="Name for the new alignment"
    )
    
    default_radius: FloatProperty(
        name="Default Curve Radius",
        default=500.0,
        min=10.0,
        unit='LENGTH',
        description="Default radius for curves at PIs"
    )
    
    design_speed: FloatProperty(
        name="Design Speed",
        default=35.0,
        min=5.0,
        max=120.0,
        description="Design speed (mph) for this alignment"
    )
    
    def execute(self, context):
        """Execute the alignment creation"""
        
        # Find all PI Empties in scene
        pis = [obj for obj in context.scene.objects 
               if obj.type == 'EMPTY' and obj.name.startswith('PI_')]
        
        if len(pis) < 2:
            self.report({'ERROR'}, "Need at least 2 PI points (Empty objects named PI_*)")
            return {'CANCELLED'}
        
        # Sort PIs by name
        pis.sort(key=lambda x: x.name)
        
        print("\n" + "="*60)
        print(f"Creating Professional Alignment: {self.alignment_name}")
        print(f"  PIs: {len(pis)}")
        print(f"  Default Radius: {self.default_radius}")
        print(f"  Design Speed: {self.design_speed} mph")
        print("="*60)
        
        # Create alignment root
        alignment_root = align_obj.create_alignment_root(
            name=self.alignment_name,
            alignment_type='CENTERLINE',
            design_speed=self.design_speed
        )
        
        # Convert existing Empties to PI points with properties
        pi_objects = []
        for i, pi_empty in enumerate(pis):
            # Set PI properties on existing empty
            pi_empty.parent = alignment_root
            
            props = pi_empty.alignment_pi
            props.index = i + 1
            props.radius = self.default_radius
            props.design_speed = self.design_speed
            props.alignment_root = alignment_root
            
            # Update display
            pi_empty.empty_display_type = 'ARROWS'
            pi_empty.empty_display_size = 5.0
            
            pi_objects.append(pi_empty)
            
            # Move to horizontal layout collection
            h_layout_name = f"{alignment_root.name}_Horizontal"
            if h_layout_name in bpy.data.collections:
                collection = bpy.data.collections[h_layout_name]
                if pi_empty.name not in collection.objects:
                    collection.objects.link(pi_empty)
                # Remove from scene collection if present
                if pi_empty.name in context.scene.collection.objects:
                    context.scene.collection.objects.unlink(pi_empty)
        
        print(f"\nâœ“ Converted {len(pi_objects)} PIs to enhanced objects")
        
        # Create tangent lines between consecutive PIs
        tangents = []
        for i in range(len(pi_objects) - 1):
            tangent_name = f"Tangent_{i+1:03d}"
            tangent = align_obj.create_tangent_line(
                name=tangent_name,
                pi_start=pi_objects[i],
                pi_end=pi_objects[i+1],
                alignment_root=alignment_root
            )
            tangents.append(tangent)
        
        print(f"âœ“ Created {len(tangents)} tangent lines")
        
        # Create curves at intermediate PIs
        curves = []
        for i in range(1, len(pi_objects) - 1):
            curve_name = f"Curve_{i:03d}"
            
            # Get radius from PI properties
            radius = pi_objects[i].alignment_pi.radius
            
            curve = align_obj.create_curve(
                name=curve_name,
                pi=pi_objects[i],
                pi_prev=pi_objects[i-1],
                pi_next=pi_objects[i+1],
                radius=radius,
                alignment_root=alignment_root,
                sample_interval=5.0
            )
            
            if curve:
                curves.append(curve)
                
                # Set up element relationships (linked list structure)
                curve.alignment_curve.previous_element = tangents[i-1]
                curve.alignment_curve.next_element = tangents[i]
                
                tangents[i-1].alignment_tangent.next_element = curve
                tangents[i].alignment_tangent.previous_element = curve
        
        print(f"âœ“ Created {len(curves)} curves")
        
        # Set up tangent-to-tangent relationships where no curve exists
        for i in range(len(tangents) - 1):
            if not tangents[i].alignment_tangent.next_element:
                tangents[i].alignment_tangent.next_element = tangents[i+1]
                tangents[i+1].alignment_tangent.previous_element = tangents[i]
        
        # Calculate stations along alignment
        align_obj.update_stations(alignment_root)
        
        # Print summary
        print("\n" + "="*60)
        print("ALIGNMENT CREATION SUMMARY")
        print("="*60)
        print(f"Name: {self.alignment_name}")
        print(f"Total PIs: {len(pi_objects)}")
        print(f"Tangent Segments: {len(tangents)}")
        print(f"Curve Segments: {len(curves)}")
        print(f"Total Length: {alignment_root.alignment_root.total_length:.2f}")
        print(f"Auto-Update: {'ON' if alignment_root.alignment_root.auto_update_enabled else 'OFF'}")
        print("="*60)
        
        # Report element details
        total_length = alignment_root.alignment_root.total_length
        
        print("\nELEMENT DETAILS:")
        print("-" * 60)
        
        # Get all elements sorted by station
        h_layout_name = f"{alignment_root.name}_Horizontal"
        if h_layout_name in bpy.data.collections:
            collection = bpy.data.collections[h_layout_name]
            
            elements = []
            for obj in collection.objects:
                if hasattr(obj, 'alignment_tangent') and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT':
                    props = obj.alignment_tangent
                    elements.append(('TANGENT', obj.name, props.start_station, props.end_station, props.length))
                elif hasattr(obj, 'alignment_curve') and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE':
                    props = obj.alignment_curve
                    elements.append(('CURVE', obj.name, props.start_station, props.end_station, props.length))
            
            elements.sort(key=lambda x: x[2])  # Sort by start station
            
            for elem_type, name, start_sta, end_sta, length in elements:
                if elem_type == 'TANGENT':
                    print(f"  {elem_type:8s} | {name:15s} | Sta {start_sta:7.2f} - {end_sta:7.2f} | L={length:7.2f}")
                else:
                    obj = bpy.data.objects[name]
                    radius = obj.alignment_curve.radius
                    delta = math.degrees(obj.alignment_curve.delta_angle)
                    print(f"  {elem_type:8s} | {name:15s} | Sta {start_sta:7.2f} - {end_sta:7.2f} | L={length:7.2f} | R={radius:.1f} | Î”={delta:.1f}Â°")
        
        print("=" * 60 + "\n")
        
        self.report({'INFO'}, f"Created alignment '{self.alignment_name}' with {len(tangents)} tangents and {len(curves)} curves")
        
        return {'FINISHED'}


class CIVIL_OT_update_alignment_v2(Operator):
    """
    Update alignment geometry after PI movements.
    
    Manually triggers recalculation of tangents and curves when PIs have been moved.
    This is the manual update button (auto-update uses depsgraph handler).
    """
    bl_idname = "civil.update_alignment_v2"
    bl_label = "Update Alignment (v2)"
    bl_description = "Manually update alignment after moving PIs"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        """Execute the alignment update"""
        
        # Find all alignment roots in scene
        alignment_roots = [obj for obj in context.scene.objects
                          if obj.type == 'EMPTY' and hasattr(obj, 'alignment_root')
                          and obj.alignment_root.object_type == 'ALIGNMENT_ROOT']
        
        if not alignment_roots:
            self.report({'WARNING'}, "No alignments found in scene")
            return {'CANCELLED'}
        
        print("\n" + "="*60)
        print("UPDATING ALIGNMENTS")
        print("="*60)
        
        for alignment_root in alignment_roots:
            print(f"\nUpdating: {alignment_root.name}")
            
            # Get horizontal layout collection
            h_layout_name = f"{alignment_root.name}_Horizontal"
            if h_layout_name not in bpy.data.collections:
                continue
            
            collection = bpy.data.collections[h_layout_name]
            
            # Update all tangents
            tangents = [obj for obj in collection.objects
                       if hasattr(obj, 'alignment_tangent')
                       and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT']
            
            for tangent in tangents:
                align_obj.update_tangent_geometry(tangent)
            
            # Update all curves
            curves = [obj for obj in collection.objects
                     if hasattr(obj, 'alignment_curve')
                     and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE']
            
            for curve in curves:
                align_obj.update_curve_geometry(curve)
            
            # Recalculate stations
            align_obj.update_stations(alignment_root)
            
            print(f"  âœ“ Updated {len(tangents)} tangents and {len(curves)} curves")
            print(f"  âœ“ New total length: {alignment_root.alignment_root.total_length:.2f}")
        
        print("="*60 + "\n")
        
        self.report({'INFO'}, f"Updated {len(alignment_roots)} alignment(s)")
        return {'FINISHED'}


class CIVIL_OT_analyze_alignment_v2(Operator):
    """
    Generate detailed analysis report for alignment.
    
    Prints comprehensive information about the alignment structure,
    elements, and geometric properties.
    """
    bl_idname = "civil.analyze_alignment_v2"
    bl_label = "Analyze Alignment (v2)"
    bl_description = "Generate detailed alignment analysis report"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        """Execute the alignment analysis"""
        
        # Find all alignment roots
        alignment_roots = [obj for obj in context.scene.objects
                          if obj.type == 'EMPTY' and hasattr(obj, 'alignment_root')
                          and obj.alignment_root.object_type == 'ALIGNMENT_ROOT']
        
        if not alignment_roots:
            self.report({'WARNING'}, "No alignments found in scene")
            return {'CANCELLED'}
        
        for alignment_root in alignment_roots:
            props = alignment_root.alignment_root
            
            print("\n" + "="*80)
            print(f"ALIGNMENT ANALYSIS: {props.alignment_name}")
            print("="*80)
            
            print(f"\nGENERAL PROPERTIES:")
            print(f"  Type: {props.alignment_type}")
            print(f"  Design Speed: {props.design_speed} mph")
            print(f"  Total Length: {props.total_length:.2f}")
            print(f"  Auto-Update: {'ENABLED' if props.auto_update_enabled else 'DISABLED'}")
            
            # Get horizontal layout
            h_layout_name = f"{alignment_root.name}_Horizontal"
            if h_layout_name not in bpy.data.collections:
                print("\n  âš  No horizontal layout found")
                continue
            
            collection = bpy.data.collections[h_layout_name]
            
            # Count elements
            pis = [obj for obj in collection.objects
                  if hasattr(obj, 'alignment_pi')
                  and obj.alignment_pi.object_type == 'ALIGNMENT_PI']
            
            tangents = [obj for obj in collection.objects
                       if hasattr(obj, 'alignment_tangent')
                       and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT']
            
            curves = [obj for obj in collection.objects
                     if hasattr(obj, 'alignment_curve')
                     and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE']
            
            print(f"\nELEMENT COUNT:")
            print(f"  PIs: {len(pis)}")
            print(f"  Tangents: {len(tangents)}")
            print(f"  Curves: {len(curves)}")
            print(f"  Total Elements: {len(tangents) + len(curves)}")
            
            # PI Details
            print(f"\nPI DETAILS:")
            print("-" * 80)
            pis.sort(key=lambda x: x.alignment_pi.index)
            for pi in pis:
                pi_props = pi.alignment_pi
                loc = pi.location
                print(f"  {pi.name:10s} | Index: {pi_props.index:2d} | "
                      f"Location: ({loc.x:7.2f}, {loc.y:7.2f}, {loc.z:7.2f}) | "
                      f"Radius: {pi_props.radius:6.1f}")
            
            # Element Details
            print(f"\nELEMENT DETAILS:")
            print("-" * 80)
            
            # Collect and sort all elements
            elements = []
            for obj in collection.objects:
                if hasattr(obj, 'alignment_tangent') and obj.alignment_tangent.object_type == 'ALIGNMENT_TANGENT':
                    props = obj.alignment_tangent
                    elements.append(('TANGENT', obj, props.start_station))
                elif hasattr(obj, 'alignment_curve') and obj.alignment_curve.object_type == 'ALIGNMENT_CURVE':
                    props = obj.alignment_curve
                    elements.append(('CURVE', obj, props.start_station))
            
            elements.sort(key=lambda x: x[2])
            
            for elem_type, obj, _ in elements:
                if elem_type == 'TANGENT':
                    props = obj.alignment_tangent
                    print(f"  {elem_type:8s} | {obj.name:15s} | "
                          f"Sta {props.start_station:8.2f} - {props.end_station:8.2f} | "
                          f"Length: {props.length:8.2f} | "
                          f"Bearing: {math.degrees(props.bearing):7.2f}Â° | "
                          f"Constraint: {props.constraint}")
                else:  # CURVE
                    props = obj.alignment_curve
                    print(f"  {elem_type:8s} | {obj.name:15s} | "
                          f"Sta {props.start_station:8.2f} - {props.end_station:8.2f} | "
                          f"Length: {props.length:8.2f} | "
                          f"R={props.radius:6.1f} | "
                          f"Î”={math.degrees(props.delta_angle):6.2f}Â° | "
                          f"T={props.tangent_length:6.2f} | "
                          f"Constraint: {props.constraint}")
            
            print("="*80 + "\n")
        
        self.report({'INFO'}, f"Analyzed {len(alignment_roots)} alignment(s) - see console for details")
        return {'FINISHED'}


class CIVIL_OT_set_curve_radius_v2(Operator):
    """
    Set the radius of a selected curve.
    
    This operator allows you to modify the radius of an existing curve
    in the alignment and automatically updates the geometry.
    
    Workflow:
    1. Select a curve object
    2. Run operator and specify new radius
    3. Curve geometry updates automatically
    """
    bl_idname = "civil.set_curve_radius_v2"
    bl_label = "Set Curve Radius"
    bl_description = "Set radius of selected curve"
    bl_options = {'REGISTER', 'UNDO'}
    
    radius: FloatProperty(
        name="Radius",
        default=500.0,
        min=10.0,
        unit='LENGTH',
        description="New radius for the curve"
    )
    
    @classmethod
    def poll(cls, context):
        """Only enable if a curve is selected"""
        obj = context.active_object
        return (obj and obj.type == 'CURVE' and 
                hasattr(obj, 'alignment_curve') and
                obj.alignment_curve.object_type == 'ALIGNMENT_CURVE')
    
    def invoke(self, context, event):
        """Set default radius to current curve radius"""
        obj = context.active_object
        if obj and hasattr(obj, 'alignment_curve'):
            self.radius = obj.alignment_curve.radius
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        """Set new radius and update curve"""
        obj = context.active_object
        
        if not obj or obj.type != 'CURVE':
            self.report({'ERROR'}, "No curve object selected")
            return {'CANCELLED'}
        
        if not hasattr(obj, 'alignment_curve'):
            self.report({'ERROR'}, "Selected object is not an alignment curve")
            return {'CANCELLED'}
        
        # Update curve properties
        obj.alignment_curve.radius = self.radius
        
        # Get the alignment root
        alignment_root = obj.parent
        if not alignment_root or not hasattr(alignment_root, 'alignment_root'):
            self.report({'ERROR'}, "Could not find alignment root")
            return {'CANCELLED'}
        
        # Update the curve geometry
        try:
            align_obj.update_curve_geometry(obj)
            
            # Update stations
            align_obj.update_stations(alignment_root)
            
            self.report({'INFO'}, f"Curve radius set to {self.radius:.2f}")
            print(f"Updated curve {obj.name} radius to {self.radius:.2f}")
            
        except Exception as e:
            self.report({'ERROR'}, f"Failed to update curve: {str(e)}")
            return {'CANCELLED'}
        
        return {'FINISHED'}


class CIVIL_OT_insert_pi(Operator):
    """
    Insert a new PI between two existing PIs.
    
    This operator adds a new PI at a specified location between two selected PIs,
    splitting the connecting tangent and creating new curves to maintain continuity.
    
    Workflow:
    1. Select exactly 2 consecutive PIs
    2. Run operator and specify location for new PI
    3. Alignment automatically rebuilds with new PI inserted
    """
    bl_idname = "civil.insert_pi"
    bl_label = "Insert PI"
    bl_description = "Insert a new PI between two selected PIs"
    bl_options = {'REGISTER', 'UNDO'}
    
    location_x: FloatProperty(
        name="X Location",
        default=0.0,
        unit='LENGTH',
        description="X coordinate for new PI"
    )
    
    location_y: FloatProperty(
        name="Y Location",
        default=0.0,
        unit='LENGTH',
        description="Y coordinate for new PI"
    )
    
    location_z: FloatProperty(
        name="Z Location",
        default=0.0,
        unit='LENGTH',
        description="Z coordinate for new PI (elevation)"
    )
    
    curve_radius: FloatProperty(
        name="Curve Radius",
        default=500.0,
        min=10.0,
        unit='LENGTH',
        description="Radius for curves at the new PI"
    )
    
    @classmethod
    def poll(cls, context):
        """Only enable if exactly 2 PIs are selected"""
        selected = [obj for obj in context.selected_objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        return len(selected) == 2
    
    def invoke(self, context, event):
        """Set default location to midpoint between selected PIs"""
        selected_pis = [obj for obj in context.selected_objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        if len(selected_pis) == 2:
            # Calculate midpoint
            mid = (selected_pis[0].location + selected_pis[1].location) / 2
            self.location_x = mid.x
            self.location_y = mid.y
            self.location_z = mid.z
        return context.window_manager.invoke_props_dialog(self)
    
    def execute(self, context):
        """Insert new PI between selected PIs"""
        # Get selected PIs
        selected_pis = sorted(
            [obj for obj in context.selected_objects if obj.type == 'EMPTY' and 'PI_' in obj.name],
            key=lambda x: int(x.name.split('_')[1]) if '_' in x.name else 0
        )
        
        if len(selected_pis) != 2:
            self.report({'ERROR'}, "Must select exactly 2 PIs")
            return {'CANCELLED'}
        
        pi_before = selected_pis[0]
        pi_after = selected_pis[1]
        
        # Verify they are consecutive
        index_before = int(pi_before.name.split('_')[1])
        index_after = int(pi_after.name.split('_')[1])
        
        if index_after != index_before + 1:
            self.report({'ERROR'}, "Selected PIs must be consecutive")
            return {'CANCELLED'}
        
        # Find alignment root
        alignment_root = None
        for obj in bpy.data.objects:
            if hasattr(obj, 'alignment_root') and obj.alignment_root.alignment_name:
                # Check if this PI belongs to this alignment
                if pi_before.parent == obj or self._find_alignment_for_pi(pi_before, obj):
                    alignment_root = obj
                    break
        
        if not alignment_root:
            self.report({'ERROR'}, "Could not find alignment root")
            return {'CANCELLED'}
        
        # Get all PIs in alignment
        all_pis = self._get_all_pis(alignment_root)
        
        # Create new PI location
        new_location = Vector((self.location_x, self.location_y, self.location_z))
        
        # Insert the new PI
        self._insert_pi_in_alignment(
            alignment_root,
            all_pis,
            index_before,
            new_location,
            self.curve_radius
        )
        
        self.report({'INFO'}, f"Inserted new PI between PI_{index_before:03d} and PI_{index_after:03d}")
        return {'FINISHED'}
    
    def _find_alignment_for_pi(self, pi, alignment_root):
        """Check if PI belongs to this alignment"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        if h_layout_name in bpy.data.collections:
            h_layout = bpy.data.collections[h_layout_name]
            return pi.name in h_layout.objects
        return False
    
    def _get_all_pis(self, alignment_root):
        """Get all PI objects for this alignment, sorted by index"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        
        if h_layout_name not in bpy.data.collections:
            return []
        
        h_layout = bpy.data.collections[h_layout_name]
        pis = [obj for obj in h_layout.objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        return sorted(pis, key=lambda x: int(x.name.split('_')[1]) if '_' in x.name else 0)
    
    def _insert_pi_in_alignment(self, alignment_root, all_pis, insert_after_index, location, radius):
        """Insert new PI and rebuild alignment"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        h_layout = bpy.data.collections[h_layout_name]
        
        # Step 1: Create the new PI object
        new_index = insert_after_index + 1
        new_pi_name = f"PI_{new_index:03d}"
        new_pi = align_obj.create_pi_point(
            new_pi_name,
            location,
            new_index,
            alignment_root,
            radius=radius
        )
        
        # Link to collection
        h_layout.objects.link(new_pi)
        new_pi.parent = alignment_root
        
        # Step 2: Renumber all PIs after the insertion point
        for pi in all_pis:
            current_index = int(pi.name.split('_')[1])
            if current_index > insert_after_index:
                new_name = f"PI_{current_index + 1:03d}"
                pi.name = new_name
                if hasattr(pi, 'alignment_pi'):
                    pi.alignment_pi.pi_index = current_index + 1
        
        # Step 3: Find and delete the tangent between the two original PIs
        tangent_to_delete = None
        for obj in h_layout.objects:
            if 'Tangent_' in obj.name and hasattr(obj, 'alignment_tangent'):
                props = obj.alignment_tangent
                pi_start = props.pi_start
                pi_end = props.pi_end
                if pi_start and pi_end:
                    start_idx = int(pi_start.name.split('_')[1]) if '_' in pi_start.name else 0
                    end_idx = int(pi_end.name.split('_')[1]) if '_' in pi_end.name else 0
                    # Adjust for renumbering
                    if start_idx == insert_after_index and end_idx == insert_after_index + 2:
                        tangent_to_delete = obj
                        break
        
        # Step 4: Find and delete curves adjacent to the deleted tangent
        curves_to_delete = []
        if tangent_to_delete:
            for obj in h_layout.objects:
                if 'Curve_' in obj.name and hasattr(obj, 'alignment_curve'):
                    props = obj.alignment_curve
                    if props.tangent_before == tangent_to_delete or props.tangent_after == tangent_to_delete:
                        curves_to_delete.append(obj)
        
        # Delete old elements
        if tangent_to_delete:
            bpy.data.objects.remove(tangent_to_delete, do_unlink=True)
        for curve in curves_to_delete:
            bpy.data.objects.remove(curve, do_unlink=True)
        
        # Step 5: Rebuild alignment with new PI
        # We'll use the update operator to regenerate everything
        bpy.ops.civil.update_alignment_v2()
        
        print(f"Inserted PI at index {new_index}")


class CIVIL_OT_delete_pi(Operator):
    """
    Delete an existing PI from the alignment.
    
    This operator removes a PI and reconnects the alignment by creating a new
    tangent between the neighboring PIs, maintaining continuity.
    
    Workflow:
    1. Select exactly 1 PI (not first or last)
    2. Run operator
    3. PI is deleted and alignment automatically rebuilds
    """
    bl_idname = "civil.delete_pi"
    bl_label = "Delete PI"
    bl_description = "Delete selected PI from alignment"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        """Only enable if exactly 1 PI is selected"""
        selected = [obj for obj in context.selected_objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        return len(selected) == 1
    
    def execute(self, context):
        """Delete selected PI"""
        # Get selected PI
        selected_pis = [obj for obj in context.selected_objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        
        if len(selected_pis) != 1:
            self.report({'ERROR'}, "Must select exactly 1 PI")
            return {'CANCELLED'}
        
        pi_to_delete = selected_pis[0]
        pi_index = int(pi_to_delete.name.split('_')[1])
        
        # Find alignment root
        alignment_root = None
        for obj in bpy.data.objects:
            if hasattr(obj, 'alignment_root') and obj.alignment_root.alignment_name:
                if pi_to_delete.parent == obj or self._find_alignment_for_pi(pi_to_delete, obj):
                    alignment_root = obj
                    break
        
        if not alignment_root:
            self.report({'ERROR'}, "Could not find alignment root")
            return {'CANCELLED'}
        
        # Get all PIs
        all_pis = self._get_all_pis(alignment_root)
        
        # Cannot delete first or last PI
        if pi_index == 1 or pi_index == len(all_pis):
            self.report({'ERROR'}, "Cannot delete first or last PI")
            return {'CANCELLED'}
        
        # Delete the PI
        self._delete_pi_from_alignment(alignment_root, all_pis, pi_to_delete, pi_index)
        
        self.report({'INFO'}, f"Deleted PI_{pi_index:03d}")
        return {'FINISHED'}
    
    def _find_alignment_for_pi(self, pi, alignment_root):
        """Check if PI belongs to this alignment"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        if h_layout_name in bpy.data.collections:
            h_layout = bpy.data.collections[h_layout_name]
            return pi.name in h_layout.objects
        return False
    
    def _get_all_pis(self, alignment_root):
        """Get all PI objects for this alignment, sorted by index"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        
        if h_layout_name not in bpy.data.collections:
            return []
        
        h_layout = bpy.data.collections[h_layout_name]
        pis = [obj for obj in h_layout.objects if obj.type == 'EMPTY' and 'PI_' in obj.name]
        return sorted(pis, key=lambda x: int(x.name.split('_')[1]) if '_' in x.name else 0)
    
    def _delete_pi_from_alignment(self, alignment_root, all_pis, pi_to_delete, pi_index):
        """Delete PI and rebuild alignment"""
        align_name = alignment_root.alignment_root.alignment_name
        h_layout_name = f"{align_name}_Horizontal"
        h_layout = bpy.data.collections[h_layout_name]
        
        # Step 1: Find tangents connected to this PI
        tangents_to_delete = []
        for obj in h_layout.objects:
            if 'Tangent_' in obj.name and hasattr(obj, 'alignment_tangent'):
                props = obj.alignment_tangent
                pi_start = props.pi_start
                pi_end = props.pi_end
                if pi_start == pi_to_delete or pi_end == pi_to_delete:
                    tangents_to_delete.append(obj)
        
        # Step 2: Find curves connected to those tangents
        curves_to_delete = []
        for tangent in tangents_to_delete:
            for obj in h_layout.objects:
                if 'Curve_' in obj.name and hasattr(obj, 'alignment_curve'):
                    props = obj.alignment_curve
                    if props.tangent_before == tangent or props.tangent_after == tangent:
                        curves_to_delete.append(obj)
        
        # Step 3: Delete the PI and its connected elements
        bpy.data.objects.remove(pi_to_delete, do_unlink=True)
        
        for tangent in tangents_to_delete:
            bpy.data.objects.remove(tangent, do_unlink=True)
        
        for curve in curves_to_delete:
            bpy.data.objects.remove(curve, do_unlink=True)
        
        # Step 4: Renumber all PIs after the deleted one
        for pi in all_pis:
            if pi == pi_to_delete:
                continue
            current_index = int(pi.name.split('_')[1])
            if current_index > pi_index:
                new_name = f"PI_{current_index - 1:03d}"
                pi.name = new_name
                if hasattr(pi, 'alignment_pi'):
                    pi.alignment_pi.pi_index = current_index - 1
        
        # Step 5: Rebuild alignment
        bpy.ops.civil.update_alignment_v2()
        
        print(f"Deleted PI_{pi_index:03d}")


# Registration
classes = (
    CIVIL_OT_create_alignment_separate_v2,
    CIVIL_OT_update_alignment_v2,
    CIVIL_OT_analyze_alignment_v2,
    CIVIL_OT_set_curve_radius_v2,
    CIVIL_OT_insert_pi,
    CIVIL_OT_delete_pi,
)


def register():
    """Register operators"""
    for cls in classes:
        bpy.utils.register_class(cls)
    print("âœ“ BlenderCivil v0.3.0: Operators registered")


def unregister():
    """Unregister operators"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
