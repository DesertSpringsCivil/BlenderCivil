"""
BlenderCivil - CRS Searcher Module
Provides coordinate reference system search and metadata retrieval.

Uses EPSG.io API as primary source, with PyProj fallback for offline/validation.
"""

import requests
from typing import Dict, List, Optional, Tuple
import logging

try:
    import pyproj
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    logging.warning("PyProj not available - CRS validation will be limited")


class CRSInfo:
    """Container for CRS metadata"""
    
    def __init__(
        self,
        epsg_code: int,
        name: str,
        kind: str,
        area: str = "",
        bbox: Optional[Tuple[float, float, float, float]] = None,
        unit: str = "metre",
        proj4: str = "",
        wkt: str = ""
    ):
        self.epsg_code = epsg_code
        self.name = name
        self.kind = kind  # "CRS-PROJCRS", "CRS-GEOGCRS", etc.
        self.area = area
        self.bbox = bbox  # (west, south, east, north)
        self.unit = unit
        self.proj4 = proj4
        self.wkt = wkt
    
    def __repr__(self):
        return f"CRSInfo(EPSG:{self.epsg_code}, {self.name}, {self.kind})"
    
    def is_projected(self) -> bool:
        """Check if this is a projected CRS (vs geographic)"""
        return "PROJCRS" in self.kind
    
    def is_geographic(self) -> bool:
        """Check if this is a geographic CRS"""
        return "GEOGCRS" in self.kind
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for IFC storage"""
        return {
            'epsg_code': self.epsg_code,
            'name': self.name,
            'kind': self.kind,
            'area': self.area,
            'bbox': self.bbox,
            'unit': self.unit,
            'proj4': self.proj4,
            'wkt': self.wkt
        }


class CRSSearcher:
    """
    Search and retrieve coordinate reference system information.
    
    Primary source: EPSG.io API
    Fallback: PyProj library (if available)
    
    Examples:
        >>> searcher = CRSSearcher()
        >>> results = searcher.search("UTM Zone 10")
        >>> crs = searcher.get_crs(26910)  # NAD83 / UTM zone 10N
    """
    
    EPSG_IO_BASE = "https://epsg.io/"
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def search(
        self,
        query: str,
        kind: Optional[str] = None,
        limit: int = 20
    ) -> List[CRSInfo]:
        """
        Search for coordinate reference systems by name or identifier.
        
        Args:
            query: Search term (e.g., "UTM Zone 10", "NAD83", "26910")
            kind: Filter by CRS kind (e.g., "PROJCRS", "GEOGCRS")
            limit: Maximum number of results to return
        
        Returns:
            List of CRSInfo objects matching the search
        """
        self.logger.info(f"Searching for CRS: {query}")
        
        # Try EPSG.io API first
        results = self._search_epsg_io(query, kind, limit)
        
        if not results and PYPROJ_AVAILABLE:
            # Fallback to PyProj
            self.logger.info("Falling back to PyProj database")
            results = self._search_pyproj(query, kind, limit)
        
        return results
    
    def get_crs(self, epsg_code: int) -> Optional[CRSInfo]:
        """
        Get detailed information about a specific EPSG code.
        
        Args:
            epsg_code: EPSG code (e.g., 26910 for NAD83 / UTM zone 10N)
        
        Returns:
            CRSInfo object with full metadata, or None if not found
        """
        self.logger.info(f"Fetching CRS details for EPSG:{epsg_code}")
        
        # Try EPSG.io API first
        crs_info = self._get_from_epsg_io(epsg_code)
        
        if not crs_info and PYPROJ_AVAILABLE:
            # Fallback to PyProj
            self.logger.info("Falling back to PyProj database")
            crs_info = self._get_from_pyproj(epsg_code)
        
        return crs_info
    
    def validate_epsg(self, epsg_code: int) -> bool:
        """
        Validate that an EPSG code exists and is valid.
        
        Args:
            epsg_code: EPSG code to validate
        
        Returns:
            True if valid, False otherwise
        """
        crs_info = self.get_crs(epsg_code)
        return crs_info is not None
    
    def _search_epsg_io(
        self,
        query: str,
        kind: Optional[str],
        limit: int
    ) -> List[CRSInfo]:
        """Search using EPSG.io API"""
        try:
            # Build query parameters
            params = {
                'q': query,
                'format': 'json'
            }
            
            # Make request
            url = f"{self.EPSG_IO_BASE}?{self._build_query_string(params)}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            # Parse results
            if 'results' in data:
                for item in data['results'][:limit]:
                    # Filter by kind if specified
                    if kind and item.get('kind', '').upper() != kind.upper():
                        continue
                    
                    crs_info = self._parse_epsg_io_result(item)
                    if crs_info:
                        results.append(crs_info)
            
            self.logger.info(f"Found {len(results)} results from EPSG.io")
            return results
            
        except requests.RequestException as e:
            self.logger.warning(f"EPSG.io API error: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Unexpected error in EPSG.io search: {e}")
            return []
    
    def _get_from_epsg_io(self, epsg_code: int) -> Optional[CRSInfo]:
        """Get CRS details from EPSG.io API"""
        try:
            # Request JSON format with full details
            url = f"{self.EPSG_IO_BASE}{epsg_code}.json"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_epsg_io_result(data)
            
        except requests.RequestException as e:
            self.logger.warning(f"EPSG.io API error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error fetching EPSG:{epsg_code}: {e}")
            return None
    
    def _parse_epsg_io_result(self, data: Dict) -> Optional[CRSInfo]:
        """Parse EPSG.io API response into CRSInfo"""
        try:
            # Extract bbox if available
            bbox = None
            if 'bbox' in data:
                b = data['bbox']
                bbox = (b[0], b[1], b[2], b[3])  # west, south, east, north
            
            return CRSInfo(
                epsg_code=int(data.get('code', 0)),
                name=data.get('name', ''),
                kind=data.get('kind', ''),
                area=data.get('area', ''),
                bbox=bbox,
                unit=data.get('unit', 'metre'),
                proj4=data.get('proj4', ''),
                wkt=data.get('wkt', '')
            )
        except (KeyError, ValueError) as e:
            self.logger.warning(f"Failed to parse EPSG.io result: {e}")
            return None
    
    def _search_pyproj(
        self,
        query: str,
        kind: Optional[str],
        limit: int
    ) -> List[CRSInfo]:
        """Search using PyProj database (fallback)"""
        if not PYPROJ_AVAILABLE:
            return []
        
        try:
            results = []
            query_upper = query.upper()
            
            # Search through PyProj CRS database
            # Note: This is a simplified search - PyProj doesn't have a built-in search function
            for crs_auth in ['EPSG', 'ESRI']:
                try:
                    # Try direct code lookup if query is numeric
                    if query.isdigit():
                        crs = pyproj.CRS.from_epsg(int(query))
                        info = self._pyproj_to_crs_info(crs)
                        if info:
                            results.append(info)
                            break
                except Exception:
                    pass
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"PyProj search error: {e}")
            return []
    
    def _get_from_pyproj(self, epsg_code: int) -> Optional[CRSInfo]:
        """Get CRS details from PyProj (fallback)"""
        if not PYPROJ_AVAILABLE:
            return None
        
        try:
            crs = pyproj.CRS.from_epsg(epsg_code)
            return self._pyproj_to_crs_info(crs)
        except Exception as e:
            self.logger.warning(f"PyProj lookup error for EPSG:{epsg_code}: {e}")
            return None
    
    def _pyproj_to_crs_info(self, crs: 'pyproj.CRS') -> Optional[CRSInfo]:
        """Convert PyProj CRS to CRSInfo"""
        try:
            # Determine kind
            kind = "CRS-PROJCRS" if crs.is_projected else "CRS-GEOGCRS"
            
            # Get bbox if available
            bbox = None
            if crs.area_of_use:
                bbox = (
                    crs.area_of_use.west,
                    crs.area_of_use.south,
                    crs.area_of_use.east,
                    crs.area_of_use.north
                )
            
            # Get unit
            unit = "metre"
            if crs.axis_info:
                unit = crs.axis_info[0].unit_name or "metre"
            
            return CRSInfo(
                epsg_code=int(crs.to_epsg() or 0),
                name=crs.name or "",
                kind=kind,
                area=crs.area_of_use.name if crs.area_of_use else "",
                bbox=bbox,
                unit=unit,
                proj4=crs.to_proj4() or "",
                wkt=crs.to_wkt() or ""
            )
        except Exception as e:
            self.logger.warning(f"Failed to convert PyProj CRS: {e}")
            return None
    
    @staticmethod
    def _build_query_string(params: Dict) -> str:
        """Build URL query string from parameters"""
        return '&'.join(f"{k}={v}" for k, v in params.items())


# Common CRS presets for quick access
COMMON_CRS = {
    'WGS84': 4326,
    'WGS84_UTM_10N': 32610,
    'NAD83': 4269,
    'NAD83_UTM_10N': 26910,
    'NAD83_CA_ZONE_3': 2227,  # California State Plane Zone 3
    'ETRS89_UTM_32N': 25832,
    'OSGB36': 27700,  # British National Grid
}


def get_common_crs(name: str) -> Optional[int]:
    """
    Get EPSG code for commonly used CRS by name.
    
    Args:
        name: Common name (e.g., 'WGS84', 'NAD83_UTM_10N')
    
    Returns:
        EPSG code or None if not found
    """
    return COMMON_CRS.get(name.upper())


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    searcher = CRSSearcher()
    
    # Search for UTM Zone 10
    print("\n=== Searching for 'UTM Zone 10' ===")
    results = searcher.search("UTM Zone 10")
    for crs in results[:5]:
        print(f"  {crs}")
    
    # Get specific CRS details
    print("\n=== Getting details for EPSG:26910 ===")
    crs = searcher.get_crs(26910)
    if crs:
        print(f"  Name: {crs.name}")
        print(f"  Kind: {crs.kind}")
        print(f"  Area: {crs.area}")
        print(f"  Unit: {crs.unit}")
        print(f"  Projected: {crs.is_projected()}")
    
    # Validate EPSG code
    print("\n=== Validating EPSG codes ===")
    print(f"  EPSG:26910 valid: {searcher.validate_epsg(26910)}")
    print(f"  EPSG:99999 valid: {searcher.validate_epsg(99999)}")
