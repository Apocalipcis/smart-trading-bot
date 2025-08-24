"""
Strategy Registry

This module provides a registry system for discovering and managing
trading strategies. It supports auto-discovery, versioning, and
dynamic loading of strategy classes.
"""

import importlib
import inspect
import os
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import json
import logging

from .base import BaseStrategy


class StrategyInfo:
    """Information about a registered strategy."""
    
    def __init__(self, name: str, strategy_class: Type[BaseStrategy], 
                 file_path: str, version: str = "1.0.0"):
        self.name = name
        self.strategy_class = strategy_class
        self.file_path = file_path
        self.version = version
        self.registration_date = datetime.utcnow()
        self.description = getattr(strategy_class, '__doc__', 'No description available')
        self.parameters = self._extract_parameters()
    
    def _extract_parameters(self) -> Dict[str, Any]:
        """Extract strategy parameters from the class."""
        if hasattr(self.strategy_class, 'params'):
            # Backtrader params are stored as a namedtuple-like object
            try:
                return dict(self.strategy_class.params._asdict())
            except AttributeError:
                # Fallback for different param formats
                try:
                    return dict(self.strategy_class.params)
                except (TypeError, ValueError):
                    return {}
        return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'name': self.name,
            'version': self.version,
            'file_path': self.file_path,
            'registration_date': self.registration_date.isoformat(),
            'description': self.description,
            'parameters': self.parameters
        }
    
    def __repr__(self):
        return f"StrategyInfo(name='{self.name}', version='{self.version}')"


class StrategyRegistry:
    """
    Registry for managing trading strategies.
    
    This class provides functionality to discover, register, and manage
    trading strategies. It supports auto-discovery from directories and
    provides versioning information.
    """
    
    def __init__(self, strategies_dir: Optional[str] = None):
        """
        Initialize the strategy registry.
        
        Args:
            strategies_dir: Directory to scan for strategies (defaults to package directory)
        """
        if strategies_dir is None:
            # Default to the directory containing this file
            strategies_dir = Path(__file__).parent
        
        self.strategies_dir = Path(strategies_dir)
        self.strategies: Dict[str, StrategyInfo] = {}
        self.logger = logging.getLogger(__name__)
        
        # Auto-discover strategies on initialization
        self.discover_strategies()
    
    def discover_strategies(self) -> List[str]:
        """
        Discover strategies in the strategies directory.
        
        Returns:
            List[str]: List of discovered strategy names
        """
        discovered = []
        
        if not self.strategies_dir.exists():
            self.logger.warning(f"Strategies directory does not exist: {self.strategies_dir}")
            return discovered
        
        # Look for Python files in the strategies directory
        for py_file in self.strategies_dir.glob("*.py"):
            if py_file.name.startswith('_') or py_file.name == 'base.py':
                continue  # Skip private files and base class
            
            try:
                strategy_name = self._load_strategy_from_file(py_file)
                if strategy_name:
                    discovered.append(strategy_name)
            except Exception as e:
                self.logger.error(f"Failed to load strategy from {py_file}: {e}")
        
        self.logger.info(f"Discovered {len(discovered)} strategies: {discovered}")
        return discovered
    
    def _load_strategy_from_file(self, file_path: Path) -> Optional[str]:
        """
        Load a strategy from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Optional[str]: Strategy name if loaded successfully, None otherwise
        """
        try:
            # Import the module
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for strategy classes in the module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseStrategy) and 
                    obj != BaseStrategy):
                    
                    # Extract version from class or file
                    version = self._extract_version(obj, file_path)
                    
                    # Register the strategy
                    strategy_info = StrategyInfo(
                        name=name,
                        strategy_class=obj,
                        file_path=str(file_path),
                        version=version
                    )
                    
                    self.strategies[name] = strategy_info
                    self.logger.info(f"Registered strategy: {name} v{version}")
                    return name
            
        except Exception as e:
            self.logger.error(f"Error loading strategy from {file_path}: {e}")
            return None
        
        return None
    
    def _extract_version(self, strategy_class: Type[BaseStrategy], file_path: Path) -> str:
        """
        Extract version information from a strategy class or file.
        
        Args:
            strategy_class: The strategy class
            file_path: Path to the strategy file
            
        Returns:
            str: Version string
        """
        # Try to get version from class
        if hasattr(strategy_class, 'version'):
            return str(strategy_class.version)
        
        # Try to get version from module
        if hasattr(strategy_class, '__module__'):
            try:
                module = importlib.import_module(strategy_class.__module__)
                if hasattr(module, 'version'):
                    return str(module.version)
            except ImportError:
                pass
        
        # Try to extract from file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for version pattern
                import re
                version_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if version_match:
                    return version_match.group(1)
        except Exception:
            pass
        
        # Default version
        return "1.0.0"
    
    def register_strategy(self, name: str, strategy_class: Type[BaseStrategy], 
                         file_path: str, version: str = "1.0.0") -> StrategyInfo:
        """
        Manually register a strategy.
        
        Args:
            name: Strategy name
            strategy_class: Strategy class
            file_path: Path to the strategy file
            version: Strategy version
            
        Returns:
            StrategyInfo: Information about the registered strategy
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy")
        
        strategy_info = StrategyInfo(name, strategy_class, file_path, version)
        self.strategies[name] = strategy_info
        
        self.logger.info(f"Manually registered strategy: {name} v{version}")
        return strategy_info
    
    def get_strategy(self, name: str) -> Optional[Type[BaseStrategy]]:
        """
        Get a strategy class by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Optional[Type[BaseStrategy]]: Strategy class if found, None otherwise
        """
        if name in self.strategies:
            return self.strategies[name].strategy_class
        return None
    
    def get_strategy_info(self, name: str) -> Optional[StrategyInfo]:
        """
        Get strategy information by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Optional[StrategyInfo]: Strategy information if found, None otherwise
        """
        return self.strategies.get(name)
    
    def list_strategies(self) -> List[Dict[str, Any]]:
        """
        List all registered strategies.
        
        Returns:
            List[Dict[str, Any]]: List of strategy information dictionaries
        """
        return [info.to_dict() for info in self.strategies.values()]
    
    def get_strategy_parameters(self, name: str) -> Dict[str, Any]:
        """
        Get parameters for a specific strategy.
        
        Args:
            name: Strategy name
            
        Returns:
            Dict[str, Any]: Strategy parameters
        """
        if name in self.strategies:
            return self.strategies[name].parameters
        return {}
    
    def validate_strategy(self, name: str) -> Dict[str, Any]:
        """
        Validate a strategy for correctness.
        
        Args:
            name: Strategy name
            
        Returns:
            Dict[str, Any]: Validation results
        """
        if name not in self.strategies:
            return {
                'valid': False,
                'errors': [f"Strategy '{name}' not found"]
            }
        
        strategy_info = self.strategies[name]
        strategy_class = strategy_info.strategy_class
        errors = []
        
        # Check if required methods are implemented
        if not hasattr(strategy_class, 'generate_signals'):
            errors.append("Missing required method: generate_signals")
        
        # Check if parameters are valid
        try:
            # Try to instantiate with default parameters
            instance = strategy_class()
            instance._validate_parameters()
        except Exception as e:
            errors.append(f"Parameter validation failed: {e}")
        
        # Check if it's not abstract
        if inspect.isabstract(strategy_class):
            errors.append("Strategy class is abstract")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strategy_info': strategy_info.to_dict()
        }
    
    def reload_strategy(self, name: str) -> bool:
        """
        Reload a strategy from its file.
        
        Args:
            name: Strategy name
            
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        if name not in self.strategies:
            return False
        
        strategy_info = self.strategies[name]
        file_path = Path(strategy_info.file_path)
        
        # Remove from registry
        del self.strategies[name]
        
        # Reload
        try:
            self._load_strategy_from_file(file_path)
            return name in self.strategies
        except Exception as e:
            self.logger.error(f"Failed to reload strategy {name}: {e}")
            return False
    
    def export_registry(self, file_path: str) -> bool:
        """
        Export registry information to a JSON file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            bool: True if exported successfully, False otherwise
        """
        try:
            registry_data = {
                'export_date': datetime.utcnow().isoformat(),
                'strategies_dir': str(self.strategies_dir),
                'total_strategies': len(self.strategies),
                'strategies': self.list_strategies()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Registry exported to {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export registry: {e}")
            return False


# Global registry instance
_registry: Optional[StrategyRegistry] = None


def get_registry() -> StrategyRegistry:
    """
    Get the global strategy registry instance.
    
    Returns:
        StrategyRegistry: Global registry instance
    """
    global _registry
    if _registry is None:
        _registry = StrategyRegistry()
    return _registry


def register_strategy(name: str, strategy_class: Type[BaseStrategy], 
                     file_path: str, version: str = "1.0.0") -> StrategyInfo:
    """
    Register a strategy in the global registry.
    
    Args:
        name: Strategy name
        strategy_class: Strategy class
        file_path: Path to the strategy file
        version: Strategy version
        
    Returns:
        StrategyInfo: Information about the registered strategy
    """
    return get_registry().register_strategy(name, strategy_class, file_path, version)


def get_strategy(name: str) -> Optional[Type[BaseStrategy]]:
    """
    Get a strategy from the global registry.
    
    Args:
        name: Strategy name
        
    Returns:
        Optional[Type[BaseStrategy]]: Strategy class if found, None otherwise
    """
    return get_registry().get_strategy(name)
