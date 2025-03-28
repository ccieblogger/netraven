# NetRaven Troubleshooting Guide

## Introduction

This troubleshooting guide provides solutions for common issues that may occur when operating NetRaven. It is designed to help administrators diagnose and resolve problems with installation, configuration, connectivity, backups, and other aspects of the system.

## Purpose

By following this guide, you will be able to:
- Identify and resolve common NetRaven issues
- Collect diagnostic information for troubleshooting
- Perform basic recovery procedures
- Know when to contact support for further assistance

## Diagnostic Tools

### System Logs

NetRaven logs are a primary source of troubleshooting information:

1. **API Service Logs**:
   ```bash
   # Docker deployment
   docker logs netraven-api
   
   # Manual deployment
   cat /var/log/netraven/api.log
   ```

2. **Device Gateway Logs**:
   ```bash
   # Docker deployment
   docker logs netraven-gateway
   
   # Manual deployment
   cat /var/log/netraven/gateway.log
   ```

3. **Scheduler Logs**:
   ```bash
   # Docker deployment
   docker logs netraven-scheduler
   
   # Manual deployment
   cat /var/log/netraven/scheduler.log
   ```

4. **Database Logs**:
   ```bash
   # Docker deployment
   docker logs netraven-db
   
   # Manual deployment
   cat /var/log/postgresql/postgresql.log
   ```

### Health Checks

NetRaven provides health check endpoints for all services:

1. API Service: `http://your-server:8000/api/health`
2. Device Gateway: `http://your-server:8001/health`
3. Scheduler: `http://your-server:8002/health`

Each endpoint returns a JSON response with service status and component health.

### Database Diagnostics

To check database connectivity and performance:

```bash
# Inside the API container
docker exec -it netraven-api python -m tools.db_diagnostics

# Manual deployment
cd /opt/netraven
python -m tools.db_diagnostics
```

## Common Issues and Solutions

### Installation Issues

#### Docker Compose Failure

**Issue**: Docker Compose fails to start all services.

**Solutions**:
1. Check Docker and Docker Compose versions:
   ```bash
   docker --version
   docker-compose --version
   ```
   Ensure you have Docker 19.03+ and Docker Compose 1.27+.

2. Check for port conflicts:
   ```bash
   netstat -tulpn | grep -E '8000|8001|8002|8080|5432'
   ```
   If ports are in use, modify the docker-compose.yml file to use different ports.

3. Check disk space:
   ```bash
   df -h
   ```
   Ensure you have at least 10GB free.

4. Review detailed Docker Compose logs:
   ```bash
   docker-compose logs
   ```
   Look for specific error messages for each service.

#### Database Initialization Failure

**Issue**: The database fails to initialize on first start.

**Solutions**:
1. Check database logs:
   ```bash
   docker-compose logs db
   ```

2. Verify database volume permissions:
   ```bash
   ls -la /path/to/db/volume
   ```
   Ensure the directory is writable by the PostgreSQL user.

3. Reset the database and try again:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```
   Note: This will delete any existing data.

### Authentication Issues

#### Login Failures

**Issue**: Unable to log in with valid credentials.

**Solutions**:
1. Reset the admin password:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.reset_admin_password --username admin --password newpassword
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.reset_admin_password --username admin --password newpassword
   ```

2. Check authentication logs:
   ```bash
   docker exec -it netraven-api cat /app/logs/auth.log | tail -50
   ```

3. Verify JWT secret key configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api env | grep TOKEN_SECRET_KEY
   
   # Manual deployment
   grep TOKEN_SECRET_KEY /opt/netraven/.env
   ```

#### LDAP Integration Issues

**Issue**: LDAP authentication not working.

**Solutions**:
1. Test LDAP connectivity:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.ldap_test
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.ldap_test
   ```

2. Check LDAP configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.show_config --section auth.ldap
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.show_config --section auth.ldap
   ```

3. Verify LDAP server accessibility:
   ```bash
   # Docker deployment
   docker exec -it netraven-api ping -c 3 ldap.example.com
   
   # Manual deployment
   ping -c 3 ldap.example.com
   ```

### Device Connectivity Issues

#### SSH Connection Failures

**Issue**: Unable to connect to network devices via SSH.

**Solutions**:
1. Verify device reachability from NetRaven server:
   ```bash
   # Docker deployment
   docker exec -it netraven-gateway ping -c 3 192.168.1.1
   
   # Manual deployment
   ping -c 3 192.168.1.1
   ```

2. Check device credentials in NetRaven:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.check_device_credentials --device-id 123
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.check_device_credentials --device-id 123
   ```

3. Test SSH connection manually:
   ```bash
   # Docker deployment
   docker exec -it netraven-gateway ssh -p 22 -l username 192.168.1.1
   
   # Manual deployment
   ssh -p 22 -l username 192.168.1.1
   ```

4. Check SSH library debug output:
   ```bash
   # Docker deployment
   docker exec -it netraven-gateway env PARAMIKO_DEBUG=1 python -m tools.ssh_test --device-id 123
   
   # Manual deployment
   cd /opt/netraven
   PARAMIKO_DEBUG=1 python -m tools.ssh_test --device-id 123
   ```

#### Device Adapter Issues

**Issue**: Device commands fail or return unexpected results.

**Solutions**:
1. Verify device type configuration:
   ```bash
   # List supported device types
   docker exec -it netraven-api python -m tools.list_device_types
   
   # Show device type details
   docker exec -it netraven-api python -m tools.show_device_type --type cisco_ios
   ```

2. Check command templates for the device type:
   ```bash
   docker exec -it netraven-api python -m tools.show_command_templates --type cisco_ios
   ```

3. Test command execution manually:
   ```bash
   docker exec -it netraven-gateway python -m tools.run_device_command --device-id 123 --command "show version"
   ```

### Backup Issues

#### Failed Backups

**Issue**: Configuration backups fail to complete.

**Solutions**:
1. Check backup logs:
   ```bash
   # Docker deployment
   docker exec -it netraven-api cat /app/logs/backups.log | tail -50
   
   # Manual deployment
   cat /var/log/netraven/backups.log | tail -50
   ```

2. Verify storage configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.check_storage
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.check_storage
   ```

3. Test backup manually:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.run_backup --device-id 123
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.run_backup --device-id 123
   ```

#### Storage Access Issues

**Issue**: Cannot access backup storage (S3 or local).

**Solutions**:
1. For S3 storage, check credentials and connectivity:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.s3_test
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.s3_test
   ```

2. For local storage, check permissions:
   ```bash
   # Docker deployment
   docker exec -it netraven-api ls -la /app/data/backups
   
   # Manual deployment
   ls -la /opt/netraven/data/backups
   ```

3. Verify storage configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.show_config --section storage
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.show_config --section storage
   ```

### Scheduler Issues

#### Scheduled Backups Not Running

**Issue**: Automated backup schedules do not execute.

**Solutions**:
1. Check scheduler status:
   ```bash
   # Docker deployment
   docker exec -it netraven-scheduler python -m tools.scheduler_status
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.scheduler_status
   ```

2. Verify schedule configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.list_schedules
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.list_schedules
   ```

3. Check scheduler logs:
   ```bash
   # Docker deployment
   docker exec -it netraven-scheduler cat /app/logs/scheduler.log | tail -50
   
   # Manual deployment
   cat /var/log/netraven/scheduler.log | tail -50
   ```

4. Restart scheduler:
   ```bash
   # Docker deployment
   docker restart netraven-scheduler
   
   # Manual deployment
   systemctl restart netraven-scheduler
   ```

### Web Interface Issues

#### Page Load Failures

**Issue**: Web interface fails to load or shows errors.

**Solutions**:
1. Check frontend logs:
   ```bash
   # Docker deployment
   docker logs netraven-frontend
   
   # Manual deployment
   cat /var/log/nginx/error.log
   ```

2. Verify API connectivity from browser:
   ```
   # Open browser developer tools (F12)
   # Check Network tab for API calls to /api/*
   # Look for failed requests or error responses
   ```

3. Clear browser cache and cookies
4. Try a different browser or incognito mode

#### File Upload Issues

**Issue**: Configuration or CSV uploads fail.

**Solutions**:
1. Check file size limits:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.show_config --section api.uploads
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.show_config --section api.uploads
   ```

2. Verify upload directory permissions:
   ```bash
   # Docker deployment
   docker exec -it netraven-api ls -la /app/data/uploads
   
   # Manual deployment
   ls -la /opt/netraven/data/uploads
   ```

3. Check API logs for upload errors:
   ```bash
   # Docker deployment
   docker exec -it netraven-api cat /app/logs/api.log | grep "upload"
   
   # Manual deployment
   cat /var/log/netraven/api.log | grep "upload"
   ```

## Performance Issues

### Slow API Response

**Issue**: API endpoints are slow to respond.

**Solutions**:
1. Check API service load:
   ```bash
   # Docker deployment
   docker stats netraven-api
   
   # Manual deployment
   top -p $(pgrep -f "uvicorn.workers")
   ```

2. Monitor database performance:
   ```bash
   # Docker deployment
   docker exec -it netraven-db psql -U postgres -c "SELECT * FROM pg_stat_activity;"
   
   # Manual deployment
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   ```

3. Check for long-running queries:
   ```bash
   # Docker deployment
   docker exec -it netraven-db psql -U postgres -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
   
   # Manual deployment
   sudo -u postgres psql -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
   ```

4. Increase API workers (if CPU resources allow):
   ```
   # In docker-compose.yml, modify the API service:
   environment:
     - WORKERS=4  # Increase from default
   ```

### Database Performance

**Issue**: Database operations are slow.

**Solutions**:
1. Check database metrics:
   ```bash
   # Docker deployment
   docker exec -it netraven-db psql -U postgres -c "SELECT * FROM pg_stat_database WHERE datname='netraven';"
   
   # Manual deployment
   sudo -u postgres psql -c "SELECT * FROM pg_stat_database WHERE datname='netraven';"
   ```

2. Verify index usage:
   ```bash
   # Docker deployment
   docker exec -it netraven-db psql -U postgres -d netraven -c "SELECT * FROM pg_stat_user_indexes;"
   
   # Manual deployment
   sudo -u postgres psql -d netraven -c "SELECT * FROM pg_stat_user_indexes;"
   ```

3. Run database vacuum:
   ```bash
   # Docker deployment
   docker exec -it netraven-db psql -U postgres -d netraven -c "VACUUM ANALYZE;"
   
   # Manual deployment
   sudo -u postgres psql -d netraven -c "VACUUM ANALYZE;"
   ```

## Recovery Procedures

### Database Recovery

If the database becomes corrupted or data is lost:

1. Stop all services:
   ```bash
   # Docker deployment
   docker-compose stop
   
   # Manual deployment
   systemctl stop netraven-api netraven-gateway netraven-scheduler
   ```

2. Restore from backup:
   ```bash
   # Docker deployment
   docker-compose down
   # Replace the postgres data volume with backup
   cp -r /path/to/db/backup /path/to/postgres/data
   docker-compose up -d
   
   # Manual deployment
   sudo -u postgres pg_restore -d netraven /path/to/backup.dump
   ```

3. Verify database integrity:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.db_check
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.db_check
   ```

### Configuration Reset

If the system configuration becomes corrupted:

1. Export current configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.export_config > config_backup.json
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.export_config > config_backup.json
   ```

2. Reset configuration:
   ```bash
   # Docker deployment
   docker exec -it netraven-api python -m tools.reset_config
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.reset_config
   ```

3. Import saved configuration (optional):
   ```bash
   # Docker deployment
   cat config_backup.json | docker exec -i netraven-api python -m tools.import_config
   
   # Manual deployment
   cd /opt/netraven
   python -m tools.import_config < config_backup.json
   ```

## Collecting Diagnostic Information

When reporting issues to support, collect the following information:

### System Information

```bash
# Docker deployment
docker version
docker-compose version
docker ps -a
docker stats

# Manual deployment
uname -a
lsb_release -a
free -m
df -h
```

### Application Logs

```bash
# Docker deployment
docker logs --tail=1000 netraven-api > api_logs.txt
docker logs --tail=1000 netraven-gateway > gateway_logs.txt
docker logs --tail=1000 netraven-scheduler > scheduler_logs.txt
docker logs --tail=1000 netraven-db > db_logs.txt
docker logs --tail=1000 netraven-frontend > frontend_logs.txt

# Manual deployment
cat /var/log/netraven/api.log | tail -1000 > api_logs.txt
cat /var/log/netraven/gateway.log | tail -1000 > gateway_logs.txt
cat /var/log/netraven/scheduler.log | tail -1000 > scheduler_logs.txt
cat /var/log/postgresql/postgresql.log | tail -1000 > db_logs.txt
cat /var/log/nginx/error.log | tail -1000 > frontend_logs.txt
```

### Configuration

```bash
# Docker deployment
docker exec -it netraven-api python -m tools.export_config --sanitize > config.json

# Manual deployment
cd /opt/netraven
python -m tools.export_config --sanitize > config.json
```

### Database Statistics

```bash
# Docker deployment
docker exec -it netraven-db psql -U postgres -d netraven -c "SELECT COUNT(*) FROM devices;" > db_stats.txt
docker exec -it netraven-db psql -U postgres -d netraven -c "SELECT COUNT(*) FROM backups;" >> db_stats.txt
docker exec -it netraven-db psql -U postgres -d netraven -c "SELECT COUNT(*) FROM users;" >> db_stats.txt

# Manual deployment
sudo -u postgres psql -d netraven -c "SELECT COUNT(*) FROM devices;" > db_stats.txt
sudo -u postgres psql -d netraven -c "SELECT COUNT(*) FROM backups;" >> db_stats.txt
sudo -u postgres psql -d netraven -c "SELECT COUNT(*) FROM users;" >> db_stats.txt
```

## When to Contact Support

Contact NetRaven support when:

1. You've followed the relevant troubleshooting steps and the issue persists
2. You encounter an error message not covered in this guide
3. You need assistance with a complex migration or upgrade
4. You suspect a security breach or data corruption
5. You need help with disaster recovery

### Support Contact Information

- Email: support@netraven.io
- Support Portal: https://support.netraven.io
- Community Forum: https://community.netraven.io
- Emergency Hotline: +1-555-NET-RAVEN (for enterprise customers)

When contacting support, include:
- Your NetRaven version
- Deployment type (Docker or manual)
- Collected diagnostic information
- A clear description of the issue
- Steps to reproduce the problem
- Any error messages or screenshots

## Related Documentation

- [Installation Guide](../getting-started/installation.md)
- [Upgrade Guide](./upgrades.md)
- [Backup and Recovery](./backup-recovery.md)
- [Performance Optimization](./performance-optimization.md) 