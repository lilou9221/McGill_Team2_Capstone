"""
Map Generators Module

Contains all code for generating interactive maps:
- Biochar suitability maps
- Soil property maps (SOC, pH, moisture)
- Municipality-level maps
- Color scheme utilities
"""

from src.map_generators.biochar_map import create_biochar_suitability_map
from src.map_generators.soc_map import create_soc_map
from src.map_generators.ph_map import create_ph_map
from src.map_generators.moisture_map import create_moisture_map
from src.map_generators.color_scheme import get_color_for_score, get_color_rgb, get_biochar_suitability_color_rgb

__all__ = [
    'create_biochar_suitability_map',
    'create_soc_map',
    'create_ph_map',
    'create_moisture_map',
    'get_color_for_score',
    'get_color_rgb',
    'get_biochar_suitability_color_rgb',
]

