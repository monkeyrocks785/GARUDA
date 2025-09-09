#!/usr/bin/env python3
"""
GARUDA Infrastructure Growth Prediction & Monitoring
"""

import numpy as np
import os
from datetime import datetime, timedelta
import json

class GarudaGrowthPredictor:
    """
    Advanced infrastructure growth prediction and analysis
    """
    
    def __init__(self):
        self.growth_patterns = {}
        self.predictions = {}
        
    def analyze_growth_patterns(self, assets_data):
        """Analyze infrastructure growth patterns by region and type"""
        
        print("Analyzing Infrastructure Growth Patterns...")
        
        growth_analysis = {}
        
        for asset_id, asset in assets_data.items():
            try:
                asset_type = asset.get('type', 'Unknown')
                priority = asset.get('priority', 'LOW')
                
                # Get coordinates
                if hasattr(asset.get('polygon'), 'centroid'):
                    lat, lon = asset['polygon'].centroid.y, asset['polygon'].centroid.x
                else:
                    lat, lon = 28.6139, 77.2090
                
                # Determine region
                region = self.determine_region(lat, lon)
                
                # Initialize tracking
                key = f"{asset_type}_{region}"
                if key not in growth_analysis:
                    growth_analysis[key] = {
                        'count': 0,
                        'high_priority': 0,
                        'medium_priority': 0,
                        'low_priority': 0,
                        'coordinates': [],
                        'growth_indicators': []
                    }
                
                # Update counts
                growth_analysis[key]['count'] += 1
                growth_analysis[key][f'{priority.lower()}_priority'] += 1
                growth_analysis[key]['coordinates'].append((lat, lon))
                
                # Calculate growth indicators
                growth_score = self.calculate_growth_score(asset, region)
                growth_analysis[key]['growth_indicators'].append(growth_score)
                
            except Exception as e:
                print(f"Error processing asset {asset_id}: {e}")
                continue
        
        # Analyze patterns
        self.growth_patterns = {}
        
        for key, data in growth_analysis.items():
            try:
                asset_type, region = key.split('_', 1)
                
                avg_growth = np.mean(data['growth_indicators']) if data['growth_indicators'] else 0.5
                growth_trend = self.determine_growth_trend(data['growth_indicators'])
                
                self.growth_patterns[key] = {
                    'asset_type': asset_type,
                    'region': region,
                    'total_assets': data['count'],
                    'priority_distribution': {
                        'HIGH': data['high_priority'],
                        'MEDIUM': data['medium_priority'],
                        'LOW': data['low_priority']
                    },
                    'average_growth_score': avg_growth,
                    'growth_trend': growth_trend,
                    'predicted_growth_rate': self.predict_regional_growth(avg_growth, region),
                    'risk_assessment': self.assess_growth_risk(data, region)
                }
            except Exception as e:
                print(f"Error analyzing pattern {key}: {e}")
                continue
        
        return self.growth_patterns
    
    def determine_region(self, lat, lon):
        """Determine region based on coordinates"""
        try:
            if lat > 32:
                return 'North_Kashmir'
            elif lat > 28 and lon < 77:
                return 'North_Punjab'
            elif lat > 28:
                return 'North_Delhi_NCR'
            elif lat > 23 and lon < 73:
                return 'West_Rajasthan'
            elif lat > 23 and lon < 80:
                return 'Central_MP_UP'
            elif lat > 20 and lon > 80:
                return 'East_Bengal'
            elif lat > 15 and lon > 77:
                return 'South_Deccan'
            elif lon < 75:
                return 'West_Maharashtra'
            else:
                return 'South_Tamil_Nadu'
        except:
            return 'Central_India'
    
    def calculate_growth_score(self, asset, region):
        """Calculate growth potential score for an asset"""
        try:
            score = 0.5  # Base score
            
            # Priority influence
            priority = asset.get('priority', 'LOW')
            if priority == 'HIGH':
                score += 0.3
            elif priority == 'MEDIUM':
                score += 0.2
            
            # Type influence
            type_growth_potential = {
                'Airport': 0.4,
                'Power Infrastructure': 0.3,
                'Railway Infrastructure': 0.35,
                'Bridge': 0.25,
                'Military Facility': 0.1,
                'Border Infrastructure': 0.2
            }
            asset_type = asset.get('type', 'Unknown')
            score += type_growth_potential.get(asset_type, 0.2)
            
            # Regional factors
            regional_growth = {
                'North_Delhi_NCR': 0.4,
                'South_Deccan': 0.35,
                'West_Maharashtra': 0.3,
                'North_Kashmir': 0.1,
                'East_Bengal': 0.25
            }
            score += regional_growth.get(region, 0.2)
            
            return min(1.0, score)
        except:
            return 0.5
    
    def determine_growth_trend(self, growth_indicators):
        """Determine overall growth trend"""
        try:
            if not growth_indicators:
                return 'STABLE'
            
            avg_growth = np.mean(growth_indicators)
            
            if avg_growth > 0.7:
                return 'RAPID_GROWTH'
            elif avg_growth > 0.5:
                return 'MODERATE_GROWTH'
            elif avg_growth > 0.3:
                return 'SLOW_GROWTH'
            else:
                return 'STABLE'
        except:
            return 'STABLE'
    
    def predict_regional_growth(self, current_score, region):
        """Predict future growth rate for region"""
        try:
            base_rate = current_score * 0.1
            
            regional_multipliers = {
                'North_Delhi_NCR': 1.3,
                'South_Deccan': 1.2,
                'West_Maharashtra': 1.15,
                'Central_MP_UP': 1.1,
                'North_Kashmir': 0.7,
                'East_Bengal': 1.0
            }
            
            multiplier = regional_multipliers.get(region, 1.0)
            predicted_rate = base_rate * multiplier
            
            return min(0.2, predicted_rate)
        except:
            return 0.02
    
    def assess_growth_risk(self, data, region):
        """Assess risk factors for infrastructure growth"""
        try:
            risks = []
            risk_score = 0
            
            # High concentration risk
            if data['count'] > 10:
                risks.append('HIGH_CONCENTRATION')
                risk_score += 0.2
            
            # High priority concentration
            if data['count'] > 0:
                high_priority_ratio = data['high_priority'] / data['count']
                if high_priority_ratio > 0.5:
                    risks.append('HIGH_VALUE_CONCENTRATION')
                    risk_score += 0.3
            
            # Border region risks
            border_regions = ['North_Kashmir', 'North_Punjab', 'East_Bengal']
            if region in border_regions:
                risks.append('BORDER_VULNERABILITY')
                risk_score += 0.4
            
            # Growth velocity risk
            if data['growth_indicators']:
                avg_growth = np.mean(data['growth_indicators'])
                if avg_growth > 0.8:
                    risks.append('RAPID_DEVELOPMENT')
                    risk_score += 0.2
            
            return {
                'risk_factors': risks,
                'risk_score': min(1.0, risk_score),
                'risk_level': 'HIGH' if risk_score > 0.6 else 'MEDIUM' if risk_score > 0.3 else 'LOW'
            }
        except Exception as e:
            return {
                'risk_factors': ['ANALYSIS_ERROR'],
                'risk_score': 0.5,
                'risk_level': 'MEDIUM'
            }
    
    def generate_growth_predictions(self, time_horizon_months=12):
        """Generate detailed growth predictions"""
        predictions = {}
        
        for pattern_key, pattern_data in self.growth_patterns.items():
            try:
                monthly_rate = pattern_data['predicted_growth_rate'] / 12
                months = range(1, time_horizon_months + 1)
                
                predicted_values = []
                current_count = pattern_data['total_assets']
                
                for month in months:
                    seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * month / 12)
                    growth_factor = (1 + monthly_rate * seasonal_factor)
                    current_count *= growth_factor
                    predicted_values.append(current_count)
                
                confidence = self.calculate_prediction_confidence(pattern_data)
                
                predictions[pattern_key] = {
                    'region': pattern_data['region'],
                    'asset_type': pattern_data['asset_type'],
                    'current_count': pattern_data['total_assets'],
                    'predicted_counts': predicted_values,
                    'growth_rate_annual': pattern_data['predicted_growth_rate'],
                    'confidence_level': confidence,
                    'risk_assessment': pattern_data['risk_assessment'],
                    'prediction_date': datetime.now().isoformat()
                }
            except Exception as e:
                print(f"Error generating predictions for {pattern_key}: {e}")
                continue
        
        self.predictions = predictions
        return predictions
    
    def calculate_prediction_confidence(self, pattern_data):
        """Calculate confidence in predictions"""
        try:
            confidence = 0.7
            
            if pattern_data['total_assets'] > 10:
                confidence += 0.2
            elif pattern_data['total_assets'] > 5:
                confidence += 0.1
            
            priorities = pattern_data['priority_distribution']
            total = sum(priorities.values())
            if total > 0:
                balance = 1 - max(priorities.values()) / total
                confidence += balance * 0.1
            
            return min(1.0, confidence)
        except:
            return 0.7
    
    def identify_growth_hotspots(self):
        """Identify regions with highest growth potential"""
        hotspots = []
        
        for pattern_key, pattern_data in self.growth_patterns.items():
            try:
                hotspot_score = (
                    pattern_data['predicted_growth_rate'] * 0.4 +
                    pattern_data['average_growth_score'] * 0.3 +
                    (pattern_data['total_assets'] / 20) * 0.3
                )
                
                hotspots.append({
                    'region': pattern_data['region'],
                    'asset_type': pattern_data['asset_type'],
                    'hotspot_score': hotspot_score,
                    'predicted_growth': pattern_data['predicted_growth_rate'],
                    'current_assets': pattern_data['total_assets'],
                    'risk_level': pattern_data['risk_assessment']['risk_level']
                })
            except Exception as e:
                print(f"Error calculating hotspot for {pattern_key}: {e}")
                continue
        
        hotspots.sort(key=lambda x: x['hotspot_score'], reverse=True)
        return hotspots[:10]
    
    def generate_growth_report(self):
        """Generate comprehensive growth analysis report"""
        try:
            if not self.growth_patterns:
                return "No growth patterns analyzed yet. Run analyze_growth_patterns() first."
            
            report = []
            report.append("GARUDA INFRASTRUCTURE GROWTH ANALYSIS REPORT")
            report.append("=" * 60)
            report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Regions Analyzed: {len(set(p['region'] for p in self.growth_patterns.values()))}")
            report.append(f"Asset Categories: {len(set(p['asset_type'] for p in self.growth_patterns.values()))}")
            report.append("")
            
            # Growth hotspots
            hotspots = self.identify_growth_hotspots()
            report.append("TOP GROWTH HOTSPOTS:")
            report.append("-" * 30)
            
            for i, hotspot in enumerate(hotspots[:5], 1):
                report.append(f"{i}. {hotspot['region']} - {hotspot['asset_type']}")
                report.append(f"   Growth Score: {hotspot['hotspot_score']:.3f}")
                report.append(f"   Predicted Growth: {hotspot['predicted_growth']:.1%} annually")
                report.append(f"   Risk Level: {hotspot['risk_level']}")
                report.append("")
            
            # Regional summary
            report.append("REGIONAL GROWTH SUMMARY:")
            report.append("-" * 30)
            
            regional_summary = {}
            for pattern_data in self.growth_patterns.values():
                region = pattern_data['region']
                if region not in regional_summary:
                    regional_summary[region] = {
                        'total_assets': 0,
                        'avg_growth': [],
                        'high_risk_count': 0
                    }
                
                regional_summary[region]['total_assets'] += pattern_data['total_assets']
                regional_summary[region]['avg_growth'].append(pattern_data['predicted_growth_rate'])
                
                if pattern_data['risk_assessment']['risk_level'] == 'HIGH':
                    regional_summary[region]['high_risk_count'] += 1
            
            for region, summary in regional_summary.items():
                avg_growth = np.mean(summary['avg_growth']) if summary['avg_growth'] else 0
                report.append(f"Region: {region}:")
                report.append(f"   Total Assets: {summary['total_assets']}")
                report.append(f"   Average Growth: {avg_growth:.1%}")
                report.append(f"   High Risk Categories: {summary['high_risk_count']}")
                report.append("")
            
            return "\n".join(report)
            
        except Exception as e:
            return f"Error generating growth report: {e}"

if __name__ == "__main__":
    predictor = GarudaGrowthPredictor()
    print("GARUDA Growth Predictor - Ready for Infrastructure Analysis")
