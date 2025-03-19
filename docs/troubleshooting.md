# NetRaven Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using NetRaven.

## Authentication Issues

### Invalid Credentials

**Symptom**: Unable to log in with "Invalid credentials" error message.

**Possible causes and solutions**:

1. **Incorrect username or password**
   - Double-check that you're using the correct username and password
   - Ensure caps lock is not enabled
   - Try resetting your password using the "Forgot Password" feature

2. **Account locked due to too many failed attempts**
   - Wait 15 minutes and try again
   - Contact your administrator to reset the rate limiting counter

3. **Expired account**
   - Contact your administrator to reactivate your account

### Token Issues

**Symptom**: Authenticated requests fail with "Token expired" or "Invalid token" errors.

**Possible causes and solutions**:

1. **Token has expired**
   - Use the token refresh endpoint (`/api/auth/refresh`) to obtain a new token
   - If refresh fails, log in again to obtain a completely new token

2. **Malformed token**
   - Ensure you're sending the token in the correct format: `Authorization: Bearer <token>`
   - Check that the token is properly encoded and hasn't been truncated

3. **Token has been revoked**
   - Log in again to obtain a new token
   - Check with your administrator if your access has been restricted

### Permission Issues

**Symptom**: "Insufficient permissions" or "Access denied" errors when accessing certain resources.

**Possible causes and solutions**:

1. **Missing required scope**
   - Check the API documentation for required scopes for each endpoint
   - Contact your administrator to grant additional scopes if needed

2. **Resource ownership restriction**
   - You may only have access to resources you own or were explicitly granted access to
   - Contact the resource owner or administrator to request access

## Backup Storage Issues

### Backup Content Not Found

**Symptom**: Unable to retrieve backup content with "Backup content not found" error.

**Possible causes and solutions**:

1. **Incorrect file path**
   - Verify the backup record in the database has the correct file path
   - Check if the storage backend configuration has changed

2. **Storage backend unavailable**
   - Check connectivity to the storage backend (S3, local filesystem)
   - Verify storage backend credentials and permissions

3. **File deleted outside of application**
   - If the file was deleted directly from storage rather than through the API, the database record might still exist
   - Restore the file from a backup or mark the backup as unavailable

### Content Hash Mismatch

**Symptom**: "Content hash mismatch" warning when retrieving backup content.

**Possible causes and solutions**:

1. **Corrupted file**
   - The file might have been corrupted during storage or transmission
   - Try to restore from an earlier backup

2. **File modified outside of application**
   - If the file was modified directly in storage, the hash will no longer match
   - Restore the file from a backup or update the hash in the database

### Storage Capacity Issues

**Symptom**: "No space left on device" or similar storage errors.

**Possible causes and solutions**:

1. **Local storage full**
   - Free up disk space
   - Configure a shorter retention period
   - Move to a storage backend with more capacity

2. **S3 bucket limits**
   - Check S3 bucket quotas and limits
   - Contact your AWS administrator to increase limits if needed

## Device Connection Issues

### Device Unreachable

**Symptom**: Cannot connect to device with "Device unreachable" error.

**Possible causes and solutions**:

1. **Network connectivity**
   - Verify network connectivity between the NetRaven server and the device
   - Check firewall rules that might be blocking connections
   - Ensure the device is powered on and operational

2. **Incorrect device IP or hostname**
   - Verify the device IP address or hostname is correct
   - Try pinging the device from the NetRaven server

3. **SSH/NETCONF port not open**
   - Verify the required ports are open on the device (SSH: 22, NETCONF: 830)
   - Check device configuration to ensure these services are enabled

### Authentication Failed

**Symptom**: Cannot authenticate to device with "Authentication failed" error.

**Possible causes and solutions**:

1. **Incorrect credentials**
   - Verify the username and password are correct for the device
   - Ensure the credential has the required privileges on the device

2. **SSH key issues**
   - Verify the SSH key is valid and has been properly added to the device
   - Check if the key has expired or been revoked

3. **Account locked on device**
   - Some devices lock accounts after multiple failed login attempts
   - Try accessing the device directly to unlock the account

### Command Execution Timeout

**Symptom**: Device command execution times out.

**Possible causes and solutions**:

1. **Device overloaded**
   - The device might be CPU-constrained or have high memory utilization
   - Try again later or during a maintenance window

2. **Command taking too long**
   - Some commands take longer to execute than the default timeout
   - Increase the timeout setting for that specific device

3. **Unstable connection**
   - Network instability might cause timeouts
   - Check for packet loss or high latency between NetRaven and the device

## API Rate Limiting Issues

### Too Many Requests

**Symptom**: Receiving "429 Too Many Requests" error responses.

**Possible causes and solutions**:

1. **Exceeding API rate limits**
   - Reduce the frequency of API calls
   - Implement backoff and retry strategies in your client
   - Cache responses where appropriate

2. **Login attempt limits**
   - Wait for the rate limit window to reset (typically 15 minutes)
   - Ensure credentials are correct to avoid triggering rate limiting

3. **IP-based rate limiting**
   - If multiple users share the same IP, consider changing your network configuration
   - Contact your administrator to adjust rate limit settings if needed

## Database Issues

### Connection Issues

**Symptom**: Application logs show database connection errors.

**Possible causes and solutions**:

1. **Database server down**
   - Verify the database server is running
   - Check network connectivity to the database server

2. **Connection pool exhaustion**
   - Too many concurrent connections might exhaust the connection pool
   - Adjust connection pool settings or optimize queries to release connections faster

3. **Authentication issues**
   - Verify database credentials are correct
   - Check if database user accounts are locked or expired

### Performance Issues

**Symptom**: Slow API responses, timeouts, or high server load.

**Possible causes and solutions**:

1. **Missing indexes**
   - Check if appropriate indexes are created for common queries
   - Add indexes to frequently queried columns

2. **Complex queries**
   - Optimize complex queries that might be causing performance issues
   - Consider denormalizing data for performance-critical paths

3. **Database server resources**
   - Check if the database server has sufficient CPU, memory, and disk I/O
   - Consider scaling up the database server resources

## Job Execution Issues

### Failed Jobs

**Symptom**: Background jobs failing or not completing.

**Possible causes and solutions**:

1. **Worker process crashed**
   - Check logs for worker process errors
   - Restart worker processes if needed

2. **Resource constraints**
   - Check if the worker has sufficient memory and CPU resources
   - Adjust job concurrency settings to prevent resource exhaustion

3. **External dependency failures**
   - Jobs might fail due to external dependencies (storage, devices, etc.)
   - Check connectivity and access to external dependencies

### Stuck Jobs

**Symptom**: Jobs remain in "running" state for an extended period.

**Possible causes and solutions**:

1. **Worker process died without updating job status**
   - Implement job timeouts that automatically mark jobs as failed after a period
   - Add job monitoring to detect and recover stuck jobs

2. **Deadlocks or infinite loops**
   - Review job code for potential deadlocks or infinite loops
   - Implement circuit breakers for resource-intensive operations

3. **External process hanging**
   - Set timeouts for external process calls
   - Implement proper error handling for external processes

## Container and Deployment Issues

### Container Startup Failures

**Symptom**: Docker containers fail to start or restart repeatedly.

**Possible causes and solutions**:

1. **Missing environment variables**
   - Check if all required environment variables are defined
   - Verify `.env` file is present and correctly formatted

2. **Port conflicts**
   - Ensure no other services are using the same ports
   - Change port mappings in docker-compose.yml if needed

3. **Volume permission issues**
   - Check permissions on mounted volumes
   - Ensure the container user has appropriate permissions

### Database Migration Issues

**Symptom**: Application fails to start with database migration errors.

**Possible causes and solutions**:

1. **Schema version mismatch**
   - Ensure all containers are running the same application version
   - Run database migrations manually if needed

2. **Incompatible migrations**
   - Check migration logs for specific errors
   - Restore database from backup and apply migrations incrementally

3. **Database connection issues during migration**
   - Ensure stable database connection during migration process
   - Increase migration timeout settings

## Testing Environment Issues

### Test Failures

**Symptom**: Unit or integration tests failing.

**Possible causes and solutions**:

1. **Environment configuration**
   - Ensure test environment is configured correctly
   - Check that test-specific settings are applied

2. **Test data issues**
   - Verify test fixtures and data are correct
   - Ensure database is properly seeded for tests

3. **Code changes breaking tests**
   - Review recent code changes that might have broken tests
   - Update tests to match new code behavior if appropriate

### Test Performance Issues

**Symptom**: Tests take too long to run.

**Possible causes and solutions**:

1. **Inefficient tests**
   - Identify slow tests and optimize them
   - Consider using test doubles (mocks, stubs) for external dependencies

2. **Too many integration tests**
   - Balance unit tests (fast) with integration tests (slower)
   - Run different test suites in parallel

3. **Resource constraints**
   - Ensure sufficient resources for test environment
   - Consider containerized testing for isolation and reproducibility

## Diagnostic Tools

### Server Logs

Access server logs to diagnose issues:

```bash
# View API server logs
docker-compose logs api

# Follow logs in real-time
docker-compose logs -f api

# View logs for a specific time period
docker-compose logs --since=1h api
```

### Database Inspection

Connect to the database for diagnostics:

```bash
# Connect to PostgreSQL database
docker-compose exec db psql -U netraven -d netraven

# Check active connections
SELECT * FROM pg_stat_activity;

# Check table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid)) 
FROM pg_catalog.pg_statio_user_tables 
ORDER BY pg_total_relation_size(relid) DESC;
```

### Storage Diagnostics

Check storage backend status:

```bash
# Local storage stats
docker-compose exec api python -c "from netraven.core.storage import get_storage_backend; from netraven.core.config import get_config; print(get_storage_backend(get_config()).get_status())"

# Verify a backup's content hash
docker-compose exec api python -c "from netraven.core.backup import retrieve_backup_content, hash_content; content = retrieve_backup_content('path/to/backup.txt'); print(hash_content(content))"
```

### API Diagnostics

Test API endpoints directly:

```bash
# Check API health endpoint
curl http://localhost:8000/api/health | jq

# Test API with authentication
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/users | jq
```

## Architecture-Specific Troubleshooting

### High Availability Setup Issues

If you're running NetRaven in a high-availability configuration:

1. **Load balancer issues**
   - Verify load balancer health checks are passing
   - Check if session persistence is configured correctly for authenticated sessions

2. **Shared storage issues**
   - Ensure shared storage is accessible from all nodes
   - Check permissions and mount points

3. **Database replication issues**
   - Verify database replication is working correctly
   - Check for replication lag or broken replication

### Advanced Debugging Techniques

For difficult-to-diagnose issues:

1. **Enable debug logging**
   - Set `LOG_LEVEL=DEBUG` in your environment
   - Restart the affected service

2. **Profile API performance**
   - Use tools like `py-spy` to profile Python performance
   - Check for slow database queries or external calls

3. **Memory leak investigation**
   - Monitor container memory usage over time
   - Use tools like `tracemalloc` to track Python memory allocations

## Getting Support

If you're unable to resolve an issue using this guide:

1. **Search the documentation**
   - The full documentation might have more specific information about your issue

2. **Check known issues**
   - The GitHub repository might have known issues documented

3. **Community support**
   - Post questions in the community forums or discussion groups

4. **Professional support**
   - Contact the NetRaven team for professional support options

Remember to provide the following when seeking support:

- NetRaven version
- Environment details (OS, container version, etc.)
- Detailed description of the issue
- Steps to reproduce
- Relevant logs or error messages

## Preventative Measures

To avoid common issues:

1. **Regular backups**
   - Maintain regular backups of the database and configuration
   - Test backup restoration procedures

2. **Monitoring**
   - Set up monitoring for services, database, and storage
   - Configure alerts for critical failures

3. **Update strategy**
   - Develop a strategy for applying updates safely
   - Test updates in a staging environment before production

4. **Documentation**
   - Maintain documentation of your specific deployment
   - Document any customizations or configuration changes 