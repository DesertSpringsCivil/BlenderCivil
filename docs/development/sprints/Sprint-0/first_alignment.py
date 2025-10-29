#!/usr/bin/env python3
"""
BlenderCivil - First Native IFC Alignment
Sprint 0, Day 2: Create your first native IFC alignment!
"""

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.guid

print("=" * 60)
print("Creating Your First Native IFC Alignment!")
print("=" * 60)

# Step 1: Create new IFC file with IFC4X3 schema
print("\n[1/7] Creating IFC4X3 file...")
ifc = ifcopenshell.file(schema="IFC4X3")
print("✓ IFC file created in memory")

# Step 2: Create project (required root)
print("\n[2/7] Creating IfcProject...")
project = ifcopenshell.api.run("root.create_entity", ifc, 
    ifc_class="IfcProject", 
    name="BlenderCivil Native IFC Test")
print(f"✓ Project created: {project.Name}")
print(f"  GlobalId: {project.GlobalId}")

# Step 3: Create site (best practice hierarchy)
print("\n[3/7] Creating IfcSite...")
site = ifcopenshell.api.run("root.create_entity", ifc,
    ifc_class="IfcSite", 
    name="Test Site")
print(f"✓ Site created: {site.Name}")

# Step 4: Create alignment
print("\n[4/7] Creating IfcAlignment...")
alignment = ifc.create_entity("IfcAlignment", 
    GlobalId=ifcopenshell.guid.new(),
    Name="My First Native Alignment",
    Description="Created by BlenderCivil - proving native IFC works!")
print(f"✓ Alignment created: {alignment.Name}")

# Step 5: Create horizontal alignment
print("\n[5/7] Creating IfcAlignmentHorizontal...")
horiz_alignment = ifc.create_entity("IfcAlignmentHorizontal",
    GlobalId=ifcopenshell.guid.new())
print("✓ Horizontal alignment created")

# Step 6: Create a simple tangent segment
print("\n[6/7] Creating tangent segment...")
segment1 = ifc.create_entity("IfcAlignmentSegment",
    GlobalId=ifcopenshell.guid.new(),
    DesignParameters=ifc.create_entity("IfcAlignmentHorizontalSegment",
        StartPoint=ifc.create_entity("IfcCartesianPoint", 
            Coordinates=(0.0, 0.0)),
        StartDirection=0.0,  # 0 radians = East
        StartRadiusOfCurvature=0.0,  # Infinite radius = straight line
        EndRadiusOfCurvature=0.0,
        SegmentLength=100.0,  # 100 meters long
        PredefinedType="LINE"))
print("✓ Tangent segment created: 100m LINE starting at (0,0)")

# Step 7: Establish IFC relationships (the magic!)
print("\n[7/7] Establishing IFC relationships...")

# Link segment to horizontal alignment
rel1 = ifc.create_entity("IfcRelNests",
    GlobalId=ifcopenshell.guid.new(),
    Name="HorizontalToSegment",
    RelatingObject=horiz_alignment,
    RelatedObjects=[segment1])
print("✓ Linked segment → horizontal alignment")

# Link horizontal to alignment
rel2 = ifc.create_entity("IfcRelNests",
    GlobalId=ifcopenshell.guid.new(),
    Name="AlignmentToHorizontal",
    RelatingObject=alignment,
    RelatedObjects=[horiz_alignment])
print("✓ Linked horizontal → alignment")

# Link alignment to site
rel3 = ifc.create_entity("IfcRelContainedInSpatialStructure",
    GlobalId=ifcopenshell.guid.new(),
    RelatingStructure=site,
    RelatedElements=[alignment])
print("✓ Linked alignment → site")

# Save IFC file
output_file = "/home/claude/first_native_alignment.ifc"
print(f"\n{'=' * 60}")
print("Saving IFC file...")
ifc.write(output_file)
print(f"✓ SUCCESS! IFC file saved: {output_file}")

# Summary
print(f"\n{'=' * 60}")
print("SUMMARY")
print(f"{'=' * 60}")
print(f"Schema: {ifc.schema}")
print(f"Total entities: {len(list(ifc))}")
print(f"Projects: {len(ifc.by_type('IfcProject'))}")
print(f"Sites: {len(ifc.by_type('IfcSite'))}")
print(f"Alignments: {len(ifc.by_type('IfcAlignment'))}")
print(f"Segments: {len(ifc.by_type('IfcAlignmentSegment'))}")
print(f"\nYour IFC file structure:")
print(f"  IfcProject: '{project.Name}'")
print(f"  └─ IfcSite: '{site.Name}'")
print(f"     └─ IfcAlignment: '{alignment.Name}'")
print(f"        └─ IfcAlignmentHorizontal")
print(f"           └─ IfcAlignmentSegment (LINE, 100m)")

print(f"\n{'=' * 60}")
print("🎉 CONGRATULATIONS! You've created your first native IFC alignment!")
print("=" * 60)
print(f"\nNext steps:")
print(f"1. Open '{output_file}' in an IFC viewer")
print(f"2. Verify the alignment structure")
print(f"3. Celebrate this milestone!")
print(f"\nYou're now doing TRUE native IFC authoring! 🚀")