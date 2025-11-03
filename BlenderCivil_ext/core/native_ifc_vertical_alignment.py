"""
Native IFC Vertical Alignment Module
=====================================

Implements IFC 4.3 vertical alignments with PVI-based design.

This module provides:
- PVI (Point of Vertical Intersection) management
- Vertical curve generation (parabolic)
- Grade calculations
- Station/elevation queries
- Native IFC IfcAlignmentVertical export

Part of BlenderCivil Sprint 3: Vertical Alignments

Author: BlenderCivil Team
Date: November 2, 2025
Sprint: 3 - Day 2
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from abc import ABC, abstractmethod
import math
import ifcopenshell
import ifcopenshell.api


# ============================================================================
# CONSTANTS & DESIGN STANDARDS
# ============================================================================

# AASHTO minimum K-values (m/% grade change)
MIN_K_CREST_80KPH = 29.0  # Design speed 80 km/h
MIN_K_SAG_80KPH = 17.0

# Common design speeds (km/h) and their K-values
DESIGN_STANDARDS = {
    40: {"k_crest": 7.0, "k_sag": 6.0},
    50: {"k_crest": 11.0, "k_sag": 9.0},
    60: {"k_crest": 17.0, "k_sag": 12.0},
    80: {"k_crest": 29.0, "k_sag": 17.0},
    100: {"k_crest": 51.0, "k_sag": 26.0},
    120: {"k_crest": 84.0, "k_sag": 37.0},
}


# ============================================================================
# PVI CLASS
# ============================================================================

@dataclass
class PVI:
    """Point of Vertical Intersection
    
    Control point for vertical alignment design. PVIs define the grade 
    breakpoints and vertical curve locations.
    
    Attributes:
        station: Location along horizontal alignment (m)
        elevation: Height at this location (m)
        grade_in: Incoming grade (decimal, e.g., 0.02 = 2%)
        grade_out: Outgoing grade (decimal)
        curve_length: Length of vertical curve at this PVI (m), 0 = no curve
        k_value: K-value for curve design (m/%)
        description: Optional description of this PVI
    
    Properties:
        grade_in_percent: Incoming grade as percentage
        grade_out_percent: Outgoing grade as percentage
        grade_change: Algebraic difference in grades (A-value)
        is_crest_curve: True if this forms a crest (convex) curve
        is_sag_curve: True if this forms a sag (concave) curve
        bvc_station: Begin Vertical Curve station
        evc_station: End Vertical Curve station
    
    Example:
        >>> # Create PVI with 2% incoming and -1% outgoing grade
        >>> pvi = PVI(station=200.0, elevation=105.0, curve_length=80.0)
        >>> pvi.grade_in = 0.02
        >>> pvi.grade_out = -0.01
        >>> print(f"Grade change: {pvi.grade_change_percent:.1f}%")
        Grade change: 3.0%
    """
    
    station: float
    elevation: float
    grade_in: Optional[float] = None
    grade_out: Optional[float] = None
    curve_length: float = 0.0
    k_value: Optional[float] = None
    description: str = ""
    
    def __post_init__(self):
        """Validate PVI parameters after initialization"""
        if self.station < 0:
            raise ValueError(f"Station must be non-negative, got {self.station}")
        
        if self.curve_length < 0:
            raise ValueError(f"Curve length must be non-negative, got {self.curve_length}")
        
        # Calculate K-value if curve length and grades are known
        if self.curve_length > 0 and self.grade_in is not None and self.grade_out is not None:
            if self.k_value is None:
                self.k_value = self.calculate_k_value()
    
    @property
    def grade_in_percent(self) -> Optional[float]:
        """Incoming grade as percentage (e.g., 2.5%)"""
        return self.grade_in * 100 if self.grade_in is not None else None
    
    @property
    def grade_out_percent(self) -> Optional[float]:
        """Outgoing grade as percentage (e.g., -1.5%)"""
        return self.grade_out * 100 if self.grade_out is not None else None
    
    @property
    def grade_change(self) -> Optional[float]:
        """Algebraic difference in grades (decimal)
        
        This is the A-value: A = |g2 - g1|
        Always positive regardless of crest or sag.
        """
        if self.grade_in is not None and self.grade_out is not None:
            return abs(self.grade_out - self.grade_in)
        return None
    
    @property
    def grade_change_percent(self) -> Optional[float]:
        """Algebraic difference in grades (percentage)"""
        return self.grade_change * 100 if self.grade_change is not None else None
    
    @property
    def is_crest_curve(self) -> bool:
        """True if this PVI forms a crest (convex) curve
        
        Crest curve: incoming grade > outgoing grade (g1 > g2)
        """
        if self.grade_in is not None and self.grade_out is not None:
            return self.grade_in > self.grade_out
        return False
    
    @property
    def is_sag_curve(self) -> bool:
        """True if this PVI forms a sag (concave) curve
        
        Sag curve: incoming grade < outgoing grade (g1 < g2)
        """
        if self.grade_in is not None and self.grade_out is not None:
            return self.grade_in < self.grade_out
        return False
    
    @property
    def has_curve(self) -> bool:
        """True if this PVI has a vertical curve (curve_length > 0)"""
        return self.curve_length > 0
    
    @property
    def bvc_station(self) -> Optional[float]:
        """Begin Vertical Curve station
        
        BVC is located L/2 before the PVI station.
        Returns None if no curve at this PVI.
        """
        if self.curve_length > 0:
            return self.station - (self.curve_length / 2.0)
        return None
    
    @property
    def evc_station(self) -> Optional[float]:
        """End Vertical Curve station
        
        EVC is located L/2 after the PVI station.
        Returns None if no curve at this PVI.
        """
        if self.curve_length > 0:
            return self.station + (self.curve_length / 2.0)
        return None
    
    def calculate_k_value(self) -> float:
        """Calculate K-value from curve length and grade change
        
        K = L / A
        where:
            L = curve length (m)
            A = |g2 - g1| × 100 (% grade change)
        
        Returns:
            K-value in m/% units
        
        Raises:
            ValueError: If grades are not set or curve length is zero
        """
        if self.curve_length <= 0:
            raise ValueError("Cannot calculate K-value: curve_length is zero")
        
        if self.grade_change is None:
            raise ValueError("Cannot calculate K-value: grades not set")
        
        grade_change_percent = self.grade_change * 100
        
        if grade_change_percent == 0:
            raise ValueError("Cannot calculate K-value: grade change is zero")
        
        return self.curve_length / grade_change_percent
    
    def calculate_curve_length_from_k(self, k_value: float) -> float:
        """Calculate required curve length for a given K-value
        
        L = K × A
        where:
            K = K-value (m/%)
            A = |g2 - g1| × 100 (% grade change)
        
        Args:
            k_value: Desired K-value (m/%)
        
        Returns:
            Required curve length (m)
        
        Raises:
            ValueError: If grades are not set
        """
        if self.grade_change is None:
            raise ValueError("Cannot calculate curve length: grades not set")
        
        grade_change_percent = self.grade_change * 100
        return k_value * grade_change_percent
    
    def validate_k_value(self, design_speed: float) -> Tuple[bool, str]:
        """Validate K-value against design standards
        
        Args:
            design_speed: Design speed in km/h
        
        Returns:
            Tuple of (is_valid, message)
        """
        if self.k_value is None:
            return False, "K-value not calculated"
        
        if design_speed not in DESIGN_STANDARDS:
            return False, f"No standards for design speed {design_speed} km/h"
        
        standards = DESIGN_STANDARDS[design_speed]
        
        if self.is_crest_curve:
            min_k = standards["k_crest"]
            curve_type = "crest"
        elif self.is_sag_curve:
            min_k = standards["k_sag"]
            curve_type = "sag"
        else:
            return False, "Cannot determine curve type (grades not set)"
        
        if self.k_value >= min_k:
            return True, f"K-value {self.k_value:.1f} meets minimum {min_k:.1f} for {curve_type} at {design_speed} km/h"
        else:
            return False, f"K-value {self.k_value:.1f} below minimum {min_k:.1f} for {curve_type} at {design_speed} km/h"
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        curve_info = f"L={self.curve_length:.1f}m" if self.curve_length > 0 else "No curve"
        grade_info = ""
        
        if self.grade_in is not None and self.grade_out is not None:
            grade_info = f" g_in={self.grade_in_percent:.2f}% g_out={self.grade_out_percent:.2f}%"
        
        return f"PVI(sta={self.station:.1f}m, elev={self.elevation:.3f}m, {curve_info}{grade_info})"


# ============================================================================
# VERTICAL SEGMENT BASE CLASS
# ============================================================================

class VerticalSegment(ABC):
    """Abstract base class for vertical alignment segments
    
    Vertical alignments are composed of segments:
    - TangentSegment: constant grade
    - ParabolicSegment: parabolic vertical curve
    
    All segments must implement:
    - get_elevation(station): elevation at given station
    - get_grade(station): grade at given station
    - to_ifc_segment(): export to IFC format
    """
    
    def __init__(self, start_station: float, end_station: float, segment_type: str):
        """Initialize base segment
        
        Args:
            start_station: Starting station (m)
            end_station: Ending station (m)
            segment_type: Type identifier ("TANGENT", "PARABOLIC", etc.)
        """
        if end_station <= start_station:
            raise ValueError(f"End station ({end_station}) must be > start station ({start_station})")
        
        self.start_station = start_station
        self.end_station = end_station
        self.segment_type = segment_type
    
    @property
    def length(self) -> float:
        """Segment length in meters"""
        return self.end_station - self.start_station
    
    @property
    def mid_station(self) -> float:
        """Station at segment midpoint"""
        return (self.start_station + self.end_station) / 2.0
    
    def contains_station(self, station: float, tolerance: float = 1e-6) -> bool:
        """Check if station is within this segment
        
        Args:
            station: Station to check (m)
            tolerance: Numerical tolerance (m)
        
        Returns:
            True if station is in [start_station, end_station]
        """
        return (self.start_station - tolerance) <= station <= (self.end_station + tolerance)
    
    @abstractmethod
    def get_elevation(self, station: float) -> float:
        """Calculate elevation at given station
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Elevation (m)
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        pass
    
    @abstractmethod
    def get_grade(self, station: float) -> float:
        """Calculate grade at given station
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Grade as decimal (e.g., 0.02 = 2%)
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        pass
    
    @abstractmethod
    def to_ifc_segment(self, ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """Export segment to IFC IfcAlignmentVerticalSegment
        
        Args:
            ifc_file: IFC file instance
        
        Returns:
            IfcAlignmentVerticalSegment entity
        """
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"{self.__class__.__name__}({self.start_station:.1f}-{self.end_station:.1f}m)"


# ============================================================================
# TANGENT SEGMENT CLASS
# ============================================================================

class TangentSegment(VerticalSegment):
    """Constant grade (tangent) segment
    
    Linear elevation profile with constant grade.
    Simpler and faster than curved segments.
    
    Elevation equation:
        E(x) = E₀ + g × (x - x₀)
    
    where:
        E₀ = elevation at start
        g = grade (decimal)
        x = current station
        x₀ = start station
    
    Attributes:
        start_station: Starting station (m)
        end_station: Ending station (m)
        start_elevation: Elevation at start (m)
        grade: Constant grade (decimal, e.g., 0.02 = 2%)
    
    Example:
        >>> # Create 2% upgrade tangent
        >>> tangent = TangentSegment(0.0, 100.0, 100.0, 0.02)
        >>> tangent.get_elevation(50.0)  # Elevation at station 50m
        101.0
        >>> tangent.get_grade(50.0)       # Grade at station 50m
        0.02
    """
    
    def __init__(
        self,
        start_station: float,
        end_station: float,
        start_elevation: float,
        grade: float
    ):
        """Initialize tangent segment
        
        Args:
            start_station: Starting station (m)
            end_station: Ending station (m)
            start_elevation: Elevation at start station (m)
            grade: Constant grade (decimal)
        """
        super().__init__(start_station, end_station, "TANGENT")
        
        self.start_elevation = start_elevation
        self.grade = grade
    
    @property
    def end_elevation(self) -> float:
        """Elevation at end of segment"""
        return self.start_elevation + (self.grade * self.length)
    
    @property
    def grade_percent(self) -> float:
        """Grade as percentage"""
        return self.grade * 100
    
    def get_elevation(self, station: float) -> float:
        """Calculate elevation at given station
        
        Uses linear equation: E = E₀ + g×(x - x₀)
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Elevation (m)
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        if not self.contains_station(station):
            raise ValueError(
                f"Station {station:.3f}m outside segment bounds "
                f"[{self.start_station:.3f}, {self.end_station:.3f}]"
            )
        
        distance_along = station - self.start_station
        elevation = self.start_elevation + (self.grade * distance_along)
        
        return elevation
    
    def get_grade(self, station: float) -> float:
        """Calculate grade at given station
        
        For tangent segments, grade is constant everywhere.
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Grade as decimal (constant for tangent)
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        if not self.contains_station(station):
            raise ValueError(
                f"Station {station:.3f}m outside segment bounds "
                f"[{self.start_station:.3f}, {self.end_station:.3f}]"
            )
        
        return self.grade
    
    def to_ifc_segment(self, ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """Export to IFC IfcAlignmentVerticalSegment
        
        Creates IFC entity with CONSTANTGRADIENT type.
        
        Args:
            ifc_file: IFC file instance
        
        Returns:
            IfcAlignmentVerticalSegment entity
        """
        segment = ifc_file.create_entity(
            "IfcAlignmentVerticalSegment",
            StartDistAlong=self.start_station,
            HorizontalLength=self.length,
            StartHeight=self.start_elevation,
            StartGradient=self.grade,
            PredefinedType="CONSTANTGRADIENT"
        )
        
        return segment
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"TangentSegment({self.start_station:.1f}-{self.end_station:.1f}m, "
            f"g={self.grade_percent:.2f}%)"
        )


# ============================================================================
# PARABOLIC SEGMENT CLASS
# ============================================================================

class ParabolicSegment(VerticalSegment):
    """Parabolic vertical curve segment
    
    Smooth transition between two grades using a parabolic arc.
    Used at PVIs to provide comfortable grade changes.
    
    Mathematics:
        Elevation: E(x) = E_BVC + g₁×x + ((g₂-g₁)/(2L))×x²
        Grade:     g(x) = g₁ + ((g₂-g₁)/L)×x
    
    where:
        x = distance from BVC (begin vertical curve)
        E_BVC = elevation at BVC
        g₁ = incoming grade (decimal)
        g₂ = outgoing grade (decimal)
        L = curve length
    
    Curve Types:
        - Crest: g₁ > g₂ (convex, looks like hilltop)
        - Sag: g₁ < g₂ (concave, looks like valley)
    
    Attributes:
        start_station: BVC station (m)
        end_station: EVC station (m)
        start_elevation: Elevation at BVC (m)
        g1: Incoming grade (decimal)
        g2: Outgoing grade (decimal)
        pvi_station: PVI station (midpoint of curve)
    
    Example:
        >>> # Create crest curve: +2% to -1%
        >>> curve = ParabolicSegment(
        ...     start_station=160.0,  # BVC
        ...     end_station=240.0,    # EVC
        ...     start_elevation=104.0,
        ...     g1=0.02,               # +2% incoming
        ...     g2=-0.01               # -1% outgoing
        ... )
        >>> curve.get_elevation(200.0)  # At PVI
        105.6
        >>> curve.get_grade(200.0)       # At PVI
        0.005
    """
    
    def __init__(
        self,
        start_station: float,
        end_station: float,
        start_elevation: float,
        g1: float,
        g2: float,
        pvi_station: Optional[float] = None
    ):
        """Initialize parabolic segment
        
        Args:
            start_station: BVC station (m)
            end_station: EVC station (m)
            start_elevation: Elevation at BVC (m)
            g1: Incoming grade (decimal)
            g2: Outgoing grade (decimal)
            pvi_station: Optional PVI station (defaults to midpoint)
        """
        super().__init__(start_station, end_station, "PARABOLIC")
        
        self.start_elevation = start_elevation
        self.g1 = g1
        self.g2 = g2
        
        # PVI is at curve midpoint
        if pvi_station is None:
            self.pvi_station = (start_station + end_station) / 2.0
        else:
            self.pvi_station = pvi_station
    
    @property
    def end_elevation(self) -> float:
        """Elevation at end of curve (EVC)"""
        return self.get_elevation(self.end_station)
    
    @property
    def is_crest(self) -> bool:
        """True if this is a crest (convex) curve"""
        return self.g1 > self.g2
    
    @property
    def is_sag(self) -> bool:
        """True if this is a sag (concave) curve"""
        return self.g1 < self.g2
    
    @property
    def grade_change(self) -> float:
        """Algebraic difference in grades (A-value)"""
        return abs(self.g2 - self.g1)
    
    @property
    def k_value(self) -> float:
        """K-value of this curve (L/A in m/%)"""
        grade_change_percent = self.grade_change * 100
        if grade_change_percent == 0:
            return float('inf')
        return self.length / grade_change_percent
    
    @property
    def pvi_elevation(self) -> float:
        """Elevation at PVI (highest/lowest point for crest/sag)"""
        return self.get_elevation(self.pvi_station)
    
    @property
    def turning_point_station(self) -> Optional[float]:
        """Station where grade = 0 (high/low point of curve)
        
        Returns None if curve doesn't cross zero grade.
        """
        # At grade = 0: g₁ + ((g₂-g₁)/L)×x = 0
        # Solve for x: x = -g₁ × L / (g₂ - g₁)
        
        if self.g2 == self.g1:
            return None  # No grade change
        
        x = -self.g1 * self.length / (self.g2 - self.g1)
        
        # Check if turning point is within curve
        if 0 <= x <= self.length:
            return self.start_station + x
        
        return None
    
    def get_elevation(self, station: float) -> float:
        """Calculate elevation at given station
        
        Uses parabolic equation:
            E(x) = E_BVC + g₁×x + ((g₂-g₁)/(2L))×x²
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Elevation (m)
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        if not self.contains_station(station):
            raise ValueError(
                f"Station {station:.3f}m outside segment bounds "
                f"[{self.start_station:.3f}, {self.end_station:.3f}]"
            )
        
        # Distance from BVC
        x = station - self.start_station
        
        # Parabolic elevation equation
        # E = E₀ + g₁×x + ((g₂-g₁)/(2L))×x²
        elevation = (
            self.start_elevation +
            self.g1 * x +
            ((self.g2 - self.g1) / (2.0 * self.length)) * (x ** 2)
        )
        
        return elevation
    
    def get_grade(self, station: float) -> float:
        """Calculate grade at given station
        
        Uses parabolic grade equation:
            g(x) = g₁ + ((g₂-g₁)/L)×x
        
        Args:
            station: Station along alignment (m)
        
        Returns:
            Grade as decimal at this station
        
        Raises:
            ValueError: If station is outside segment bounds
        """
        if not self.contains_station(station):
            raise ValueError(
                f"Station {station:.3f}m outside segment bounds "
                f"[{self.start_station:.3f}, {self.end_station:.3f}]"
            )
        
        # Distance from BVC
        x = station - self.start_station
        
        # Linear grade change
        # g = g₁ + ((g₂-g₁)/L)×x
        grade = self.g1 + ((self.g2 - self.g1) / self.length) * x
        
        return grade
    
    def to_ifc_segment(self, ifc_file: ifcopenshell.file) -> ifcopenshell.entity_instance:
        """Export to IFC IfcAlignmentVerticalSegment
        
        Creates IFC entity with PARABOLICARC type.
        
        Args:
            ifc_file: IFC file instance
        
        Returns:
            IfcAlignmentVerticalSegment entity
        """
        segment = ifc_file.create_entity(
            "IfcAlignmentVerticalSegment",
            StartDistAlong=self.start_station,
            HorizontalLength=self.length,
            StartHeight=self.start_elevation,
            StartGradient=self.g1,
            EndGradient=self.g2,
            PredefinedType="PARABOLICARC"
        )
        
        return segment
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        curve_type = "CREST" if self.is_crest else "SAG"
        return (
            f"ParabolicSegment({self.start_station:.1f}-{self.end_station:.1f}m, "
            f"{curve_type}, g₁={self.g1*100:.2f}% → g₂={self.g2*100:.2f}%, "
            f"K={self.k_value:.1f})"
        )


# ============================================================================
# VERTICAL ALIGNMENT MANAGER CLASS
# ============================================================================

class VerticalAlignment:
    """Complete vertical alignment with PVI-based design
    
    Manages PVIs (Points of Vertical Intersection) and automatically
    generates vertical segments (tangents and parabolic curves).
    
    Design workflow:
        1. Create alignment
        2. Add PVIs (control points)
        3. Set curve lengths at PVIs
        4. Generate segments automatically
        5. Query elevation at any station
        6. Export to IFC 4.3
    
    Attributes:
        name: Alignment name
        pvis: List of PVI control points (sorted by station)
        segments: Generated vertical segments (tangents + curves)
        design_speed: Design speed for K-value validation (km/h)
        description: Optional description
    
    Example:
        >>> # Create vertical alignment
        >>> valign = VerticalAlignment("Main Street Profile")
        >>> 
        >>> # Add PVIs
        >>> valign.add_pvi(0.0, 100.0)              # Start
        >>> valign.add_pvi(200.0, 105.0, curve_length=80.0)  # Crest curve
        >>> valign.add_pvi(450.0, 103.0, curve_length=100.0) # Sag curve
        >>> valign.add_pvi(650.0, 110.0)            # End
        >>> 
        >>> # Query elevation
        >>> elev = valign.get_elevation(300.0)
        >>> print(f"Elevation at 300m: {elev:.3f}m")
    """
    
    def __init__(
        self,
        name: str = "Vertical Alignment",
        design_speed: float = 80.0,
        description: str = ""
    ):
        """Initialize vertical alignment
        
        Args:
            name: Alignment name
            design_speed: Design speed for K-value validation (km/h)
            description: Optional description
        """
        self.name = name
        self.design_speed = design_speed
        self.description = description
        
        self.pvis: List[PVI] = []
        self.segments: List[VerticalSegment] = []
        
        # Design standards based on speed
        if design_speed in DESIGN_STANDARDS:
            standards = DESIGN_STANDARDS[design_speed]
            self.min_k_crest = standards["k_crest"]
            self.min_k_sag = standards["k_sag"]
        else:
            # Default to 80 km/h if speed not in standards
            self.min_k_crest = MIN_K_CREST_80KPH
            self.min_k_sag = MIN_K_SAG_80KPH
    
    # ========================================================================
    # PVI MANAGEMENT
    # ========================================================================
    
    def add_pvi(
        self,
        station: float,
        elevation: float,
        curve_length: float = 0.0,
        description: str = ""
    ) -> PVI:
        """Add a PVI to the alignment
        
        PVIs are automatically sorted by station.
        Grades and segments are recalculated after adding.
        
        Args:
            station: Station location (m)
            elevation: Elevation at this station (m)
            curve_length: Vertical curve length (m), 0 = no curve
            description: Optional PVI description
        
        Returns:
            The created PVI object
        
        Raises:
            ValueError: If PVI conflicts with existing PVI
        """
        # Check for duplicate station
        for existing in self.pvis:
            if abs(existing.station - station) < 1e-6:
                raise ValueError(f"PVI already exists at station {station:.3f}m")
        
        # Create PVI
        pvi = PVI(
            station=station,
            elevation=elevation,
            curve_length=curve_length,
            description=description
        )
        
        # Insert in sorted order
        insert_idx = 0
        for i, existing in enumerate(self.pvis):
            if station > existing.station:
                insert_idx = i + 1
        
        self.pvis.insert(insert_idx, pvi)
        
        # Recalculate everything
        self._calculate_grades()
        self._generate_segments()
        
        return pvi
    
    def remove_pvi(self, index: int) -> None:
        """Remove PVI at given index
        
        Args:
            index: Index in pvis list
        
        Raises:
            IndexError: If index out of range
        """
        if not (0 <= index < len(self.pvis)):
            raise IndexError(f"PVI index {index} out of range [0, {len(self.pvis)-1}]")
        
        self.pvis.pop(index)
        
        # Recalculate
        self._calculate_grades()
        self._generate_segments()
    
    def update_pvi(
        self,
        index: int,
        station: Optional[float] = None,
        elevation: Optional[float] = None,
        curve_length: Optional[float] = None
    ) -> None:
        """Update PVI parameters
        
        Args:
            index: Index of PVI to update
            station: New station (None = keep existing)
            elevation: New elevation (None = keep existing)
            curve_length: New curve length (None = keep existing)
        
        Raises:
            IndexError: If index out of range
        """
        if not (0 <= index < len(self.pvis)):
            raise IndexError(f"PVI index {index} out of range")
        
        pvi = self.pvis[index]
        
        # Update parameters
        if station is not None:
            pvi.station = station
            # Re-sort if station changed
            self.pvis.sort(key=lambda p: p.station)
        
        if elevation is not None:
            pvi.elevation = elevation
        
        if curve_length is not None:
            pvi.curve_length = curve_length
        
        # Recalculate
        self._calculate_grades()
        self._generate_segments()
    
    def get_pvi(self, index: int) -> PVI:
        """Get PVI by index
        
        Args:
            index: PVI index
        
        Returns:
            PVI object
        
        Raises:
            IndexError: If index out of range
        """
        return self.pvis[index]
    
    def find_pvi_at_station(self, station: float, tolerance: float = 1e-3) -> Optional[int]:
        """Find PVI index at given station
        
        Args:
            station: Station to search
            tolerance: Search tolerance (m)
        
        Returns:
            PVI index or None if not found
        """
        for i, pvi in enumerate(self.pvis):
            if abs(pvi.station - station) < tolerance:
                return i
        return None
    
    # ========================================================================
    # GRADE CALCULATIONS
    # ========================================================================
    
    def _calculate_grades(self) -> None:
        """Calculate grades between all adjacent PVIs
        
        This is called automatically after PVI changes.
        Sets grade_in and grade_out for each PVI.
        """
        if len(self.pvis) < 2:
            return  # Need at least 2 PVIs
        
        # Calculate grade between each pair of PVIs
        for i in range(len(self.pvis) - 1):
            pvi1 = self.pvis[i]
            pvi2 = self.pvis[i + 1]
            
            # Grade = rise / run
            rise = pvi2.elevation - pvi1.elevation
            run = pvi2.station - pvi1.station
            
            if run == 0:
                raise ValueError(
                    f"PVIs at same station: {pvi1.station:.3f}m "
                    f"(indices {i} and {i+1})"
                )
            
            grade = rise / run
            
            # Set outgoing grade for PVI1 and incoming grade for PVI2
            pvi1.grade_out = grade
            pvi2.grade_in = grade
        
        # First PVI has no incoming grade
        self.pvis[0].grade_in = self.pvis[0].grade_out
        
        # Last PVI has no outgoing grade
        self.pvis[-1].grade_out = self.pvis[-1].grade_in
        
        # Calculate K-values for PVIs with curves
        for pvi in self.pvis:
            if pvi.curve_length > 0 and pvi.grade_in is not None and pvi.grade_out is not None:
                try:
                    pvi.k_value = pvi.calculate_k_value()
                except (ValueError, ZeroDivisionError):
                    # Grade change is zero or other issue
                    pvi.k_value = None
    
    # ========================================================================
    # SEGMENT GENERATION
    # ========================================================================
    
    def _generate_segments(self) -> None:
        """Generate vertical segments from PVIs
        
        Creates tangent and parabolic segments based on PVI configuration.
        This is called automatically after PVI changes.
        
        Segment generation rules:
        1. Between PVIs without curves: create tangent segment
        2. At PVI with curve: create parabolic segment
        3. Before/after curved PVI: create tangent to BVC/from EVC
        """
        self.segments.clear()
        
        if len(self.pvis) < 2:
            return  # Need at least 2 PVIs
        
        current_station = self.pvis[0].station
        current_elevation = self.pvis[0].elevation
        
        for i in range(len(self.pvis) - 1):
            pvi1 = self.pvis[i]
            pvi2 = self.pvis[i + 1]
            
            # Grade between these PVIs
            grade = pvi1.grade_out
            
            # Check if PVI2 has a curve
            if pvi2.curve_length > 0:
                # PVI2 has curve
                bvc_station = pvi2.bvc_station
                
                # Create tangent from current position to BVC
                if bvc_station > current_station:
                    tangent = TangentSegment(
                        start_station=current_station,
                        end_station=bvc_station,
                        start_elevation=current_elevation,
                        grade=grade
                    )
                    self.segments.append(tangent)
                    
                    current_station = bvc_station
                    current_elevation = tangent.end_elevation
                
                # Create parabolic curve
                evc_station = pvi2.evc_station
                
                curve = ParabolicSegment(
                    start_station=current_station,  # BVC
                    end_station=evc_station,         # EVC
                    start_elevation=current_elevation,
                    g1=pvi2.grade_in,
                    g2=pvi2.grade_out,
                    pvi_station=pvi2.station
                )
                self.segments.append(curve)
                
                current_station = evc_station
                current_elevation = curve.end_elevation
            
            else:
                # No curve at PVI2, check if we're at last PVI
                if i == len(self.pvis) - 2:
                    # Last segment - tangent to final PVI
                    tangent = TangentSegment(
                        start_station=current_station,
                        end_station=pvi2.station,
                        start_elevation=current_elevation,
                        grade=grade
                    )
                    self.segments.append(tangent)
                    
                    current_station = pvi2.station
                    current_elevation = tangent.end_elevation
                else:
                    # Continue to next PVI (will handle in next iteration)
                    pass
    
    # ========================================================================
    # ELEVATION & GRADE QUERIES
    # ========================================================================
    
    def get_elevation(self, station: float) -> float:
        """Get elevation at any station along alignment
        
        Args:
            station: Station location (m)
        
        Returns:
            Elevation (m)
        
        Raises:
            ValueError: If station is outside alignment range
        """
        if len(self.segments) == 0:
            raise ValueError("No segments generated (need at least 2 PVIs)")
        
        # Find segment containing this station
        for segment in self.segments:
            if segment.contains_station(station):
                return segment.get_elevation(station)
        
        # Station not found in any segment
        raise ValueError(
            f"Station {station:.3f}m outside alignment range "
            f"[{self.start_station:.3f}, {self.end_station:.3f}]"
        )
    
    def get_grade(self, station: float) -> float:
        """Get grade at any station along alignment
        
        Args:
            station: Station location (m)
        
        Returns:
            Grade as decimal (e.g., 0.02 = 2%)
        
        Raises:
            ValueError: If station is outside alignment range
        """
        if len(self.segments) == 0:
            raise ValueError("No segments generated (need at least 2 PVIs)")
        
        # Find segment containing this station
        for segment in self.segments:
            if segment.contains_station(station):
                return segment.get_grade(station)
        
        # Station not found in any segment
        raise ValueError(
            f"Station {station:.3f}m outside alignment range "
            f"[{self.start_station:.3f}, {self.end_station:.3f}]"
        )
    
    def get_profile_points(
        self,
        interval: float = 5.0,
        include_pvis: bool = True
    ) -> List[Tuple[float, float, float]]:
        """Get list of (station, elevation, grade) points along profile
        
        Useful for visualization and analysis.
        
        Args:
            interval: Station interval for sampling (m)
            include_pvis: Whether to include exact PVI stations
        
        Returns:
            List of (station, elevation, grade) tuples
        """
        if len(self.segments) == 0:
            return []
        
        points = []
        
        # Sample at regular intervals
        station = self.start_station
        while station <= self.end_station:
            try:
                elev = self.get_elevation(station)
                grade = self.get_grade(station)
                points.append((station, elev, grade))
            except ValueError:
                pass  # Skip invalid stations
            
            station += interval
        
        # Add exact PVI locations if requested
        if include_pvis:
            pvi_points = []
            for pvi in self.pvis:
                try:
                    elev = self.get_elevation(pvi.station)
                    grade = self.get_grade(pvi.station)
                    pvi_points.append((pvi.station, elev, grade))
                except ValueError:
                    pass
            
            # Merge and sort
            all_points = points + pvi_points
            all_points.sort(key=lambda p: p[0])
            
            # Remove duplicates (keep PVI points)
            unique_points = []
            last_sta = -float('inf')
            for sta, elev, grade in all_points:
                if abs(sta - last_sta) > 1e-6:
                    unique_points.append((sta, elev, grade))
                    last_sta = sta
            
            return unique_points
        
        return points
    
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    
    @property
    def start_station(self) -> float:
        """Starting station of alignment"""
        return self.pvis[0].station if self.pvis else 0.0
    
    @property
    def end_station(self) -> float:
        """Ending station of alignment"""
        return self.pvis[-1].station if self.pvis else 0.0
    
    @property
    def length(self) -> float:
        """Total alignment length"""
        return self.end_station - self.start_station
    
    @property
    def start_elevation(self) -> float:
        """Starting elevation"""
        return self.pvis[0].elevation if self.pvis else 0.0
    
    @property
    def end_elevation(self) -> float:
        """Ending elevation"""
        return self.pvis[-1].elevation if self.pvis else 0.0
    
    @property
    def elevation_change(self) -> float:
        """Total elevation change"""
        return self.end_elevation - self.start_elevation
    
    @property
    def average_grade(self) -> float:
        """Average grade over entire alignment"""
        if self.length == 0:
            return 0.0
        return self.elevation_change / self.length
    
    @property
    def num_pvis(self) -> int:
        """Number of PVIs"""
        return len(self.pvis)
    
    @property
    def num_segments(self) -> int:
        """Number of segments"""
        return len(self.segments)
    
    @property
    def num_curves(self) -> int:
        """Number of vertical curves"""
        return sum(1 for pvi in self.pvis if pvi.curve_length > 0)
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate alignment design
        
        Checks:
        - Minimum number of PVIs
        - K-values meet design standards
        - Segments generated correctly
        - No overlapping segments
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        # Check minimum PVIs
        if len(self.pvis) < 2:
            warnings.append("Need at least 2 PVIs to create alignment")
            return False, warnings
        
        # Check K-values
        for i, pvi in enumerate(self.pvis):
            if pvi.curve_length > 0:
                is_valid, msg = pvi.validate_k_value(self.design_speed)
                if not is_valid:
                    warnings.append(f"PVI {i} at {pvi.station:.1f}m: {msg}")
        
        # Check segments generated
        if len(self.segments) == 0:
            warnings.append("No segments generated")
            return False, warnings
        
        # Check segment continuity
        for i in range(len(self.segments) - 1):
            seg1 = self.segments[i]
            seg2 = self.segments[i + 1]
            
            gap = abs(seg2.start_station - seg1.end_station)
            if gap > 1e-3:
                warnings.append(
                    f"Gap between segments {i} and {i+1}: {gap:.3f}m"
                )
        
        is_valid = len(warnings) == 0
        return is_valid, warnings
    
    # ========================================================================
    # IFC EXPORT
    # ========================================================================
    
    def to_ifc(
        self,
        ifc_file: ifcopenshell.file,
        horizontal_alignment: Optional[ifcopenshell.entity_instance] = None
    ) -> ifcopenshell.entity_instance:
        """Export to IFC 4.3 IfcAlignmentVertical
        
        Args:
            ifc_file: IFC file instance
            horizontal_alignment: Optional parent horizontal alignment
        
        Returns:
            IfcAlignmentVertical entity with all segments
        """
        # Create IfcAlignmentVertical
        vertical = ifc_file.create_entity(
            "IfcAlignmentVertical",
            Name=self.name
        )
        
        # Link to horizontal if provided
        if horizontal_alignment:
            # Create nested relationship
            ifc_file.create_entity(
                "IfcRelNests",
                RelatingObject=horizontal_alignment,
                RelatedObjects=[vertical]
            )
        
        # Export all segments
        ifc_segments = []
        for segment in self.segments:
            ifc_seg = segment.to_ifc_segment(ifc_file)
            ifc_segments.append(ifc_seg)
        
        # Assign segments to vertical alignment
        if ifc_segments:
            vertical.Segments = ifc_segments
        
        return vertical
    
    # ========================================================================
    # UTILITIES
    # ========================================================================
    
    def summary(self) -> str:
        """Generate text summary of alignment
        
        Returns:
            Multi-line summary string
        """
        lines = []
        lines.append(f"Vertical Alignment: {self.name}")
        lines.append(f"  Design Speed: {self.design_speed} km/h")
        lines.append(f"  Length: {self.length:.1f}m")
        lines.append(f"  Elevation Change: {self.elevation_change:+.3f}m")
        lines.append(f"  Average Grade: {self.average_grade*100:+.2f}%")
        lines.append(f"  PVIs: {self.num_pvis}, Curves: {self.num_curves}, Segments: {self.num_segments}")
        lines.append("")
        
        lines.append("PVIs:")
        for i, pvi in enumerate(self.pvis):
            curve_info = ""
            if pvi.curve_length > 0:
                curve_type = "CREST" if pvi.is_crest_curve else "SAG"
                curve_info = f" | {curve_type} L={pvi.curve_length:.1f}m K={pvi.k_value:.1f}"
            
            lines.append(
                f"  {i}: Sta {pvi.station:.1f}m, Elev {pvi.elevation:.3f}m"
                f"{curve_info}"
            )
            if pvi.grade_in is not None:
                lines.append(f"      Grade in: {pvi.grade_in_percent:+.2f}%")
            if pvi.grade_out is not None:
                lines.append(f"      Grade out: {pvi.grade_out_percent:+.2f}%")
        
        lines.append("")
        lines.append("Segments:")
        for i, seg in enumerate(self.segments):
            lines.append(f"  {i}: {seg}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return (
            f"VerticalAlignment('{self.name}', "
            f"{self.num_pvis} PVIs, {self.num_segments} segments, "
            f"{self.length:.1f}m)"
        )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_required_curve_length(
    grade_change_percent: float,
    k_value: float
) -> float:
    """Calculate required curve length for given K-value
    
    L = K × A
    
    Args:
        grade_change_percent: Grade change in percent (e.g., 3.0 for 3%)
        k_value: Desired K-value (m/%)
    
    Returns:
        Required curve length (m)
    """
    return k_value * grade_change_percent


def calculate_k_value(
    curve_length: float,
    grade_change_percent: float
) -> float:
    """Calculate K-value for given curve length and grade change
    
    K = L / A
    
    Args:
        curve_length: Curve length (m)
        grade_change_percent: Grade change in percent
    
    Returns:
        K-value (m/%)
    
    Raises:
        ValueError: If grade change is zero
    """
    if grade_change_percent == 0:
        raise ValueError("Cannot calculate K-value: grade change is zero")
    
    return curve_length / grade_change_percent


def get_minimum_k_value(design_speed: float, is_crest: bool) -> float:
    """Get minimum K-value for design speed
    
    Args:
        design_speed: Design speed (km/h)
        is_crest: True for crest curve, False for sag curve
    
    Returns:
        Minimum K-value (m/%)
    
    Raises:
        ValueError: If design speed not in standards
    """
    if design_speed not in DESIGN_STANDARDS:
        raise ValueError(f"No standards for design speed {design_speed} km/h")
    
    standards = DESIGN_STANDARDS[design_speed]
    return standards["k_crest"] if is_crest else standards["k_sag"]


# ============================================================================
# MODULE INFO
# ============================================================================

__version__ = "1.0.0"
__author__ = "BlenderCivil Team"
__date__ = "2025-11-02"
__sprint__ = "Sprint 3 - Day 2"

# Export public API
__all__ = [
    # Classes
    "PVI",
    "VerticalSegment",
    "TangentSegment",
    "ParabolicSegment",
    "VerticalAlignment",
    # Helper functions
    "calculate_required_curve_length",
    "calculate_k_value",
    "get_minimum_k_value",
    # Constants
    "DESIGN_STANDARDS",
    "MIN_K_CREST_80KPH",
    "MIN_K_SAG_80KPH",
]

