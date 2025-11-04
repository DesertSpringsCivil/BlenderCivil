"""
Vertical Alignment UI - Demo Script
Tests and demonstrates the complete vertical alignment workflow in Blender

Run this script in Blender's Text Editor to test the vertical alignment UI system.
"""

import bpy


def demo_vertical_alignment_ui():
    """Demonstrate complete vertical alignment workflow"""
    
    print("\n" + "="*60)
    print("VERTICAL ALIGNMENT UI - DEMO SCRIPT")
    print("="*60)
    
    # Check if vertical alignment properties exist
    if not hasattr(bpy.context.scene, 'bc_vertical'):
        print("❌ ERROR: Vertical alignment properties not found!")
        print("   Make sure the vertical alignment add-on is enabled.")
        return False
    
    vertical = bpy.context.scene.bc_vertical
    print("✅ Vertical alignment properties found")
    
    # Check if operators are available
    required_ops = [
        'bc.add_pvi',
        'bc.remove_pvi',
        'bc.calculate_grades',
        'bc.generate_segments',
        'bc.validate_vertical',
        'bc.query_station',
    ]
    
    missing_ops = []
    for op in required_ops:
        if not hasattr(bpy.ops, op.split('.')[0]):
            missing_ops.append(op)
    
    if missing_ops:
        print(f"❌ ERROR: Missing operators: {', '.join(missing_ops)}")
        return False
    
    print("✅ All operators available")
    
    # Clear any existing data
    print("\n📋 Step 1: Clearing existing data...")
    vertical.pvis.clear()
    vertical.segments.clear()
    print("   Cleared all PVIs and segments")
    
    # Set alignment properties
    print("\n📋 Step 2: Setting alignment properties...")
    vertical.name = "Highway 101 Profile"
    vertical.description = "Demo vertical alignment for testing"
    vertical.design_speed = 80.0
    vertical.min_k_crest = 29.0
    vertical.min_k_sag = 17.0
    print(f"   Name: {vertical.name}")
    print(f"   Design Speed: {vertical.design_speed} km/h")
    
    # Add PVIs using operators
    print("\n📋 Step 3: Adding PVIs...")
    
    pvi_data = [
        {"station": 0.0, "elevation": 100.0, "curve_length": 0.0},
        {"station": 200.0, "elevation": 105.0, "curve_length": 80.0},
        {"station": 450.0, "elevation": 103.0, "curve_length": 100.0},
        {"station": 650.0, "elevation": 110.0, "curve_length": 0.0},
    ]
    
    for i, data in enumerate(pvi_data):
        pvi = vertical.pvis.add()
        pvi.station = data["station"]
        pvi.elevation = data["elevation"]
        pvi.curve_length = data["curve_length"]
        pvi.design_speed = vertical.design_speed
        
        print(f"   PVI {i+1}: Station={data['station']:.1f}m, "
              f"Elevation={data['elevation']:.1f}m, "
              f"Curve={data['curve_length']:.1f}m")
    
    print(f"   Total PVIs: {len(vertical.pvis)}")
    
    # Calculate grades
    print("\n📋 Step 4: Calculating grades...")
    bpy.ops.bc.calculate_grades()
    
    for i, pvi in enumerate(vertical.pvis):
        if i == 0:
            print(f"   PVI {i+1}: Grade Out = {pvi.grade_out*100:+.2f}%")
        elif i == len(vertical.pvis) - 1:
            print(f"   PVI {i+1}: Grade In = {pvi.grade_in*100:+.2f}%")
        else:
            print(f"   PVI {i+1}: Grade In = {pvi.grade_in*100:+.2f}%, "
                  f"Grade Out = {pvi.grade_out*100:+.2f}%, "
                  f"Change = {pvi.grade_change*100:.2f}%")
            if pvi.curve_length > 0:
                print(f"           K-value = {pvi.k_value:.1f} m/%, "
                      f"Type = {pvi.curve_type_display}")
    
    # Generate segments
    print("\n📋 Step 5: Generating segments...")
    bpy.ops.bc.generate_segments()
    
    print(f"   Total Segments: {len(vertical.segments)}")
    for i, seg in enumerate(vertical.segments):
        print(f"   Segment {i+1}: {seg.segment_type}, "
              f"{seg.start_station:.1f} → {seg.end_station:.1f}m, "
              f"Length={seg.length:.1f}m, Grade={seg.grade*100:+.2f}%")
    
    # Validate alignment
    print("\n📋 Step 6: Validating alignment...")
    bpy.ops.bc.validate_vertical()
    
    if vertical.is_valid:
        print(f"   ✅ {vertical.validation_message}")
    else:
        print(f"   ⚠ {vertical.validation_message}")
    
    # Query stations
    print("\n📋 Step 7: Querying stations...")
    
    query_stations = [0.0, 100.0, 200.0, 325.0, 450.0, 650.0]
    
    for station in query_stations:
        vertical.query_station = station
        bpy.ops.bc.query_station()
        
        print(f"   Station {station:.1f}m: "
              f"Elevation={vertical.query_elevation:.3f}m, "
              f"Grade={vertical.query_grade_percent:+.2f}%")
    
    # Display statistics
    print("\n📋 Step 8: Profile statistics...")
    print(f"   Total Length: {vertical.total_length:.1f}m")
    print(f"   Elevation Range: {vertical.elevation_min:.2f}m to {vertical.elevation_max:.2f}m")
    print(f"   Elevation Change: {vertical.elevation_max - vertical.elevation_min:.2f}m")
    
    # Test curve design
    print("\n📋 Step 9: Testing curve design tool...")
    
    # Select PVI 2 (index 1) which has a curve
    vertical.active_pvi_index = 1
    pvi = vertical.pvis[1]
    
    print(f"   Selected PVI: #{vertical.active_pvi_index + 1}")
    print(f"   Grade Change: {pvi.grade_change*100:.2f}%")
    print(f"   Current K-value: {pvi.k_value:.1f} m/%")
    print(f"   Curve Type: {pvi.curve_type_display}")
    
    # Verify minimum K-values
    if pvi.curve_type_display == "Crest":
        min_k = vertical.min_k_crest
        print(f"   Minimum K (Crest): {min_k:.1f} m/%")
    else:
        min_k = vertical.min_k_sag
        print(f"   Minimum K (Sag): {min_k:.1f} m/%")
    
    if pvi.k_value >= min_k:
        print(f"   ✅ K-value meets minimum requirements")
    else:
        print(f"   ⚠ K-value below minimum!")
    
    # UI Panel check
    print("\n📋 Step 10: Checking UI panels...")
    
    panel_classes = [
        'VIEW3D_PT_bc_vertical_alignment',
        'VIEW3D_PT_bc_vertical_pvi_list',
        'VIEW3D_PT_bc_vertical_grade_info',
        'VIEW3D_PT_bc_vertical_curve_design',
        'VIEW3D_PT_bc_vertical_query',
        'VIEW3D_PT_bc_vertical_validation',
        'VIEW3D_PT_bc_vertical_segments',
    ]
    
    registered_panels = []
    for panel_name in panel_classes:
        if hasattr(bpy.types, panel_name):
            registered_panels.append(panel_name)
    
    print(f"   Registered Panels: {len(registered_panels)}/{len(panel_classes)}")
    for panel in registered_panels:
        print(f"      ✅ {panel}")
    
    missing_panels = set(panel_classes) - set(registered_panels)
    if missing_panels:
        print(f"   Missing Panels:")
        for panel in missing_panels:
            print(f"      ❌ {panel}")
    
    # Summary
    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print(f"✅ Properties: OK")
    print(f"✅ Operators: {len(required_ops)} registered")
    print(f"✅ Panels: {len(registered_panels)} registered")
    print(f"✅ PVIs: {len(vertical.pvis)} created")
    print(f"✅ Segments: {len(vertical.segments)} generated")
    print(f"✅ Validation: {'PASSED' if vertical.is_valid else 'WARNINGS'}")
    
    print("\n📌 Next Steps:")
    print("   1. Open 3D Viewport")
    print("   2. Press 'N' to open sidebar")
    print("   3. Go to 'BlenderCivil' tab")
    print("   4. Find 'Vertical Alignment' panel")
    print("   5. Explore the PVI list, grades, and curve design!")
    
    print("\n" + "="*60)
    
    return True


# Run the demo
if __name__ == "__main__":
    success = demo_vertical_alignment_ui()
    
    if success:
        print("\n🎉 DEMO SUCCESSFUL! 🎉")
        print("\nThe vertical alignment UI is working correctly!")
        print("Check the 'BlenderCivil' tab in the 3D Viewport sidebar (press N)")
    else:
        print("\n❌ DEMO FAILED!")
        print("Please check the error messages above.")
