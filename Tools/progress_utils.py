#!/usr/bin/env python3
"""
Progress Bar Utilities for SecIDS-CNN.

Provides standardized progress bars for various operations including:
- Data loading and processing
- Model training
- File conversion
- Live capture windows
- Batch predictions
"""

from tqdm import tqdm
import sys
import time


class ProgressBar:
    """Wrapper for tqdm progress bars with consistent styling."""
    
    def __init__(self, total, description="Processing", unit="it", colour=None):
        """
        Initialize progress bar.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
            unit: Unit name for items (e.g., 'files', 'packets', 'epochs')
            colour: Progress bar color ('green', 'blue', 'red', 'yellow', etc.)
        """
        self.pbar = tqdm(
            total=total,
            desc=description,
            unit=unit,
            ncols=100,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} ({percentage:3.0f}%) [{elapsed}<{remaining}]',
            colour=colour,
            file=sys.stdout
        )
    
    def update(self, n=1):
        """Update progress by n steps."""
        self.pbar.update(n)
    
    def set_description(self, desc):
        """Update the description."""
        self.pbar.set_description(desc)
    
    def set_postfix(self, **kwargs):
        """Set postfix values (e.g., loss=0.5, acc=0.95)."""
        self.pbar.set_postfix(**kwargs)
    
    def close(self):
        """Close the progress bar."""
        self.pbar.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


class DataLoadingProgress:
    """Progress bar for data loading operations."""
    
    @staticmethod
    def create(total_files):
        return ProgressBar(total_files, "Loading data files", "files", "blue")


class PreprocessingProgress:
    """Progress bar for data preprocessing operations."""
    
    @staticmethod
    def create(total_steps):
        return ProgressBar(total_steps, "Preprocessing data", "steps", "cyan")


class TrainingProgress:
    """Progress bar for model training operations."""
    
    @staticmethod
    def create(total_epochs):
        return ProgressBar(total_epochs, "Training model", "epochs", "green")


class PredictionProgress:
    """Progress bar for model prediction operations."""
    
    @staticmethod
    def create(total_batches):
        return ProgressBar(total_batches, "Making predictions", "batches", "yellow")


class FileConversionProgress:
    """Progress bar for file conversion operations."""
    
    @staticmethod
    def create(total_files):
        return ProgressBar(total_files, "Converting files", "files", "magenta")


class CaptureProgress:
    """Progress bar for live capture windows."""
    
    @staticmethod
    def create(total_windows):
        return ProgressBar(total_windows, "Capturing windows", "windows", "green")


class FlowProcessingProgress:
    """Progress bar for network flow processing."""
    
    @staticmethod
    def create(total_flows):
        return ProgressBar(total_flows, "Processing flows", "flows", "blue")


def simple_progress_bar(iterable, description="Processing", unit="it", colour="blue"):
    """
    Simple wrapper for tqdm on an iterable.
    
    Args:
        iterable: Iterable to wrap
        description: Operation description
        unit: Unit name
        colour: Bar colour
    
    Returns:
        tqdm iterator
    """
    return tqdm(
        iterable,
        desc=description,
        unit=unit,
        ncols=100,
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
        colour=colour,
        file=sys.stdout
    )


def indeterminate_progress(description="Processing", interval=0.1):
    """
    Create an indeterminate progress spinner for unknown duration tasks.
    
    Args:
        description: Task description
        interval: Update interval in seconds
    
    Returns:
        tqdm instance
    """
    return tqdm(
        desc=description,
        bar_format='{desc}: {elapsed}',
        ncols=100,
        file=sys.stdout
    )


class MultiStageProgress:
    """Progress tracking for multi-stage operations."""
    
    def __init__(self, stages):
        """
        Initialize multi-stage progress.
        
        Args:
            stages: List of (stage_name, total_items) tuples
        """
        self.stages = stages
        self.current_stage = 0
        self.total_stages = len(stages)
        self.current_pbar = None
        self._start_next_stage()
    
    def _start_next_stage(self):
        """Start the next stage."""
        if self.current_pbar:
            self.current_pbar.close()
        
        if self.current_stage < self.total_stages:
            stage_name, total_items = self.stages[self.current_stage]
            desc = f"[{self.current_stage + 1}/{self.total_stages}] {stage_name}"
            self.current_pbar = ProgressBar(total_items, desc, "items", "green")
        else:
            self.current_pbar = None
    
    def update(self, n=1):
        """Update current stage progress."""
        if self.current_pbar:
            self.current_pbar.update(n)
    
    def next_stage(self):
        """Move to next stage."""
        self.current_stage += 1
        self._start_next_stage()
    
    def finish(self):
        """Finish all stages and close."""
        if self.current_pbar:
            self.current_pbar.close()
            self.current_pbar = None


# Convenience context managers
class ProgressContext:
    """Generic progress context for with statements."""
    
    def __init__(self, total, description="Processing", unit="it", colour="blue"):
        self.total = total
        self.description = description
        self.unit = unit
        self.colour = colour
        self.pbar = None
    
    def __enter__(self):
        self.pbar = ProgressBar(self.total, self.description, self.unit, self.colour)
        return self.pbar
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pbar:
            self.pbar.close()
        return False


if __name__ == '__main__':
    # Test progress bars
    print("Testing Progress Bar Utilities...\n")
    
    # Test 1: Simple data loading
    print("Test 1: Data Loading")
    with DataLoadingProgress.create(5) as pbar:
        for i in range(5):
            time.sleep(0.3)
            pbar.update()
    
    # Test 2: Training progress
    print("\nTest 2: Model Training")
    with TrainingProgress.create(10) as pbar:
        for epoch in range(10):
            time.sleep(0.2)
            pbar.set_postfix(loss=0.5/(epoch+1), accuracy=0.9+epoch*0.01)
            pbar.update()
    
    # Test 3: Multi-stage progress
    print("\nTest 3: Multi-stage Operation")
    stages = [
        ("Loading data", 3),
        ("Preprocessing", 5),
        ("Training", 4)
    ]
    multi = MultiStageProgress(stages)
    for stage_idx in range(len(stages)):
        for item in range(stages[stage_idx][1]):
            time.sleep(0.1)
            multi.update()
        if stage_idx < len(stages) - 1:
            multi.next_stage()
    multi.finish()
    
    print("\n✓ All tests completed!")
