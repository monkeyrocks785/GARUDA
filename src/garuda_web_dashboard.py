#!/usr/bin/env python3
"""
GARUDA Web Dashboard
Interactive web interface for strategic asset monitoring
"""

from flask import Flask, render_template, jsonify, request
import folium
import json
import os
import sys
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils
from folium import plugins

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from garuda_main import GarudaDefenseSystem
from garuda_kml_processor import GarudaKMLProcessor

app = Flask(__name__)
app.static_folder = '../static'
app.template_folder = '../templates'

# Make hasattr available in templates
app.jinja_env.globals.update(hasattr=hasattr)

# Initialize GARUDA system
print("🦅 Initializing GARUDA Dashboard System...")

try:
    garuda_system = GarudaDefenseSystem()
    kml_processor = GarudaKMLProcessor()
    print("✅ GARUDA system initialized successfully")
except Exception as e:
    print(f"⚠️ GARUDA system initialization warning: {e}")
    garuda_system = None
    kml_processor = GarudaKMLProcessor()

def determine_threat_level(asset):
    """Determine current threat level for asset"""
    priority = asset.get('priority', 'LOW')
    threat_history = asset.get('threat_history', [])
    
    if threat_history:
        latest = threat_history[-1]
        return latest.get('threat_level', 'LOW')
    else:
        if priority == 'HIGH':
            return 'MEDIUM'
        else:
            return 'LOW'

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/assets')
def get_assets():
    """Get all strategic assets data"""
    try:
        # Load assets from KML files
        if garuda_system:
            assets = garuda_system.load_strategic_assets(garuda_system.config['directories']['kml_input'])
        else:
            assets = load_assets_fallback()
        
        if not assets:
            return jsonify({'error': 'No assets found', 'assets': []})
        
        # Convert to web-friendly format
        assets_data = []
        for asset_id, asset in assets.items():
            try:
                # Get polygon center for map display
                if hasattr(asset['polygon'], 'centroid'):
                    centroid = asset['polygon'].centroid
                    center_coords = [centroid.y, centroid.x]  # [lat, lon]
                    bounds = list(asset['polygon'].bounds)
                else:
                    center_coords = [28.6139, 77.2090]  # Delhi
                    bounds = [77.0, 28.0, 78.0, 29.0]
                
                assets_data.append({
                    'id': asset_id,
                    'name': asset['name'],
                    'type': asset['type'],
                    'priority': asset['priority'],
                    'coordinates': center_coords,
                    'bounds': bounds,
                    'description': asset.get('description', ''),
                    'source_file': asset['source_file'],
                    'last_monitored': asset.get('last_monitored', 'Never'),
                    'threat_level': determine_threat_level(asset)
                })
            except Exception as e:
                print(f"Error processing asset {asset_id}: {e}")
                continue
        
        return jsonify(assets_data)
        
    except Exception as e:
        print(f"Error in get_assets: {e}")
        return jsonify({'error': str(e), 'assets': []})


def load_assets_fallback():
    """Fallback method to load assets if main system fails"""
    try:
        assets = {}
        kml_dir = 'data/raw/kml_files/'
        
        if os.path.exists(kml_dir):
            kml_files = [f for f in os.listdir(kml_dir) if f.lower().endswith('.kml')]
            
            for kml_file in kml_files:
                kml_path = os.path.join(kml_dir, kml_file)
                try:
                    asset_data = kml_processor.load_kml_file(kml_path)
                    
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
                except Exception as e:
                    print(f"Error loading {kml_file}: {e}")
                    
        return assets
        
    except Exception as e:
        print(f"Fallback asset loading failed: {e}")
        return {}

@app.route('/api/analytics')
def get_analytics():
    """Get analytics data for dashboard"""
    try:
        # Load assets
        if garuda_system:
            assets = garuda_system.load_strategic_assets(garuda_system.config['directories']['kml_input'])
        else:
            assets = load_assets_fallback()
        
        if not assets:
            return jsonify({
                'total_assets': 0,
                'type_distribution': {},
                'priority_distribution': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'threat_distribution': {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
                'type_chart': '{}',
                'priority_chart': '{}',
                'threat_chart': '{}',
                'last_update': datetime.now().isoformat()
            })
        
        # Calculate distributions
        type_counts = {}
        priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        threat_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for asset in assets.values():
            # Asset type distribution
            asset_type = asset['type']
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            # Priority distribution
            priority = asset['priority']
            if priority in priority_counts:
                priority_counts[priority] += 1
            
            # Threat distribution
            threat_level = determine_threat_level(asset)
            if threat_level in threat_counts:
                threat_counts[threat_level] += 1
        
        # Create charts data
        type_chart = {
            'data': [{
                'values': list(type_counts.values()),
                'labels': list(type_counts.keys()),
                'type': 'pie',
                'name': 'Asset Types',
                'marker': {
                    'colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
                }
            }],
            'layout': {
                'title': {
                    'text': 'Strategic Asset Distribution',
                    'font': {'size': 16}
                },
                'showlegend': True,
                'height': 350
            }
        }
        
        priority_chart = {
            'data': [{
                'x': list(priority_counts.keys()),
                'y': list(priority_counts.values()),
                'type': 'bar',
                'name': 'Priority Levels',
                'marker': {
                    'color': ['#dc3545', '#fd7e14', '#28a745']
                }
            }],
            'layout': {
                'title': {
                    'text': 'Asset Priority Distribution',
                    'font': {'size': 16}
                },
                'xaxis': {'title': 'Priority Level'},
                'yaxis': {'title': 'Number of Assets'},
                'height': 350
            }
        }
        
        threat_chart = {
            'data': [{
                'values': list(threat_counts.values()),
                'labels': list(threat_counts.keys()),
                'type': 'pie',
                'hole': 0.4,
                'name': 'Threat Levels',
                'marker': {
                    'colors': ['#dc3545', '#ffc107', '#28a745']
                }
            }],
            'layout': {
                'title': {
                    'text': 'Current Threat Assessment',
                    'font': {'size': 16}
                },
                'showlegend': True,
                'height': 350
            }
        }
        
        return jsonify({
            'total_assets': len(assets),
            'type_distribution': type_counts,
            'priority_distribution': priority_counts,
            'threat_distribution': threat_counts,
            'type_chart': json.dumps(type_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'priority_chart': json.dumps(priority_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'threat_chart': json.dumps(threat_chart, cls=plotly.utils.PlotlyJSONEncoder),
            'last_update': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in analytics: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/map')
def get_map():
    """Generate optimized interactive map with clustering - ERROR-FREE VERSION"""
    try:
        # Load assets (keeping your existing logic)
        if garuda_system:
            assets = garuda_system.load_strategic_assets(garuda_system.config['directories']['kml_input'])
        else:
            assets = load_assets_fallback()
        
        if not assets:
            m = folium.Map(
                location=[20.5937, 78.9629], 
                zoom_start=5,
                tiles='OpenStreetMap'
            )
            return m._repr_html_()
        
        # Create optimized map with English tiles
        m = folium.Map(
            location=[20.5937, 78.9629], 
            zoom_start=5,
            tiles='OpenStreetMap'  # English tiles
        )
        
        # Add English tile alternatives (error-safe)
        try:
            folium.TileLayer(
                'CartoDB positron',
                name='Light Mode (English)'
            ).add_to(m)
            
            folium.TileLayer(
                'CartoDB dark_matter', 
                name='Dark Mode (English)'
            ).add_to(m)
        except:
            pass  # Skip if tile layers fail
        
        # Add clustering for zoom-based display (error-safe)
        try:
            # Import plugins here to avoid import errors
            from folium import plugins
            
            marker_cluster = plugins.MarkerCluster(
                name='GARUDA Strategic Assets'
            ).add_to(m)
            
        except ImportError:
            print("⚠️ Folium plugins not available, using regular markers")
            marker_cluster = m  # Fallback to regular map
        
        # Add ALL your assets to the cluster
        assets_added = 0
        for asset_id, asset in assets.items():
            try:
                if hasattr(asset['polygon'], 'centroid'):
                    centroid = asset['polygon'].centroid
                    coords = [centroid.y, centroid.x]
                else:
                    coords = [28.6139, 77.2090]
                
                # Color based on priority (your existing logic)
                color_map = {
                    'HIGH': 'red',
                    'MEDIUM': 'orange', 
                    'LOW': 'green'
                }
                color = color_map.get(asset['priority'], 'blue')
                
                # Enhanced popup (error-safe HTML)
                popup_html = f"""
                <div style="font-family: Arial; width: 300px;">
                    <h4 style="color: {color};">🦅 {asset['name']}</h4>
                    <p><strong>Type:</strong> {asset['type']}</p>
                    <p><strong>Priority:</strong> <span style="color: {color};">{asset['priority']}</span></p>
                    <p><strong>Threat Level:</strong> {determine_threat_level(asset)}</p>
                    <p><strong>Source:</strong> {asset['source_file']}</p>
                    <p><strong>Description:</strong> {asset.get('description', 'Strategic infrastructure asset')}</p>
                    <p><strong>Last Monitored:</strong> {asset.get('last_monitored', 'Never')}</p>
                </div>
                """
                
                # Enhanced tooltip
                tooltip_text = f"🦅 {asset['name']} ({asset['priority']} Priority)"
                
                # Add marker (error-safe icon)
                try:
                    # Try with FontAwesome icon
                    icon = folium.Icon(color=color, icon='info-sign')
                except:
                    # Fallback to basic icon
                    icon = folium.Icon(color=color)
                
                folium.Marker(
                    location=coords,
                    popup=folium.Popup(popup_html, max_width=350),
                    tooltip=tooltip_text,
                    icon=icon
                ).add_to(marker_cluster)
                
                assets_added += 1
                    
            except Exception as e:
                print(f"⚠️ Error adding asset {asset_id} to map: {e}")
                continue
        
        # Add layer control (error-safe)
        try:
            folium.LayerControl().add_to(m)
        except:
            pass
        
        print(f"✅ Map generated with {assets_added} assets")
        return m._repr_html_()
        
    except Exception as e:
        print(f"❌ Error generating map: {e}")
        # Fallback map in English
        m = folium.Map(
            location=[20.5937, 78.9629], 
            zoom_start=5,
            tiles='OpenStreetMap'
        )
        
        # Add a simple message on fallback map
        folium.Marker(
            location=[20.5937, 78.9629],
            popup="GARUDA Map Loading Error - Please refresh",
            tooltip="Map Error"
        ).add_to(m)
        
        return m._repr_html_()

@app.route('/asset/<asset_id>')
def asset_detail(asset_id):
    """Detailed view of specific asset"""
    try:
        if garuda_system:
            assets = garuda_system.load_strategic_assets(garuda_system.config['directories']['kml_input'])
        else:
            assets = load_assets_fallback()
        
        if asset_id in assets:
            asset = assets[asset_id]
            return render_template('asset_detail.html', asset=asset, asset_id=asset_id)
        else:
            return "Asset not found", 404
            
    except Exception as e:
        return f"Error loading asset: {e}", 500

# Template filters
@app.template_filter()
def get_priority_color(priority):
    color_map = {'HIGH': 'danger', 'MEDIUM': 'warning', 'LOW': 'success'}
    return color_map.get(priority, 'secondary')

@app.template_filter()
def get_threat_color(threat):
    color_map = {'HIGH': 'danger', 'MEDIUM': 'warning', 'LOW': 'success'}
    return color_map.get(threat, 'secondary')

@app.template_filter()
def get_type_class(asset_type):
    type_map = {
        'Bridge': 'type-bridge',
        'Tunnel': 'type-tunnel',
        'Airport': 'type-airport',
        'Railway Infrastructure': 'type-railway',
        'Port Infrastructure': 'type-port',
        'Power Infrastructure': 'type-power'
    }
    return type_map.get(asset_type, 'type-default')

@app.template_filter()
def get_type_icon(asset_type):
    icon_map = {
        'Bridge': 'fa-bridge',
        'Tunnel': 'fa-mountain',
        'Airport': 'fa-plane',
        'Railway Infrastructure': 'fa-train',
        'Port Infrastructure': 'fa-ship',
        'Power Infrastructure': 'fa-bolt'
    }
    return icon_map.get(asset_type, 'fa-building')

def load_assets_fallback():
    """Load assets with REAL classification"""
    try:
        assets = {}
        kml_dir = 'data/raw/kml_files/'
        
        if os.path.exists(kml_dir):
            kml_files = [f for f in os.listdir(kml_dir) if f.lower().endswith('.kml')]
            
            for kml_file in kml_files:
                kml_path = os.path.join(kml_dir, kml_file)
                try:
                    # Use REAL classification instead of basic
                    if hasattr(kml_processor, 'load_kml_file_with_real_classification'):
                        asset_data = kml_processor.load_kml_file_with_real_classification(kml_path)
                    else:
                        asset_data = kml_processor.load_kml_file(kml_path)
                    
                    for asset in asset_data:
                        asset_id = f"{asset['type'].replace(' ', '_')}_{len(assets):03d}"
                        assets[asset_id] = {
                            'name': asset['name'],
                            'type': asset['type'],
                            'priority': asset['priority'],  # Now REAL priority
                            'polygon': asset['polygon'],
                            'description': asset.get('description', ''),
                            'source_file': kml_file,
                            'last_monitored': None,
                            'threat_history': [],
                            'real_classification': asset.get('classification_details', {})
                        }
                except Exception as e:
                    print(f"Error loading {kml_file}: {e}")
                    
        return assets
        
    except Exception as e:
        print(f"Real asset loading failed: {e}")
        return {}


if __name__ == '__main__':
    print("\n🦅" + "="*70 + "🦅")
    print("   GARUDA WEB DASHBOARD")
    print("   Strategic Asset Monitoring Interface")
    print("🦅" + "="*70 + "🦅")
    
    print(f"\n🌐 Dashboard will be available at:")
    print(f"   🔗 http://localhost:5000")
    print(f"   🔗 http://127.0.0.1:5000")
    
    print(f"\n🦅 GARUDA Dashboard Ready!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
