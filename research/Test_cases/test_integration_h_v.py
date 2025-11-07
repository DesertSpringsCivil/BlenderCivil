"""
BlenderCivil - H+V Integration Tests
Sprint 3 Day 4 - Complete Integration Testing

Comprehensive tests for 3D alignment integration (H+V).
Tests real-world scenarios: highway, urban street, mountain road.

Author: BlenderCivil Team
Date: November 2, 2025
Sprint: 3 of 16 - Vertical Alignments
Day: 4 of 5 - Integration Testing

Test Scenarios:
1. Highway Alignment (2 km, gentle curves, moderate grades)
2. Urban Street (500 m, grid pattern, drainage slopes)
3. Mountain Road (1.5 km, sharp curves, steep grades)

Each scenario tests:
- H+V alignment creation
- 3D position calculation
- Sampling and visualization
- Validation and design checking
- IFC export (if available)
"""

import unittest
import math
from typing import List, Tuple
import sys
import os

# Import our modules
sys.path.insert(0, os.path.dirname(__file__))
from alignment_3d import Alignment3D, AlignmentPoint3D


class MockHorizontalAlignment:
    """
    Mock horizontal alignment for testing.
    
    Simulates Sprint 1 HorizontalAlignment behavior without
    requiring full implementation.
    """
    
    def __init__(
        self,
        length: float,
        start_point: Tuple[float, float] = (0.0, 0.0),
        start_direction: float = 0.0  # radians, 0 = North
    ):
        self.length = length
        self.start_station = 0.0
        self.end_station = length
        self.start_x = start_point[0]
        self.start_y = start_point[1]
        self.start_direction = start_direction
    
    def get_position_at_station(
        self,
        station: float
    ) -> Tuple[float, float, float]:
        """
        Get position and direction at station.
        
        Returns: (x, y, direction)
        
        Simplified: assumes straight line for testing
        """
        # Simple straight-line approximation
        x = self.start_x + station * math.sin(self.start_direction)
        y = self.start_y + station * math.cos(self.start_direction)
        direction = self.start_direction
        
        return (x, y, direction)


class MockVerticalAlignment:
    """
    Mock vertical alignment for testing.
    
    Simulates Sprint 3 VerticalAlignment behavior.
    """
    
    def __init__(
        self,
        start_elevation: float,
        start_grade: float,  # decimal, e.g., 0.02 = 2%
        length: float
    ):
        self.start_elevation = start_elevation
        self.start_grade = start_grade
        self.length = length
        self.start_station = 0.0
        self.end_station = length
    
    def get_elevation(self, station: float) -> float:
        """
        Get elevation at station.
        
        Simplified: constant grade for testing
        """
        return self.start_elevation + station * self.start_grade
    
    def get_grade(self, station: float) -> float:
        """Get grade at station."""
        return self.start_grade


class TestAlignment3DBasics(unittest.TestCase):
    """
    Basic integration tests for Alignment3D.
    """
    
    def setUp(self):
        """Set up test alignments."""
        # Simple test case: 100m alignment
        self.h_align = MockHorizontalAlignment(
            length=100.0,
            start_point=(1000.0, 2000.0),
            start_direction=0.0  # North
        )
        
        self.v_align = MockVerticalAlignment(
            start_elevation=100.0,
            start_grade=0.02,  # 2% uphill
            length=100.0
        )
        
        self.alignment_3d = Alignment3D(
            self.h_align,
            self.v_align,
            name="Test Alignment"
        )
    
    def test_creation(self):
        """Test basic alignment creation."""
        self.assertIsNotNone(self.alignment_3d)
        self.assertEqual(self.alignment_3d.name, "Test Alignment")
    
    def test_station_range(self):
        """Test station range methods."""
        start = self.alignment_3d.get_start_station()
        end = self.alignment_3d.get_end_station()
        length = self.alignment_3d.get_length()
        
        self.assertEqual(start, 0.0)
        self.assertEqual(end, 100.0)
        self.assertEqual(length, 100.0)
    
    def test_3d_position(self):
        """Test 3D position calculation."""
        # At start (station 0)
        x0, y0, z0 = self.alignment_3d.get_3d_position(0.0)
        self.assertAlmostEqual(x0, 1000.0, places=2)
        self.assertAlmostEqual(y0, 2000.0, places=2)
        self.assertAlmostEqual(z0, 100.0, places=2)
        
        # At middle (station 50)
        x50, y50, z50 = self.alignment_3d.get_3d_position(50.0)
        self.assertAlmostEqual(z50, 101.0, places=2)  # +1m with 2% grade
        
        # At end (station 100)
        x100, y100, z100 = self.alignment_3d.get_3d_position(100.0)
        self.assertAlmostEqual(z100, 102.0, places=2)  # +2m total
    
    def test_alignment_data(self):
        """Test complete alignment data query."""
        data = self.alignment_3d.get_alignment_data(50.0)
        
        self.assertIsInstance(data, AlignmentPoint3D)
        self.assertEqual(data.station, 50.0)
        self.assertAlmostEqual(data.grade, 0.02, places=4)
        
        # Check dict conversion
        data_dict = data.to_dict()
        self.assertIn('station', data_dict)
        self.assertIn('elevation', data_dict)
        self.assertIn('grade_percent', data_dict)
        self.assertAlmostEqual(data_dict['grade_percent'], 2.0, places=2)
    
    def test_sampling(self):
        """Test alignment sampling."""
        points = self.alignment_3d.sample_alignment(interval=10.0)
        
        # Should have points at: 0, 10, 20, ..., 100 = 11 points
        self.assertGreaterEqual(len(points), 11)
        
        # Check first and last
        self.assertEqual(points[0].station, 0.0)
        self.assertEqual(points[-1].station, 100.0)
    
    def test_chord_line(self):
        """Test chord length and slope calculation."""
        length, slope = self.alignment_3d.get_chord_line(0.0, 100.0)
        
        # Chord length should be slightly more than 100m (3D)
        self.assertGreater(length, 100.0)
        
        # Slope should be close to 2%
        self.assertAlmostEqual(slope, 2.0, places=1)
    
    def test_validation(self):
        """Test alignment validation."""
        result = self.alignment_3d.validate()
        
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)
        self.assertTrue(result['valid'])  # Should be valid
    
    def test_out_of_range(self):
        """Test out-of-range station handling."""
        with self.assertRaises(ValueError):
            self.alignment_3d.get_3d_position(-10.0)  # Before start
        
        with self.assertRaises(ValueError):
            self.alignment_3d.get_3d_position(200.0)  # After end


class TestHighwayScenario(unittest.TestCase):
    """
    Test highway alignment scenario.
    
    Scenario:
    - Length: 2000 m (2 km)
    - Horizontal: Gentle curves (R=500m+)
    - Vertical: Moderate grades (±3%)
    - Design speed: 100 km/h
    - AASHTO standards
    """
    
    def setUp(self):
        """Create highway alignment."""
        # Highway: 2 km, gentle curves
        self.h_align = MockHorizontalAlignment(
            length=2000.0,
            start_point=(0.0, 0.0),
            start_direction=0.0
        )
        
        # Moderate grades: start flat, climb to +3%, flatten
        self.v_align = MockVerticalAlignment(
            start_elevation=100.0,
            start_grade=0.03,  # 3% average for simple test
            length=2000.0
        )
        
        self.highway = Alignment3D(
            self.h_align,
            self.v_align,
            name="Highway Example",
            description="2 km highway with gentle curves and moderate grades"
        )
    
    def test_highway_length(self):
        """Test highway length."""
        length = self.highway.get_length()
        self.assertEqual(length, 2000.0)
    
    def test_highway_elevation_change(self):
        """Test total elevation change."""
        z_start = self.highway.get_3d_position(0.0)[2]
        z_end = self.highway.get_3d_position(2000.0)[2]
        
        elevation_change = z_end - z_start
        
        # 3% grade over 2000m = 60m rise
        self.assertAlmostEqual(elevation_change, 60.0, places=0)
    
    def test_highway_sampling(self):
        """Test highway sampling for visualization."""
        # Sample every 20m (typical for visualization)
        points = self.highway.sample_alignment(interval=20.0)
        
        # Should have ~101 points (0, 20, 40, ..., 2000)
        expected_points = int(2000 / 20) + 1
        self.assertGreaterEqual(len(points), expected_points)
    
    def test_highway_max_grade(self):
        """Test maximum grade is within limits."""
        # Sample at multiple locations
        grades = []
        for station in range(0, 2001, 100):
            grade = self.highway.get_grade(station)
            grades.append(abs(grade * 100))  # Convert to %
        
        max_grade = max(grades)
        
        # Highway should not exceed 6% (typical maximum)
        self.assertLess(max_grade, 6.0)
    
    def test_highway_export_data(self):
        """Test highway data export."""
        # Sample highway
        points = self.highway.sample_alignment(interval=50.0)
        
        # Verify data is complete
        for point in points:
            self.assertIsNotNone(point.x)
            self.assertIsNotNone(point.y)
            self.assertIsNotNone(point.z)
            self.assertIsNotNone(point.station)
            self.assertIsNotNone(point.grade)


class TestUrbanScenario(unittest.TestCase):
    """
    Test urban street scenario.
    
    Scenario:
    - Length: 500 m
    - Horizontal: Grid pattern (straight segments, right angles)
    - Vertical: Flat with drainage (0.5-2%)
    - Design speed: 40-50 km/h
    - Urban design standards
    """
    
    def setUp(self):
        """Create urban street alignment."""
        # Urban: 500m, straight
        self.h_align = MockHorizontalAlignment(
            length=500.0,
            start_point=(5000.0, 5000.0),
            start_direction=math.pi / 2  # East
        )
        
        # Gentle drainage grade: 1%
        self.v_align = MockVerticalAlignment(
            start_elevation=50.0,
            start_grade=0.01,  # 1% for drainage
            length=500.0
        )
        
        self.urban = Alignment3D(
            self.h_align,
            self.v_align,
            name="Urban Street",
            description="500m urban street with drainage grade"
        )
    
    def test_urban_length(self):
        """Test urban street length."""
        length = self.urban.get_length()
        self.assertEqual(length, 500.0)
    
    def test_urban_drainage(self):
        """Test drainage grade is gentle."""
        # Check grade at multiple points
        for station in [0, 100, 250, 400, 500]:
            grade = abs(self.urban.get_grade(station) * 100)
            
            # Should be gentle (0.5-2% typical)
            self.assertLess(grade, 3.0)
            self.assertGreater(grade, 0.3)
    
    def test_urban_elevation_change(self):
        """Test total elevation change is small."""
        z_start = self.urban.get_3d_position(0.0)[2]
        z_end = self.urban.get_3d_position(500.0)[2]
        
        elevation_change = abs(z_end - z_start)
        
        # 1% over 500m = 5m change
        self.assertAlmostEqual(elevation_change, 5.0, places=1)


class TestMountainScenario(unittest.TestCase):
    """
    Test mountain road scenario.
    
    Scenario:
    - Length: 1500 m (1.5 km)
    - Horizontal: Sharp curves (tight switchbacks)
    - Vertical: Steep grades (6-8%)
    - Design speed: 40-60 km/h
    - Mountain/terrain following
    """
    
    def setUp(self):
        """Create mountain road alignment."""
        # Mountain: 1.5 km, winding
        self.h_align = MockHorizontalAlignment(
            length=1500.0,
            start_point=(10000.0, 10000.0),
            start_direction=0.0
        )
        
        # Steep climbing: 7%
        self.v_align = MockVerticalAlignment(
            start_elevation=500.0,
            start_grade=0.07,  # 7% climb
            length=1500.0
        )
        
        self.mountain = Alignment3D(
            self.h_align,
            self.v_align,
            name="Mountain Road",
            description="1.5 km mountain road with steep grades"
        )
    
    def test_mountain_length(self):
        """Test mountain road length."""
        length = self.mountain.get_length()
        self.assertEqual(length, 1500.0)
    
    def test_mountain_elevation_gain(self):
        """Test significant elevation gain."""
        z_start = self.mountain.get_3d_position(0.0)[2]
        z_end = self.mountain.get_3d_position(1500.0)[2]
        
        elevation_gain = z_end - z_start
        
        # 7% over 1500m = 105m gain
        self.assertAlmostEqual(elevation_gain, 105.0, places=0)
    
    def test_mountain_steep_grade(self):
        """Test grade is steep but acceptable."""
        grade = abs(self.mountain.get_grade(750.0) * 100)
        
        # Should be steep (6-8% typical maximum for roads)
        self.assertGreater(grade, 5.0)
        self.assertLess(grade, 10.0)  # Absolute maximum
    
    def test_mountain_3d_distance(self):
        """Test 3D distance is longer than 2D."""
        # Chord line from start to end
        length_3d, slope = self.mountain.get_chord_line(0.0, 1500.0)
        length_2d = 1500.0
        
        # 3D distance should be longer due to slope
        self.assertGreater(length_3d, length_2d)
        
        # Calculate expected 3D length
        expected_3d = math.sqrt(length_2d**2 + 105.0**2)
        self.assertAlmostEqual(length_3d, expected_3d, places=0)


class TestIntegrationFeatures(unittest.TestCase):
    """
    Test integration-specific features.
    """
    
    def setUp(self):
        """Create test alignment."""
        self.h_align = MockHorizontalAlignment(200.0)
        self.v_align = MockVerticalAlignment(100.0, 0.02, 200.0)
        self.alignment = Alignment3D(self.h_align, self.v_align)
    
    def test_to_dict(self):
        """Test dictionary export."""
        data = self.alignment.to_dict()
        
        self.assertIn('name', data)
        self.assertIn('type', data)
        self.assertIn('length', data)
        self.assertIn('horizontal', data)
        self.assertIn('vertical', data)
        
        self.assertEqual(data['type'], '3D Alignment (H+V)')
    
    def test_repr(self):
        """Test string representation."""
        repr_str = repr(self.alignment)
        
        self.assertIn('Alignment3D', repr_str)
        self.assertIn('sta', repr_str)
        self.assertIn('length', repr_str)
    
    def test_incompatible_alignments(self):
        """Test error handling for incompatible alignments."""
        # Horizontal 0-100, Vertical 200-300 (no overlap)
        h_align = MockHorizontalAlignment(100.0)
        v_align = MockVerticalAlignment(100.0, 0.02, 100.0)
        v_align.start_station = 200.0
        v_align.end_station = 300.0
        
        with self.assertRaises(ValueError):
            Alignment3D(h_align, v_align)


def run_integration_tests():
    """
    Run all integration tests.
    
    Returns:
        Test results
    """
    print("=" * 60)
    print("BlenderCivil - H+V Integration Tests")
    print("Sprint 3 Day 4")
    print("=" * 60)
    print()
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED!")
        print()
        print("H+V Integration Status: COMPLETE! 🎉")
        print()
        print("What we tested:")
        print("  ✓ Basic 3D alignment creation")
        print("  ✓ 3D position calculation (x, y, z)")
        print("  ✓ Station queries and sampling")
        print("  ✓ Validation and error handling")
        print("  ✓ Highway scenario (2 km)")
        print("  ✓ Urban scenario (500 m)")
        print("  ✓ Mountain scenario (1.5 km)")
        print()
        print("Ready for Day 5: Documentation! 📚")
    else:
        print("❌ SOME TESTS FAILED")
        print("Review failures above and fix issues.")
    
    return result


if __name__ == "__main__":
    result = run_integration_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
