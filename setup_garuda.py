#!/usr/bin/env python3
"""
🦅 GARUDA Project Setup Script
Automatically sets up the complete GARUDA project environment
"""

import os
import sys
import subprocess
import platform
import venv
import shutil
from pathlib import Path

class GarudaSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.python_executable = None
        self.pip_executable = None
        
    def print_banner(self):
        """Print GARUDA setup banner"""
        print("🦅" + "="*70 + "🦅")
        print("   GARUDA PROJECT SETUP")
        print("   Geospatial Asset Reconnaissance Unified Defense Analytics")
        print("🦅" + "="*70 + "🦅")
        print()
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        print("🔍 Checking Python version...")
        
        version = sys.version_info
        print(f"   Current Python version: {version.major}.{version.minor}.{version.micro}")
        
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            print("❌ Error: Python 3.8+ is required for GARUDA")
            print("   Please install Python 3.8 or higher and try again")
            return False
        
        if version.major == 3 and version.minor >= 12:
            print("⚠️  Warning: Python 3.12+ detected. Some packages may have compatibility issues")
        
        print("✅ Python version is compatible")
        return True
        
    def create_virtual_environment(self):
        """Create virtual environment"""
        print("\n📦 Creating virtual environment...")
        
        if self.venv_path.exists():
            print(f"   Virtual environment already exists at: {self.venv_path}")
            response = input("   Do you want to recreate it? (y/N): ").strip().lower()
            if response in ['y', 'yes']:
                print("   Removing existing virtual environment...")
                shutil.rmtree(self.venv_path)
            else:
                print("   Using existing virtual environment")
                self.set_venv_executables()
                return True
        
        try:
            print(f"   Creating virtual environment in: {self.venv_path}")
            venv.create(self.venv_path, with_pip=True)
            self.set_venv_executables()
            print("✅ Virtual environment created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create virtual environment: {e}")
            return False
            
    def set_venv_executables(self):
        """Set paths to Python and pip executables in virtual environment"""
        system = platform.system().lower()
        
        if system == "windows":
            self.python_executable = self.venv_path / "Scripts" / "python.exe"
            self.pip_executable = self.venv_path / "Scripts" / "pip.exe"
        else:  # Linux, macOS
            self.python_executable = self.venv_path / "bin" / "python"
            self.pip_executable = self.venv_path / "bin" / "pip"
    
    def get_usgs_credentials(self):
        """Get USGS credentials from user input"""
        print("\n🔐 USGS Earth Explorer Credentials Setup...")
        print("   Note: You can skip this and add credentials later in config.yaml")
        print("   To get USGS credentials: https://earthexplorer.usgs.gov/")
        print()
        
        skip = input("   Do you want to enter USGS credentials now? (y/N): ").strip().lower()
        
        if skip in ['y', 'yes']:
            print("\n   Enter your USGS Earth Explorer credentials:")
            username = input("   USGS Username: ").strip()
            password = input("   USGS Password: ").strip()
            
            if username and password:
                print("   ✅ USGS credentials will be saved to config.yaml")
                return username, password
            else:
                print("   ⚠️  Empty credentials - will use default placeholders")
                return None, None
        else:
            print("   ⏭️  Skipping USGS setup - you can add credentials later")
            return None, None
        
    def create_requirements_file(self):
        """Create requirements.txt file"""
        requirements_content = """# GARUDA - Geospatial Asset Reconnaissance Unified Defense Analytics
            # Core geospatial libraries
            geopandas>=0.14.0
            shapely>=2.0.0
            fiona>=1.9.0
            pyproj>=3.6.0

            # Data processing and analysis
            numpy>=1.24.0
            pandas>=2.0.0

            # Machine learning and computer vision
            opencv-python>=4.8.0

            # Visualization
            matplotlib>=3.7.0
            plotly>=5.15.0
            folium>=0.14.0

            # Web framework and APIs
            flask>=2.3.0
            requests>=2.31.0

            # Configuration and utilities
            pyyaml>=6.0
            python-dotenv>=1.0.0

            # Development and testing
            pytest>=7.4.0

            # Asset Discovery Dependencies
            overpy>=0.6

            # Additional utilities
            tqdm>=4.66.0
            """
        
        with open("requirements.txt", "w", encoding='utf-8') as f:
            f.write(requirements_content)
            
    def install_requirements(self):
        """Install project requirements"""
        print("\n📚 Installing project dependencies...")
        
        # Create requirements.txt if it doesn't exist
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("   Creating requirements.txt...")
            self.create_requirements_file()
        
        try:
            print("   Installing dependencies (this may take a few minutes)...")
            
            # Upgrade pip first
            subprocess.run([
                str(self.python_executable), "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True)
            
            # Install requirements
            subprocess.run([
                str(self.python_executable), "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True, capture_output=True)
            
            print("✅ All dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies")
            print("   You can try installing manually later: pip install -r requirements.txt")
            return True  # Continue setup even if dependencies fail
            
    def create_directory_structure(self):
        """Create project directory structure"""
        print("\n📁 Creating project directory structure...")
        
        directories = [
            "src",
            "src/utils",
            "templates",
            "static/css",
            "static/js",
            "data/raw/kml_files",
            "data/raw/satellite_imagery", 
            "data/processed/analyzed",
            "data/processed/reports",
            "data/models",
            "tests",
            "scripts",
            "logs"
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
        print("✅ Directory structure created")
    def create_config_files(self):
        """Create configuration files"""
        print("\n⚙️ Creating configuration files...")

        # Get USGS credentials
        usgs_username, usgs_password = self.get_usgs_credentials()

        # Use provided credentials or defaults
        if usgs_username and usgs_password:
            username_value = usgs_username
            password_value = usgs_password
        else:
            username_value = "YOUR_USGS_USERNAME"
            password_value = "YOUR_USGS_PASSWORD"

        # Create config.yaml with actual or placeholder credentials
        config_content = f"""# GARUDA Configuration File
system:
name: "GARUDA"
version: "1.0.0"
description: "Strategic Asset Monitoring System"

directories:
kml_input: "./data/raw/kml_files/"
satellite_data: "./data/raw/satellite_imagery/"
processed_output: "./data/processed/analyzed/"
reports: "./data/processed/reports/"
models: "./data/models/"

satellite:
preferred_datasets:
- "LANDSAT_8_C2_L2"
- "LANDSAT_9_C2_L2"
max_cloud_cover: 15
real_mode: true

# USGS Earth Explorer API Credentials
usgs:
username: "{username_value}"
password: "{password_value}"
base_url: "https://m2m.cr.usgs.gov/api/api/json/stable/"
node: "EE"

detection:
sensitivity: "medium"
min_change_area: 500
threat_threshold: 0.2

logging:
level: "INFO"
file: "logs/garuda.log"

development:
mock_mode: false
debug_output: true
"""

        with open("config.yaml", "w", encoding='utf-8') as f:
            f.write(config_content)

        # Create .gitignore
        gitignore_content = """__pycache__/
*.pyc
*.pyo
*.pyd
*.sqlite3
*.db
.env
venv/
instance/
.DS_Store
*.log
data/raw_satellite/
data/processed/
logs/
"""

        with open(".gitignore", "w", encoding='utf-8') as f:
            f.write(gitignore_content)

        # Create README.md
        readme_content = """# GARUDA - Geospatial Asset Reconnaissance Unified Defense Analytics

Strategic Asset Monitoring & Threat Detection System

## Quick Start

1. **Activate virtual environment:**
Windows
venv\\Scripts\\activate

Linux/macOS
source venv/bin/activate


2. **Run main system:**
python src/garuda_main.py --kml-dir data/raw/kml_files/


3. **Launch web dashboard:**
python src/garuda_web_dashboard.py

Open: http://localhost:5000

## Features

- Strategic asset monitoring from KML files
- Satellite imagery integration (USGS Earth Explorer)
- Change detection and threat assessment
- Interactive web dashboard
- Asset discovery and classification
- Professional reporting system

## Next Steps

1. Add KML files to `data/raw/kml_files/`
2. Update USGS credentials in `config.yaml` (if not done during setup)
3. Run the system and explore the dashboard!

**GARUDA is ready for strategic intelligence gathering!**
"""

        with open("README.md", "w", encoding='utf-8') as f:
            f.write(readme_content)

        print("✅ Configuration files created")

        if usgs_username and usgs_password:
            print(f"✅ USGS credentials saved for user: {usgs_username}")
        else:
            print("ℹ️  Remember to update USGS credentials in config.yaml later")
            
    def create_sample_kml(self):
        """Create sample KML file for testing"""
        print("\n📍 Creating sample KML data...")
        
        sample_kml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
<name>GARUDA Sample Strategic Assets</name>
<description>Sample strategic assets for GARUDA monitoring system</description>

<Placemark>
    <name>Strategic Bridge Delhi</name>
    <description>Major transportation bridge - High Priority</description>
    <Polygon>
        <outerBoundaryIs>
            <LinearRing>
                <coordinates>
                    77.2090,28.6139,0 77.2095,28.6139,0 77.2095,28.6142,0 77.2090,28.6142,0 77.2090,28.6139,0
                </coordinates>
            </LinearRing>
        </outerBoundaryIs>
    </Polygon>
</Placemark>

<Placemark>
    <name>Border Tunnel Complex</name>  
    <description>Critical underground infrastructure</description>
    <Polygon>
        <outerBoundaryIs>
            <LinearRing>
                <coordinates>
                    77.2100,28.6130,0 77.2110,28.6130,0 77.2110,28.6135,0 77.2100,28.6135,0 77.2100,28.6130,0
                </coordinates>
            </LinearRing>
        </outerBoundaryIs>
    </Polygon>
</Placemark>

<Placemark>
    <name>Power Infrastructure Hub</name>
    <description>Electrical grid control center</description>
    <Polygon>
        <outerBoundaryIs>
            <LinearRing>
                <coordinates>
                    77.2080,28.6120,0 77.2090,28.6120,0 77.2090,28.6125,0 77.2080,28.6125,0 77.2080,28.6120,0
                </coordinates>
            </LinearRing>
        </outerBoundaryIs>
    </Polygon>
</Placemark>

</Document>
</kml>'''
        
        kml_file = self.project_root / "data" / "raw" / "kml_files" / "sample_assets.kml"
        with open(kml_file, "w", encoding='utf-8') as f:
            f.write(sample_kml_content)
            
        print("✅ Sample KML file created")
        
    def create_activation_scripts(self):
        """Create easy activation scripts"""
        print("\n🚀 Creating activation scripts...")
        
        # Windows activation script
        windows_script = '''@echo off
echo GARUDA Activating Environment...
call venv\\Scripts\\activate
echo GARUDA environment activated!
echo.
echo Available commands:
echo   python src/garuda_main.py --kml-dir data/raw/kml_files/
echo   python src/garuda_web_dashboard.py
echo.
cmd /k
'''

        with open("activate_garuda.bat", "w", encoding='utf-8') as f:
            f.write(windows_script)
            
        # Unix activation script  
        unix_script = '''#!/bin/bash
echo "GARUDA Activating Environment..."
source venv/bin/activate
echo "GARUDA environment activated!"
echo ""
echo "Available commands:"
echo "  python src/garuda_main.py --kml-dir data/raw/kml_files/"
echo "  python src/garuda_web_dashboard.py"
echo ""
exec "$SHELL"
'''
                
        with open("activate_garuda.sh", "w", encoding='utf-8') as f:
            f.write(unix_script)
            
        print("✅ Activation scripts created")
        
    def print_completion_message(self):
        """Print setup completion message with instructions"""
        system = platform.system().lower()
        
        print("\n" + "="*70)
        print("   GARUDA PROJECT SETUP COMPLETE!")
        print("="*70)
        print()
        print("📋 Next Steps:")
        print()
        print("1. Activate the virtual environment:")
        if system == "windows":
            print("   Windows: Double-click 'activate_garuda.bat'")
            print("   Or run:  venv\\Scripts\\activate")
        else:
            print("   Linux/macOS: source venv/bin/activate")
        print()
        print("2. Add your GARUDA source files to the 'src/' directory")
        print()
        print("3. Add your KML files to 'data/raw/kml_files/'")
        print("   (Sample file already created)")
        print()
        print("4. Update USGS credentials in 'config.yaml' (optional)")
        print()
        print("GARUDA project structure is ready!")
        print()

    def run_setup(self):
        """Run complete setup process"""
        self.print_banner()
        
        if not self.check_python_version():
            return False
            
        if not self.create_virtual_environment():
            return False
            
        self.install_requirements()  # Continue even if this fails
        
        self.create_directory_structure()
        self.create_config_files()
        self.create_sample_kml()
        self.create_activation_scripts()
        
        self.print_completion_message()
        return True

def main():
    """Main setup function"""
    try:
        setup = GarudaSetup()
        success = setup.run_setup()
        
        if success:
            print("🎉 Setup completed successfully!")
            return 0
        else:
            print("❌ Setup failed. Please check the errors above.")
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error during setup: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    input("\nPress Enter to exit...")
    sys.exit(exit_code)
