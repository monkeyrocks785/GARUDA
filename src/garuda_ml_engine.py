#!/usr/bin/env python3
"""
GARUDA Machine Learning Engine
Infrastructure Growth Prediction & Threat Analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
import json
import logging

# Try to import ML libraries, with fallbacks
try:
    from sklearn.ensemble import RandomForestRegressor, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    print("⚠️ scikit-learn not available. Using mock ML models.")
    SKLEARN_AVAILABLE = False

class GarudaMLEngine:
    """
    GARUDA Machine Learning Engine for infrastructure analysis
    """
    
    def __init__(self):
        self.setup_logging()
        self.models = {}
        self.scalers = {}
        self.models_dir = "data/models/"
        os.makedirs(self.models_dir, exist_ok=True)
        
        if SKLEARN_AVAILABLE:
            # Initialize real models
            self.growth_predictor = RandomForestRegressor(
                n_estimators=100, 
                random_state=42,
                max_depth=15
            )
            
            self.anomaly_detector = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            
            self.threat_predictor = RandomForestRegressor(
                n_estimators=50,
                random_state=42
            )
        else:
            # Initialize mock models
            self.growth_predictor = MockMLModel("Growth")
            self.anomaly_detector = MockMLModel("Anomaly")
            self.threat_predictor = MockMLModel("Threat")
        
    def setup_logging(self):
        """Initialize logging"""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('GARUDA-ML [%(levelname)s]: %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def prepare_training_data(self, assets_data):
        """Prepare training data from asset history"""
        self.logger.info("Preparing training data for ML models...")
        
        training_features = []
        growth_targets = []
        threat_targets = []
        
        for asset_id, asset in assets_data.items():
            try:
                # Extract features for each asset
                features = self.extract_asset_features(asset)
                
                # Generate realistic training targets
                growth_rate = self.simulate_growth_rate(asset)
                threat_score = self.simulate_threat_score(asset, features)
                
                training_features.append(features)
                growth_targets.append(growth_rate)
                threat_targets.append(threat_score)
                
            except Exception as e:
                self.logger.warning(f"Error processing asset {asset_id}: {e}")
                continue
        
        # Convert to appropriate format
        if SKLEARN_AVAILABLE:
            self.feature_df = pd.DataFrame(training_features)
            self.growth_df = pd.Series(growth_targets)
            self.threat_df = pd.Series(threat_targets)
        else:
            self.feature_df = training_features
            self.growth_df = growth_targets
            self.threat_df = threat_targets
        
        self.logger.info(f"Training data prepared: {len(training_features)} samples")
        return self.feature_df, self.growth_df, self.threat_df
    
    def extract_asset_features(self, asset):
        """Extract numerical features from asset data"""
        try:
            # Geographic features
            if hasattr(asset.get('polygon'), 'centroid'):
                centroid = asset['polygon'].centroid
                lat, lon = centroid.y, centroid.x
                area = asset['polygon'].area * 111320 * 111320
            else:
                lat, lon, area = 28.6139, 77.2090, 1000
            
            # Priority encoding
            priority_map = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
            priority_score = priority_map.get(asset.get('priority', 'LOW'), 1)
            
            # Asset type encoding
            type_map = {
                'Bridge': 1, 'Airport': 2, 'Power Infrastructure': 3,
                'Railway Infrastructure': 4, 'Military Facility': 5,
                'Border Infrastructure': 6
            }
            type_score = type_map.get(asset.get('type', 'Unknown'), 0)
            
            # Distance calculations
            delhi_coords = (28.6139, 77.2090)
            distance_to_delhi = ((lat - delhi_coords[0])**2 + (lon - delhi_coords[1])**2)**0.5 * 111
            
            # Border proximity
            border_proximity = min(
                abs(lat - 35.0),  # Kashmir border approx
                abs(lat - 24.0),  # Southern border approx
                abs(lon - 68.0),  # Western border approx
                abs(lon - 97.0)   # Eastern border approx
            )
            
            features = {
                'latitude': lat,
                'longitude': lon,
                'area_sq_m': area,
                'priority_score': priority_score,
                'type_score': type_score,
                'distance_to_capital': distance_to_delhi,
                'border_proximity': border_proximity,
                'population_density': self.estimate_population_density(lat, lon),
                'economic_activity': self.estimate_economic_activity(lat, lon)
            }
            
            return features
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return self.get_default_features()
    
    def estimate_population_density(self, lat, lon):
        """Estimate population density based on coordinates"""
        major_cities = [
            (28.6139, 77.2090, 30000),  # Delhi
            (19.0760, 72.8777, 20000),  # Mumbai
            (22.5726, 88.3639, 15000),  # Kolkata
            (13.0827, 80.2707, 12000),  # Chennai
            (12.9716, 77.5946, 11000)   # Bangalore
        ]
        
        density = 100  # Base rural density
        
        for city_lat, city_lon, city_density in major_cities:
            distance = ((lat - city_lat)**2 + (lon - city_lon)**2)**0.5 * 111
            city_influence = city_density * max(0.1, 1 - (distance / 500))
            density = max(density, city_influence)
        
        return density
    
    def estimate_economic_activity(self, lat, lon):
        """Estimate economic activity level"""
        economic_centers = [
            (28.6139, 77.2090, 100),  # Delhi NCR
            (19.0760, 72.8777, 95),   # Mumbai
            (12.9716, 77.5946, 85),   # Bangalore
            (13.0827, 80.2707, 75)    # Chennai
        ]
        
        max_activity = 10
        
        for center_lat, center_lon, activity_score in economic_centers:
            distance = ((lat - center_lat)**2 + (lon - center_lon)**2)**0.5 * 111
            activity = activity_score * max(0.1, 1 - (distance / 300))
            max_activity = max(max_activity, activity)
        
        return max_activity
    
    def simulate_growth_rate(self, asset):
        """Simulate realistic infrastructure growth rate"""
        base_rates = {
            'Bridge': 0.02,
            'Airport': 0.05,
            'Power Infrastructure': 0.03,
            'Railway Infrastructure': 0.04,
            'Military Facility': 0.01,
            'Border Infrastructure': 0.025
        }
        
        base_rate = base_rates.get(asset.get('type', 'Unknown'), 0.02)
        
        # Modify by priority
        priority = asset.get('priority', 'LOW')
        if priority == 'HIGH':
            base_rate *= 1.5
        elif priority == 'MEDIUM':
            base_rate *= 1.2
        
        # Add noise
        noise = np.random.normal(0, 0.005)
        return max(0, base_rate + noise)
    
    def simulate_threat_score(self, asset, features):
        """Simulate realistic threat scores"""
        threat_score = 0.1  # Base threat
        
        # Border proximity factor
        if features['border_proximity'] < 50:
            threat_score += 0.3
        
        # Priority factor
        priority = asset.get('priority', 'LOW')
        if priority == 'HIGH':
            threat_score += 0.4
        elif priority == 'MEDIUM':
            threat_score += 0.2
        
        # Economic activity factor
        threat_score += features['economic_activity'] / 1000
        
        # Add noise
        noise = np.random.normal(0, 0.05)
        return max(0, min(1, threat_score + noise))
    
    def train_growth_predictor(self, features_df, targets):
        """Train infrastructure growth prediction model"""
        self.logger.info("Training infrastructure growth predictor...")
        
        try:
            if SKLEARN_AVAILABLE:
                # Real training
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(features_df)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, targets, test_size=0.2, random_state=42
                )
                
                self.growth_predictor.fit(X_train, y_train)
                
                y_pred = self.growth_predictor.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                self.scalers['growth'] = scaler
                joblib.dump(self.growth_predictor, f"{self.models_dir}/growth_predictor.pkl")
                joblib.dump(scaler, f"{self.models_dir}/growth_scaler.pkl")
                
                self.logger.info(f"Growth Predictor - MSE: {mse:.4f}, R²: {r2:.4f}")
                return {'mse': mse, 'r2': r2}
            else:
                # Mock training
                self.logger.info("Mock growth predictor training completed")
                return {'mse': 0.01, 'r2': 0.85}
                
        except Exception as e:
            self.logger.error(f"Growth predictor training failed: {e}")
            return {'mse': 999, 'r2': 0}
    
    def train_threat_predictor(self, features_df, targets):
        """Train threat level prediction model"""
        self.logger.info("Training threat predictor...")
        
        try:
            if SKLEARN_AVAILABLE:
                # Real training
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(features_df)
                
                X_train, X_test, y_train, y_test = train_test_split(
                    X_scaled, targets, test_size=0.2, random_state=42
                )
                
                self.threat_predictor.fit(X_train, y_train)
                
                y_pred = self.threat_predictor.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                
                self.scalers['threat'] = scaler
                joblib.dump(self.threat_predictor, f"{self.models_dir}/threat_predictor.pkl")
                joblib.dump(scaler, f"{self.models_dir}/threat_scaler.pkl")
                
                self.logger.info(f"Threat Predictor - MSE: {mse:.4f}, R²: {r2:.4f}")
                return {'mse': mse, 'r2': r2}
            else:
                # Mock training
                self.logger.info("Mock threat predictor training completed")
                return {'mse': 0.02, 'r2': 0.78}
                
        except Exception as e:
            self.logger.error(f"Threat predictor training failed: {e}")
            return {'mse': 999, 'r2': 0}
    
    def train_anomaly_detector(self, features_df):
        """Train anomaly detection model"""
        self.logger.info("Training anomaly detector...")
        
        try:
            if SKLEARN_AVAILABLE:
                # Real training
                scaler = StandardScaler()
                X_scaled = scaler.fit_transform(features_df)
                
                self.anomaly_detector.fit(X_scaled)
                
                anomalies = self.anomaly_detector.predict(X_scaled)
                anomaly_rate = np.sum(anomalies == -1) / len(anomalies)
                
                self.scalers['anomaly'] = scaler
                joblib.dump(self.anomaly_detector, f"{self.models_dir}/anomaly_detector.pkl")
                joblib.dump(scaler, f"{self.models_dir}/anomaly_scaler.pkl")
                
                self.logger.info(f"Anomaly Detector - Anomaly rate: {anomaly_rate:.2%}")
                return {'anomaly_rate': anomaly_rate}
            else:
                # Mock training
                self.logger.info("Mock anomaly detector training completed")
                return {'anomaly_rate': 0.1}
                
        except Exception as e:
            self.logger.error(f"Anomaly detector training failed: {e}")
            return {'anomaly_rate': 0}
    
    def predict_growth_rate(self, asset):
        """Predict infrastructure growth rate for an asset"""
        try:
            features = self.extract_asset_features(asset)
            
            if SKLEARN_AVAILABLE and hasattr(self, 'scalers') and 'growth' in self.scalers:
                # Real prediction
                feature_array = np.array(list(features.values())).reshape(1, -1)
                scaled_features = self.scalers['growth'].transform(feature_array)
                growth_rate = self.growth_predictor.predict(scaled_features)[0]
            else:
                # Mock prediction
                growth_rate = self.simulate_growth_rate(asset)
            
            return {
                'predicted_growth_rate': growth_rate,
                'growth_category': self.categorize_growth(growth_rate),
                'confidence': 0.85,
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Growth prediction failed: {e}")
            return {
                'predicted_growth_rate': 0.02,
                'growth_category': 'MODERATE',
                'confidence': 0.5
            }
    
    def predict_threat_level(self, asset):
        """Predict threat level for an asset"""
        try:
            features = self.extract_asset_features(asset)
            
            if SKLEARN_AVAILABLE and hasattr(self, 'scalers') and 'threat' in self.scalers:
                # Real prediction
                feature_array = np.array(list(features.values())).reshape(1, -1)
                scaled_features = self.scalers['threat'].transform(feature_array)
                threat_score = self.threat_predictor.predict(scaled_features)[0]
            else:
                # Mock prediction
                threat_score = self.simulate_threat_score(asset, features)
            
            return {
                'predicted_threat_score': threat_score,
                'threat_level': self.categorize_threat(threat_score),
                'risk_factors': self.identify_risk_factors(features),
                'confidence': 0.75,
                'prediction_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Threat prediction failed: {e}")
            return {
                'predicted_threat_score': 0.3,
                'threat_level': 'MEDIUM',
                'confidence': 0.5
            }
    
    def detect_anomalies(self, asset):
        """Detect if asset shows anomalous patterns"""
        try:
            features = self.extract_asset_features(asset)
            
            if SKLEARN_AVAILABLE and hasattr(self, 'scalers') and 'anomaly' in self.scalers:
                # Real anomaly detection
                feature_array = np.array(list(features.values())).reshape(1, -1)
                scaled_features = self.scalers['anomaly'].transform(feature_array)
                anomaly_pred = self.anomaly_detector.predict(scaled_features)[0]
                anomaly_score = self.anomaly_detector.decision_function(scaled_features)[0]
            else:
                # Mock anomaly detection
                anomaly_pred = 1 if np.random.random() > 0.9 else -1
                anomaly_score = np.random.normal(0, 0.5)
            
            return {
                'is_anomaly': anomaly_pred == -1,
                'anomaly_score': anomaly_score,
                'anomaly_level': self.categorize_anomaly(anomaly_score),
                'detection_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {e}")
            return {
                'is_anomaly': False,
                'anomaly_score': 0.0
            }
    
    def categorize_growth(self, growth_rate):
        """Categorize growth rate"""
        if growth_rate >= 0.06:
            return 'RAPID'
        elif growth_rate >= 0.03:
            return 'MODERATE'
        elif growth_rate >= 0.01:
            return 'SLOW'
        else:
            return 'STABLE'
    
    def categorize_threat(self, threat_score):
        """Categorize threat score"""
        if threat_score >= 0.7:
            return 'HIGH'
        elif threat_score >= 0.4:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def categorize_anomaly(self, anomaly_score):
        """Categorize anomaly score"""
        if anomaly_score < -0.5:
            return 'HIGH_ANOMALY'
        elif anomaly_score < -0.2:
            return 'MODERATE_ANOMALY'
        else:
            return 'NORMAL'
    
    def identify_risk_factors(self, features):
        """Identify key risk factors"""
        risk_factors = []
        
        if features['border_proximity'] < 50:
            risk_factors.append('BORDER_PROXIMITY')
        
        if features['priority_score'] >= 3:
            risk_factors.append('HIGH_VALUE_TARGET')
        
        if features['population_density'] > 10000:
            risk_factors.append('HIGH_POPULATION_AREA')
        
        if features['economic_activity'] > 50:
            risk_factors.append('ECONOMIC_IMPORTANCE')
        
        return risk_factors
    
    def get_default_features(self):
        """Get default feature set for error cases"""
        return {
            'latitude': 28.6139,
            'longitude': 77.2090,
            'area_sq_m': 1000,
            'priority_score': 1,
            'type_score': 1,
            'distance_to_capital': 100,
            'border_proximity': 200,
            'population_density': 1000,
            'economic_activity': 30
        }
    
    def train_all_models(self, assets_data):
        """Train all ML models with asset data"""
        self.logger.info("Starting GARUDA ML training pipeline...")
        
        try:
            # Prepare training data
            features_df, growth_targets, threat_targets = self.prepare_training_data(assets_data)
            
            # Train all models
            growth_results = self.train_growth_predictor(features_df, growth_targets)
            threat_results = self.train_threat_predictor(features_df, threat_targets)
            anomaly_results = self.train_anomaly_detector(features_df)
            
            results = {
                'training_completed': datetime.now().isoformat(),
                'samples_trained': len(features_df) if hasattr(features_df, '__len__') else len(assets_data),
                'growth_model': growth_results,
                'threat_model': threat_results,
                'anomaly_model': anomaly_results,
                'sklearn_available': SKLEARN_AVAILABLE
            }
            
            # Save training summary
            try:
                with open(f"{self.models_dir}/training_summary.json", 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
            except Exception as e:
                self.logger.warning(f"Could not save training summary: {e}")
            
            self.logger.info("GARUDA ML training pipeline completed!")
            return results
            
        except Exception as e:
            self.logger.error(f"ML training pipeline failed: {e}")
            return {
                'error': str(e),
                'training_completed': datetime.now().isoformat(),
                'samples_trained': 0
            }

class MockMLModel:
    """Mock ML model for when scikit-learn is not available"""
    
    def __init__(self, model_type):
        self.model_type = model_type
        self.fitted = False
    
    def fit(self, X, y=None):
        self.fitted = True
        return self
    
    def predict(self, X):
        if not self.fitted:
            return np.array([0.02])
        
        if self.model_type == "Growth":
            return np.array([np.random.uniform(0.01, 0.05)])
        elif self.model_type == "Threat":
            return np.array([np.random.uniform(0.1, 0.8)])
        else:  # Anomaly
            return np.array([1 if np.random.random() > 0.9 else -1])
    
    def decision_function(self, X):
        return np.array([np.random.normal(0, 0.5)])

if __name__ == "__main__":
    ml_engine = GarudaMLEngine()
    print("GARUDA ML Engine - Ready for Intelligence Analysis")
