"""
BlenderCivil - LandXML Import/Export

Handles LandXML file format for survey data and civil design elements.
Supports:
- Coordinate Reference Systems (CRS)
- Alignments (horizontal and vertical)
- Surfaces (future)
- Points and point groups

LandXML Schema: http://www.landxml.org/schema/LandXML-1.2/

Author: BlenderCivil Development Team
Date: October 28, 2025
"""

import bpy
import xml.etree.ElementTree as ET
from mathutils import Vector
import math
from typing import List, Dict, Tuple, Optional


# ============================================================================
# XML NAMESPACES
# ============================================================================

# LandXML uses namespace prefixes
LANDXML_NS = {
    'lx': 'http://www.landxml.org/schema/LandXML-1.2',
    '': 'http://www.landxml.org/schema/LandXML-1.2'
}


# ============================================================================
# CRS EXTRACTION
# ============================================================================

def extract_crs_info(root: ET.Element) -> Dict:
    """
    Extract Coordinate Reference System information from LandXML.
    
    LandXML CRS can be defined in multiple ways:
    - <CoordinateSystem> element
    - EPSG code reference
    - Direct projection parameters
    
    Args:
        root: XML root element
        
    Returns:
        Dictionary with CRS info: {
            'name': str,
            'epsg_code': int or None,
            'description': str,
            'found': bool
        }
    """
    crs_info = {
        'name': '',
        'epsg_code': None,
        'description': '',
        'found': False
    }
    
    # Try to find CoordinateSystem element
    # Can be at /LandXML/CoordinateSystem or /LandXML/Units/CoordinateSystem
    for coord_sys in root.findall('.//{http://www.landxml.org/schema/LandXML-1.2}CoordinateSystem'):
        crs_info['found'] = True
        
        # Extract name
        name = coord_sys.get('name') or coord_sys.get('desc')
        if name:
            crs_info['name'] = name
        
        # Try to extract EPSG code from name or description
        # Common formats: "EPSG:26910", "NAD83 / UTM zone 10N", etc.
        import re
        
        # Try name first
        if name and 'epsg' in name.lower():
            try:
                match = re.search(r'epsg[:\s]*([0-9]+)', name.lower())
                if match:
                    crs_info['epsg_code'] = int(match.group(1))
            except:
                pass
        
        # Get description and check for EPSG code
        desc = coord_sys.get('desc')
        if desc:
            crs_info['description'] = desc
            # Check if desc contains EPSG code
            if 'epsg' in desc.lower() and not crs_info['epsg_code']:
                try:
                    match = re.search(r'epsg[:\s]*([0-9]+)', desc.lower())
                    if match:
                        crs_info['epsg_code'] = int(match.group(1))
                except:
                    pass
        
        break  # Use first CoordinateSystem found
    
    # If no CoordinateSystem, check for epsgCode attribute on Project
    if not crs_info['found']:
        project = root.find('.//{http://www.landxml.org/schema/LandXML-1.2}Project')
        if project is not None:
            epsg = project.get('epsgCode')
            if epsg:
                try:
                    crs_info['epsg_code'] = int(epsg)
                    crs_info['found'] = True
                    crs_info['name'] = f'EPSG:{epsg}'
                except:
                    pass
    
    return crs_info


# ============================================================================
# COORDINATE EXTRACTION
# ============================================================================

def parse_pntlist3d(pntlist_text: str) -> List[Vector]:
    """
    Parse PntList3D text content into list of Vector coordinates.
    
    LandXML PntList3D format: "x1 y1 z1 x2 y2 z2 x3 y3 z3..."
    Space or newline separated coordinates.
    
    Args:
        pntlist_text: Raw text from PntList3D element
        
    Returns:
        List of Vector(x, y, z) in map coordinates
    """
    coords = []
    
    # Split by whitespace and convert to floats
    values = pntlist_text.split()
    
    # Group into triplets (x, y, z)
    for i in range(0, len(values), 3):
        if i + 2 < len(values):
            try:
                x = float(values[i])
                y = float(values[i + 1])
                z = float(values[i + 2])
                coords.append(Vector((x, y, z)))
            except ValueError:
                continue  # Skip invalid coordinates
    
    return coords


def calculate_bounding_box(coords: List[Vector]) -> Tuple[Vector, Vector]:
    """
    Calculate bounding box for a list of coordinates.
    
    Args:
        coords: List of Vector coordinates
        
    Returns:
        Tuple of (min_point, max_point) as Vectors
    """
    if not coords:
        return (Vector((0, 0, 0)), Vector((0, 0, 0)))
    
    min_x = min(c.x for c in coords)
    min_y = min(c.y for c in coords)
    min_z = min(c.z for c in coords)
    
    max_x = max(c.x for c in coords)
    max_y = max(c.y for c in coords)
    max_z = max(c.z for c in coords)
    
    return (Vector((min_x, min_y, min_z)), Vector((max_x, max_y, max_z)))


# ============================================================================
# ALIGNMENT EXTRACTION
# ============================================================================

def extract_alignments(root: ET.Element) -> List[Dict]:
    """
    Extract alignment data from LandXML.
    
    Alignments can contain:
    - Horizontal geometry (lines, curves, spirals)
    - Vertical geometry (grades)
    - Station equations
    
    Args:
        root: XML root element
        
    Returns:
        List of alignment dictionaries with structure:
        {
            'name': str,
            'length': float,
            'start_station': float,
            'end_station': float,
            'horizontal': List[Dict],  # Geometric elements
            'coordinates': List[Vector],  # 3D points
            'pis': List[Vector]  # PI points if available
        }
    """
    alignments = []
    
    # Find all Alignment elements
    for alignment in root.findall('.//{http://www.landxml.org/schema/LandXML-1.2}Alignment'):
        align_data = {
            'name': alignment.get('name', 'Unnamed'),
            'length': 0.0,
            'start_station': 0.0,
            'end_station': 0.0,
            'horizontal': [],
            'coordinates': [],
            'pis': []
        }
        
        # Extract length and station range
        length = alignment.get('length')
        if length:
            align_data['length'] = float(length)
        
        start_sta = alignment.get('staStart')
        if start_sta:
            align_data['start_station'] = float(start_sta)
        
        # Get horizontal geometry (CoordGeom)
        coord_geom = alignment.find('.//{http://www.landxml.org/schema/LandXML-1.2}CoordGeom')
        if coord_geom is not None:
            align_data['horizontal'] = extract_coord_geom(coord_geom)
        
        # Try to get coordinates from PntList3D if available
        for pntlist in alignment.findall('.//{http://www.landxml.org/schema/LandXML-1.2}PntList3D'):
            text = pntlist.text
            if text:
                coords = parse_pntlist3d(text)
                align_data['coordinates'].extend(coords)
        
        # Calculate end station if not provided
        if align_data['end_station'] == 0.0 and align_data['length'] > 0:
            align_data['end_station'] = align_data['start_station'] + align_data['length']
        
        alignments.append(align_data)
    
    return alignments


def extract_coord_geom(coord_geom: ET.Element) -> List[Dict]:
    """
    Extract coordinate geometry elements (lines, curves, spirals).
    
    Args:
        coord_geom: CoordGeom XML element
        
    Returns:
        List of geometry dictionaries with type-specific data
    """
    elements = []
    
    # Process each child element
    for elem in coord_geom:
        elem_type = elem.tag.split('}')[-1]  # Remove namespace
        
        if elem_type == 'Line':
            elements.append(extract_line(elem))
        elif elem_type == 'Curve':
            elements.append(extract_curve(elem))
        elif elem_type == 'Spiral':
            elements.append(extract_spiral(elem))
        elif elem_type == 'IrregularLine':
            elements.append(extract_irregular_line(elem))
    
    return elements


def extract_line(line: ET.Element) -> Dict:
    """Extract line segment data."""
    start = line.find('{http://www.landxml.org/schema/LandXML-1.2}Start')
    end = line.find('{http://www.landxml.org/schema/LandXML-1.2}End')
    
    line_data = {
        'type': 'Line',
        'start': None,
        'end': None,
        'length': 0.0
    }
    
    if start is not None:
        line_data['start'] = Vector((
            float(start.get('east', 0)),
            float(start.get('north', 0)),
            float(start.get('elev', 0))
        ))
    
    if end is not None:
        line_data['end'] = Vector((
            float(end.get('east', 0)),
            float(end.get('north', 0)),
            float(end.get('elev', 0))
        ))
    
    # Calculate length
    if line_data['start'] and line_data['end']:
        line_data['length'] = (line_data['end'] - line_data['start']).length
    
    return line_data


def extract_curve(curve: ET.Element) -> Dict:
    """Extract curve data."""
    curve_data = {
        'type': 'Curve',
        'radius': 0.0,
        'length': 0.0,
        'delta': 0.0,
        'rot': 'cw',
        'center': None,
        'start': None,
        'end': None
    }
    
    # Get curve parameters
    radius = curve.get('radius')
    if radius:
        curve_data['radius'] = float(radius)
    
    length = curve.get('length')
    if length:
        curve_data['length'] = float(length)
    
    # Get rotation (clockwise or counterclockwise)
    rot = curve.get('rot')
    if rot:
        curve_data['rot'] = rot
    
    # Get start and end points
    start = curve.find('{http://www.landxml.org/schema/LandXML-1.2}Start')
    if start is not None:
        curve_data['start'] = Vector((
            float(start.get('east', 0)),
            float(start.get('north', 0)),
            float(start.get('elev', 0))
        ))
    
    end = curve.find('{http://www.landxml.org/schema/LandXML-1.2}End')
    if end is not None:
        curve_data['end'] = Vector((
            float(end.get('east', 0)),
            float(end.get('north', 0)),
            float(end.get('elev', 0))
        ))
    
    # Get center point if available
    center = curve.find('{http://www.landxml.org/schema/LandXML-1.2}Center')
    if center is not None:
        curve_data['center'] = Vector((
            float(center.get('east', 0)),
            float(center.get('north', 0)),
            float(center.get('elev', 0))
        ))
    
    # Calculate delta angle if not provided
    if curve_data['radius'] > 0 and curve_data['length'] > 0:
        curve_data['delta'] = curve_data['length'] / curve_data['radius']
    
    return curve_data


def extract_spiral(spiral: ET.Element) -> Dict:
    """Extract spiral (transition curve) data."""
    spiral_data = {
        'type': 'Spiral',
        'length': 0.0,
        'radius_start': 0.0,
        'radius_end': 0.0,
        'rot': 'cw',
        'start': None,
        'end': None
    }
    
    # Get spiral parameters
    length = spiral.get('length')
    if length:
        spiral_data['length'] = float(length)
    
    rad_start = spiral.get('radiusStart')
    if rad_start:
        spiral_data['radius_start'] = float(rad_start)
    
    rad_end = spiral.get('radiusEnd')
    if rad_end:
        spiral_data['radius_end'] = float(rad_end)
    
    rot = spiral.get('rot')
    if rot:
        spiral_data['rot'] = rot
    
    # Get start and end points
    start = spiral.find('{http://www.landxml.org/schema/LandXML-1.2}Start')
    if start is not None:
        spiral_data['start'] = Vector((
            float(start.get('east', 0)),
            float(start.get('north', 0)),
            float(start.get('elev', 0))
        ))
    
    end = spiral.find('{http://www.landxml.org/schema/LandXML-1.2}End')
    if end is not None:
        spiral_data['end'] = Vector((
            float(end.get('east', 0)),
            float(end.get('north', 0)),
            float(end.get('elev', 0))
        ))
    
    return spiral_data


def extract_irregular_line(irreg_line: ET.Element) -> Dict:
    """Extract irregular line (polyline) data."""
    irreg_data = {
        'type': 'IrregularLine',
        'coordinates': []
    }
    
    # Get PntList3D
    pntlist = irreg_line.find('.//{http://www.landxml.org/schema/LandXML-1.2}PntList3D')
    if pntlist is not None and pntlist.text:
        irreg_data['coordinates'] = parse_pntlist3d(pntlist.text)
    
    return irreg_data


# ============================================================================
# SURFACE EXTRACTION (Future)
# ============================================================================

def extract_surfaces(root: ET.Element) -> List[Dict]:
    """
    Extract surface data from LandXML.
    
    Surfaces can be:
    - TIN (Triangulated Irregular Network)
    - Grid
    - Breaklines
    
    Args:
        root: XML root element
        
    Returns:
        List of surface dictionaries (TODO: Implementation)
    """
    # TODO: Implement surface extraction for Sprint 5+
    return []


# ============================================================================
# MAIN PARSER FUNCTION
# ============================================================================

def parse_landxml_file(filepath: str) -> Dict:
    """
    Parse a LandXML file and extract all relevant data.
    
    Args:
        filepath: Path to LandXML file
        
    Returns:
        Dictionary with parsed data:
        {
            'crs': Dict,  # CRS information
            'alignments': List[Dict],  # Alignment data
            'surfaces': List[Dict],  # Surface data (future)
            'bbox_min': Vector,  # Bounding box minimum
            'bbox_max': Vector,  # Bounding box maximum
            'all_coordinates': List[Vector],  # All coordinates for false origin calc
            'units': str,  # Linear units
            'success': bool,
            'error': str or None
        }
    """
    result = {
        'crs': {},
        'alignments': [],
        'surfaces': [],
        'bbox_min': Vector((0, 0, 0)),
        'bbox_max': Vector((0, 0, 0)),
        'all_coordinates': [],
        'units': 'meter',
        'success': False,
        'error': None
    }
    
    try:
        # Parse XML file
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        # Validate it's a LandXML file
        if 'LandXML' not in root.tag:
            result['error'] = "Not a valid LandXML file"
            return result
        
        # Extract units
        units_elem = root.find('.//{http://www.landxml.org/schema/LandXML-1.2}Units')
        if units_elem is not None:
            linear_unit = units_elem.get('linearUnit')
            if linear_unit:
                result['units'] = linear_unit.lower()
        
        # Extract CRS
        result['crs'] = extract_crs_info(root)
        
        # Extract alignments
        result['alignments'] = extract_alignments(root)
        
        # Collect all coordinates for bounding box
        for alignment in result['alignments']:
            result['all_coordinates'].extend(alignment['coordinates'])
            for elem in alignment['horizontal']:
                if elem.get('start'):
                    result['all_coordinates'].append(elem['start'])
                if elem.get('end'):
                    result['all_coordinates'].append(elem['end'])
        
        # Calculate bounding box
        if result['all_coordinates']:
            result['bbox_min'], result['bbox_max'] = calculate_bounding_box(
                result['all_coordinates']
            )
        
        result['success'] = True
        
    except ET.ParseError as e:
        result['error'] = f"XML parse error: {str(e)}"
    except Exception as e:
        result['error'] = f"Error parsing LandXML: {str(e)}"
    
    return result


# ============================================================================
# EXPORT FUNCTIONS (TO BE IMPLEMENTED)
# ============================================================================

# ============================================================================
# EXPORT FUNCTIONS
# ============================================================================

def generate_landxml(alignments_data: List[Dict], georef_data: Dict, filepath: str) -> bool:
    """
    Generate LandXML file from BlenderCivil alignment data.
    
    Args:
        alignments_data: List of alignment dictionaries with:
            {
                'name': str,
                'length': float,
                'start_station': float,
                'end_station': float,
                'coordinates': List[Vector],  # Local coordinates
            }
        georef_data: Georeferencing dictionary with:
            {
                'crs_name': str,
                'epsg_code': int,
                'false_easting': float,
                'false_northing': float,
                'false_elevation': float,
                'scale_factor': float,
                'rotation_angle': float,
            }
        filepath: Output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from datetime import datetime
        
        # Create root element
        NS = "{http://www.landxml.org/schema/LandXML-1.2}"
        ET.register_namespace('', 'http://www.landxml.org/schema/LandXML-1.2')
        
        root = ET.Element('LandXML')
        root.set('xmlns', 'http://www.landxml.org/schema/LandXML-1.2')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:schemaLocation', 
                 'http://www.landxml.org/schema/LandXML-1.2 '
                 'http://www.landxml.org/schema/LandXML-1.2/LandXML-1.2.xsd')
        root.set('version', '1.2')
        root.set('date', datetime.now().strftime('%Y-%m-%d'))
        root.set('time', datetime.now().strftime('%H:%M:%S'))
        
        # Add Units
        units = ET.SubElement(root, 'Units')
        metric = ET.SubElement(units, 'Metric')
        metric.set('linearUnit', 'meter')
        metric.set('areaUnit', 'squareMeter')
        metric.set('volumeUnit', 'cubicMeter')
        
        # Add CoordinateSystem
        if georef_data.get('crs_name'):
            coord_sys = ET.SubElement(root, 'CoordinateSystem')
            coord_sys.set('name', georef_data['crs_name'])
            if georef_data.get('epsg_code'):
                coord_sys.set('desc', f"EPSG:{georef_data['epsg_code']}")
        
        # Add Project
        project = ET.SubElement(root, 'Project')
        project.set('name', 'BlenderCivil Export')
        
        # Add Alignments
        if alignments_data:
            alignments_elem = ET.SubElement(root, 'Alignments')
            
            for align_data in alignments_data:
                create_alignment_xml(alignments_elem, align_data, georef_data, NS)
        
        # Write to file with pretty formatting
        tree = ET.ElementTree(root)
        ET.indent(tree, space='  ')
        tree.write(filepath, encoding='utf-8', xml_declaration=True)
        
        return True
        
    except Exception as e:
        print(f"Error generating LandXML: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_alignment_xml(parent: ET.Element, align_data: Dict, georef_data: Dict, NS: str):
    """
    Create an Alignment XML element with geometry.
    
    Args:
        parent: Parent XML element (Alignments)
        align_data: Alignment data dictionary
        georef_data: Georeferencing data
        NS: Namespace string
    """
    alignment = ET.SubElement(parent, 'Alignment')
    alignment.set('name', align_data['name'])
    alignment.set('length', f"{align_data['length']:.6f}")
    alignment.set('staStart', f"{align_data['start_station']:.6f}")
    
    # Create CoordGeom
    coord_geom = ET.SubElement(alignment, 'CoordGeom')
    
    # If we have coordinates, create an irregular line (polyline)
    if align_data.get('coordinates'):
        coords = align_data['coordinates']
        
        if len(coords) >= 2:
            # Transform coordinates from local to map
            from core.georeferencing import GeoreferencingUtils
            import bpy
            
            # Build georef object for transformation
            class GeorefProxy:
                def __init__(self, data):
                    self.false_easting = data['false_easting']
                    self.false_northing = data['false_northing']
                    self.false_elevation = data['false_elevation']
                    self.scale_factor = data['scale_factor']
                    self.rotation_angle = data['rotation_angle']
                    self.x_axis_abscissa = math.cos(data['rotation_angle'])
                    self.x_axis_ordinate = math.sin(data['rotation_angle'])
                
                def get_false_origin_vector(self):
                    return Vector((self.false_easting, self.false_northing, self.false_elevation))
                
                def get_rotation_matrix(self):
                    import mathutils
                    angle = self.rotation_angle
                    rot_matrix = mathutils.Matrix.Rotation(angle, 3, 'Z')
                    return rot_matrix
            
            georef_proxy = GeorefProxy(georef_data)
            
            # Transform all coordinates
            map_coords = [GeoreferencingUtils.local_to_map(c, georef_proxy) for c in coords]
            
            # Create as series of Line segments or IrregularLine
            if len(coords) <= 3:
                # Use individual Line elements for short sequences
                for i in range(len(map_coords) - 1):
                    create_line_xml(coord_geom, map_coords[i], map_coords[i+1], NS)
            else:
                # Use IrregularLine for longer sequences
                create_irregular_line_xml(coord_geom, map_coords, NS)


def create_line_xml(parent: ET.Element, start: Vector, end: Vector, NS: str):
    """Create a Line element."""
    line = ET.SubElement(parent, 'Line')
    
    start_elem = ET.SubElement(line, 'Start')
    start_elem.set('east', f"{start.x:.6f}")
    start_elem.set('north', f"{start.y:.6f}")
    start_elem.set('elev', f"{start.z:.6f}")
    
    end_elem = ET.SubElement(line, 'End')
    end_elem.set('east', f"{end.x:.6f}")
    end_elem.set('north', f"{end.y:.6f}")
    end_elem.set('elev', f"{end.z:.6f}")


def create_irregular_line_xml(parent: ET.Element, coords: List[Vector], NS: str):
    """Create an IrregularLine element (polyline)."""
    irreg_line = ET.SubElement(parent, 'IrregularLine')
    
    # Create PntList3D
    pntlist = ET.SubElement(irreg_line, 'PntList3D')
    
    # Format coordinates as space-separated triplets
    coord_text = []
    for coord in coords:
        coord_text.append(f"{coord.x:.6f} {coord.y:.6f} {coord.z:.6f}")
    
    pntlist.text = '\n        '.join(coord_text)


def create_curve_xml(parent: ET.Element, curve_data: Dict, NS: str):
    """Create a Curve element."""
    curve = ET.SubElement(parent, 'Curve')
    curve.set('radius', f"{curve_data['radius']:.6f}")
    curve.set('length', f"{curve_data['length']:.6f}")
    curve.set('rot', curve_data.get('rot', 'cw'))
    
    if curve_data.get('start'):
        start_elem = ET.SubElement(curve, 'Start')
        start_elem.set('east', f"{curve_data['start'].x:.6f}")
        start_elem.set('north', f"{curve_data['start'].y:.6f}")
        start_elem.set('elev', f"{curve_data['start'].z:.6f}")
    
    if curve_data.get('end'):
        end_elem = ET.SubElement(curve, 'End')
        end_elem.set('east', f"{curve_data['end'].x:.6f}")
        end_elem.set('north', f"{curve_data['end'].y:.6f}")
        end_elem.set('elev', f"{curve_data['end'].z:.6f}")
    
    if curve_data.get('center'):
        center_elem = ET.SubElement(curve, 'Center')
        center_elem.set('east', f"{curve_data['center'].x:.6f}")
        center_elem.set('north', f"{curve_data['center'].y:.6f}")
        center_elem.set('elev', f"{curve_data['center'].z:.6f}")

