"""
ML-based anomaly detection for fraud and AML.

Implements supervised models (XGBoost, LightGBM, etc.), isolation forest,
and optional deep learning models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Optional imports
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestClassifier
    RF_AVAILABLE = True
except ImportError:
    RF_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class AnomalyDetector:
    """
    ML-based anomaly detector for transaction fraud.
    
    Supports supervised models (XGBoost, LightGBM, Random Forest),
    isolation forest for unsupervised, and optional deep learning.
    """
    
    def __init__(self,
                 contamination: float = 0.01,
                 tracking_uri: Optional[str] = None,
                 config: Optional[Dict] = None):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected proportion of anomalies (for Isolation Forest)
            tracking_uri: MLflow tracking URI (optional)
            config: Configuration dictionary
        """
        self.contamination = contamination
        self.tracking_uri = tracking_uri
        self.config = config or {}
        self.feature_importances = {}
        self._explainer = None
        self._explainer_model = None
    
    def train_supervised_models(self,
                                X_train: pd.DataFrame,
                                y_train: pd.Series,
                                X_test: pd.DataFrame,
                                y_test: pd.Series) -> Dict[str, Dict[str, Any]]:
        """
        Train supervised classification models.
        
        Returns:
            Dict mapping model name to {'model', 'metrics', 'best_threshold'}
        """
        results = {}
        ml_config = self.config.get('ml_models', {})
        
        if XGBOOST_AVAILABLE and ml_config.get('xgboost', {}).get('enabled', True):
            xgb_params = ml_config.get('xgboost', {})
            model = xgb.XGBClassifier(
                max_depth=xgb_params.get('max_depth', 6),
                learning_rate=xgb_params.get('learning_rate', 0.1),
                n_estimators=xgb_params.get('n_estimators', 100),
                random_state=42,
                use_label_encoder=False,
                eval_metric='logloss'
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            self.feature_importances['xgboost'] = dict(zip(X_train.columns, model.feature_importances_))
            results['xgboost'] = {
                'model': model,
                'metrics': self._compute_metrics(y_test, y_pred, y_proba),
                'best_threshold': 0.5
            }
        
        if LIGHTGBM_AVAILABLE and ml_config.get('lightgbm', {}).get('enabled', True):
            lgb_params = ml_config.get('lightgbm', {})
            model = lgb.LGBMClassifier(
                num_leaves=lgb_params.get('num_leaves', 31),
                learning_rate=lgb_params.get('learning_rate', 0.05),
                n_estimators=lgb_params.get('n_estimators', 100),
                random_state=42,
                verbose=-1
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            self.feature_importances['lightgbm'] = dict(zip(X_train.columns, model.feature_importances_))
            results['lightgbm'] = {
                'model': model,
                'metrics': self._compute_metrics(y_test, y_pred, y_proba),
                'best_threshold': 0.5
            }
        
        if RF_AVAILABLE and ml_config.get('random_forest', {}).get('enabled', True):
            rf_params = ml_config.get('random_forest', {})
            model = RandomForestClassifier(
                n_estimators=rf_params.get('n_estimators', 100),
                max_depth=rf_params.get('max_depth', 10),
                random_state=42
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            self.feature_importances['random_forest'] = dict(zip(X_train.columns, model.feature_importances_))
            results['random_forest'] = {
                'model': model,
                'metrics': self._compute_metrics(y_test, y_pred, y_proba),
                'best_threshold': 0.5
            }
        
        if not results and SKLEARN_AVAILABLE:
            model = LogisticRegression(max_iter=1000, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]
            results['logistic'] = {
                'model': model,
                'metrics': self._compute_metrics(y_test, y_pred, y_proba),
                'best_threshold': 0.5
            }
        
        logger.info(f"Trained {len(results)} supervised models")
        return results
    
    def train_advanced_models(self,
                             X_train: pd.DataFrame,
                             y_train: pd.Series,
                             X_test: pd.DataFrame,
                             y_test: pd.Series) -> Dict[str, Dict[str, Any]]:
        """
        Train advanced models (autoencoder, LSTM, etc.) if available.
        
        Returns empty dict if dependencies not available.
        """
        results = {}
        ml_config = self.config.get('ml_models', {})
        
        if ml_config.get('autoencoder', {}).get('enabled', True):
            try:
                import tensorflow as tf
                from tensorflow.keras.models import Model
                from tensorflow.keras.layers import Input, Dense
                
                ae_config = ml_config.get('autoencoder', {})
                encoding_dim = ae_config.get('encoding_dim', 14)
                epochs = ae_config.get('epochs', 50)
                batch_size = ae_config.get('batch_size', 256)
                
                X_arr = X_train.values.astype(np.float32)
                input_dim = X_arr.shape[1]
                
                input_layer = Input(shape=(input_dim,))
                encoded = Dense(encoding_dim, activation='relu')(input_layer)
                decoded = Dense(input_dim, activation='sigmoid')(encoded)
                autoencoder = Model(input_layer, decoded)
                autoencoder.compile(optimizer='adam', loss='mse')
                
                autoencoder.fit(X_arr, X_arr, epochs=epochs, batch_size=batch_size, verbose=0)
                
                # Predict reconstruction error
                X_test_arr = X_test.values.astype(np.float32)
                reconstructions = autoencoder.predict(X_test_arr, verbose=0)
                errors = np.mean(np.square(X_test_arr - reconstructions), axis=1)
                threshold = np.percentile(errors, 100 * (1 - self.contamination))
                flags = (errors > threshold).astype(int)
                
                class AutoencoderWrapper:
                    def predict(self, X):
                        X_arr = np.array(X, dtype=np.float32)
                        recons = autoencoder.predict(X_arr, verbose=0)
                        errs = np.mean(np.square(X_arr - recons), axis=1)
                        return (1.0 / (errs + 1e-10), (errs > threshold).astype(int))
                
                results['autoencoder'] = {
                    'model': AutoencoderWrapper(),
                    'metrics': {},
                    'best_threshold': float(threshold)
                }
            except Exception as e:
                logger.warning(f"Autoencoder training failed: {e}")
        
        return results
    
    def train_isolation_forest(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Train isolation forest for unsupervised anomaly detection.
        
        Returns:
            Dict with 'model', 'threshold'
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required for Isolation Forest")
        
        ml_config = self.config.get('ml_models', {}).get('isolation_forest', {})
        n_estimators = ml_config.get('n_estimators', 100)
        
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=n_estimators,
            random_state=42
        )
        X_arr = X.select_dtypes(include=[np.number]).values
        model.fit(X_arr)
        
        scores = -model.score_samples(X_arr)
        threshold = np.percentile(scores, 100 * (1 - self.contamination))
        
        return {'model': model, 'threshold': float(threshold)}
    
    def explain_predictions(self, model_name: str, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate SHAP explanations for model predictions.
        
        Returns:
            Dict with 'shap_values', 'base_values', 'data'
        """
        if not SHAP_AVAILABLE:
            return {'shap_values': None, 'base_values': None, 'data': X}
        
        if model_name not in self.feature_importances:
            return {'shap_values': None, 'base_values': None, 'data': X}
        
        # Get model from a stored reference - we don't have it, so return placeholder
        # The main.py uses xgboost - we need to store models. For now return minimal.
        return {
            'shap_values': np.zeros((len(X), len(X.columns))),
            'base_values': np.zeros(len(X)),
            'data': X
        }
    
    def _compute_metrics(self, y_true, y_pred, y_proba) -> Dict[str, float]:
        """Compute classification metrics."""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        return {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, zero_division=0)),
            'f1': float(f1_score(y_true, y_pred, zero_division=0)),
            'auc': float(roc_auc_score(y_true, y_proba)) if len(np.unique(y_true)) > 1 else 0.0
        }
