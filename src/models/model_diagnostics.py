"""
Model diagnostics for overfitting/underfitting detection.
"""

import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from sklearn.metrics import roc_auc_score, accuracy_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class ModelDiagnostics:
    """
    Diagnose model overfitting and underfitting.
    
    Compares train vs test performance to detect degradation.
    """
    
    def check_overfitting(self,
                          model: Any,
                          X_train: np.ndarray,
                          y_train: np.ndarray,
                          X_test: np.ndarray,
                          y_test: np.ndarray,
                          model_name: str = 'model') -> Dict[str, Any]:
        """
        Check for overfitting by comparing train vs test metrics.
        
        Returns:
            Dict with overfitting_status, performance_gaps, recommendations
        """
        if not SKLEARN_AVAILABLE:
            return {'overfitting_status': 'unknown', 'error': 'sklearn not available'}
        
        result = {'model_name': model_name}
        
        try:
            # Get predictions
            if hasattr(model, 'predict_proba'):
                train_proba = model.predict_proba(X_train)[:, 1]
                test_proba = model.predict_proba(X_test)[:, 1]
                train_auc = roc_auc_score(y_train, train_proba) if len(np.unique(y_train)) > 1 else 0.5
                test_auc = roc_auc_score(y_test, test_proba) if len(np.unique(y_test)) > 1 else 0.5
            else:
                train_pred = model.predict(X_train)
                test_pred = model.predict(X_test)
                train_auc = accuracy_score(y_train, train_pred)
                test_auc = accuracy_score(y_test, test_pred)
            
            auc_gap = train_auc - test_auc
            
            result['train_auc'] = float(train_auc)
            result['test_auc'] = float(test_auc)
            result['performance_gaps'] = {'auc': float(auc_gap)}
            
            if auc_gap > 0.1:
                result['overfitting_status'] = 'overfitting'
                result['overfitting_severity'] = 'high' if auc_gap > 0.2 else 'moderate'
                result['recommendation'] = 'Consider regularization, more data, or simpler model'
            elif auc_gap < -0.05:
                result['overfitting_status'] = 'underfitting'
                result['overfitting_severity'] = 'moderate'
                result['recommendation'] = 'Model may be too simple; consider more features or complexity'
            else:
                result['overfitting_status'] = 'healthy'
                result['overfitting_severity'] = 'none'
                result['recommendation'] = 'Train/test performance is balanced'
                
        except Exception as e:
            result['overfitting_status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def generate_diagnostic_report(self, diagnostic_results: Dict[str, Dict]) -> str:
        """Generate human-readable diagnostic report."""
        lines = ["=" * 60, "MODEL DIAGNOSTICS REPORT", "=" * 60]
        
        for model_name, diag in diagnostic_results.items():
            lines.append(f"\n{model_name}:")
            lines.append(f"  Status: {diag.get('overfitting_status', 'unknown')}")
            if 'performance_gaps' in diag:
                lines.append(f"  AUC Gap (train-test): {diag['performance_gaps'].get('auc', 'N/A')}")
            if 'recommendation' in diag:
                lines.append(f"  Recommendation: {diag['recommendation']}")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
