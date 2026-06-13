import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class RiskManagementModel(ABC):
    @abstractmethod
    def evaluate(self, targets: dict[str, float], state: dict) -> dict[str, float]:
        """
        targets: current target weights.
        state: {'equity': float, 'peak_equity': float, 'current_weights': dict, 
                'prices': dict, 'entry_prices': dict}.
        returns adjusted target weights.
        """
        pass

class MaximumDrawdownRisk(RiskManagementModel):
    def __init__(self, max_drawdown: float = 0.2):
        self.max_drawdown = max_drawdown

    def evaluate(self, targets: dict[str, float], state: dict) -> dict[str, float]:
        equity = state.get('equity', 1.0)
        peak = state.get('peak_equity', 1.0)
        if peak > 0:
            dd = (equity / peak) - 1
            if dd <= -self.max_drawdown:
                return {} # Liquidate everything
        return targets

class MaxPositionSizeRisk(RiskManagementModel):
    def __init__(self, max_weight: float = 0.25):
        self.max_weight = max_weight

    def evaluate(self, targets: dict[str, float], state: dict) -> dict[str, float]:
        adjusted = {}
        for sym, weight in targets.items():
            if weight > self.max_weight:
                adjusted[sym] = self.max_weight
            elif weight < -self.max_weight:
                adjusted[sym] = -self.max_weight
            else:
                adjusted[sym] = weight
        return adjusted

class TrailingStopRisk(RiskManagementModel):
    def __init__(self, stop_pct: float = 0.15):
        self.stop_pct = stop_pct

    def evaluate(self, targets: dict[str, float], state: dict) -> dict[str, float]:
        current_weights = state.get('current_weights', {})
        prices = state.get('prices', {})
        entry_prices = state.get('entry_prices', {})
        
        adjusted = targets.copy()
        for sym in current_weights:
            if current_weights[sym] == 0:
                continue
            
            price = prices.get(sym)
            entry = entry_prices.get(sym)
            
            if price is None or entry is None:
                continue
                
            # Long position
            if current_weights[sym] > 0:
                if (price / entry) - 1 <= -self.stop_pct:
                    adjusted[sym] = 0.0
            # Short position
            elif current_weights[sym] < 0:
                if (price / entry) - 1 >= self.stop_pct:
                    adjusted[sym] = 0.0
                    
        return adjusted
