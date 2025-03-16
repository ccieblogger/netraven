# NetRaven

A Python-based tool for automated backup of Cisco network device configurations to multiple storage destinations.

## Project Structure

The project is organized into the following components:

```
netraven/
├── core/                      # Core functionality
│   ├── device_comm.py         # Device communication
│   ├── storage.py             # Storage backends (Local, S3)
│   └── ...                    # Other core modules
├── web/                       # Web interface
│   ├── backend/               # FastAPI backend
│   │   ├── app/               # Application code
│   │   │   ├── api/           # API endpoints
│   │   │   ├── core/          # Backend core modules
│   │   │   ├── db/            # Database models
│   │   │   ├── schemas/       # Pydantic schemas
│   │   │   └── storage/       # Storage adapters
│   │   └── ...                # Backend files
│   └── frontend/              # Vue.js frontend
│       ├── src/               # Frontend source
│       └── ...                # Frontend files
```

## Components

### Core

The core package provides the fundamental functionality for:
- Connecting to network devices
- Retrieving configurations
- Storing backups in various backends (local filesystem, S3)

### Web Interface

The web interface provides:
- REST API for managing devices, jobs, and backups
- User authentication and authorization
- Scheduled backup jobs
- Modern UI for configuration and monitoring

## Development

### Setting Up Your Environment

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Start the server:
   ```bash
   cd netraven/web
   docker-compose up
   ```

### API Documentation

When running, the API documentation is available at:
- http://localhost:8000/docs

## License

MIT 