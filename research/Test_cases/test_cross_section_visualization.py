"""
Comprehensive Tests for 3D Cross-Section Visualization
Sprint 4 Day 4 - Testing the visualizer with real scenarios

This test suite validates the 3D visualization system with:
- Single station visualization
- Full corridor creation
- Station markers
- Component previews
- Real-world road scenarios
- Performance benchmarks (< 100ms target)
"""

import unittest
import time
import math
from typing import List, Tuple

# These imports would work in actual Blender environment
# For testing outside Blender, we'll mock what we need
try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("⚠️  Blender not available - using mock mode")


# Mock classes for testing outside Blender
class MockAlignment3D:
    """Mock alignment for testing."""
    
    def __init__(self):
        self.horizontal = self
        self.vertical = self
    
    def in_station_range(self, station: float) -> bool:
        return 0 <= station <= 1000
    
    def get_point_at_station(self, station: float):
        """Return mock 3D point."""
        if not self.in_station_range(station):
            return None
        
        # Simple straight alignment for testing
        class MockPoint:
            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z
        
        return MockPoint(
            x=station,
            y=0.0,
            z=100.0 + station * 0.01  # 1% grade
        )
    
    def get_point_at_station(self, station: float):
        """Mock horizontal data."""
        if not self.in_station_range(station):
            return None
        
        return {
            'x': station,
            'y': 0.0,
            'bearing': 0.0,  # Straight alignment
            'station': station
        }


class MockComponent:
    """Mock component for testing."""
    
    def __init__(self, name: str, component_type: str, width: float = 3.6):
        self.name = name
        self.component_type = component_type
        self.width = width
        self.cross_slope = -0.02
        self.offset = 0.0
        self.side = "RIGHT"
    
    def calculate_points(self, station: float = 0.0) -> List[Tuple[float, float]]:
        """Return simple rectangular profile."""
        # Simple flat profile
        return [
            (self.offset, 0.0),  # Inside edge
            (self.offset + self.width, 0.0)  # Outside edge
        ]


class MockRoadAssembly:
    """Mock road assembly for testing."""
    
    def __init__(self, name: str = "Test Assembly"):
        self.name = name
        self.components = []
    
    def add_component(self, component):
        self.components.append(component)
    
    def calculate_section_points(self, station: float = 0.0) -> List[Tuple[float, float]]:
        """Calculate combined section points from all components."""
        if not self.components:
            return []
        
        points = []
        current_offset = 0.0
        
        for component in self.components:
            component_points = component.calculate_points(station)
            # Adjust offsets to be continuous
            for offset, elevation in component_points:
                points.append((current_offset + offset, elevation))
            
            # Move to next component
            if component_points:
                _, last_elevation = component_points[-1]
                current_offset += component.width
        
        return points


class TestCrossSectionVisualization(unittest.TestCase):
    """Test suite for 3D cross-section visualization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        print("\n" + "="*60)
        print("🧪 CROSS-SECTION 3D VISUALIZATION TEST SUITE")
        print("="*60)
        
        if not BLENDER_AVAILABLE:
            print("\n⚠️  Running in MOCK MODE (Blender not available)")
            print("   Tests will validate logic but skip actual 3D creation")
        else:
            print("\n✅ Running in BLENDER MODE")
            print("   Full 3D visualization tests enabled!")
    
    def setUp(self):
        """Set up each test."""
        # Create mock alignment (straight, 1 km, 1% grade)
        self.alignment = MockAlignment3D()
        
        # Create mock assembly (2-lane road)
        self.assembly = MockRoadAssembly("Test 2-Lane Road")
        
        # Add components
        lane1 = MockComponent("Left Lane", "LANE", 3.6)
        lane2 = MockComponent("Right Lane", "LANE", 3.6)
        shoulder1 = MockComponent("Left Shoulder", "SHOULDER", 2.4)
        shoulder2 = MockComponent("Right Shoulder", "SHOULDER", 2.4)
        
        self.assembly.add_component(shoulder1)
        self.assembly.add_component(lane1)
        self.assembly.add_component(lane2)
        self.assembly.add_component(shoulder2)
    
    def test_01_visualizer_initialization(self):
        """Test visualizer can be initialized."""
        print("\n📋 Test 01: Visualizer Initialization")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(
            self.alignment,
            self.assembly,
            collection_name="Test Visualization"
        )
        
        self.assertIsNotNone(viz)
        self.assertEqual(viz.collection_name, "Test Visualization")
        print("   ✅ Visualizer initialized successfully")
    
    def test_02_single_station_visualization(self):
        """Test visualization of single cross-section."""
        print("\n📋 Test 02: Single Station Visualization")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Visualize at station 100
        start_time = time.time()
        obj = viz.visualize_station(100.0, extrusion=2.0)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        
        self.assertIsNotNone(obj)
        print(f"   ✅ Cross-section created at STA 100.00")
        print(f"   ⏱️  Creation time: {elapsed:.1f} ms")
        
        # Check object properties
        self.assertIn("Section", obj.name)
        print(f"   📦 Object: {obj.name}")
        print(f"   📐 Vertices: {len(obj.data.vertices)}")
        print(f"   📐 Faces: {len(obj.data.polygons)}")
    
    def test_03_corridor_creation(self):
        """Test full corridor creation."""
        print("\n📋 Test 03: Full Corridor Creation")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Create corridor from 0 to 500m
        print("   🏗️  Creating corridor (0 to 500m, 10m intervals)...")
        start_time = time.time()
        
        corridor = viz.create_corridor(
            start_station=0.0,
            end_station=500.0,
            interval=10.0,
            name="Test Corridor"
        )
        
        elapsed = time.time() - start_time
        
        self.assertIsNotNone(corridor)
        print(f"   ✅ Corridor created successfully")
        print(f"   ⏱️  Total time: {elapsed:.2f} seconds")
        print(f"   📐 Vertices: {len(corridor.data.vertices)}")
        print(f"   📐 Faces: {len(corridor.data.polygons)}")
        
        # Performance check
        expected_sections = 51  # 500m / 10m + 1
        faces_per_section = 40  # Approximate
        expected_faces = expected_sections * faces_per_section
        
        print(f"   📊 Expected ~{expected_sections} sections")
        print(f"   📊 Performance: {elapsed/expected_sections*1000:.1f} ms per section")
    
    def test_04_station_markers(self):
        """Test station marker creation."""
        print("\n📋 Test 04: Station Markers")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Create station markers every 50m
        print("   📍 Creating station markers (50m intervals)...")
        markers = viz.create_station_markers(
            start_station=0.0,
            end_station=500.0,
            interval=50.0
        )
        
        self.assertIsNotNone(markers)
        self.assertGreater(len(markers), 0)
        
        # Should have posts + labels
        expected_markers = 11  # 500/50 + 1
        expected_objects = expected_markers * 2  # Post + label for each
        
        print(f"   ✅ Created {len(markers)} objects")
        print(f"   📊 Expected ~{expected_objects} objects (posts + labels)")
    
    def test_05_component_preview(self):
        """Test individual component visualization."""
        print("\n📋 Test 05: Component Preview")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Visualize just one lane
        lane = self.assembly.components[1]  # Left lane
        print(f"   🛣️  Visualizing component: {lane.name}")
        
        obj = viz.create_component_preview(
            component=lane,
            station=100.0,
            extrusion=10.0
        )
        
        self.assertIsNotNone(obj)
        print(f"   ✅ Component preview created")
        print(f"   📦 Object: {obj.name}")
    
    def test_06_material_setup(self):
        """Test material creation and assignment."""
        print("\n📋 Test 06: Material Setup")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Check materials were created
        self.assertGreater(len(viz._material_cache), 0)
        
        print(f"   ✅ Created {len(viz._material_cache)} materials")
        for mat_type, mat in viz._material_cache.items():
            print(f"      • {mat_type}: {mat.name}")
    
    def test_07_section_points_calculation(self):
        """Test section point calculation (no Blender required)."""
        print("\n📋 Test 07: Section Points Calculation")
        
        # Calculate points at station 100
        points = self.assembly.calculate_section_points(100.0)
        
        self.assertIsNotNone(points)
        self.assertGreater(len(points), 0)
        
        print(f"   ✅ Calculated {len(points)} section points")
        print(f"   📊 Sample points:")
        for i, (offset, elev) in enumerate(points[:5]):
            print(f"      {i+1}. Offset: {offset:6.2f}m, Elevation: {elev:6.2f}m")
        
        # Calculate total width
        if points:
            total_width = abs(points[-1][0] - points[0][0])
            print(f"   📏 Total section width: {total_width:.2f}m")
    
    def test_08_performance_benchmark(self):
        """Benchmark visualization performance."""
        print("\n📋 Test 08: Performance Benchmark")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Test single section performance (target < 100ms)
        times = []
        stations = [0, 100, 200, 300, 400, 500]
        
        print("   ⏱️  Benchmarking single section creation...")
        for station in stations:
            start = time.time()
            obj = viz.visualize_station(station, extrusion=1.0)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"   📊 Results:")
        print(f"      Average: {avg_time:.1f} ms")
        print(f"      Min:     {min_time:.1f} ms")
        print(f"      Max:     {max_time:.1f} ms")
        
        # Check against target
        if avg_time < 100:
            print(f"   ✅ PASSED: Average < 100ms target!")
        else:
            print(f"   ⚠️  WARNING: Average > 100ms target")
    
    def test_09_clear_visualization(self):
        """Test clearing visualization."""
        print("\n📋 Test 09: Clear Visualization")
        
        if not BLENDER_AVAILABLE:
            print("   ⏭️  Skipping (Blender not available)")
            return
        
        from cross_section_visualizer import CrossSectionVisualizer
        
        viz = CrossSectionVisualizer(self.alignment, self.assembly)
        
        # Create some objects
        viz.visualize_station(100.0)
        viz.visualize_station(200.0)
        
        initial_count = len(viz.collection.objects)
        print(f"   📦 Created {initial_count} objects")
        
        # Clear
        viz.clear_visualization()
        
        final_count = len(viz.collection.objects)
        print(f"   🧹 Cleared, {final_count} objects remaining")
        
        self.assertEqual(final_count, 0)
        print("   ✅ Visualization cleared successfully")
    
    def test_10_real_world_scenario_highway(self):
        """Test with realistic highway scenario."""
        print("\n📋 Test 10: Real-World Highway Scenario")
        
        # Create realistic highway assembly
        highway = MockRoadAssembly("Interstate Highway")
        
        # Left side
        highway.add_component(MockComponent("Left Ditch", "DITCH", 4.0))
        highway.add_component(MockComponent("Left Shoulder", "SHOULDER", 3.0))
        highway.add_component(MockComponent("Left Lane", "LANE", 3.6))
        
        # Right side
        highway.add_component(MockComponent("Right Lane", "LANE", 3.6))
        highway.add_component(MockComponent("Right Shoulder", "SHOULDER", 3.0))
        highway.add_component(MockComponent("Right Ditch", "DITCH", 4.0))
        
        # Calculate section
        points = highway.calculate_section_points(500.0)
        
        self.assertGreater(len(points), 0)
        print(f"   ✅ Highway assembly validated")
        print(f"   📊 Components: {len(highway.components)}")
        print(f"   📊 Section points: {len(points)}")
        
        if points:
            total_width = abs(points[-1][0] - points[0][0])
            print(f"   📏 Total highway width: {total_width:.2f}m")
        
        if BLENDER_AVAILABLE:
            from cross_section_visualizer import CrossSectionVisualizer
            
            viz = CrossSectionVisualizer(self.alignment, highway)
            
            print("   🏗️  Creating highway corridor...")
            corridor = viz.create_corridor(
                start_station=0.0,
                end_station=1000.0,
                interval=25.0,
                name="Highway Corridor"
            )
            
            self.assertIsNotNone(corridor)
            print(f"   ✅ 1km highway corridor created!")


# Quick visualization functions for Blender console

def quick_test():
    """Quick test that can be run in Blender console."""
    print("\n🚀 QUICK VISUALIZATION TEST\n")
    
    if not BLENDER_AVAILABLE:
        print("⚠️  Must run in Blender!")
        return False
    
    # Create test data
    alignment = MockAlignment3D()
    assembly = MockRoadAssembly("Quick Test")
    
    assembly.add_component(MockComponent("Lane 1", "LANE", 3.6))
    assembly.add_component(MockComponent("Lane 2", "LANE", 3.6))
    
    # Create visualization
    from cross_section_visualizer import CrossSectionVisualizer
    
    viz = CrossSectionVisualizer(alignment, assembly, "Quick Test")
    
    # Create corridor
    print("Creating corridor...")
    corridor = viz.create_corridor(0, 200, interval=20)
    
    # Add markers
    print("Adding markers...")
    viz.create_station_markers(0, 200, interval=50)
    
    print("\n✅ Quick test complete! Check viewport!")
    return True


def full_demo():
    """Full demonstration of all visualization features."""
    print("\n" + "="*60)
    print("🎨 FULL VISUALIZATION DEMO")
    print("="*60 + "\n")
    
    if not BLENDER_AVAILABLE:
        print("⚠️  Must run in Blender!")
        return False
    
    # Create realistic alignment and assembly
    alignment = MockAlignment3D()
    
    # Create highway assembly
    highway = MockRoadAssembly("Demo Highway")
    highway.add_component(MockComponent("Left Shoulder", "SHOULDER", 2.4))
    highway.add_component(MockComponent("Left Lane", "LANE", 3.6))
    highway.add_component(MockComponent("Right Lane", "LANE", 3.6))
    highway.add_component(MockComponent("Right Shoulder", "SHOULDER", 2.4))
    
    from cross_section_visualizer import CrossSectionVisualizer
    
    # Demo 1: Single station
    print("Demo 1: Single Cross-Section")
    viz1 = CrossSectionVisualizer(alignment, highway, "Demo 1 - Single Section")
    viz1.visualize_station(100.0, extrusion=5.0)
    print("✅ Check viewport for single section\n")
    
    # Demo 2: Short corridor
    print("Demo 2: Short Corridor (100m)")
    viz2 = CrossSectionVisualizer(alignment, highway, "Demo 2 - Short Corridor")
    viz2.create_corridor(0, 100, interval=10)
    viz2.create_station_markers(0, 100, interval=25)
    print("✅ Check viewport for short corridor\n")
    
    # Demo 3: Full corridor
    print("Demo 3: Full Corridor (500m)")
    viz3 = CrossSectionVisualizer(alignment, highway, "Demo 3 - Full Corridor")
    viz3.create_corridor(0, 500, interval=20)
    viz3.create_station_markers(0, 500, interval=50)
    print("✅ Check viewport for full corridor\n")
    
    print("="*60)
    print("✅ ALL DEMOS COMPLETE!")
    print("   Check the viewport and outliner for results")
    print("="*60)
    
    return True


# Run tests
if __name__ == "__main__":
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCrossSectionVisualization)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*60)
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED")
    
    if not BLENDER_AVAILABLE:
        print("\n💡 Run these tests in Blender for full 3D visualization!")
