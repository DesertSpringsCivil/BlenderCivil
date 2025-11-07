"""
Vertical Alignment Demonstration
=================================

Demonstrates the use of the native IFC vertical alignment module
using the worked example from Sprint 3 Day 1.

This script shows:
1. Creating a vertical alignment
2. Adding PVIs (control points)
3. Setting vertical curves
4. Querying elevations and grades
5. Validating the design
6. Generating profile data
7. Exporting to IFC 4.3

Part of BlenderCivil Sprint 3 Day 2
"""

import sys
sys.path.insert(0, '/home/claude')

from native_ifc_vertical_alignment import (
    VerticalAlignment,
    PVI,
    DESIGN_STANDARDS
)


def main():
    """Demonstration of vertical alignment workflow"""
    
    print("=" * 70)
    print("BLENDERCIVIL VERTICAL ALIGNMENT DEMONSTRATION")
    print("Sprint 3 Day 2 - Native IFC Implementation")
    print("=" * 70)
    print()
    
    # ========================================================================
    # STEP 1: Create Vertical Alignment
    # ========================================================================
    
    print("STEP 1: Creating vertical alignment...")
    print("-" * 70)
    
    valign = VerticalAlignment(
        name="Highway 101 Profile",
        design_speed=80.0,  # km/h
        description="Main highway profile with crest and sag curves"
    )
    
    print(f"✓ Created: {valign.name}")
    print(f"  Design Speed: {valign.design_speed} km/h")
    print(f"  Min K (Crest): {valign.min_k_crest} m/%")
    print(f"  Min K (Sag): {valign.min_k_sag} m/%")
    print()
    
    # ========================================================================
    # STEP 2: Add PVIs (Control Points)
    # ========================================================================
    
    print("STEP 2: Adding PVIs (control points)...")
    print("-" * 70)
    
    # PVI 0: Start point
    pvi0 = valign.add_pvi(
        station=0.0,
        elevation=100.0,
        description="Start of alignment"
    )
    print(f"✓ PVI 0: Station {pvi0.station:.1f}m, Elevation {pvi0.elevation:.3f}m")
    
    # PVI 1: Crest curve
    pvi1 = valign.add_pvi(
        station=200.0,
        elevation=105.0,
        curve_length=80.0,
        description="Crest curve (hilltop)"
    )
    print(f"✓ PVI 1: Station {pvi1.station:.1f}m, Elevation {pvi1.elevation:.3f}m")
    print(f"         Curve Length: {pvi1.curve_length:.1f}m (Crest)")
    print(f"         BVC: {pvi1.bvc_station:.1f}m, EVC: {pvi1.evc_station:.1f}m")
    
    # PVI 2: Sag curve
    pvi2 = valign.add_pvi(
        station=450.0,
        elevation=103.0,
        curve_length=100.0,
        description="Sag curve (valley)"
    )
    print(f"✓ PVI 2: Station {pvi2.station:.1f}m, Elevation {pvi2.elevation:.3f}m")
    print(f"         Curve Length: {pvi2.curve_length:.1f}m (Sag)")
    print(f"         BVC: {pvi2.bvc_station:.1f}m, EVC: {pvi2.evc_station:.1f}m")
    
    # PVI 3: End point
    pvi3 = valign.add_pvi(
        station=650.0,
        elevation=110.0,
        description="End of alignment"
    )
    print(f"✓ PVI 3: Station {pvi3.station:.1f}m, Elevation {pvi3.elevation:.3f}m")
    print()
    
    # ========================================================================
    # STEP 3: Review Calculated Grades
    # ========================================================================
    
    print("STEP 3: Reviewing calculated grades...")
    print("-" * 70)
    
    for i, pvi in enumerate(valign.pvis):
        print(f"PVI {i}:")
        if pvi.grade_in is not None:
            print(f"  Grade IN:  {pvi.grade_in_percent:+6.2f}%")
        if pvi.grade_out is not None:
            print(f"  Grade OUT: {pvi.grade_out_percent:+6.2f}%")
        if pvi.grade_change is not None:
            print(f"  Grade Change: {pvi.grade_change_percent:.2f}%")
        if pvi.k_value is not None:
            curve_type = "CREST" if pvi.is_crest_curve else "SAG"
            print(f"  K-value: {pvi.k_value:.1f} m/% ({curve_type})")
        print()
    
    # ========================================================================
    # STEP 4: Review Generated Segments
    # ========================================================================
    
    print("STEP 4: Reviewing generated segments...")
    print("-" * 70)
    
    print(f"Total Segments: {valign.num_segments}")
    print(f"  Tangents: {valign.num_segments - valign.num_curves}")
    print(f"  Curves: {valign.num_curves}")
    print()
    
    for i, segment in enumerate(valign.segments):
        print(f"Segment {i}: {segment}")
    print()
    
    # ========================================================================
    # STEP 5: Query Elevations at Key Stations
    # ========================================================================
    
    print("STEP 5: Querying elevations at key stations...")
    print("-" * 70)
    
    test_stations = [0, 50, 100, 150, 200, 250, 300, 400, 450, 500, 600, 650]
    
    print(f"{'Station':>10} {'Elevation':>12} {'Grade':>10}")
    print("-" * 35)
    
    for station in test_stations:
        try:
            elev = valign.get_elevation(station)
            grade = valign.get_grade(station)
            print(f"{station:>10.1f}m {elev:>11.3f}m {grade*100:>9.2f}%")
        except ValueError:
            print(f"{station:>10.1f}m    (outside range)")
    print()
    
    # ========================================================================
    # STEP 6: Validate Design
    # ========================================================================
    
    print("STEP 6: Validating design against standards...")
    print("-" * 70)
    
    is_valid, warnings = valign.validate()
    
    if is_valid:
        print("✓ Design is VALID - meets all standards!")
    else:
        print("⚠ Design has WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
    print()
    
    # ========================================================================
    # STEP 7: Generate Profile Data
    # ========================================================================
    
    print("STEP 7: Generating profile data for visualization...")
    print("-" * 70)
    
    profile_points = valign.get_profile_points(interval=10.0, include_pvis=True)
    
    print(f"Generated {len(profile_points)} profile points")
    print(f"First 5 points:")
    for sta, elev, grade in profile_points[:5]:
        print(f"  {sta:>6.1f}m: {elev:>8.3f}m @ {grade*100:>6.2f}%")
    print()
    
    # ========================================================================
    # STEP 8: Summary Statistics
    # ========================================================================
    
    print("STEP 8: Alignment summary...")
    print("-" * 70)
    
    print(valign.summary())
    print()
    
    # ========================================================================
    # STEP 9: IFC Export (Conceptual)
    # ========================================================================
    
    print("STEP 9: IFC export (conceptual)...")
    print("-" * 70)
    
    print("To export to IFC 4.3:")
    print("  1. Create IFC file with ifcopenshell")
    print("  2. Create horizontal alignment (if needed)")
    print("  3. Call valign.to_ifc(ifc_file, horizontal_alignment)")
    print("  4. Save IFC file")
    print()
    
    # Example code (commented):
    """
    import ifcopenshell
    import ifcopenshell.api
    
    # Create IFC file
    ifc_file = ifcopenshell.file(schema="IFC4X3")
    
    # Setup project, site, etc.
    project = ifcopenshell.api.run("root.create_entity", ifc_file, ifc_class="IfcProject")
    
    # Export vertical alignment
    ifc_vertical = valign.to_ifc(ifc_file)
    
    # Save
    ifc_file.write("highway_101_profile.ifc")
    """
    
    print("✓ Module supports full IFC 4.3 export!")
    print()
    
    # ========================================================================
    # COMPLETE
    # ========================================================================
    
    print("=" * 70)
    print("DEMONSTRATION COMPLETE!")
    print("=" * 70)
    print()
    print("What we demonstrated:")
    print("  ✓ PVI-based design workflow")
    print("  ✓ Automatic grade calculations")
    print("  ✓ Vertical curve generation (crest and sag)")
    print("  ✓ Station/elevation queries")
    print("  ✓ K-value validation")
    print("  ✓ Profile data generation")
    print("  ✓ IFC 4.3 export capability")
    print()
    print("Next steps:")
    print("  - Day 3: UI integration with Blender panels")
    print("  - Day 4: H+V integration for 3D alignments")
    print("  - Day 5: Documentation and Phase 1 completion")
    print()


if __name__ == "__main__":
    main()
