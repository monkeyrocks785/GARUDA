#!/usr/bin/env python3
"""
GARUDA ML Visualization System
Generate graphs and charts for ML analysis
"""

import os
import numpy as np
from datetime import datetime

# Try to import matplotlib, with fallback
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    print("Warning: matplotlib not available. Charts will be saved as data files only.")
    MATPLOTLIB_AVAILABLE = False

class GarudaVisualizer:
    """
    GARUDA ML visualization and reporting system
    """
    
    def __init__(self, output_dir="data/processed/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def plot_growth_predictions(self, predictions, pattern_key=None):
        """Plot growth predictions over time"""
        
        if not predictions:
            print("No predictions available to plot")
            return
        
        # Use first pattern if none specified
        if pattern_key is None:
            pattern_key = list(predictions.keys())[0]
        
        if pattern_key not in predictions:
            print(f"Pattern '{pattern_key}' not found in predictions")
            return
        
        data = predictions[pattern_key]
        months = np.arange(1, len(data['predicted_counts']) + 1)
        counts = data['predicted_counts']
        
        if MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(10, 6))
            plt.plot(months, counts, marker='o', linestyle='-', color='tab:blue', linewidth=2)
            plt.title(f"Infrastructure Growth Prediction: {data['region']} / {data['asset_type']}", fontsize=14)
            plt.xlabel("Months into Future", fontsize=12)
            plt.ylabel("Predicted Asset Count", fontsize=12)
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            filename = os.path.join(self.output_dir, f"growth_prediction_{pattern_key}.png")
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Growth prediction chart saved: {filename}")
        else:
            # Save as text data
            filename = os.path.join(self.output_dir, f"growth_prediction_{pattern_key}.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Growth Prediction Data: {data['region']} / {data['asset_type']}\n")
                f.write("Month\tPredicted Count\n")
                for month, count in zip(months, counts):
                    f.write(f"{month}\t{count:.2f}\n")
            
            print(f"Growth prediction data saved: {filename}")
    
    def plot_threat_distribution(self, asset_predictions):
        """Plot distribution of threat scores"""
        
        threat_scores = []
        for pred in asset_predictions:
            if isinstance(pred, dict) and 'predicted_threat_score' in pred:
                threat_scores.append(pred['predicted_threat_score'])
        
        if not threat_scores:
            print("No threat scores available to plot")
            return
        
        if MATPLOTLIB_AVAILABLE:
            plt.figure(figsize=(8, 6))
            plt.hist(threat_scores, bins=15, color='tab:red', edgecolor='black', alpha=0.7)
            plt.title("Distribution of Predicted Threat Scores", fontsize=14)
            plt.xlabel("Threat Score", fontsize=12)
            plt.ylabel("Number of Assets", fontsize=12)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            filename = os.path.join(self.output_dir, "threat_score_distribution.png")
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Threat distribution chart saved: {filename}")
        else:
            # Save as text summary
            filename = os.path.join(self.output_dir, "threat_distribution_summary.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Threat Score Distribution Summary\n")
                f.write("=" * 35 + "\n")
                f.write(f"Total Assets Analyzed: {len(threat_scores)}\n")
                f.write(f"Average Threat Score: {np.mean(threat_scores):.3f}\n")
                f.write(f"Minimum Threat Score: {np.min(threat_scores):.3f}\n")
                f.write(f"Maximum Threat Score: {np.max(threat_scores):.3f}\n")
                f.write(f"Standard Deviation: {np.std(threat_scores):.3f}\n")
                
                # Threat level categories
                high_threat = sum(1 for s in threat_scores if s >= 0.7)
                medium_threat = sum(1 for s in threat_scores if 0.4 <= s < 0.7)
                low_threat = sum(1 for s in threat_scores if s < 0.4)
                
                f.write(f"\nThreat Level Distribution:\n")
                f.write(f"High Threat (>=0.7): {high_threat} assets\n")
                f.write(f"Medium Threat (0.4-0.7): {medium_threat} assets\n")
                f.write(f"Low Threat (<0.4): {low_threat} assets\n")
            
            print(f"Threat distribution summary saved: {filename}")
    
    def plot_regional_analysis(self, growth_patterns):
        """Plot regional analysis charts"""
        
        if not growth_patterns:
            print("No growth patterns available to plot")
            return
        
        # Extract regional data
        regions = {}
        for pattern_key, pattern_data in growth_patterns.items():
            region = pattern_data['region']
            if region not in regions:
                regions[region] = {
                    'total_assets': 0,
                    'growth_rates': [],
                    'risk_scores': []
                }
            
            regions[region]['total_assets'] += pattern_data['total_assets']
            regions[region]['growth_rates'].append(pattern_data['predicted_growth_rate'])
            regions[region]['risk_scores'].append(pattern_data['risk_assessment']['risk_score'])
        
        if MATPLOTLIB_AVAILABLE:
            # Regional asset distribution
            region_names = list(regions.keys())
            asset_counts = [regions[r]['total_assets'] for r in region_names]
            
            plt.figure(figsize=(12, 8))
            
            # Subplot 1: Asset distribution by region
            plt.subplot(2, 2, 1)
            plt.bar(region_names, asset_counts, color='tab:green', alpha=0.7)
            plt.title("Asset Distribution by Region")
            plt.xlabel("Region")
            plt.ylabel("Number of Assets")
            plt.xticks(rotation=45, ha='right')
            
            # Subplot 2: Average growth rates by region
            plt.subplot(2, 2, 2)
            avg_growth_rates = [np.mean(regions[r]['growth_rates']) for r in region_names]
            plt.bar(region_names, avg_growth_rates, color='tab:blue', alpha=0.7)
            plt.title("Average Growth Rates by Region")
            plt.xlabel("Region")
            plt.ylabel("Growth Rate")
            plt.xticks(rotation=45, ha='right')
            
            # Subplot 3: Risk scores by region
            plt.subplot(2, 2, 3)
            avg_risk_scores = [np.mean(regions[r]['risk_scores']) for r in region_names]
            plt.bar(region_names, avg_risk_scores, color='tab:red', alpha=0.7)
            plt.title("Average Risk Scores by Region")
            plt.xlabel("Region")
            plt.ylabel("Risk Score")
            plt.xticks(rotation=45, ha='right')
            
            # Subplot 4: Growth vs Risk scatter
            plt.subplot(2, 2, 4)
            plt.scatter(avg_growth_rates, avg_risk_scores, s=100, alpha=0.7, c='tab:orange')
            for i, region in enumerate(region_names):
                plt.annotate(region, (avg_growth_rates[i], avg_risk_scores[i]), 
                           xytext=(5, 5), textcoords='offset points', fontsize=8)
            plt.title("Growth Rate vs Risk Score")
            plt.xlabel("Growth Rate")
            plt.ylabel("Risk Score")
            
            plt.tight_layout()
            
            filename = os.path.join(self.output_dir, "regional_analysis.png")
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"Regional analysis chart saved: {filename}")
        else:
            # Save regional summary as text
            filename = os.path.join(self.output_dir, "regional_analysis_summary.txt")
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("REGIONAL ANALYSIS SUMMARY\n")
                f.write("=" * 25 + "\n\n")
                
                for region, data in regions.items():
                    f.write(f"Region: {region}\n")
                    f.write(f"  Total Assets: {data['total_assets']}\n")
                    f.write(f"  Avg Growth Rate: {np.mean(data['growth_rates']):.3f}\n")
                    f.write(f"  Avg Risk Score: {np.mean(data['risk_scores']):.3f}\n\n")
            
            print(f"Regional analysis summary saved: {filename}")
    
    def create_ml_report(self, training_results, predictions, growth_patterns, asset_predictions):
        """Create comprehensive ML analysis report"""
        
        report_lines = []
        report_lines.append("GARUDA MACHINE LEARNING ANALYSIS REPORT")
        report_lines.append("=" * 50)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Training Results
        if training_results:
            report_lines.append("MACHINE LEARNING MODEL TRAINING RESULTS")
            report_lines.append("-" * 40)
            report_lines.append(f"Training Date: {training_results.get('training_completed', 'N/A')}")
            report_lines.append(f"Samples Trained: {training_results.get('samples_trained', 0)}")
            
            if 'growth_model' in training_results:
                growth = training_results['growth_model']
                report_lines.append(f"Growth Model R²: {growth.get('r2', 'N/A'):.3f}")
                report_lines.append(f"Growth Model MSE: {growth.get('mse', 'N/A'):.3f}")
            
            if 'threat_model' in training_results:
                threat = training_results['threat_model']
                report_lines.append(f"Threat Model R²: {threat.get('r2', 'N/A'):.3f}")
                report_lines.append(f"Threat Model MSE: {threat.get('mse', 'N/A'):.3f}")
            
            if 'anomaly_model' in training_results:
                anomaly = training_results['anomaly_model']
                report_lines.append(f"Anomaly Detection Rate: {anomaly.get('anomaly_rate', 'N/A'):.1%}")
            
            report_lines.append("")
        
        # Growth Analysis
        if growth_patterns:
            report_lines.append("INFRASTRUCTURE GROWTH ANALYSIS")
            report_lines.append("-" * 35)
            report_lines.append(f"Total Growth Patterns: {len(growth_patterns)}")
            
            # Top growing regions
            sorted_patterns = sorted(growth_patterns.items(), 
                                   key=lambda x: x[1]['predicted_growth_rate'], reverse=True)
            
            report_lines.append("Top Growth Areas:")
            for i, (key, pattern) in enumerate(sorted_patterns[:5], 1):
                report_lines.append(f"  {i}. {pattern['region']} - {pattern['asset_type']}")
                report_lines.append(f"     Growth Rate: {pattern['predicted_growth_rate']:.1%}")
                report_lines.append(f"     Assets: {pattern['total_assets']}")
                report_lines.append(f"     Risk: {pattern['risk_assessment']['risk_level']}")
            
            report_lines.append("")
        
        # Threat Analysis
        if asset_predictions:
            threat_scores = [p.get('predicted_threat_score', 0) for p in asset_predictions 
                           if isinstance(p, dict)]
            
            if threat_scores:
                report_lines.append("THREAT ASSESSMENT ANALYSIS")
                report_lines.append("-" * 28)
                report_lines.append(f"Assets Analyzed: {len(threat_scores)}")
                report_lines.append(f"Average Threat Score: {np.mean(threat_scores):.3f}")
                
                high_threat = sum(1 for s in threat_scores if s >= 0.7)
                medium_threat = sum(1 for s in threat_scores if 0.4 <= s < 0.7)
                low_threat = sum(1 for s in threat_scores if s < 0.4)
                
                report_lines.append(f"High Threat Assets: {high_threat}")
                report_lines.append(f"Medium Threat Assets: {medium_threat}")
                report_lines.append(f"Low Threat Assets: {low_threat}")
                report_lines.append("")
        
        # Predictions Summary
        if predictions:
            report_lines.append("GROWTH PREDICTIONS SUMMARY")
            report_lines.append("-" * 27)
            report_lines.append(f"Prediction Patterns: {len(predictions)}")
            report_lines.append("12-Month Growth Forecasts:")
            
            for key, pred in list(predictions.items())[:5]:
                final_count = pred['predicted_counts'][-1] if pred['predicted_counts'] else 0
                current_count = pred['current_count']
                growth_pct = ((final_count - current_count) / current_count * 100) if current_count > 0 else 0
                
                report_lines.append(f"  {pred['region']} - {pred['asset_type']}: +{growth_pct:.1f}%")
        
        # Save report
        report_content = "\n".join(report_lines)
        
        filename = os.path.join(self.output_dir, "ml_analysis_report.txt")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"ML analysis report saved: {filename}")
        return report_content

if __name__ == "__main__":
    visualizer = GarudaVisualizer()
    print("GARUDA Visualizer - Ready for ML Chart Generation")
