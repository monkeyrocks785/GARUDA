#!/usr/bin/env python3
"""
Configure GARUDA with M2M API Token
"""

import requests
import yaml
import os

class M2MTokenConfig:
    def __init__(self):
        self.base_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"
        
    def setup_token(self):
        """Configure M2M API token"""
        print("🔑 GARUDA M2M Token Configuration")
        print("="*50)
        
        # Get token from user
        token = input("Enter your M2M API Token: ").strip()
        
        if not token:
            print("❌ Invalid token!")
            return False
            
        print("🔍 Testing M2M token...")
        
        if self.test_token(token):
            print("✅ M2M token validated successfully!")
            self.save_token(token)
            return True
        else:
            print("❌ Token validation failed!")
            return False
            
    def test_token(self, token):
        """Test M2M API token"""
        try:
            # Test with datasets endpoint
            test_payload = {
                "apiKey": token
            }
            
            response = requests.post(
                f"{self.base_url}datasets",
                json=test_payload,
                timeout=30,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'GARUDA-Defense-System/1.0'
                }
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"   API response received")
                
                if result.get('errorCode') is None:
                    datasets = result.get('data', [])
                    print(f"✅ Token valid! Found {len(datasets)} available datasets")
                    return True
                else:
                    error_msg = result.get('errorMessage', 'Unknown error')
                    print(f"❌ API Error: {error_msg}")
                    return False
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Token test error: {e}")
            return False
            
    def save_token(self, token):
        """Save token to config.yaml"""
        config_path = "config.yaml"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                
            # Update USGS section
            if 'usgs' not in config:
                config['usgs'] = {}
                
            config['usgs']['api_token'] = token
            config['usgs']['auth_method'] = 'token'
            
            # Ensure real mode is enabled
            config['development']['mock_mode'] = False
            config['satellite']['real_mode'] = True
            
            with open(config_path, 'w') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
                
            print(f"✅ Token saved to {config_path}")
            print("✅ Real data mode enabled")
        else:
            print("⚠️  config.yaml not found")
            
    def test_search_functionality(self, token):
        """Test actual satellite scene search"""
        print("\n🔍 Testing satellite scene search...")
        
        try:
            # Test scene search around Delhi
            search_payload = {
                "datasetName": "landsat_ot_c2_l2",
                "spatialFilter": {
                    "filterType": "mbr",
                    "lowerLeft": {"latitude": 28.4, "longitude": 77.0},
                    "upperRight": {"latitude": 28.8, "longitude": 77.4}
                },
                "temporalFilter": {
                    "startDate": "2024-01-01",
                    "endDate": "2024-12-31"
                },
                "maxResults": 5,
                "apiKey": token
            }
            
            response = requests.post(
                f"{self.base_url}scene-search",
                json=search_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errorCode') is None:
                    scenes = result.get('data', {}).get('results', [])
                    print(f"✅ Scene search successful! Found {len(scenes)} scenes")
                    
                    if scenes:
                        scene = scenes[0]
                        print(f"   Sample scene: {scene.get('displayId', 'Unknown')}")
                        print(f"   Date: {scene.get('temporalCoverage', {}).get('startDate', 'Unknown')}")
                        print(f"   Cloud cover: {scene.get('cloudCover', 'Unknown')}%")
                        
                    return True
                else:
                    print(f"❌ Scene search error: {result.get('errorMessage')}")
                    return False
            else:
                print(f"❌ Scene search failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Scene search test error: {e}")
            return False

if __name__ == "__main__":
    config = M2MTokenConfig()
    
    if config.setup_token():
        # Get the token from user input again for testing
        with open("config.yaml", 'r') as f:
            cfg = yaml.safe_load(f)
            token = cfg.get('usgs', {}).get('api_token')
            
        if token:
            config.test_search_functionality(token)
            
        print("\n🦅 GARUDA is now configured for real satellite data!")
        print("\nNext steps:")
        print("1. Run: python scripts/generate_real_kml.py")
        print("2. Run: python src/garuda_main.py")
        print("3. Launch dashboard: python src/garuda_web_dashboard.py")
    else:
        print("❌ Token configuration failed")
