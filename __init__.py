# __init__.py

"""
FetchOmics Package

This package contains modules for processing omics data, including downloading,
converting, and aligning reads from GEO datasets.
"""

# Importing key classes or functions for easier access
from .GeoDataset import GeoDataset
from .SRRDownload import SRRDownload
from .SRRConvert import SRRConvert
from .STARAlign import STARAlign
from .utils import log_message, create_directory

__all__ = [
    "GeoDataset",
    "SRRDownload",
    "SRRConvert",
    "STARAlign",
    "log_message",
    "create_directory"
]
