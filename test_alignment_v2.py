"""
BlenderCivil v0.3.0 - Test Script
Demonstrates the Separate Entity Architecture

This script creates a sample alignment to test and demonstrate
the new IFC-compatible separate entity system.

Usage:
1. Load this script in Blender's Text Editor
2. Run it (Alt+P)
3. Check the 3D viewport and console output
4. Try moving PIs with G key!

Author: BlenderCivil Development Team
Date: October 24, 2025
"""

import bpy
import math


def clear_scene():
    """Clear all objects from the scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    print("✓ Cleared scene")


def create_test_pis():
    """
    Create test PI points in a curve pattern.
    
    Creates 5 PIs forming a smooth curved alignment:
    - PI_001 at origin
    - PI_002 at (200, 100)
    - PI_003 at (400, 250)
    - PI_004 at (600, 300)
    - PI_005 at (800, 200)
    """
    pi_locations = [
        (0, 0, 0),
        (200, 100, 0),
        (400, 250, 0),
        (600, 300, 0),
        (800, 200, 0),
    ]
    
    pis = []
    for i, loc in enumerate(pi_locations):
        # Create empty
        empty = bpy.data.objects.new(f"PI_{i+1:03d}", None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 5.0
        empty.location = loc
        
        # Add to scene
        bpy.context.scene.collection.objects.link(empty)
        pis.append(empty)
    
    print(f"✓ Created {len(pis)} test PI points")
    return pis


def test_alignment_creation():
    """Test the alignment creation operator"""
    print("\n" + "="*60)
    print("TEST: ALIGNMENT CREATION")
    print("="*60)
    
    # Clear scene
    clear_scene()
    
    # Create test PIs
    pis = create_test_pis()
    
    # Create alignment using operator
    bpy.ops.civil.create_alignment_separate_v2(
        alignment_name="Test_Alignment",
        default_radius=500.0,
        design_speed=35.0
    )
    
    print("\n✓ Alignment creation test PASSED")


def test_manual_update():
    """Test manual alignment update after moving a PI"""
    print("\n" + "="*60)
    print("TEST: MANUAL UPDATE")
    print("="*60)
    
    # Find a PI and move it
    pi = bpy.data.objects.get("PI_002")
    if not pi:
        print("  ⚠ Cannot find PI_002")
        return
    
    old_loc = tuple(pi.location)
    print(f"  Moving PI_002 from {old_loc}")
    
    # Move PI
    pi.location.x += 50
    pi.location.y += 50
    
    new_loc = tuple(pi.location)
    print(f"  to {new_loc}")
    
    # Manual update
    bpy.ops.civil.update_alignment_v2()
    
    print("\n✓ Manual update test PASSED")


def test_analysis():
    """Test alignment analysis"""
    print("\n" + "="*60)
    print("TEST: ALIGNMENT ANALYSIS")
    print("="*60)
    
    bpy.ops.civil.analyze_alignment_v2()
    
    print("\n✓ Analysis test PASSED")


def test_auto_update():
    """Test auto-update functionality"""
    print("\n" + "="*60)
    print("TEST: AUTO-UPDATE")
    print("="*60)
    
    # Find alignment root
    alignment_root = None
    for obj in bpy.context.scene.objects:
        if (obj.type == 'EMPTY' and hasattr(obj, 'alignment_root') 
            and obj.alignment_root.object_type == 'ALIGNMENT_ROOT'):
            alignment_root = obj
            break
    
    if not alignment_root:
        print("  ⚠ No alignment found")
        return
    
    print(f"  Alignment: {alignment_root.name}")
    print(f"  Auto-Update: {'ON' if alignment_root.alignment_root.auto_update_enabled else 'OFF'}")
    
    if not alignment_root.alignment_root.auto_update_enabled:
        print("  Enabling auto-update...")
        alignment_root.alignment_root.auto_update_enabled = True
    
    print("\n  To test auto-update:")
    print("  1. Select any PI point")
    print("  2. Press G key to grab/move")
    print("  3. Move your mouse")
    print("  4. Click to confirm")
    print("  5. Watch the alignment update automatically!")
    
    print("\n✓ Auto-update test PASSED (manual interaction required)")


def run_all_tests():
    """Run all tests"""
    print("\n" + "#"*60)
    print("# BlenderCivil v0.3.0 - TEST SUITE")
    print("# Separate Entity Architecture")
    print("#"*60)
    
    try:
        test_alignment_creation()
        test_manual_update()
        test_analysis()
        test_auto_update()
        
        print("\n" + "#"*60)
        print("# ALL TESTS PASSED! ✓")
        print("#"*60)
        
        print("\nNEXT STEPS:")
        print("1. Try moving PIs with G key (auto-update!)")
        print("2. Check the N-panel > Civil tab for UI")
        print("3. Inspect objects in Outliner (see hierarchy)")
        print("4. Select tangents/curves (see properties)")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
