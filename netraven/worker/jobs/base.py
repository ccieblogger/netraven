# BaseJob and metaclass for NetRaven job plugins
from abc import ABC, abstractmethod, ABCMeta
from typing import Dict, Type, Any

class JobMeta(ABCMeta):
    """Metaclass that registers all subclasses of BaseJob."""
    registry: Dict[str, Type['BaseJob']] = {}

    def __new__(mcs, name, bases, attrs):
        cls = super().__new__(mcs, name, bases, attrs)
        if not attrs.get('__abstract__', False):
            # Register only concrete jobs
            job_name = attrs.get('name', name)
            mcs.registry[job_name] = cls
        return cls

class BaseJob(ABC, metaclass=JobMeta):
    __abstract__ = True
    name: str = "BaseJob"
    description: str = ""

    @abstractmethod
    def run(self, device, job_id, config, db) -> Any:
        pass

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description
        }
