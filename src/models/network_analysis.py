"""
Transaction network analysis for AML.

Builds transaction graphs and detects cycles, fan patterns,
communities, and suspicious accounts.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Set, Optional, Any
import logging

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


class TransactionNetworkAnalyzer:
    """
    Analyze transaction networks for money laundering patterns.
    
    Detects cycles, fan-out/fan-in patterns, communities, and
    identifies suspicious accounts.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize network analyzer.
        
        Args:
            config: Configuration with network analysis settings
        """
        self.config = config or {}
        net_config = self.config.get('network_analysis', {})
        self.max_cycle_length = net_config.get('max_cycle_length', 10)
        self.fan_out_threshold = net_config.get('fan_out_threshold', 10)
        self.fan_in_threshold = net_config.get('fan_in_threshold', 10)
        
        self.G = None
        self._cycles = []
        self._fan_out = []
        self._fan_in = []
        self._centrality = {}
        self._communities = {}
        self._suspicious_accounts = set()
    
    def build_transaction_network(self, df: pd.DataFrame):
        """
        Build directed graph from transaction data.
        
        Args:
            df: DataFrame with nameOrig, nameDest, amount columns
            
        Returns:
            NetworkX DiGraph
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("networkx required for network analysis")
        
        self.G = nx.DiGraph()
        
        if 'nameOrig' not in df.columns or 'nameDest' not in df.columns:
            logger.warning("Missing nameOrig/nameDest columns")
            return self.G
        
        for _, row in df.iterrows():
            orig = str(row['nameOrig'])
            dest = str(row['nameDest'])
            amount = float(row.get('amount', 0))
            if self.G.has_edge(orig, dest):
                self.G[orig][dest]['weight'] += amount
                self.G[orig][dest]['count'] += 1
            else:
                self.G.add_edge(orig, dest, weight=amount, count=1)
        
        logger.info(f"Built network with {self.G.number_of_nodes()} nodes, {self.G.number_of_edges()} edges")
        return self.G
    
    def detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the transaction network (potential layering)."""
        if self.G is None or not NETWORKX_AVAILABLE:
            return []
        
        self._cycles = []
        try:
            for cycle in nx.simple_cycles(self.G):
                if len(cycle) <= self.max_cycle_length:
                    self._cycles.append(cycle)
        except Exception as e:
            logger.warning(f"Cycle detection limited: {e}")
        
        return self._cycles
    
    def detect_fan_patterns(self) -> tuple:
        """Detect fan-out and fan-in patterns."""
        if self.G is None or not NETWORKX_AVAILABLE:
            return [], []
        
        self._fan_out = [n for n in self.G.nodes() if self.G.out_degree(n) >= self.fan_out_threshold]
        self._fan_in = [n for n in self.G.nodes() if self.G.in_degree(n) >= self.fan_in_threshold]
        
        return self._fan_out, self._fan_in
    
    def calculate_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality for nodes."""
        if self.G is None or not NETWORKX_AVAILABLE:
            return {}
        
        try:
            self._centrality = nx.betweenness_centrality(self.G)
        except Exception as e:
            logger.warning(f"Centrality calculation failed: {e}")
            self._centrality = {n: 0.0 for n in self.G.nodes()}
        
        return self._centrality
    
    def detect_communities(self) -> Dict[str, int]:
        """Detect communities using label propagation."""
        if self.G is None or not NETWORKX_AVAILABLE:
            return {}
        
        try:
            undirected = self.G.to_undirected()
            communities = nx.community.label_propagation_communities(undirected)
            self._communities = {}
            for i, comm in enumerate(communities):
                for node in comm:
                    self._communities[node] = i
        except Exception as e:
            logger.warning(f"Community detection failed: {e}")
            self._communities = {n: 0 for n in self.G.nodes()}
        
        return self._communities
    
    def identify_suspicious_accounts(self) -> Set[str]:
        """Identify accounts that appear in cycles, fan patterns, or have high centrality."""
        if self.G is None:
            return set()
        
        self.detect_cycles()
        self.detect_fan_patterns()
        self.calculate_centrality()
        
        suspicious = set()
        for cycle in self._cycles:
            suspicious.update(cycle)
        suspicious.update(self._fan_out)
        suspicious.update(self._fan_in)
        
        if self._centrality:
            high_centrality = sorted(
                self._centrality.items(),
                key=lambda x: x[1],
                reverse=True
            )[:max(100, self.G.number_of_nodes() // 10)]
            suspicious.update(n for n, _ in high_centrality)
        
        self._suspicious_accounts = suspicious
        return self._suspicious_accounts
    
    def flag_suspicious_transactions(self,
                                    df: pd.DataFrame,
                                    suspicious_accounts: Set[str]) -> pd.Series:
        """Flag transactions involving suspicious accounts."""
        if not suspicious_accounts:
            return pd.Series(0, index=df.index)
        
        orig_flag = df['nameOrig'].astype(str).isin(suspicious_accounts) if 'nameOrig' in df.columns else pd.Series(False, index=df.index)
        dest_flag = df['nameDest'].astype(str).isin(suspicious_accounts) if 'nameDest' in df.columns else pd.Series(False, index=df.index)
        return (orig_flag | dest_flag).astype(int)
    
    def visualize_network(self,
                          highlight_nodes: Optional[List[str]] = None,
                          highlight_communities: bool = False,
                          filename: str = 'transaction_network.png') -> None:
        """Visualize the transaction network."""
        if self.G is None or not NETWORKX_AVAILABLE:
            return
        
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(12, 10))
            pos = nx.spring_layout(self.G, k=0.5, iterations=50, seed=42)
            
            node_colors = ['red' if n in (highlight_nodes or []) else 'lightblue' for n in self.G.nodes()]
            nx.draw(self.G, pos, node_color=node_colors, node_size=50, with_labels=False, arrows=True)
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info(f"Network visualization saved to {filename}")
        except Exception as e:
            logger.warning(f"Network visualization failed: {e}")
