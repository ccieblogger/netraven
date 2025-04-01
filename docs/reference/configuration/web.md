# Web Service Configuration

This document provides a reference for the web service configuration settings in NetRaven.

## Web Service Overview

The web service configuration controls:
- HTTP server settings
- API behavior
- Database connection
- Authentication and security
- CORS and external access

## Configuration Properties

### Web Server Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.host` | String | `"0.0.0.0"` | Host IP address to bind to. Use `0.0.0.0` to listen on all interfaces |
| `web.port` | Integer | `8000` | Port number for the web service to listen on |
| `web.debug` | Boolean | `false` | Enable debug mode for the web service |
| `web.log_level` | String | `"INFO"` | Logging level specifically for web components |
| `web.workers` | Integer | `4` | Number of worker processes for the web server |
| `web.allowed_origins` | List | `["*"]` | CORS allowed origins. Use `["*"]` to allow all origins |

### Database Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.database.type` | String | `"sqlite"` | Database type. Options: `sqlite`, `postgres`, `mysql` |
| `web.database.sqlite.path` | String | `"data/netraven.db"` | Path to the SQLite database file |
| `web.database.postgres.host` | String | `"postgres"` | PostgreSQL server hostname |
| `web.database.postgres.port` | Integer | `5432` | PostgreSQL server port |
| `web.database.postgres.database` | String | `"netraven"` | PostgreSQL database name |
| `web.database.postgres.user` | String | `"netraven"` | PostgreSQL username |
| `web.database.postgres.password` | String | `"netraven"` | PostgreSQL password |

### Authentication Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.authentication.token_expiration` | Integer | `86400` | Token expiration time in seconds (default: 24 hours) |
| `web.authentication.jwt_algorithm` | String | `"HS256"` | JWT signing algorithm |
| `web.authentication.require_https` | Boolean | `false` | Whether to require HTTPS for authentication requests |
| `web.authentication.cookie_secure` | Boolean | `false` | Whether to set the secure flag on authentication cookies |
| `web.authentication.password_min_length` | Integer | `8` | Minimum password length for user accounts |

### CORS Settings

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `web.cors.allow_origins` | List | `["*"]` | List of allowed origins for CORS requests |
| `web.cors.allow_credentials` | Boolean | `true` | Whether to allow credentials in CORS requests |
| `web.cors.allow_methods` | List | `["*"]` | List of allowed HTTP methods for CORS requests |
| `web.cors.allow_headers` | List | `["*"]` | List of allowed HTTP headers for CORS requests |

## Environment Variables

The following environment variables can be used to override web service settings:

| Environment Variable | Configuration Property | Description |
|----------------------|------------------------|-------------|
| `NETRAVEN_WEB_HOST` | `web.host` | Host IP address |
| `NETRAVEN_WEB_PORT` | `web.port` | Web server port |
| `NETRAVEN_WEB_DATABASE_TYPE` | `web.database.type` | Database type |
| `NETRAVEN_WEB_DATABASE_HOST` | `web.database.postgres.host` or similar | Database host |
| `NETRAVEN_WEB_DATABASE_PORT` | `web.database.postgres.port` or similar | Database port |
| `NETRAVEN_WEB_DATABASE_NAME` | `web.database.postgres.database` or similar | Database name |
| `NETRAVEN_WEB_DATABASE_USER` | `web.database.postgres.user` or similar | Database username |
| `NETRAVEN_WEB_DATABASE_PASSWORD` | `web.database.postgres.password` or similar | Database password |

## Example Configuration

```yaml
# Web service configuration example
web:
  host: 0.0.0.0
  port: 8000
  debug: false
  log_level: INFO
  workers: 8
  
  # Database configuration
  database:
    type: postgres
    postgres:
      host: db.example.com
      port: 5432
      database: netraven_prod
      user: netraven_user
      password: ${DB_PASSWORD}  # Use environment variable
  
  # Authentication configuration
  authentication:
    token_expiration: 43200  # 12 hours
    jwt_algorithm: HS256
    require_https: true
    cookie_secure: true
    password_min_length: 12
  
  # CORS configuration
  cors:
    allow_origins:
      - https://app.example.com
      - https://admin.example.com
    allow_credentials: true
    allow_methods:
      - GET
      - POST
      - PUT
      - DELETE
    allow_headers:
      - Content-Type
      - Authorization
```

## Development vs. Production

In development environments (`NETRAVEN_ENV=development`):
- Debug mode is typically enabled
- CORS settings are usually more permissive
- Database credentials may be simplified
- HTTPS may be disabled for local testing

In production environments:
- Debug mode should be disabled
- CORS should be restricted to specific origins
- HTTPS should be required for authentication
- Cookies should be marked secure
- Database credentials should be strong and managed securely

## Docker Configuration

When running in Docker, the web service is typically configured in the Docker Compose file:

```yaml
services:
  api:
    image: netraven-api
    ports:
      - "8000:8000"
    environment:
      - NETRAVEN_WEB_HOST=0.0.0.0
      - NETRAVEN_WEB_PORT=8000
      - NETRAVEN_WEB_DATABASE_TYPE=postgres
      - NETRAVEN_WEB_DATABASE_HOST=postgres
    volumes:
      - ./config.yml:/app/config.yml
```

## Security Considerations

- **Database Credentials**: Never store database credentials in the configuration file. Use environment variables.
- **Production Settings**: In production, always set `require_https` and `cookie_secure` to `true`.
- **CORS Configuration**: Be specific about allowed origins in production to prevent cross-site attacks.
- **Debug Mode**: Never enable debug mode in production as it may expose sensitive information.
- **Token Expiration**: Set an appropriate token expiration time. Shorter times are more secure but less convenient. 