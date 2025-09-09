#!/usr/bin/env python3
"""
GARUDA ML Training Pipeline - COMPLETE ERROR-FREE VERSION
Train all machine learning models with current asset data
"""

import sys
import os
from datetime import datetime

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')

sys.path.insert(0, parent_dir)
sys.path.insert(0, src_dir)

# Import with error handling
def safe_import():
    """Safely import all required modules"""
    modules = {}
    
    try:
        from src.garuda_main import GarudaDefenseSystem
        modules['GarudaDefenseSystem'] = GarudaDefenseSystem
        print("✅ GarudaDefenseSystem imported")
    except Exception as e:
        print(f"⚠️ Could not import GarudaDefenseSystem: {e}")
        return None
    
    try:
        from src.garuda_ml_engine import GarudaMLEngine
        modules['GarudaMLEngine'] = GarudaMLEngine
        print("✅ GarudaMLEngine imported")
    except Exception as e:
        print(f"⚠️ Could not import GarudaMLEngine: {e}")
        modules['GarudaMLEngine'] = None
    
    try:
        from src.garuda_growth_predictor import GarudaGrowthPredictor
        modules['GarudaGrowthPredictor'] = GarudaGrowthPredictor
        print("✅ GarudaGrowthPredictor imported")
    except Exception as e:
        print(f"⚠️ Could not import GarudaGrowthPredictor: {e}")
        modules['GarudaGrowthPredictor'] = None
    
    try:
        from src.garuda_visualizer import GarudaVisualizer
        modules['GarudaVisualizer'] = GarudaVisualizer
        print("✅ GarudaVisualizer imported")
    except Exception as e:
        print(f"⚠️ Could not import GarudaVisualizer: {e}")
        modules['GarudaVisualizer'] = None
    
    return modules

def main():
    print("🚀 GARUDA ML Training Pipeline Starting...")
    print("=" * 50)
    
    # Import modules
    modules = safe_import()
    if not modules or not modules['GarudaDefenseSystem']:
        print("❌ Cannot proceed without core GARUDA system")
        return
    
    # Initialize systems
    print("\n📦 Initializing GARUDA systems...")
    try:
        garuda = modules['GarudaDefenseSystem']()
        
        ml_engine = None
        if modules['GarudaMLEngine']:
            ml_engine = modules['GarudaMLEngine']()
        
        growth_predictor = None
        if modules['GarudaGrowthPredictor']:
            growth_predictor = modules['GarudaGrowthPredictor']()
        
        visualizer = None
        if modules['GarudaVisualizer']:
            visualizer = modules['GarudaVisualizer']()
        
        print("✅ Systems initialized")
        
    except Exception as e:
        print(f"❌ System initialization failed: {e}")
        return
    
    # Load asset data
    print("\n📊 Loading asset data...")
    try:
        assets = garuda.load_strategic_assets('data/raw/kml_files/')
        
        if not assets:
            print("❌ No assets found. Please run: python scripts/generate_real_kml.py")
            return
        
        print(f"✅ Loaded {len(assets)} strategic assets")
        
        # Asset summary
        asset_types = {}
        priority_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        
        for asset in assets.values():
            asset_type = asset.get('type', 'Unknown')
            priority = asset.get('priority', 'LOW')
            
            asset_types[asset_type] = asset_types.get(asset_type, 0) + 1
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        print("📈 Asset Distribution:")
        for asset_type, count in asset_types.items():
            print(f"   • {asset_type}: {count}")
        
        print(f"🎯 Priority Distribution: HIGH: {priority_counts['HIGH']}, "
              f"MEDIUM: {priority_counts['MEDIUM']}, LOW: {priority_counts['LOW']}")
    
    except Exception as e:
        print(f"❌ Failed to load assets: {e}")
        return
    
    # Train ML models
    training_results = {}
    if ml_engine:
        print("\n🤖 Training machine learning models...")
        try:
            training_results = ml_engine.train_all_models(assets)
            
            print("📈 Training Results:")
            if 'growth_model' in training_results:
                print(f"  Growth Model R²: {training_results['growth_model'].get('r2', 'N/A')}")
            if 'threat_model' in training_results:
                print(f"  Threat Model R²: {training_results['threat_model'].get('r2', 'N/A')}")
            if 'anomaly_model' in training_results:
                print(f"  Anomaly Detection Rate: {training_results['anomaly_model'].get('anomaly_rate', 'N/A')}")
        
        except Exception as e:
            print(f"⚠️ ML training failed: {e}")
            training_results = {}
    else:
        print("⚠️ ML Engine not available - skipping model training")
    
    # Growth pattern analysis
    growth_patterns = {}
    predictions = {}
    
    if growth_predictor:
        print("\n📊 Analyzing growth patterns...")
        try:
            growth_patterns = growth_predictor.analyze_growth_patterns(assets)
            print(f"✅ Analyzed {len(growth_patterns)} growth patterns")
            
            # Generate predictions
            print("🔮 Generating growth predictions...")
            predictions = growth_predictor.generate_growth_predictions(12)
            print(f"✅ Generated predictions for {len(predictions)} patterns")
            
            # Show top growth areas
            if growth_patterns:
                sorted_patterns = sorted(growth_patterns.items(), 
                                       key=lambda x: x[1]['predicted_growth_rate'], reverse=True)
                print("🎯 Top Growth Areas:")
                for i, (key, pattern) in enumerate(sorted_patterns[:3], 1):
                    print(f"   {i}. {pattern['region']} - {pattern['asset_type']}")
                    print(f"      Growth: {pattern['predicted_growth_rate']:.1%}, "
                          f"Assets: {pattern['total_assets']}")
        
        except Exception as e:
            print(f"⚠️ Growth analysis failed: {e}")
    else:
        print("⚠️ Growth Predictor not available - skipping growth analysis")
    
    # Test predictions on sample assets
    asset_predictions = []
    
    if ml_engine:
        print("\n🧪 Testing predictions on sample assets...")
        sample_assets = list(assets.items())[:5]  # Test on first 5 assets
        
        for asset_id, asset in sample_assets:
            try:
                print(f"\n📍 Asset: {asset['name']}")
                
                # Growth prediction
                growth_pred = ml_engine.predict_growth_rate(asset)
                print(f"  🔺 Growth: {growth_pred['predicted_growth_rate']:.1%} ({growth_pred['growth_category']})")
                
                # Threat prediction  
                threat_pred = ml_engine.predict_threat_level(asset)
                print(f"  ⚠️  Threat: {threat_pred['threat_level']} (Score: {threat_pred['predicted_threat_score']:.2f})")
                
                # Anomaly detection
                anomaly = ml_engine.detect_anomalies(asset)
                print(f"  🔍 Anomaly: {'YES' if anomaly['is_anomaly'] else 'NO'} (Level: {anomaly['anomaly_level']})")
                
                asset_predictions.append(threat_pred)
                
            except Exception as e:
                print(f"  ❌ Prediction failed: {e}")
    
    # Generate visualizations
    if visualizer:
        print("\n📊 Generating visualizations...")
        try:
            # Plot growth predictions
            if predictions:
                first_pattern = list(predictions.keys())[0]
                visualizer.plot_growth_predictions(predictions, first_pattern)
            
            # Plot threat distribution
            if asset_predictions:
                visualizer.plot_threat_distribution(asset_predictions)
            
            # Plot regional analysis
            if growth_patterns:
                visualizer.plot_regional_analysis(growth_patterns)
            
            # Create comprehensive report
            visualizer.create_ml_report(training_results, predictions, growth_patterns, asset_predictions)
            
        except Exception as e:
            print(f"⚠️ Visualization failed: {e}")
    
    # Generate text reports
    print("\n📋 Generating analysis reports...")
    
    try:
        # Create comprehensive text report
        report_lines = []
        report_lines.append("GARUDA MACHINE LEARNING ANALYSIS REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Total Assets Analyzed: {len(assets)}")
        report_lines.append("")
        
        report_lines.append("ASSET SUMMARY:")
        report_lines.append(f"  HIGH Priority: {priority_counts['HIGH']} assets")
        report_lines.append(f"  MEDIUM Priority: {priority_counts['MEDIUM']} assets")
        report_lines.append(f"  LOW Priority: {priority_counts['LOW']} assets")
        report_lines.append("")
        
        report_lines.append("ASSET TYPES:")
        for asset_type, count in asset_types.items():
            report_lines.append(f"  {asset_type}: {count} assets")
        report_lines.append("")
        
        if training_results:
            report_lines.append("ML TRAINING RESULTS:")
            report_lines.append(f"  Samples Trained: {training_results.get('samples_trained', 0)}")
            if 'growth_model' in training_results:
                report_lines.append(f"  Growth Model R²: {training_results['growth_model'].get('r2', 'N/A')}")
            if 'threat_model' in training_results:
                report_lines.append(f"  Threat Model R²: {training_results['threat_model'].get('r2', 'N/A')}")
            report_lines.append("")
        
        if growth_patterns:
            report_lines.append("GROWTH ANALYSIS:")
            report_lines.append(f"  Growth Patterns Identified: {len(growth_patterns)}")
            sorted_patterns = sorted(growth_patterns.items(), 
                                   key=lambda x: x[1]['predicted_growth_rate'], reverse=True)
            report_lines.append("  Top Growth Areas:")
            for i, (key, pattern) in enumerate(sorted_patterns[:5], 1):
                report_lines.append(f"    {i}. {pattern['region']} - {pattern['asset_type']} ({pattern['predicted_growth_rate']:.1%})")
            report_lines.append("")
        
        report_lines.append("SYSTEM STATUS:")
        report_lines.append("  GARUDA Core: OPERATIONAL")
        report_lines.append(f"  ML Engine: {'AVAILABLE' if ml_engine else 'LIMITED'}")
        report_lines.append(f"  Growth Predictor: {'AVAILABLE' if growth_predictor else 'LIMITED'}")
        report_lines.append(f"  Visualizer: {'AVAILABLE' if visualizer else 'LIMITED'}")
        report_lines.append("")
        
        report_lines.append("NEXT STEPS:")
        report_lines.append("1. Monitor high-growth regions for infrastructure changes")
        report_lines.append("2. Implement real-time satellite monitoring")
        report_lines.append("3. Enhance threat detection algorithms")
        report_lines.append("4. Expand asset database with additional sources")
        
        # Save report
        os.makedirs('data/processed/reports', exist_ok=True)
        with open('data/processed/reports/ml_training_report.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print("✅ ML training report saved to: data/processed/reports/ml_training_report.txt")
        
    except Exception as e:
        print(f"⚠️ Could not save report: {e}")
    
    print(f"\n🎉 GARUDA ML Training Pipeline Complete!")
    print(f"📊 Processed {len(assets)} strategic assets")
    print(f"🤖 ML models: {'Trained' if training_results else 'Limited'}")
    print(f"📈 Growth analysis: {'Complete' if growth_patterns else 'Limited'}")
    print(f"🦅 GARUDA ready for strategic intelligence operations!")

if __name__ == "__main__":
    main()
