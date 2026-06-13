from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class BondSpec:
    coupon_rate: float          # annual coupon as decimal, e.g. 0.05 for 5%
    years_to_maturity: float    # e.g. 10
    frequency: int = 2          # coupon payments per year (1,2,4,12)
    face_value: float = 100.0

def bond_price(spec: BondSpec, ytm: float) -> float:
    """Clean price from yield to maturity (ytm as decimal, annualised).
    Discount each coupon and the final face value at ytm/frequency over
    spec.years_to_maturity*spec.frequency periods."""
    n = spec.years_to_maturity * spec.frequency
    coupon = (spec.coupon_rate * spec.face_value) / spec.frequency
    y = ytm / spec.frequency
    
    price = 0.0
    # Use integer part for the main loop
    for i in range(1, int(n) + 1):
        price += coupon / ((1 + y) ** i)
    
    # Simple model assumes integer number of periods for clean price.
    price += spec.face_value / ((1 + y) ** n)
    return price

def bond_ytm(spec: BondSpec, price: float) -> float:
    """Solve yield to maturity from a clean price using bisection on
    bond_price. Search range [-0.5, 2.0], ~100 iterations, tol 1e-8."""
    low = -0.5
    high = 2.0
    for _ in range(100):
        mid = (low + high) / 2
        if bond_price(spec, mid) > price:
            low = mid
        else:
            high = mid
        if abs(high - low) < 1e-8:
            break
    return (low + high) / 2

def macaulay_duration(spec: BondSpec, ytm: float) -> float:
    """PV-weighted average time (in years) to cash flows."""
    n = spec.years_to_maturity * spec.frequency
    coupon = (spec.coupon_rate * spec.face_value) / spec.frequency
    y = ytm / spec.frequency
    
    weighted_pv = 0.0
    total_pv = 0.0
    for i in range(1, int(n) + 1):
        t = i / spec.frequency
        pv = coupon / ((1 + y) ** i)
        weighted_pv += t * pv
        total_pv += pv
    
    # Add face value
    pv_face = spec.face_value / ((1 + y) ** n)
    weighted_pv += (n / spec.frequency) * pv_face
    total_pv += pv_face
    
    return weighted_pv / total_pv

def modified_duration(spec: BondSpec, ytm: float) -> float:
    """macaulay_duration / (1 + ytm/frequency)."""
    return macaulay_duration(spec, ytm) / (1 + ytm / spec.frequency)

def convexity(spec: BondSpec, ytm: float) -> float:
    """Standard bond convexity (in years^2)."""
    n = spec.years_to_maturity * spec.frequency
    coupon = (spec.coupon_rate * spec.face_value) / spec.frequency
    y = ytm / spec.frequency
    price = bond_price(spec, ytm)
    
    conv = 0.0
    for i in range(1, int(n) + 1):
        t = i / spec.frequency
        pv = coupon / ((1 + y) ** i)
        conv += pv * t * (t + 1/spec.frequency)
    
    pv_face = spec.face_value / ((1 + y) ** n)
    t_n = n / spec.frequency
    conv += pv_face * t_n * (t_n + 1/spec.frequency)
    
    return conv / (price * (1 + y)**2)

def dv01(spec: BondSpec, ytm: float) -> float:
    """Dollar value of 1 basis point: price change for a 1bp yield move.
    Return a positive number = abs(price(ytm) - price(ytm+0.0001))."""
    p1 = bond_price(spec, ytm)
    p2 = bond_price(spec, ytm + 0.0001)
    return abs(p1 - p2)

def current_yield(spec: BondSpec) -> float:
    """annual coupon income / face_value (since price defaults to par-based;
    actually compute coupon_amount*frequency... -> use annual coupon / price?).
    Define as: (coupon_rate*face_value) / bond_price_at_par_is_face.
    Simplest correct def: coupon_rate (annual) relative to price -- accept a
    price arg is NOT in signature, so return coupon_rate*face_value/face_value =
    coupon_rate. Keep it: return spec.coupon_rate."""
    return spec.coupon_rate

def analytics(spec: BondSpec, *, ytm: float | None = None, price: float | None = None) -> dict:
    """Convenience aggregator. Exactly one of ytm/price must be provided.
    If price given, derive ytm via bond_ytm. Return dict with keys:
    face_value, coupon_rate, years_to_maturity, frequency, ytm, price,
    macaulay_duration, modified_duration, convexity, dv01, current_yield.
    Round floats to 6 dp. Raise ValueError if neither/both of ytm,price given."""
    if (ytm is None and price is None) or (ytm is not None and price is not None):
        raise ValueError("Exactly one of ytm or price must be provided.")
    
    if ytm is None:
        ytm = bond_ytm(spec, price)
    else:
        price = bond_price(spec, ytm)
    
    res = {
        "face_value": spec.face_value,
        "coupon_rate": spec.coupon_rate,
        "years_to_maturity": spec.years_to_maturity,
        "frequency": spec.frequency,
        "ytm": round(ytm, 6),
        "price": round(price, 6),
        "macaulay_duration": round(macaulay_duration(spec, ytm), 6),
        "modified_duration": round(modified_duration(spec, ytm), 6),
        "convexity": round(convexity(spec, ytm), 6),
        "dv01": round(dv01(spec, ytm), 6),
        "current_yield": round(current_yield(spec), 6),
    }
    return res
