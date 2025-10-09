"""Shared constants for EV charging tools."""

# Session times
AVG_SESSION_MIN_DC = 28
AVG_SESSION_MIN_AC = 75

# Trust factors by badge
TRUST_FACTOR = {
    "A": 0.9,  # Most reliable
    "B": 1.0,  # Baseline
    "C": 1.2,  # Less reliable
    "D": 1.5   # Least reliable
}

# Probability factors
RETRY_SUCCESS_PROB = 0.70
SOS_RISK_THRESHOLD = 0.70

# Points system
POINTS_EARN_DELTA = {
    "report_fault": 5,
    "slot_resale": 8,
    "purchase": 10
}

# Partner service thresholds
MIN_WAIT_FOR_PARTNER_MIN = 10