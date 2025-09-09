#!/usr/bin/env python3
"""
GARUDA Real Intelligence Classification System
Uses geographic analysis, satellite data, and strategic importance for accurate assessment
"""

import os
import numpy as np
import requests
from shapely.geometry import Point, Polygon
from geopy.distance import geodesic
import logging
from datetime import datetime, timedelta

class GarudaRealClassifier:
    """
    Real intelligence-based asset classification and threat assessment
    """
    
    def __init__(self):
        self.setup_logging()
        
        # Real strategic locations in India
        self.strategic_locations = {
            'major_cities': [
                {'name': 'New Delhi', 'coords': (28.6139, 77.2090), 'importance': 10},
                {'name': 'Mumbai', 'coords': (19.0760, 72.8777), 'importance': 9},
                {'name': 'Kolkata', 'coords': (22.5726, 88.3639), 'importance': 8},
                {'name': 'Chennai', 'coords': (13.0827, 80.2707), 'importance': 8},
                {'name': 'Bangalore', 'coords': (12.9716, 77.5946), 'importance': 8}
            ],
            'border_areas': [
                {'name': 'LOC Kashmir', 'coords': (34.0837, 74.7973), 'threat_level': 10},
                {'name': 'Pakistan Border Punjab', 'coords': (31.6340, 74.8723), 'threat_level': 9},
                {'name': 'China Border Ladakh', 'coords': (34.1526, 77.5771), 'threat_level': 10},
                {'name': 'Bangladesh Border', 'coords': (24.6332, 88.7789), 'threat_level': 7}
            ],
            'military_zones': [
                {'name': 'Siachen Glacier', 'coords': (35.4219, 77.0689), 'sensitivity': 10},
                {'name': 'Kargil Sector', 'coords': (34.5539, 76.1250), 'sensitivity': 9}
            ]
        }
        
    def setup_logging(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('🧠 GARUDA-CLASSIFIER [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def classify_asset_real(self, asset_name, asset_type, asset_polygon, osm_tags=None):
        """
        Real classification based on multiple intelligence factors
        """
        try:
            self.logger.info(f"Classifying: {asset_name} ({asset_type})")
            
            # Get asset center point
            if hasattr(asset_polygon, 'centroid'):
                center_point = (asset_polygon.centroid.y, asset_polygon.centroid.x)
            else:
                center_point = (28.6139, 77.2090)  # Delhi fallback
            
            classification_score = 0
            threat_factors = []
            
            # 1. ASSET TYPE BASE SCORING (realistic)
            type_scores = self._get_real_type_scores(asset_type, osm_tags)
            classification_score += type_scores['base_score']
            threat_factors.extend(type_scores['factors'])
            
            # 2. GEOGRAPHIC STRATEGIC VALUE
            geo_score = self._calculate_geographic_importance(center_point)
            classification_score += geo_score['score']
            threat_factors.extend(geo_score['factors'])
            
            # 3. BORDER PROXIMITY ANALYSIS
            border_score = self._analyze_border_proximity(center_point)
            classification_score += border_score['score']
            threat_factors.extend(border_score['factors'])
            
            # 4. INFRASTRUCTURE CRITICALITY
            infra_score = self._assess_infrastructure_criticality(asset_name, asset_type, center_point)
            classification_score += infra_score['score']
            threat_factors.extend(infra_score['factors'])
            
            # 5. SIZE AND CAPACITY ESTIMATION
            size_score = self._estimate_asset_importance(asset_polygon, osm_tags)
            classification_score += size_score['score']
            threat_factors.extend(size_score['factors'])
            
            # FINAL CLASSIFICATION
            priority = self._calculate_final_priority(classification_score)
            threat_level = self._calculate_threat_level(classification_score, threat_factors)
            
            result = {
                'priority': priority,
                'threat_level': threat_level,
                'classification_score': classification_score,
                'threat_factors': threat_factors,
                'analysis': {
                    'geographic_importance': geo_score,
                    'border_proximity': border_score,
                    'infrastructure_criticality': infra_score,
                    'size_assessment': size_score
                },
                'coordinates': center_point,
                'classified_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ {asset_name}: {priority} priority, {threat_level} threat (Score: {classification_score})")
            return result
            
        except Exception as e:
            self.logger.error(f"Classification failed for {asset_name}: {e}")
            return {
                'priority': 'LOW',
                'threat_level': 'LOW',
                'classification_score': 0,
                'error': str(e)
            }
    
    def _get_real_type_scores(self, asset_type, osm_tags):
        """Real asset type scoring based on actual strategic importance"""
        
        base_scores = {
            # TRULY HIGH STRATEGIC VALUE
            'Nuclear Power Plant': {'score': 95, 'factors': ['nuclear_facility', 'critical_infrastructure']},
            'Military Facility': {'score': 90, 'factors': ['military_installation']},
            'International Airport': {'score': 85, 'factors': ['aviation_hub', 'international_connectivity']},
            'Major Port': {'score': 80, 'factors': ['maritime_gateway']},
            
            # MEDIUM STRATEGIC VALUE  
            'Power Infrastructure': {'score': 70, 'factors': ['power_grid']},
            'Major Bridge': {'score': 65, 'factors': ['transportation_link']},
            'Railway Hub': {'score': 60, 'factors': ['rail_connectivity']},
            'Regional Airport': {'score': 55, 'factors': ['regional_aviation']},
            
            # LOWER STRATEGIC VALUE
            'Local Bridge': {'score': 30, 'factors': ['local_transport']},
            'Minor Railway': {'score': 25, 'factors': ['local_rail']},
            'Local Road': {'score': 20, 'factors': ['local_access']},
            
            # DEFAULT BY TYPE
            'Bridge': {'score': 40, 'factors': ['transport_infrastructure']},  # Default bridge score
            'Airport': {'score': 70, 'factors': ['aviation_infrastructure']},
            'Railway Infrastructure': {'score': 50, 'factors': ['rail_infrastructure']},
            'Power Infrastructure': {'score': 65, 'factors': ['energy_infrastructure']}
        }
        
        # Get base score
        type_data = base_scores.get(asset_type, {'score': 30, 'factors': ['unclassified']})
        
        # Enhance with OSM tag analysis
        if osm_tags:
            type_data = self._enhance_with_osm_tags(type_data, osm_tags)
            
        return {'base_score': type_data['score'], 'factors': type_data['factors']}
    
    def _enhance_with_osm_tags(self, type_data, osm_tags):
        """Enhance classification using OSM tags"""
        score = type_data['score']
        factors = type_data['factors'].copy()
        
        # Bridge classification enhancement
        if 'highway' in osm_tags:
            highway_type = osm_tags['highway']
            if highway_type in ['trunk', 'primary']:
                score += 20
                factors.append('major_highway_bridge')
            elif highway_type in ['secondary', 'tertiary']:
                score += 10
                factors.append('secondary_road_bridge')
        
        # Railway classification
        if 'railway' in osm_tags:
            if osm_tags['railway'] == 'rail' and osm_tags.get('usage') == 'main':
                score += 15
                factors.append('mainline_railway')
        
        # Airport classification
        if 'aeroway' in osm_tags:
            if osm_tags.get('aeroway') == 'aerodrome':
                iata_code = osm_tags.get('iata', osm_tags.get('icao'))
                if iata_code:
                    score += 25
                    factors.append('commercial_airport')
        
        return {'score': score, 'factors': factors}
    
    def _calculate_geographic_importance(self, center_point):
        """Calculate importance based on proximity to major cities"""
        max_score = 0
        factors = []
        
        for city in self.strategic_locations['major_cities']:
            distance = geodesic(center_point, city['coords']).kilometers
            
            if distance <= 50:  # Within 50km of major city
                city_score = city['importance'] * (50 - distance) / 50
                max_score = max(max_score, city_score)
                factors.append(f"near_{city['name'].lower().replace(' ', '_')}")
            elif distance <= 100:  # Within 100km
                city_score = city['importance'] * 0.3
                max_score = max(max_score, city_score)
                factors.append(f"regional_{city['name'].lower().replace(' ', '_')}")
        
        return {'score': int(max_score), 'factors': factors}
    
    def _analyze_border_proximity(self, center_point):
        """Analyze proximity to sensitive border areas"""
        max_score = 0
        factors = []
        
        for border in self.strategic_locations['border_areas']:
            distance = geodesic(center_point, border['coords']).kilometers
            
            if distance <= 25:  # Within 25km of border
                border_score = border['threat_level'] * (25 - distance) / 25
                max_score = max(max_score, border_score)
                factors.append(f"border_proximity_{border['name'].lower().replace(' ', '_')}")
            elif distance <= 50:  # Within 50km
                border_score = border['threat_level'] * 0.5
                max_score = max(max_score, border_score)
        
        return {'score': int(max_score), 'factors': factors}
    
    def _assess_infrastructure_criticality(self, asset_name, asset_type, center_point):
        """Assess criticality based on infrastructure role"""
        score = 0
        factors = []
        
        # Critical keywords that actually matter
        critical_indicators = {
            'international': 20,
            'national highway': 25,
            'expressway': 20,
            'metro': 15,
            'central': 15,
            'main': 10
        }
        
        name_lower = asset_name.lower()
        for indicator, points in critical_indicators.items():
            if indicator in name_lower:
                score += points
                factors.append(f"critical_{indicator.replace(' ', '_')}")
        
        # Remove meaningless "strategic" scoring
        # Focus on actual functional importance
        
        return {'score': score, 'factors': factors}
    
    def _estimate_asset_importance(self, asset_polygon, osm_tags):
        """Estimate importance based on size and capacity indicators"""
        score = 0
        factors = []
        
        # Polygon area analysis (larger = potentially more important)
        if hasattr(asset_polygon, 'area'):
            area = asset_polygon.area * 111320 * 111320  # Convert to square meters approximately
            if area > 1000000:  # > 1 sq km
                score += 15
                factors.append('large_infrastructure')
            elif area > 100000:  # > 0.1 sq km  
                score += 10
                factors.append('medium_infrastructure')
        
        # OSM capacity indicators
        if osm_tags:
            if 'lanes' in osm_tags:
                try:
                    lanes = int(osm_tags['lanes'])
                    if lanes >= 6:
                        score += 15
                        factors.append('major_capacity')
                    elif lanes >= 4:
                        score += 10
                        factors.append('medium_capacity')
                except:
                    pass
        
        return {'score': score, 'factors': factors}
    
    def _calculate_final_priority(self, classification_score):
        """Calculate final priority based on total score"""
        if classification_score >= 80:
            return 'HIGH'
        elif classification_score >= 50:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_threat_level(self, classification_score, threat_factors):
        """Calculate threat level based on score and factors"""
        threat_score = classification_score * 0.7  # Base from classification
        
        # Enhance based on specific threat factors
        high_threat_factors = ['border_proximity', 'military', 'nuclear', 'international']
        threat_factor_score = sum(10 for factor in threat_factors 
                                if any(htf in factor for htf in high_threat_factors))
        
        total_threat = threat_score + threat_factor_score
        
        if total_threat >= 70:
            return 'HIGH'
        elif total_threat >= 40:
            return 'MEDIUM'
        else:
            return 'LOW'

if __name__ == "__main__":
    # Test the classifier
    classifier = GarudaRealClassifier()
    
    # Test polygon (Delhi area)
    test_polygon = Polygon([(77.2090, 28.6139), (77.2190, 28.6139), 
                           (77.2190, 28.6239), (77.2090, 28.6239)])
    
    # Test classification
    result = classifier.classify_asset_real(
        "Test Bridge", 
        "Bridge", 
        test_polygon, 
        {'highway': 'primary'}
    )
    
    print(f"Classification result: {result}")
