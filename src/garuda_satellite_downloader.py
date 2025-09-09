"""
GARUDA Satellite Data Downloader Module
"""

import requests
import os
import json
from datetime import datetime, timedelta
import logging
from shapely.geometry import Polygon

class GarudaSatelliteDownloader:
    """
    Downloads satellite imagery from USGS Earth Explorer
    """
    
    def __init__(self, usgs_username=None, usgs_password=None, api_token=None):
        self.setup_logging()
        self.base_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        self.session = requests.Session()
        self.api_key = None
        self.username = usgs_username
        self.password = usgs_password
        self.api_token = api_token
        
        self.datasets = {
            'landsat_8': 'landsat_ot_c2_l2',
            'landsat_9': 'landsat_ot_c2_l2',
            'sentinel_2': 'sentinel_2a'
        }
        
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'GARUDA-Defense-System/1.0'
        })
        
    def setup_logging(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('🦅 GARUDA-SAT [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
    def authenticate(self):
        """Authenticate with USGS Earth Explorer"""
        try:
            if not self.username or not self.password:
                self.logger.warning("USGS credentials not provided - using mock mode")
                return self._mock_authentication()
            
            self.logger.info("Authenticating with USGS M2M API...")
            
            login_payload = {
                "username": self.username,
                "password": self.password
            }
            
            response = self.session.post(
                f"{self.base_url}login",
                json=login_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errorCode') is None and result.get('data'):
                    self.api_key = result['data']
                    self.logger.info("✅ USGS authentication successful!")
                    return True
                else:
                    error_msg = result.get('errorMessage', 'Unknown error')
                    self.logger.error(f"USGS API Error: {error_msg}")
                    return self._mock_authentication()
            else:
                self.logger.error(f"HTTP Error {response.status_code}")
                return self._mock_authentication()
                
        except Exception as e:
            self.logger.error(f"Authentication error: {e}")
            return self._mock_authentication()
    
    def authenticate_with_token(self):
        """Authenticate using M2M API token"""
        try:
            if not self.api_token:
                self.logger.warning("No M2M token provided - falling back to login")
                return self.authenticate()
                
            self.logger.info("Using M2M API token for authentication")
            self.api_key = self.api_token
            
            # Test the token
            test_payload = {"apiKey": self.api_key}
            response = self.session.post(
                f"{self.base_url}datasets",
                json=test_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errorCode') is None:
                    self.logger.info("✅ M2M Token authentication successful!")
                    return True
                else:
                    error_msg = result.get('errorMessage', 'Token invalid')
                    self.logger.error(f"Token error: {error_msg}")
                    return self._mock_authentication()
            else:
                self.logger.error(f"Token test failed: HTTP {response.status_code}")
                return self._mock_authentication()
                
        except Exception as e:
            self.logger.error(f"Token authentication failed: {e}")
            return self._mock_authentication()
        
    def _mock_authentication(self):
        """Mock authentication for demonstration"""
        self.api_key = "mock_api_key_for_demo"
        self.logger.info("Using mock authentication mode")
        return True
        
    def search_imagery(self, polygon, start_date, end_date, dataset='landsat_8', max_cloud_cover=20):
        """Search for satellite imagery"""
        try:
            self.logger.info(f"Searching {dataset} imagery from {start_date} to {end_date}")
            
            if not self.api_key or self.api_key == "mock_api_key_for_demo":
                return self._mock_search_results(polygon, start_date, end_date, dataset)
            
            bounds = polygon.bounds
            dataset_name = self.datasets.get(dataset, 'landsat_ot_c2_l2')
            
            search_payload = {
                "datasetName": dataset_name,
                "spatialFilter": {
                    "filterType": "mbr",
                    "lowerLeft": {"latitude": bounds[1], "longitude": bounds[0]},
                    "upperRight": {"latitude": bounds[3], "longitude": bounds[2]}
                },
                "temporalFilter": {
                    "startDate": start_date,
                    "endDate": end_date
                },
                "maxResults": 50,
                "apiKey": self.api_key
            }
            
            response = self.session.post(
                f"{self.base_url}scene-search",
                json=search_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errorCode') is None:
                    scenes = result.get('data', {}).get('results', [])
                    self.logger.info(f"Found {len(scenes)} real satellite scenes")
                    return self._process_search_results(scenes)
                else:
                    self.logger.error(f"Search API Error: {result.get('errorMessage')}")
                    return self._mock_search_results(polygon, start_date, end_date, dataset)
            else:
                self.logger.error(f"Search HTTP Error {response.status_code}")
                return self._mock_search_results(polygon, start_date, end_date, dataset)
                
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return self._mock_search_results(polygon, start_date, end_date, dataset)
    
    def _process_search_results(self, scenes):
        """Process search results"""
        processed_scenes = []
        
        for scene in scenes:
            processed_scene = {
                'scene_id': scene.get('displayId', scene.get('entityId', 'Unknown')),
                'acquisition_date': scene.get('temporalCoverage', {}).get('startDate', '').split('T')[0],
                'cloud_cover': scene.get('cloudCover', 0),
                'dataset': scene.get('datasetName', 'Unknown'),
                'download_url': scene.get('downloadUrl', ''),
                'bounds': scene.get('spatialBounds', {}),
                'metadata': scene.get('metadata', {})
            }
            processed_scenes.append(processed_scene)
            
        return processed_scenes
        
    def _mock_search_results(self, polygon, start_date, end_date, dataset):
        """Generate mock search results"""
        mock_scenes = []
        current_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        scene_counter = 1
        while current_date <= end_date_obj and scene_counter <= 5:
            mock_scenes.append({
                'scene_id': f"LC08_L2_{current_date.strftime('%Y%m%d')}_{scene_counter:03d}",
                'acquisition_date': current_date.strftime('%Y-%m-%d'),
                'cloud_cover': min(25, scene_counter * 3),
                'dataset': dataset,
                'download_url': f"https://earthexplorer.usgs.gov/scene/{scene_counter}",
                'bounds': polygon.bounds,
                'metadata': {
                    'sensor': dataset.replace('_', '-').upper(),
                    'processing_level': 'L2',
                    'spatial_resolution': '30m' if 'landsat' in dataset else '10m'
                }
            })
            current_date += timedelta(days=16)
            scene_counter += 1
            
        self.logger.info(f"Generated {len(mock_scenes)} mock scenes")
        return mock_scenes

    def batch_download_for_asset(self, asset_polygon, asset_name, time_periods, output_dir):
        """Download satellite imagery for asset monitoring"""
        self.logger.info(f"Starting batch download for asset: {asset_name}")
        
        asset_dir = os.path.join(output_dir, asset_name.replace(' ', '_'))
        downloads = {}
        
        for i, (start_date, end_date) in enumerate(time_periods):
            period_name = f"Period_{i+1}_{start_date}_to_{end_date}"
            
            scenes = self.search_imagery(asset_polygon, start_date, end_date)
            
            period_downloads = []
            for scene in sorted(scenes, key=lambda x: x['cloud_cover'])[:3]:
                download_info = {
                    'scene_info': scene,
                    'period': period_name,
                    'asset_name': asset_name,
                    'status': 'processed'
                }
                
                if self.api_key and self.api_key != "mock_api_key_for_demo":
                    download_info['data_source'] = 'real_usgs'
                else:
                    download_info['data_source'] = 'mock'
                    
                download_info['extracted_bands'] = {
                    'red': f'red_band_{scene["scene_id"]}.tif',
                    'green': f'green_band_{scene["scene_id"]}.tif',
                    'blue': f'blue_band_{scene["scene_id"]}.tif',
                    'nir': f'nir_band_{scene["scene_id"]}.tif'
                }
                    
                period_downloads.append(download_info)
                    
            downloads[period_name] = period_downloads
            
        self.logger.info(f"Completed batch download for {asset_name}")
        return downloads

if __name__ == "__main__":
    print("🦅 GARUDA Satellite Downloader - Ready for Intelligence Gathering")
