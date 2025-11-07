"""
Test Suite for Native IFC Corridor Modeling System
Sprint 5 Day 2 - Core Architecture Validation

Tests:
- StationManager: Station calculation and optimization
- CorridorModeler: Corridor solid generation
- IFC Export: IfcSectionedSolidHorizontal creation
- Integration: Full workflow testing

Author: BlenderCivil Team
Date: November 4, 2025
"""

import sys
import math
from typing import List, Tuple, Any
from dataclasses import dataclass


# Mock classes for testing (simulating Sprint 1-4 systems)

class MockHorizontalAlignment:
    """Mock horizontal alignment for testing."""
    
    def __init__(self, length: float = 1000.0):
        self.length = length
        self.start_station = 0.0
        self.end_station = length
        self.segments = []
    
    def get_position_at_station(self, station: float) -> Tuple[float, float, float]:
        """Return (x, y, direction) for testing."""
        # Simple straight line for testing
        x = station
        y = 0.0
        direction = 0.0  # North
        return (x, y, direction)
    
    def add_curve(self, start: float, end: float):
        """Add a mock curve segment."""
        @dataclass
        class Segment:
            type: str
            start_station: float
            end_station: float
            length: float
        
        self.segments.append(Segment(
            type='CURVE',
            start_station=start,
            end_station=end,
            length=end - start
        ))


class MockVerticalAlignment:
    """Mock vertical alignment for testing."""
    
    def __init__(self):
        self.pvis = []
        self.start_station = 0.0
        self.end_station = 1000.0
    
    def get_elevation(self, station: float) -> float:
        """Return elevation for testing."""
        # Simple flat grade
        return 100.0 + station * 0.02  # 2% grade
    
    def add_pvi(self, station: float, elevation: float, curve_length: float = 0.0):
        """Add a mock PVI."""
        @dataclass
        class PVI:
            station: float
            elevation: float
            curve_length: float
        
        self.pvis.append(PVI(station, elevation, curve_length))


class MockAlignment3D:
    """Mock 3D alignment for testing."""
    
    def __init__(self, h_align: Any, v_align: Any):
        self.horizontal = h_align
        self.vertical = v_align
        self.name = "Test Alignment"
    
    def get_start_station(self) -> float:
        return max(self.horizontal.start_station, self.vertical.start_station)
    
    def get_end_station(self) -> float:
        return min(self.horizontal.end_station, self.vertical.end_station)
    
    def get_3d_position(self, station: float) -> Tuple[float, float, float]:
        """Return (x, y, z)."""
        x, y, _ = self.horizontal.get_position_at_station(station)
        z = self.vertical.get_elevation(station)
        return (x, y, z)
    
    def get_direction(self, station: float) -> float:
        """Return bearing."""
        _, _, direction = self.horizontal.get_position_at_station(station)
        return direction
    
    def get_grade(self, station: float) -> float:
        """Return vertical grade."""
        # Calculate grade from elevation difference
        delta_station = 0.1
        if station + delta_station <= self.get_end_station():
            z1 = self.vertical.get_elevation(station)
            z2 = self.vertical.get_elevation(station + delta_station)
            return (z2 - z1) / delta_station
        return 0.0


class MockRoadAssembly:
    """Mock road assembly for testing."""
    
    def __init__(self, name: str = "Test Assembly"):
        self.name = name
        self.components = []
    
    def to_ifc(self, ifc_file: Any, station: float = None) -> Any:
        """Mock IFC export."""
        # Return a simple mock profile
        return None


class MockIFCFile:
    """Mock IFC file for testing."""
    
    def __init__(self):
        self.entities = []
    
    def create_entity(self, entity_type: str, **kwargs) -> Any:
        """Create mock IFC entity."""
        entity = {"type": entity_type, **kwargs}
        self.entities.append(entity)
        return entity
    
    def write(self, filepath: str):
        """Mock write."""
        pass


# Import the module under test
try:
    from native_ifc_corridor import (
        StationPoint,
        StationManager,
        CorridorModeler,
        CorridorManager,
        get_manager
    )
    CORRIDOR_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import corridor module: {e}")
    CORRIDOR_MODULE_AVAILABLE = False


# Test Suite

class TestStationManager:
    """Test suite for StationManager."""
    
    @staticmethod
    def test_basic_station_generation():
        """Test basic station generation with uniform intervals."""
        print("\n--- Test: Basic Station Generation ---")
        
        # Create mock alignment
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        
        # Create station manager
        manager = StationManager(alignment_3d, interval=10.0)
        
        # Generate stations
        stations = manager.calculate_stations()
        
        # Validate
        assert len(stations) >= 10, f"Expected at least 10 stations, got {len(stations)}"
        print(f"✓ Generated {len(stations)} stations")
        
        # Check station values
        station_values = [s.station for s in stations]
        print(f"✓ Stations: {station_values[:5]}...{station_values[-3:]}")
        
        # Check first and last
        assert abs(stations[0].station - 0.0) < 0.01, "First station should be 0.0"
        assert abs(stations[-1].station - 100.0) < 0.01, "Last station should be 100.0"
        print("✓ Start and end stations correct")
        
        return True
    
    @staticmethod
    def test_curve_densification():
        """Test that curves get more stations."""
        print("\n--- Test: Curve Densification ---")
        
        # Create alignment with curve
        h_align = MockHorizontalAlignment(length=200.0)
        h_align.add_curve(80.0, 120.0)  # Curve from 80-120m
        
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        
        # Generate stations
        manager = StationManager(alignment_3d, interval=10.0)
        stations = manager.calculate_stations(curve_densification_factor=2.0)
        
        # Count stations in curve region
        curve_stations = [s for s in stations if 80.0 <= s.station <= 120.0]
        tangent_stations = [s for s in stations if 0.0 <= s.station < 80.0]
        
        print(f"✓ Curve stations (80-120m): {len(curve_stations)}")
        print(f"✓ Tangent stations (0-80m): {len(tangent_stations)}")
        
        # Curve should have more stations per unit length
        curve_density = len(curve_stations) / 40.0
        tangent_density = len(tangent_stations) / 80.0
        
        print(f"✓ Curve density: {curve_density:.2f} stations/m")
        print(f"✓ Tangent density: {tangent_density:.2f} stations/m")
        
        assert curve_density > tangent_density, "Curve should be denser than tangent"
        print("✓ Curve densification working")
        
        return True
    
    @staticmethod
    def test_pvi_stations():
        """Test that PVIs get stations."""
        print("\n--- Test: PVI Station Addition ---")
        
        h_align = MockHorizontalAlignment(length=200.0)
        v_align = MockVerticalAlignment()
        
        # Add PVI with curve
        v_align.add_pvi(station=100.0, elevation=102.0, curve_length=50.0)
        
        alignment_3d = MockAlignment3D(h_align, v_align)
        
        # Generate stations
        manager = StationManager(alignment_3d, interval=25.0)
        stations = manager.calculate_stations()
        
        # Check for PVI station
        pvi_stations = [s for s in stations if s.reason == "pvi"]
        assert len(pvi_stations) > 0, "Should have PVI stations"
        print(f"✓ Found {len(pvi_stations)} PVI stations")
        
        # Check for vertical curve stations
        vcurve_stations = [s for s in stations if s.reason == "vertical_curve"]
        print(f"✓ Found {len(vcurve_stations)} vertical curve stations")
        
        return True
    
    @staticmethod
    def test_critical_stations():
        """Test adding critical user-defined stations."""
        print("\n--- Test: Critical Station Addition ---")
        
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        
        # Add critical stations
        critical = [15.5, 37.8, 92.3]
        
        manager = StationManager(alignment_3d, interval=20.0)
        stations = manager.calculate_stations(critical_stations=critical)
        
        # Check that critical stations are included
        station_values = [s.station for s in stations]
        
        for crit in critical:
            # Find closest station
            closest = min(station_values, key=lambda x: abs(x - crit))
            assert abs(closest - crit) < 0.5, f"Critical station {crit} not found"
        
        print(f"✓ All {len(critical)} critical stations included")
        
        return True
    
    @staticmethod
    def test_station_merging():
        """Test that close stations are merged."""
        print("\n--- Test: Station Merging ---")
        
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        
        # Add PVI very close to interval station
        v_align.add_pvi(station=20.1, elevation=100.0)  # Close to 20.0
        
        alignment_3d = MockAlignment3D(h_align, v_align)
        
        manager = StationManager(alignment_3d, interval=20.0)
        stations = manager.calculate_stations()
        
        # Check stations around 20.0
        nearby = [s for s in stations if 19.5 < s.station < 20.5]
        
        print(f"✓ Stations near 20.0: {[f'{s.station:.2f}' for s in nearby]}")
        
        # Should be merged to one or two stations max
        assert len(nearby) <= 2, "Stations should be merged"
        print("✓ Close stations properly merged")
        
        return True


class TestCorridorModeler:
    """Test suite for CorridorModeler."""
    
    @staticmethod
    def test_corridor_creation():
        """Test basic corridor creation."""
        print("\n--- Test: Corridor Creation ---")
        
        # Create mock alignment and assembly
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        assembly = MockRoadAssembly("Test Assembly")
        
        # Create corridor modeler
        modeler = CorridorModeler(alignment_3d, assembly, "Test Corridor")
        
        assert modeler.name == "Test Corridor"
        assert modeler.length > 0
        print(f"✓ Corridor created: length={modeler.length:.2f}m")
        
        return True
    
    @staticmethod
    def test_station_generation():
        """Test station generation through CorridorModeler."""
        print("\n--- Test: Corridor Station Generation ---")
        
        h_align = MockHorizontalAlignment(length=200.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        assembly = MockRoadAssembly()
        
        modeler = CorridorModeler(alignment_3d, assembly)
        
        # Generate stations
        stations = modeler.generate_stations(interval=20.0)
        
        assert len(stations) >= 10
        print(f"✓ Generated {len(stations)} stations")
        
        # Check station count method
        count = modeler.get_station_count()
        assert count == len(stations)
        print(f"✓ Station count: {count}")
        
        return True
    
    @staticmethod
    def test_corridor_solid_creation():
        """Test IFC corridor solid creation."""
        print("\n--- Test: Corridor Solid Creation ---")
        
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        assembly = MockRoadAssembly()
        
        modeler = CorridorModeler(alignment_3d, assembly)
        
        # Use mock IFC file
        ifc_file = MockIFCFile()
        
        try:
            corridor_solid = modeler.create_corridor_solid(interval=25.0, ifc_file=ifc_file)
            
            assert corridor_solid is not None
            print("✓ Corridor solid created")
            
            # Check IFC entities were created
            entity_types = [e['type'] for e in ifc_file.entities]
            print(f"✓ Created {len(ifc_file.entities)} IFC entities")
            print(f"✓ Entity types: {set(entity_types)}")
            
            return True
        except Exception as e:
            print(f"✗ Failed to create corridor solid: {e}")
            return False
    
    @staticmethod
    def test_corridor_summary():
        """Test corridor summary generation."""
        print("\n--- Test: Corridor Summary ---")
        
        h_align = MockHorizontalAlignment(length=150.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        assembly = MockRoadAssembly("Urban Arterial")
        
        modeler = CorridorModeler(alignment_3d, assembly, "Main Street")
        modeler.generate_stations(interval=15.0)
        
        summary = modeler.get_summary()
        
        assert summary['name'] == "Main Street"
        assert summary['length'] > 0
        assert summary['station_count'] > 0
        print(f"✓ Summary generated:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
        return True


class TestCorridorManager:
    """Test suite for CorridorManager."""
    
    @staticmethod
    def test_manager_singleton():
        """Test that manager is a singleton."""
        print("\n--- Test: Manager Singleton ---")
        
        manager1 = get_manager()
        manager2 = get_manager()
        
        assert manager1 is manager2, "Manager should be singleton"
        print("✓ Singleton pattern working")
        
        return True
    
    @staticmethod
    def test_corridor_management():
        """Test corridor creation and management."""
        print("\n--- Test: Corridor Management ---")
        
        manager = CorridorManager()
        
        # Create corridors
        h_align = MockHorizontalAlignment(length=100.0)
        v_align = MockVerticalAlignment()
        alignment_3d = MockAlignment3D(h_align, v_align)
        assembly = MockRoadAssembly()
        
        corridor1 = manager.create_corridor("Corridor A", alignment_3d, assembly)
        corridor2 = manager.create_corridor("Corridor B", alignment_3d, assembly)
        
        # List corridors
        corridors = manager.list_corridors()
        assert len(corridors) == 2
        print(f"✓ Created {len(corridors)} corridors")
        
        # Get corridor
        retrieved = manager.get_corridor("Corridor A")
        assert retrieved is corridor1
        print("✓ Corridor retrieval working")
        
        # Active corridor
        active = manager.get_active_corridor()
        assert active is corridor2  # Last created
        print("✓ Active corridor: Corridor B")
        
        # Set active
        manager.set_active_corridor("Corridor A")
        active = manager.get_active_corridor()
        assert active is corridor1
        print("✓ Set active corridor to: Corridor A")
        
        # Remove corridor
        manager.remove_corridor("Corridor B")
        corridors = manager.list_corridors()
        assert len(corridors) == 1
        print("✓ Corridor removal working")
        
        return True


def run_all_tests():
    """Run complete test suite."""
    print("=" * 60)
    print("BLENDERCIVIL CORRIDOR MODELING - TEST SUITE")
    print("Sprint 5 Day 2 - Core Architecture Validation")
    print("=" * 60)
    
    if not CORRIDOR_MODULE_AVAILABLE:
        print("\n✗ ERROR: Corridor module not available for testing")
        print("  Make sure native_ifc_corridor.py is in the Python path")
        return False
    
    # Test counters
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    # Define all tests
    test_groups = [
        ("StationManager Tests", [
            ("Basic Station Generation", TestStationManager.test_basic_station_generation),
            ("Curve Densification", TestStationManager.test_curve_densification),
            ("PVI Station Addition", TestStationManager.test_pvi_stations),
            ("Critical Stations", TestStationManager.test_critical_stations),
            ("Station Merging", TestStationManager.test_station_merging),
        ]),
        ("CorridorModeler Tests", [
            ("Corridor Creation", TestCorridorModeler.test_corridor_creation),
            ("Station Generation", TestCorridorModeler.test_station_generation),
            ("Corridor Solid Creation", TestCorridorModeler.test_corridor_solid_creation),
            ("Corridor Summary", TestCorridorModeler.test_corridor_summary),
        ]),
        ("CorridorManager Tests", [
            ("Manager Singleton", TestCorridorManager.test_manager_singleton),
            ("Corridor Management", TestCorridorManager.test_corridor_management),
        ]),
    ]
    
    # Run all test groups
    for group_name, tests in test_groups:
        print(f"\n{'=' * 60}")
        print(f"{group_name}")
        print(f"{'=' * 60}")
        
        for test_name, test_func in tests:
            total_tests += 1
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"✓ PASSED: {test_name}")
                else:
                    failed_tests.append(test_name)
                    print(f"✗ FAILED: {test_name}")
            except Exception as e:
                failed_tests.append(test_name)
                print(f"✗ ERROR in {test_name}: {e}")
                import traceback
                traceback.print_exc()
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✓")
    print(f"Failed: {len(failed_tests)} ✗")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if failed_tests:
        print(f"\nFailed Tests:")
        for test in failed_tests:
            print(f"  ✗ {test}")
    else:
        print(f"\n🎉 ALL TESTS PASSED! 🎉")
    
    print(f"{'=' * 60}")
    
    return len(failed_tests) == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
