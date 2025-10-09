"""Color band mapping (green/amber/red) based on thresholds."""

from apps.backend.app.config import SETTINGS

def band_from_minutes(expected_start_min: float, bands: str | None = None) -> str:
    """Map expected start time to a color band.
    
    Args:
        expected_start_min: Expected start time in minutes
        bands: Optional override for band thresholds (format: "low,high")
    
    Returns:
        "green", "amber", or "red" based on thresholds
    """
    # Use provided bands or default from settings
    band_str = bands if bands is not None else SETTINGS.COLOR_BANDS
    
    try:
        # Parse thresholds
        low, high = map(float, band_str.split(","))
        
        # Map to color bands
        if expected_start_min <= low:
            return "green"
        elif expected_start_min <= high:
            return "amber"
        else:
            return "red"
            
    except (ValueError, AttributeError):
        # On any parsing error, use conservative defaults
        if expected_start_min <= 10:
            return "green"
        elif expected_start_min <= 25:
            return "amber"
        else:
            return "red"