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
        
        print(f"\n✓ Converted {len(pi_objects)} PIs to enhanced objects")
        
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
        
        print(f"✓ Created {len(tangents)} tangent lines")
        
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
        
        print(f"✓ Created {len(curves)} curves")
        
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
                    print(f"  {elem_type:8s} | {name:15s} | Sta {start_sta:7.2f} - {end_sta:7.2f} | L={length:7.2f} | R={radius:.1f} | Δ={delta:.1f}°")
        
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
            
            print(f"  ✓ Updated {len(tangents)} tangents and {len(curves)} curves")
            print(f"  ✓ New total length: {alignment_root.alignment_root.total_length:.2f}")
        
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
                print("\n  ⚠ No horizontal layout found")
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
                          f"Bearing: {math.degrees(props.bearing):7.2f}° | "
                          f"Constraint: {props.constraint}")
                else:  # CURVE
                    props = obj.alignment_curve
                    print(f"  {elem_type:8s} | {obj.name:15s} | "
                          f"Sta {props.start_station:8.2f} - {props.end_station:8.2f} | "
                          f"Length: {props.length:8.2f} | "
                          f"R={props.radius:6.1f} | "
                          f"Δ={math.degrees(props.delta_angle):6.2f}° | "
                          f"T={props.tangent_length:6.2f} | "
                          f"Constraint: {props.constraint}")
            
            print("="*80 + "\n")
        
        self.report({'INFO'}, f"Analyzed {len(alignment_roots)} alignment(s) - see console for details")
        return {'FINISHED'}


# Registration
classes = (
    CIVIL_OT_create_alignment_separate_v2,
    CIVIL_OT_update_alignment_v2,
    CIVIL_OT_analyze_alignment_v2,
)


def register():
    """Register operators"""
    for cls in classes:
        bpy.utils.register_class(cls)
    print("✓ BlenderCivil v0.3.0: Operators registered")


def unregister():
    """Unregister operators"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
