# BaseJob and metaclass for NetRaven job plugins
from abc import ABC, abstractmethod, ABCMeta
from typing import Dict, Type, Any, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .context import PluginContext

class ParamsModel(BaseModel):
    class Config:
        extra = 'forbid'
        orm_mode = True

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
    plugin_context: 'PluginContext' = None

    @abstractmethod
    def run(self, device, job_id, config, db) -> Any:
        pass

    @classmethod
    def create(cls, user):
        from .context import PluginContext
        context = PluginContext(user)
        instance = cls()
        instance.plugin_context = context
        return instance

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        return {
            "name": cls.name,
            "description": cls.description
        }

    @classmethod
    def get_params_schema(cls):
        """
        Return the JSON schema for the Params class if defined, else None.
        """
        if hasattr(cls, 'Params') and issubclass(cls.Params, ParamsModel):
            return cls.Params.schema_json()
        return None

class ExampleJob(BaseJob):
    __abstract__ = False
    name = "ExampleJob"
    description = "A sample job to demonstrate PluginContext injection."

    def run(self, device, job_id, config, db):
        # Use the injected plugin_context
        assert self.plugin_context is not None
        # Example: log something and return a result
        self.plugin_context.logger.info(f"Running ExampleJob for device {device}, job_id {job_id}")
        return {"success": True, "job_id": job_id}
