"""
Processing pipelines for entry and indoor monitoring.
"""
from .entry_pipeline import EntryPipeline
from .indoor_pipeline import IndoorPipeline

__all__ = ["EntryPipeline", "IndoorPipeline"]
