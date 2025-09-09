"""
GARUDA KML Processor Module
"""

import os
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
import logging

class GarudaKMLProcessor:
    """
    Processes KML files to extract strategic asset information
    """
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('🦅 GARUDA-KML [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
    def load_kml_file(self, kml_path):
        """Load and process a KML file"""
        try:
            self.logger.info(f"Loading KML file: {kml_path}")
            
            tree = ET.parse(kml_path)
            root = tree.getroot()
            
            # Handle namespace
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            assets = []
            
            # Find all Placemark elements
            for placemark in root.findall('.//kml:Placemark', namespace):
                asset = self._process_placemark(placemark, namespace)
                if asset:
                    assets.append(asset)
                    
            self.logger.info(f"Successfully processed {len(assets)} assets from {kml_path}")
            return assets
            
        except Exception as e:
            self.logger.error(f"Error loading KML file {kml_path}: {e}")
            return []
    
    def _process_placemark(self, placemark, namespace):
        """Process a single KML Placemark"""
        try:
            # Extract name
            name_elem = placemark.find('kml:name', namespace)
            name = name_elem.text if name_elem is not None else "Unnamed Asset"
            
            # Extract description
            desc_elem = placemark.find('kml:description', namespace)
            description = desc_elem.text if desc_elem is not None else ""
            
            # Extract coordinates from Polygon
            polygon_elem = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', namespace)
            
            if polygon_elem is not None:
                coords_text = polygon_elem.text.strip()
                polygon = self._parse_coordinates(coords_text)
                
                if polygon:
                    asset_type = self._classify_asset_type(name, description)
                    priority = self._assess_priority(asset_type, name, description)
                    
                    return {
                        'name': name,
                        'type': asset_type,
                        'priority': priority,
                        'polygon': polygon,
                        'description': description
                    }
                    
        except Exception as e:
            self.logger.error(f"Error processing placemark: {e}")
            
        return None
    
    def _parse_coordinates(self, coords_text):
        """Parse KML coordinate string into Shapely Polygon"""
        try:
            coord_pairs = coords_text.replace('\n', ' ').replace('\t', ' ').split()
            coordinates = []
            
            for coord_pair in coord_pairs:
                if coord_pair.strip():
                    parts = coord_pair.split(',')
                    if len(parts) >= 2:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        coordinates.append((lon, lat))
            
            if len(coordinates) >= 3:
                if coordinates[0] != coordinates[-1]:
                    coordinates.append(coordinates[0])
                    
                return Polygon(coordinates)
                
        except Exception as e:
            self.logger.error(f"Error parsing coordinates: {e}")
            
        return None
    
    def _classify_asset_type(self, name, description):
        """Classify asset type based on name and description"""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        classifications = {
            'Bridge': ['bridge', 'overpass', 'flyover', 'viaduct'],
            'Tunnel': ['tunnel', 'underpass', 'subway'],
            'Airport': ['airport', 'airfield', 'aerodrome', 'runway'],
            'Railway Infrastructure': ['railway', 'train', 'metro', 'station', 'rail'],
            'Port Infrastructure': ['port', 'harbor', 'harbour', 'dock', 'terminal'],
            'Power Infrastructure': ['power', 'plant', 'substation', 'grid', 'nuclear', 'thermal'],
            'Military Facility': ['military', 'base', 'camp', 'barracks', 'installation'],
            'Border Infrastructure': ['border', 'checkpoint', 'crossing', 'fence'],
            'Communication Infrastructure': ['tower', 'antenna', 'satellite', 'communication'],
            'Critical Infrastructure': ['dam', 'reservoir', 'water', 'treatment', 'facility']
        }
        
        for asset_type, keywords in classifications.items():
            for keyword in keywords:
                if keyword in name_lower or keyword in desc_lower:
                    return asset_type
                    
        return 'Critical Infrastructure'
    
    def _assess_priority(self, asset_type, name, description):
        """Assess asset priority"""
        high_priority_types = [
            'Military Facility', 
            'Border Infrastructure', 
            'Power Infrastructure',
            'Airport'
        ]
        
        high_priority_keywords = [
            'international', 'major', 'main', 'primary', 'strategic',
            'nuclear', 'military', 'defense', 'national', 'critical'
        ]
        
        name_desc = (name + ' ' + description).lower()
        
        if asset_type in high_priority_types:
            return 'HIGH'
            
        if any(keyword in name_desc for keyword in high_priority_keywords):
            return 'HIGH'
            
        medium_priority_keywords = [
            'regional', 'state', 'provincial', 'secondary', 'important'
        ]
        
        if any(keyword in name_desc for keyword in medium_priority_keywords):
            return 'MEDIUM'
            
        return 'LOW'
    
    def load_kml_file_with_real_classification(self, kml_path):
        """Load KML with real intelligence classification"""
        try:
            # Import the real classifier
            from garuda_real_classifier import GarudaRealClassifier
            classifier = GarudaRealClassifier()
            
            self.logger.info(f"Loading KML with REAL classification: {kml_path}")
            
            # Your existing KML parsing code...
            tree = ET.parse(kml_path)
            root = tree.getroot()
            namespace = {'kml': 'http://www.opengis.net/kml/2.2'}
            
            assets = []
            
            for placemark in root.findall('.//kml:Placemark', namespace):
                asset = self._process_placemark_real(placemark, namespace, classifier)
                if asset:
                    assets.append(asset)
                    
            self.logger.info(f"REAL classification complete: {len(assets)} assets processed")
            return assets
            
        except Exception as e:
            self.logger.error(f"Real classification failed, falling back to basic: {e}")
            return self.load_kml_file(kml_path)  # Fallback to your existing method

    def _process_placemark_real(self, placemark, namespace, classifier):
        """Process placemark with real classification"""
        try:
            # Extract basic info (your existing code)
            name_elem = placemark.find('kml:name', namespace)
            name = name_elem.text if name_elem is not None else "Unnamed Asset"
            
            desc_elem = placemark.find('kml:description', namespace)
            description = desc_elem.text if desc_elem is not None else ""
            
            # Extract coordinates
            polygon_elem = placemark.find('.//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates', namespace)
            
            if polygon_elem is not None:
                coords_text = polygon_elem.text.strip()
                polygon = self._parse_coordinates(coords_text)
                
                if polygon:
                    # Basic type classification (your existing logic)
                    basic_asset_type = self._classify_asset_type(name, description)
                    
                    # Extract OSM tags if available in description
                    osm_tags = self._extract_osm_tags(description)
                    
                    # REAL CLASSIFICATION HERE
                    real_classification = classifier.classify_asset_real(
                        name, basic_asset_type, polygon, osm_tags
                    )
                    
                    return {
                        'name': name,
                        'type': basic_asset_type,
                        'priority': real_classification['priority'],  # REAL priority
                        'threat_level': real_classification['threat_level'],  # REAL threat
                        'polygon': polygon,
                        'description': description,
                        'classification_details': real_classification,  # Full analysis
                        'real_classified': True
                    }
                    
        except Exception as e:
            self.logger.error(f"Real classification failed for placemark: {e}")
            
        return None

    def _extract_osm_tags(self, description):
        """Extract OSM tags from description if available"""
        tags = {}
        if 'OSM' in description or 'highway' in description.lower():
            # Simple extraction - you can enhance this
            if 'highway' in description.lower():
                tags['highway'] = 'primary'  # Default assumption
        return tags



if __name__ == "__main__":
    processor = GarudaKMLProcessor()
    print("🦅 GARUDA KML Processor - Ready for Asset Processing")
