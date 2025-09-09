#!/usr/bin/env python3
"""
🦅 GARUDA - Geospatial Asset Reconnaissance Unified Defense Analytics
Main Integration Script - Strategic Asset Monitoring System
"""

import os
import sys
import json
from datetime import datetime, timedelta
import argparse
import logging
from pathlib import Path

try:
    from garuda_kml_processor import GarudaKMLProcessor
    from garuda_satellite_downloader import GarudaSatelliteDownloader
    from garuda_change_detector import GarudaChangeDetector
    from shapely.geometry import Polygon
    import yaml
except ImportError as e:
    print(f"❌ Error importing GARUDA modules: {e}")
    print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

class GarudaDefenseSystem:
    """
    Main GARUDA Defense Monitoring System
    """
    
    def __init__(self, config_file=None):
        self.setup_logging()
        self.config = self.load_configuration(config_file)
        self.initialize_components()
        self.monitored_assets = {}
        
        self.logger.info("🦅 GARUDA Defense System Initialized")
        
    def setup_logging(self):
        """Initialize system-wide logging"""
        os.makedirs('logs', exist_ok=True)
        
        file_formatter = logging.Formatter(
            'GARUDA [%(levelname)s] %(asctime)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_formatter = logging.Formatter(
            '🦅 GARUDA [%(levelname)s] %(asctime)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler = logging.FileHandler('logs/garuda.log', encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def load_configuration(self, config_file):
        """Load system configuration"""
        default_config = {
            'directories': {
                'kml_input': './data/raw/kml_files/',
                'satellite_data': './data/raw/satellite_imagery/',
                'processed_output': './data/processed/',
                'reports': './data/processed/reports/'
            },
            'satellite': {
                'datasets': ['landsat_8', 'landsat_9'],
                'max_cloud_cover': 15,
                'real_mode': True
            },
            'detection': {
                'sensitivity': 'medium',
                'use_real_algorithms': True
            },
            'usgs': {
                'username': '',
                'password': '',
                'api_token': '',
                'auth_method': 'login'
            },
            'development': {
                'mock_mode': False
            }
        }
        
        config_path = config_file or 'config.yaml'
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    self._merge_configs(default_config, user_config)
                    self.logger.info(f"Configuration loaded from: {config_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config file: {e}, using defaults")
                
        return default_config
    
    def _merge_configs(self, default, user):
        """Recursively merge user config into default config"""
        for key, value in user.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_configs(default[key], value)
                else:
                    default[key] = value
            else:
                default[key] = value
        
    def initialize_components(self):
        """Initialize GARUDA subsystems"""
        try:
            self.kml_processor = GarudaKMLProcessor()
            
            # Initialize satellite downloader
            usgs_config = self.config.get('usgs', {})
            self.satellite_downloader = GarudaSatelliteDownloader(
                usgs_username=usgs_config.get('username'),
                usgs_password=usgs_config.get('password'),
                api_token=usgs_config.get('api_token')
            )
            
            # Initialize change detector
            detection_config = self.config.get('detection', {})
            self.change_detector = GarudaChangeDetector(
                sensitivity=detection_config.get('sensitivity', 'medium')
            )
            
            # Authenticate with satellite services
            if usgs_config.get('auth_method') == 'token' and usgs_config.get('api_token'):
                auth_success = self.satellite_downloader.authenticate_with_token()
            else:
                auth_success = self.satellite_downloader.authenticate()
            
            if auth_success:
                self.logger.info("✅ GARUDA components initialized successfully")
            else:
                self.logger.warning("⚠️ Satellite authentication failed - using mock mode")
            
        except Exception as e:
            self.logger.error(f"Component initialization failed: {e}")
            raise
            
    def create_directory_structure(self):
        """Create necessary directories"""
        for dir_type, dir_path in self.config['directories'].items():
            os.makedirs(dir_path, exist_ok=True)
            self.logger.debug(f"Directory ensured: {dir_path}")
            
    def load_strategic_assets(self, kml_directory):
        """Load strategic assets from KML files"""
        self.logger.info(f"Loading strategic assets from: {kml_directory}")
        
        assets = {}
        kml_files = []
        
        if os.path.exists(kml_directory):
            kml_files = [f for f in os.listdir(kml_directory) if f.lower().endswith(('.kml', '.kmz'))]
        
        if not kml_files:
            self.logger.warning(f"No KML files found in {kml_directory}")
            print(f"❌ No KML files found in: {kml_directory}")
            print("   Please add KML files to this directory and try again.")
            return {}
            
        print(f"📁 Found {len(kml_files)} KML file(s): {', '.join(kml_files)}")
        
        for kml_file in kml_files:
            kml_path = os.path.join(kml_directory, kml_file)
            try:
                print(f"\n📍 Processing: {kml_file}")
                asset_data = self.kml_processor.load_kml_file(kml_path)
                
                if not asset_data:
                    print(f"   ⚠️  No valid assets found in {kml_file}")
                    continue
                
                for asset in asset_data:
                    asset_id = f"{asset['type'].replace(' ', '_')}_{len(assets):03d}"
                    assets[asset_id] = {
                        'name': asset['name'],
                        'type': asset['type'],
                        'priority': asset['priority'],
                        'polygon': asset['polygon'],
                        'description': asset.get('description', ''),
                        'source_file': kml_file,
                        'last_monitored': None,
                        'threat_history': []
                    }
                    
                    print(f"   ✅ Loaded: {asset['name']} ({asset['type']}) - Priority: {asset['priority']}")
                
                self.logger.info(f"Loaded {len(asset_data)} assets from {kml_file}")
                
            except Exception as e:
                self.logger.error(f"Failed to load {kml_file}: {e}")
                print(f"   ❌ Error loading {kml_file}: {e}")
                
        self.monitored_assets = assets
        self.logger.info(f"Total strategic assets loaded: {len(assets)}")
        
        if assets:
            print(f"\n🎯 Successfully loaded {len(assets)} strategic assets for monitoring")
        
        return assets

def main():
    """Main GARUDA system entry point"""
    parser = argparse.ArgumentParser(description='GARUDA Defense Monitoring System')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--kml-dir', default='data/raw/kml_files/', help='KML files directory')
    parser.add_argument('--asset-id', help='Monitor specific asset by ID')
    
    args = parser.parse_args()
    
    try:
        print("🦅" + "="*70 + "🦅")
        print("   GARUDA - Geospatial Asset Reconnaissance Unified Defense Analytics")
        print("   Strategic Asset Monitoring & Threat Detection System")
        print("🦅" + "="*70 + "🦅")
        print()
        
        garuda = GarudaDefenseSystem(config_file=args.config)
        garuda.create_directory_structure()
        
        # Load strategic assets
        assets = garuda.load_strategic_assets(args.kml_dir)
        
        if not assets:
            print("\n❌ No strategic assets loaded. Please:")
            print(f"   1. Add KML files to: {args.kml_dir}")
            print(f"   2. Run asset discovery: python scripts/generate_real_kml.py")
            return 1
        
        print(f"\n✅ GARUDA system ready with {len(assets)} strategic assets")
        print(f"   📊 Asset Summary:")
        
        # Display asset summary
        asset_types = {}
        priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for asset in assets.values():
            asset_types[asset['type']] = asset_types.get(asset['type'], 0) + 1
            priority_counts[asset['priority']] = priority_counts.get(asset['priority'], 0) + 1
            
        for asset_type, count in asset_types.items():
            print(f"   • {asset_type}: {count}")
            
        print(f"   📈 Priority Distribution: HIGH: {priority_counts['HIGH']}, MEDIUM: {priority_counts['MEDIUM']}, LOW: {priority_counts['LOW']}")
        
        print(f"\n🌐 Web Dashboard: Run 'python src/garuda_web_dashboard.py' for interactive interface")
        print(f"🦅 GARUDA monitoring system operational and ready!")
        
        return 0
        
    except Exception as e:
        print(f"❌ GARUDA system error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
