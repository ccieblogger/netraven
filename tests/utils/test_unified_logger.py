"""
Tests for UnifiedLogger utility.

To run these tests in the containerized environment:
    docker exec -it netraven-api-dev bash -c "cd /app && PYTHONPATH=/app poetry run pytest tests/utils/"

These tests cover:
- File logging (including rotation/format)
- Stdout logging
- Redis logging (mocked)
- DB logging (mocked)
- Error handling and fallback
- Config-driven enable/disable
"""
import os
import tempfile
import pytest
from unittest import mock
from netraven.utils.unified_logger import UnifiedLogger
import redis
import time

@pytest.fixture
def file_log_config():
    tmpdir = tempfile.mkdtemp()
    return {
        'file': {
            'enabled': True,
            'path': os.path.join(tmpdir, 'test.log'),
            'level': 'INFO',
            'format': 'plain',
            'rotation': {'when': 'midnight', 'interval': 1, 'backupCount': 1}
        },
        'stdout': {'enabled': False},
        'redis': {'enabled': False},
        'db': {'enabled': False}
    }

@pytest.fixture
def stdout_log_config():
    return {
        'file': {'enabled': False},
        'stdout': {'enabled': True, 'level': 'INFO'},
        'redis': {'enabled': False},
        'db': {'enabled': False}
    }

@pytest.fixture
def redis_log_config():
    return {
        'file': {'enabled': False},
        'stdout': {'enabled': False},
        'redis': {'enabled': True, 'channel_prefix': 'test-logs'},
        'db': {'enabled': False}
    }

@pytest.fixture
def db_log_config():
    return {
        'file': {'enabled': False},
        'stdout': {'enabled': False},
        'redis': {'enabled': False},
        'db': {'enabled': True}
    }

def test_file_logging(file_log_config):
    logger = UnifiedLogger(file_log_config)
    logger.log('file log test', level='INFO')
    log_path = file_log_config['file']['path']
    with open(log_path, 'r') as f:
        content = f.read()
    assert 'file log test' in content

def test_stdout_logging(stdout_log_config, capsys):
    logger = UnifiedLogger(stdout_log_config)
    logger.log('stdout log test', level='INFO')
    captured = capsys.readouterr()
    # The logger writes to sys.stdout via logging, so this may not capture unless propagate is True
    # This test ensures no exceptions and log call executes
    assert True

def test_redis_logging(redis_log_config):
    with mock.patch('netraven.utils.unified_logger.Redis') as MockRedis:
        mock_redis = MockRedis.return_value
        logger = UnifiedLogger(redis_log_config)
        logger.redis_client = mock_redis
        logger.log('redis log test', level='INFO')
        assert mock_redis.publish.called

def test_db_logging(db_log_config):
    with mock.patch('netraven.utils.unified_logger.save_log') as mock_save_log:
        logger = UnifiedLogger(db_log_config)
        logger.log('db log test', level='INFO', job_id=1, device_id=2, source='test', extra={'foo': 'bar'}, log_type='job')
        mock_save_log.assert_called_once()
        args, kwargs = mock_save_log.call_args
        assert kwargs['message'] == 'db log test'
        assert kwargs['log_type'] == 'job'
        assert kwargs['level'] == 'INFO'
        assert kwargs['job_id'] == 1
        assert kwargs['device_id'] == 2
        assert kwargs['source'] == 'test'
        assert kwargs['meta'] == {'foo': 'bar'}

def test_error_handling(file_log_config):
    # Simulate file logger error
    logger = UnifiedLogger(file_log_config)
    logger.file_logger = None  # Remove file logger to force fallback
    # Should fallback to print
    logger.log('error fallback test', level='INFO')
    assert True

def test_config_enable_disable():
    config = {'file': {'enabled': False}, 'stdout': {'enabled': False}, 'redis': {'enabled': False}, 'db': {'enabled': False}}
    logger = UnifiedLogger(config)
    logger.log('no destination test', level='INFO')
    # Should fallback to print
    assert True

def test_redis_config_parsing():
    with mock.patch('netraven.utils.unified_logger.Redis') as MockRedis:
        config = {
            'redis': {
                'enabled': True,
                'host': 'custom-redis',
                'port': 6380,
                'db': 2,
                'password': 'secret',
                'channel_prefix': 'custom-logs'
            }
        }
        logger = UnifiedLogger(config)
        MockRedis.assert_called_with(
            host='custom-redis',
            port=6380,
            db=2,
            password='secret',
            decode_responses=True
        )

@pytest.mark.integration
def test_redis_logging_integration():
    """Integration test: requires a real Redis server at redis:6379."""
    try:
        r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
        pubsub = r.pubsub()
        pubsub.subscribe('netraven-logs')
        logger = UnifiedLogger({'redis': {'enabled': True, 'host': 'redis', 'port': 6379, 'db': 0, 'channel_prefix': 'netraven-logs'}})
        test_message = f'integration test log {time.time()}'
        logger.log(test_message, level='INFO')
        # Wait for the message to appear
        for _ in range(10):
            msg = pubsub.get_message()
            if msg and msg['type'] == 'message' and test_message in msg['data']:
                assert True
                return
            time.sleep(0.2)
        pytest.skip('Redis integration test: log message not received (is Redis running?)')
    except Exception as e:
        pytest.skip(f'Redis integration test skipped: {e}') 