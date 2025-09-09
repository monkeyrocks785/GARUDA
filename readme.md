🦅 GARUDA
Geospatial Asset Reconnaissance Unified Defense Analytics

GARUDA is a comprehensive system for strategic asset monitoring, change detection, and growth prediction using real satellite imagery, KML-defined assets, and machine learning.

Features
KML Asset Ingestion: Load strategic infrastructure from KML files (bridges, airports, power plants, railways, military facilities, border controls).

Real Satellite Integration: Automated download via USGS M2M API token (Landsat 8/9, Sentinel-2) with mock fallback.

Change Detection: Multi-algorithm analysis (NDVI, structural, texture) for real threat assessment.

Intelligent Classification: Geography-aware, OSM-augmented scoring for accurate priority & threat levels.

Machine Learning:

Infrastructure growth prediction (Random Forest).

Threat score forecasting.

Anomaly detection.

Interactive Dashboard: Flask + Folium + Plotly for real-time maps, statistics, charts, asset detail views.

Reporting & Visualization: Automated PNG charts, text reports, Jupyter-friendly scripts.

Installation
Clone repository

bash
git clone <your-repo-url>
cd GARUDA
Run setup script

bash
python setup_garuda.py
Creates venv/ (Python 3.8+ required)

Installs dependencies from requirements.txt

Generates directory structure, config.yaml, sample KML, activation scripts

Activate virtual environment

Windows

bash
.\activate_garuda.bat
Linux/macOS

bash
source activate_garuda.sh
Configure USGS M2M API token

bash
python scripts/configure_m2m_token.py
Enter your token when prompted. This updates config.yaml automatically.

Usage
Generate real assets KML (OpenStreetMap)

bash
python scripts/generate_real_kml.py
Run core monitoring system

bash
python src/garuda_main.py --kml-dir data/raw/kml_files/
Loads assets

Downloads imagery

Performs change detection & classification

Prints summary and guidance

Launch web dashboard

bash
python src/garuda_web_dashboard.py
Open in browser: http://localhost:5000

Train ML models & analyze growth

bash
python scripts/run_ml_training.py
Trains growth, threat, anomaly models

Analyzes growth patterns

Generates predictions & visualizations

Saves reports in data/processed/reports/

Configuration (config.yaml)
text
usgs:
api_token: "YOUR_M2M_TOKEN"
auth_method: "token"

satellite:
real_mode: true
preferred_datasets: - "LANDSAT_8_C2_L2" - "LANDSAT_9_C2_L2" - "SENTINEL_2A"
max_cloud_cover: 15

development:
mock_mode: false
debug_output: true
mock_mode: true to use fake data

real_mode: true to enable USGS API calls
