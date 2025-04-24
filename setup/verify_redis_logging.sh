#!/bin/bash
# Verifies Redis logging by emitting a test log and subscribing to the log channel.

set -e

CHANNEL="netraven-logs"
MESSAGE="[verify_redis_logging.sh] Test log message $(date)"

# Emit a test log message using Python
python3 -c "from netraven.utils.unified_logger import get_unified_logger; get_unified_logger().log('$MESSAGE', level='INFO')"

# Subscribe to the Redis log channel and print the next message
redis-cli SUBSCRIBE "$CHANNEL" | grep --line-buffered "$MESSAGE" && echo "[SUCCESS] Log message received on Redis channel: $CHANNEL" 