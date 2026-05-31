"""Model registry for managing simulation models."""

from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelMetadata:
    """Metadata for a registered model."""
    name: str
    version: str
    description: str
    model_class: Type
    created_at: datetime
    parameters: Dict[str, Any]


class ModelRegistry:
    """Model registry for managing simulation models.
    
    This class provides a central registry for simulation models, allowing
    models to be registered, discovered, and loaded dynamically.
    """
    
    def __init__(self):
        """Initialize model registry."""
        self._models: Dict[str, ModelMetadata] = {}
        self._versions: Dict[str, List[str]] = {}
    
    def register(
        self,
        name: str,
        model_class: Type,
        version: str = "1.0.0",
        description: str = "",
        parameters: Optional[Dict[str, Any]] = None,
    ):
        """Register a model.
        
        Args:
            name: Model name
            model_class: Model class
            version: Model version
            description: Model description
            parameters: Default model parameters
        """
        metadata = ModelMetadata(
            name=name,
            version=version,
            description=description,
            model_class=model_class,
            created_at=datetime.now(),
            parameters=parameters or {},
        )
        
        self._models[name] = metadata
        
        # Track versions
        if name not in self._versions:
            self._versions[name] = []
        if version not in self._versions[name]:
            self._versions[name].append(version)
    
    def get(self, name: str) -> Optional[Type]:
        """Get a model class by name.
        
        Args:
            name: Model name
            
        Returns:
            Model class or None if not found
        """
        metadata = self._models.get(name)
        if metadata:
            return metadata.model_class
        return None
    
    def get_metadata(self, name: str) -> Optional[ModelMetadata]:
        """Get model metadata by name.
        
        Args:
            name: Model name
            
        Returns:
            Model metadata or None if not found
        """
        return self._models.get(name)
    
    def list_models(self) -> List[str]:
        """List all registered model names.
        
        Returns:
            List of model names
        """
        return list(self._models.keys())
    
    def get_versions(self, name: str) -> List[str]:
        """Get all versions of a model.
        
        Args:
            name: Model name
            
        Returns:
            List of version strings
        """
        return self._versions.get(name, [])
    
    def get_latest_version(self, name: str) -> Optional[str]:
        """Get the latest version of a model.
        
        Args:
            name: Model name
            
        Returns:
            Latest version string or None if not found
        """
        versions = self.get_versions(name)
        if versions:
            # Simple version comparison (assumes semver-like format)
            return max(versions, key=lambda v: [int(x) for x in v.split('.')])
        return None
    
    def unregister(self, name: str):
        """Unregister a model.
        
        Args:
            name: Model name
        """
        if name in self._models:
            del self._models[name]
        if name in self._versions:
            del self._versions[name]
