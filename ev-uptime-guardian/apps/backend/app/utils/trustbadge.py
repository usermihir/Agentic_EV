"""Trust badge calculation and mapping utilities."""

def station_trust_badge(badges: list[str]) -> str:
    """Return the 'worst' (highest trust factor) among connector badges.
    
    Args:
        badges: List of connector trust badges ('A'-'D')
        
    Returns:
        Trust badge letter, defaulting to 'D' for unknown/missing badges
    """
    # Define badge order (A=best, D=worst)
    order = {"A": 0, "B": 1, "C": 2, "D": 3}
    
    # Return worst (highest order value) badge, defaulting unknown to D
    return max(badges, key=lambda b: order.get(b, 3))