"""
Technical analysis package for stock market analysis.

This package provides modules for computing technical indicators,
detecting cyclical patterns, generating trade recommendations,
and creating visualizations.
"""

from analysis.technical import compute_indicators
from analysis.cyclical import detect_cyclicality
from analysis.recommendations import generate_recommendation
from analysis.charts import generate_charts

__all__ = [
    "compute_indicators",
    "detect_cyclicality",
    "generate_recommendation",
    "generate_charts",
]
