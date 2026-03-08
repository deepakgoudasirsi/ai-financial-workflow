"""
Rule-based AML detection scenarios.

Implements AML rules for large transactions, structuring, rapid movement,
and high-risk account monitoring.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class AdaptiveThresholdCalculator:
    """
    Calculate adaptive thresholds based on transaction patterns.
    
    Uses IQR or similar methods to set dynamic thresholds per segment.
    """
    
    def __init__(self, n_segments: int = 5, method: str = 'iqr'):
        """
        Initialize adaptive threshold calculator.
        
        Args:
            n_segments: Number of segments for adaptive thresholds
            method: Outlier detection method ('iqr', 'zscore', 'mad')
        """
        self.n_segments = n_segments
        self.method = method
        self.segment_thresholds = {}
    
    def fit(self, amounts: pd.Series) -> 'AdaptiveThresholdCalculator':
        """Fit thresholds based on amount distribution."""
        segments = pd.qcut(amounts.rank(method='first'), self.n_segments, labels=False, duplicates='drop')
        for seg in range(int(segments.max()) + 1):
            seg_amounts = amounts[segments == seg]
            if len(seg_amounts) > 0:
                q1, q3 = seg_amounts.quantile(0.25), seg_amounts.quantile(0.75)
                iqr = q3 - q1
                self.segment_thresholds[seg] = float(q3 + 1.5 * iqr) if iqr > 0 else float(q3)
        return self
    
    def get_threshold(self, segment: int) -> float:
        """Get threshold for a segment."""
        return self.segment_thresholds.get(segment, 10000.0)


class AMLRuleEngine:
    """
    AML rule-based detection engine.
    
    Implements scenarios for large transactions, structuring, rapid movement,
    and high-risk account monitoring.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize rule engine.
        
        Args:
            config: Configuration with rule thresholds
        """
        self.config = config or {}
        rule_config = self.config.get('rule_engine', {})
        self.large_txn_threshold = rule_config.get('large_transaction_threshold', 10000.0)
        self.structuring_threshold = rule_config.get('structuring_threshold', 9000.0)
        self.structuring_window = rule_config.get('structuring_window', 24)
        self.rapid_movement_threshold = rule_config.get('rapid_movement_threshold', 5)
        self.rapid_movement_window = rule_config.get('rapid_movement_window', 10)
    
    def run_all_scenarios(self,
                          df: pd.DataFrame,
                          high_risk_accounts: Optional[Set[str]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Run all AML rule scenarios and return results.
        
        Args:
            df: Preprocessed transaction DataFrame
            high_risk_accounts: Set of high-risk account IDs (optional)
            
        Returns:
            Tuple of (results_df with flags, summary_df)
        """
        high_risk_accounts = high_risk_accounts or set()
        
        results = df.copy()
        results['large_txn_flag'] = self._large_transaction(df)
        results['structuring_flag'] = self._structuring(df)
        results['rapid_movement_flag'] = self._rapid_movement(df)
        results['high_risk_account_flag'] = self._high_risk_account(df, high_risk_accounts)
        
        # AML risk score (0-10 scale)
        results['aml_risk_score'] = (
            results['large_txn_flag'].astype(float) * 2.0 +
            results['structuring_flag'].astype(float) * 3.0 +
            results['rapid_movement_flag'].astype(float) * 2.0 +
            results['high_risk_account_flag'].astype(float) * 3.0
        ).clip(0, 10)
        
        results['is_suspicious'] = results['aml_risk_score'] >= 2.0
        
        # Summary
        summary_data = {
            'scenario': ['large_transaction', 'structuring', 'rapid_movement', 'high_risk_account'],
            'flagged_count': [
                results['large_txn_flag'].sum(),
                results['structuring_flag'].sum(),
                results['rapid_movement_flag'].sum(),
                results['high_risk_account_flag'].sum()
            ],
            'total_transactions': len(results)
        }
        summary_df = pd.DataFrame(summary_data)
        
        return results, summary_df
    
    def _large_transaction(self, df: pd.DataFrame) -> pd.Series:
        """Flag transactions above large transaction threshold."""
        return (df['amount'] >= self.large_txn_threshold).astype(int)
    
    def _structuring(self, df: pd.DataFrame) -> pd.Series:
        """Flag potential structuring (multiple transactions just under threshold)."""
        if 'step' not in df.columns or 'nameOrig' not in df.columns:
            return pd.Series(0, index=df.index)
        
        flags = pd.Series(0, index=df.index)
        for orig, group in df.groupby('nameOrig'):
            group = group.sort_values('step')
            if len(group) < 2:
                continue
            for i in range(len(group) - 1):
                window = group.iloc[i:i + self.structuring_window]
                total = window['amount'].sum()
                count = len(window)
                if count >= 2 and total >= self.structuring_threshold * 2:
                    avg = total / count
                    if avg < self.structuring_threshold:
                        flags.loc[window.index] = 1
        return flags
    
    def _rapid_movement(self, df: pd.DataFrame) -> pd.Series:
        """Flag rapid movement of funds."""
        if 'step' not in df.columns or 'nameOrig' not in df.columns:
            return pd.Series(0, index=df.index)
        
        flags = pd.Series(0, index=df.index)
        for orig, group in df.groupby('nameOrig'):
            group = group.sort_values('step')
            if len(group) < self.rapid_movement_threshold:
                continue
            step_diff = group['step'].diff()
            rapid = (step_diff <= self.rapid_movement_window) & (step_diff > 0)
            if rapid.sum() >= self.rapid_movement_threshold - 1:
                flags.loc[group.index] = 1
        return flags
    
    def _high_risk_account(self, df: pd.DataFrame, high_risk_accounts: Set[str]) -> pd.Series:
        """Flag transactions involving high-risk accounts."""
        if not high_risk_accounts:
            return pd.Series(0, index=df.index)
        
        orig_in = df['nameOrig'].isin(high_risk_accounts) if 'nameOrig' in df.columns else pd.Series(False, index=df.index)
        dest_in = df['nameDest'].isin(high_risk_accounts) if 'nameDest' in df.columns else pd.Series(False, index=df.index)
        return (orig_in | dest_in).astype(int)
