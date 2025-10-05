"""
Dataset Manager for Saving and Loading Ragas Datasets

This module provides functionality to save and load Ragas datasets
to avoid regenerating them every time.
"""

import os
import json
import pandas as pd
from typing import Optional, Dict, Any
from ragas.testset import TestsetGenerator
from ragas import EvaluationDataset
from langchain_core.documents import Document


class DatasetManager:
    """
    Manages saving and loading of Ragas datasets.
    """
    
    def __init__(self, data_dir: str = "saved_datasets"):
        """
        Initialize the DatasetManager.
        
        Args:
            data_dir: Directory to save/load datasets
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def save_dataset(self, dataset, dataset_name: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Save a Ragas dataset to disk.
        
        Args:
            dataset: The Ragas dataset to save
            dataset_name: Name for the dataset (will be used as filename)
            metadata: Optional metadata to save with the dataset
        """
        # Convert dataset to pandas DataFrame
        df = dataset.to_pandas()
        
        # Create filename
        csv_filename = f"{dataset_name}.csv"
        metadata_filename = f"{dataset_name}_metadata.json"
        
        csv_path = os.path.join(self.data_dir, csv_filename)
        metadata_path = os.path.join(self.data_dir, metadata_filename)
        
        # Save the dataset as CSV
        df.to_csv(csv_path, index=False)
        print(f"Dataset saved to: {csv_path}")
        
        # Save metadata if provided
        if metadata:
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"Metadata saved to: {metadata_path}")
        
        return csv_path, metadata_path
    
    def load_dataset(self, dataset_name: str) -> EvaluationDataset:
        """
        Load a saved Ragas dataset from disk.
        
        Args:
            dataset_name: Name of the dataset to load
            
        Returns:
            Ragas EvaluationDataset object
        """
        csv_filename = f"{dataset_name}.csv"
        csv_path = os.path.join(self.data_dir, csv_filename)
        
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found: {csv_path}")
        
        # Load the CSV file
        df = pd.read_csv(csv_path)
        
        # Convert back to Ragas EvaluationDataset
        dataset = EvaluationDataset.from_pandas(df)
        
        print(f"Dataset loaded from: {csv_path}")
        print(f"Dataset contains {len(dataset)} samples")
        
        return dataset
    
    def list_saved_datasets(self) -> list:
        """
        List all saved datasets.
        
        Returns:
            List of dataset names
        """
        if not os.path.exists(self.data_dir):
            return []
        
        datasets = []
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.csv') and not filename.endswith('_metadata.json'):
                dataset_name = filename.replace('.csv', '')
                datasets.append(dataset_name)
        
        return datasets
    
    def delete_dataset(self, dataset_name: str):
        """
        Delete a saved dataset.
        
        Args:
            dataset_name: Name of the dataset to delete
        """
        csv_filename = f"{dataset_name}.csv"
        metadata_filename = f"{dataset_name}_metadata.json"
        
        csv_path = os.path.join(self.data_dir, csv_filename)
        metadata_path = os.path.join(self.data_dir, metadata_filename)
        
        files_deleted = []
        
        if os.path.exists(csv_path):
            os.remove(csv_path)
            files_deleted.append(csv_path)
        
        if os.path.exists(metadata_path):
            os.remove(metadata_path)
            files_deleted.append(metadata_path)
        
        if files_deleted:
            print(f"Deleted files: {files_deleted}")
        else:
            print(f"No files found for dataset: {dataset_name}")
    
    def get_dataset_info(self, dataset_name: str) -> Dict[str, Any]:
        """
        Get information about a saved dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Dictionary with dataset information
        """
        csv_filename = f"{dataset_name}.csv"
        metadata_filename = f"{dataset_name}_metadata.json"
        
        csv_path = os.path.join(self.data_dir, csv_filename)
        metadata_path = os.path.join(self.data_dir, metadata_filename)
        
        info = {
            "dataset_name": dataset_name,
            "csv_path": csv_path,
            "exists": os.path.exists(csv_path)
        }
        
        if info["exists"]:
            # Get CSV file info
            df = pd.read_csv(csv_path)
            info.update({
                "num_samples": len(df),
                "columns": list(df.columns),
                "file_size": os.path.getsize(csv_path)
            })
        
        # Get metadata if exists
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            info["metadata"] = metadata
        
        return info


# Convenience functions for quick usage
def save_ragas_dataset(dataset, dataset_name: str, data_dir: str = "saved_datasets", **metadata):
    """
    Quick function to save a Ragas dataset.
    
    Args:
        dataset: The Ragas dataset to save
        dataset_name: Name for the dataset
        data_dir: Directory to save the dataset
        **metadata: Additional metadata to save
    """
    manager = DatasetManager(data_dir)
    return manager.save_dataset(dataset, dataset_name, metadata)


def load_ragas_dataset(dataset_name: str, data_dir: str = "saved_datasets") -> EvaluationDataset:
    """
    Quick function to load a Ragas dataset.
    
    Args:
        dataset_name: Name of the dataset to load
        data_dir: Directory where the dataset is saved
        
    Returns:
        Ragas EvaluationDataset object
    """
    manager = DatasetManager(data_dir)
    return manager.load_dataset(dataset_name)


def list_ragas_datasets(data_dir: str = "saved_datasets") -> list:
    """
    Quick function to list saved datasets.
    
    Args:
        data_dir: Directory to look for datasets
        
    Returns:
        List of dataset names
    """
    manager = DatasetManager(data_dir)
    return manager.list_saved_datasets()
