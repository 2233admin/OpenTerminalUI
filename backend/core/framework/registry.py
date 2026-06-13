from backend.core.framework.alpha_models import MomentumAlpha, MeanReversionAlpha, RsiAlpha
from backend.core.framework.portfolio_construction import EqualWeighting, InsightWeighting, MeanVarianceOptimization
from backend.core.framework.risk_management import MaximumDrawdownRisk, MaxPositionSizeRisk, TrailingStopRisk

def list_models() -> dict:
    return {
        'alpha': [
            {
                'id': 'momentum',
                'label': 'Momentum Alpha',
                'params': [{'key': 'lookback_days', 'label': 'Lookback Days', 'type': 'int', 'default': 63}]
            },
            {
                'id': 'mean_reversion',
                'label': 'Mean Reversion Alpha',
                'params': [
                    {'key': 'lookback_days', 'label': 'Lookback Days', 'type': 'int', 'default': 21},
                    {'key': 'z_entry', 'label': 'Z-Score Entry', 'type': 'float', 'default': 1.0}
                ]
            },
            {
                'id': 'rsi',
                'label': 'RSI Alpha',
                'params': [
                    {'key': 'period', 'label': 'RSI Period', 'type': 'int', 'default': 14},
                    {'key': 'low', 'label': 'Low Threshold', 'type': 'float', 'default': 30.0},
                    {'key': 'high', 'label': 'High Threshold', 'type': 'float', 'default': 70.0}
                ]
            }
        ],
        'portfolio_construction': [
            {'id': 'equal', 'label': 'Equal Weighting', 'params': []},
            {'id': 'insight', 'label': 'Insight Weighting', 'params': []},
            {
                'id': 'mean_variance',
                'label': 'Mean Variance Optimization',
                'params': [{'key': 'lookback_days', 'label': 'Lookback Days', 'type': 'int', 'default': 126}]
            }
        ],
        'risk': [
            {
                'id': 'max_drawdown',
                'label': 'Maximum Drawdown Risk',
                'params': [{'key': 'max_drawdown', 'label': 'Max Drawdown %', 'type': 'float', 'default': 0.2}]
            },
            {
                'id': 'max_position',
                'label': 'Max Position Size Risk',
                'params': [{'key': 'max_weight', 'label': 'Max Weight', 'type': 'float', 'default': 0.25}]
            },
            {
                'id': 'trailing_stop',
                'label': 'Trailing Stop Risk',
                'params': [{'key': 'stop_pct', 'label': 'Stop %', 'type': 'float', 'default': 0.15}]
            }
        ]
    }

def build_alpha(spec: dict):
    model_id = spec.get('id')
    params = spec.get('params', {})
    if model_id == 'momentum':
        return MomentumAlpha(**params)
    elif model_id == 'mean_reversion':
        return MeanReversionAlpha(**params)
    elif model_id == 'rsi':
        return RsiAlpha(**params)
    raise ValueError(f"Unknown alpha model id: {model_id}")

def build_portfolio_construction(spec: dict):
    model_id = spec.get('id')
    params = spec.get('params', {})
    if model_id == 'equal':
        return EqualWeighting()
    elif model_id == 'insight':
        return InsightWeighting()
    elif model_id == 'mean_variance':
        return MeanVarianceOptimization(**params)
    raise ValueError(f"Unknown portfolio construction model id: {model_id}")

def build_risk(specs: list[dict]):
    models = []
    for spec in specs:
        model_id = spec.get('id')
        params = spec.get('params', {})
        if model_id == 'max_drawdown':
            models.append(MaximumDrawdownRisk(**params))
        elif model_id == 'max_position':
            models.append(MaxPositionSizeRisk(**params))
        elif model_id == 'trailing_stop':
            models.append(TrailingStopRisk(**params))
        else:
            raise ValueError(f"Unknown risk model id: {model_id}")
    return models
