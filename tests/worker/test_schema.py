import pytest
from netraven.worker.jobs.plugins import config_backup, reachability
from pydantic import ValidationError


def test_config_backup_params_schema():
    schema = config_backup.Params.schema()
    assert 'properties' in schema
    # Example: no required fields by default
    assert isinstance(schema['properties'], dict)


def test_reachability_params_schema():
    schema = reachability.Params.schema()
    assert 'properties' in schema
    assert isinstance(schema['properties'], dict)


def test_config_backup_params_validation():
    # Should accept no fields (all optional)
    params = config_backup.Params()
    assert isinstance(params, config_backup.Params)
    # Should reject extra fields
    with pytest.raises(ValidationError):
        config_backup.Params(extra_field='not allowed')


def test_reachability_params_validation():
    params = reachability.Params()
    assert isinstance(params, reachability.Params)
    with pytest.raises(ValidationError):
        reachability.Params(timeout=5, extra='bad')
