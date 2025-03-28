# NetRaven Deployment Options

## Introduction

This guide outlines the various deployment options for NetRaven, helping you choose the most appropriate setup for your environment. NetRaven supports several deployment models, from simple single-server setups to sophisticated high-availability configurations.

## Purpose

By following this guide, you will:
- Understand the different deployment options available
- Learn the advantages and considerations for each deployment type
- Select the appropriate deployment model for your environment
- Identify the resources needed for your chosen deployment

## Deployment Models

### Development Environment

A development environment is designed for testing, evaluation, or development purposes. It typically runs on a single machine with all components co-located.

#### Characteristics
- All services run on a single host
- Uses Docker Compose for service orchestration
- Simplified setup and configuration
- Not recommended for production use

#### Requirements
- A single server (physical or virtual)
- Minimum 4GB RAM, 2 CPU cores
- 20GB disk space
- Docker Engine 19.03+
- Docker Compose 1.27+

#### Deployment Steps
1. [Install Docker and Docker Compose](https://docs.docker.com/compose/install/)
2. Clone the NetRaven repository
3. Run with Docker Compose
   ```bash
   docker-compose up -d
   ```
4. Access the web interface at http://localhost:8080

#### Considerations
- Limited scalability
- No built-in redundancy
- Suitable for environments with up to 100 devices
- Ideal for pilot deployments or testing

### Standard Production Environment

A standard production environment provides a reliable, maintainable setup for organizations with moderate scaling needs.

#### Characteristics
- Runs on a single server or a small set of servers
- Uses Docker Compose or Kubernetes for orchestration
- External PostgreSQL database (optional)
- S3-compatible storage for backups

#### Requirements
- 1-2 servers (physical or virtual)
- Recommended 8GB RAM, 4 CPU cores per server
- 50GB+ disk space
- Docker Engine 19.03+ or Kubernetes 1.19+
- PostgreSQL 12+ (if using external database)

#### Deployment Steps

##### Docker Compose Option
1. Install Docker and Docker Compose
2. Configure external PostgreSQL (optional)
3. Configure S3 storage
4. Deploy with customized docker-compose.yml:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

##### Kubernetes Option
1. Set up Kubernetes cluster
2. Apply Kubernetes manifests:
   ```bash
   kubectl apply -f kubernetes/
   ```
3. Configure Ingress or LoadBalancer for API and frontend services

#### Considerations
- Suitable for environments with up to 500 devices
- Limited horizontal scaling
- Simple to maintain
- Moderate redundancy options

### High-Availability Environment

A high-availability environment is designed for mission-critical deployments where reliability and uptime are paramount.

#### Characteristics
- Distributed across multiple servers
- Kubernetes-based orchestration
- Replicated components for redundancy
- External managed database with replication
- Distributed storage system for backups
- Load balancing for all components

#### Requirements
- Minimum 3 servers for Kubernetes cluster
- Recommended 16GB RAM, 8 CPU cores per server
- 100GB+ disk space
- Kubernetes 1.19+
- PostgreSQL 12+ with replication
- S3-compatible storage with cross-region replication (optional)
- Load balancer for services

#### Deployment Steps
1. Set up Kubernetes cluster with minimum 3 nodes
2. Configure external PostgreSQL with replication
3. Configure S3 storage with appropriate redundancy
4. Deploy with high-availability Kubernetes manifests:
   ```bash
   kubectl apply -f kubernetes/ha/
   ```
5. Configure auto-scaling and pod disruption budgets:
   ```bash
   kubectl apply -f kubernetes/ha/autoscaling.yml
   ```

#### Considerations
- Suitable for environments with 500+ devices
- Provides automatic failover
- Requires Kubernetes expertise
- Higher resource requirements
- More complex to set up and maintain

### Airgapped Environment

An airgapped deployment is designed for environments with strict security requirements and no internet connectivity.

#### Characteristics
- No internet connectivity required
- All dependencies pre-packaged
- Internal container registry
- Internal S3-compatible storage
- Streamlined updates through offline packages

#### Requirements
- Similar to Standard Production or High-Availability, depending on scale
- Internal container registry
- Internal S3-compatible storage (MinIO recommended)
- Update server for offline updates

#### Deployment Steps
1. Set up internal container registry
2. Import NetRaven container images:
   ```bash
   # From internet-connected system
   docker save netraven/api netraven/gateway netraven/scheduler netraven/frontend > netraven-images.tar
   
   # On airgapped system
   docker load < netraven-images.tar
   docker tag netraven/api internal-registry:5000/netraven/api
   docker push internal-registry:5000/netraven/api
   # Repeat for other images
   ```
3. Set up MinIO for S3-compatible storage
4. Deploy using airgapped configuration files

#### Considerations
- Meets strict security and compliance requirements
- Requires additional infrastructure for internal services
- More complex update procedures
- May require customization for specific needs

### Multi-Region Deployment

A multi-region deployment distributes NetRaven across multiple geographic regions for global operations or disaster recovery.

#### Characteristics
- Components distributed across regions
- Regional API and Gateway services
- Centralized database with regional read replicas
- Cross-region backup replication
- Global load balancing

#### Requirements
- Infrastructure in multiple regions
- Global load balancing solution
- Database with cross-region replication
- S3 with cross-region replication
- Kubernetes clusters in each region

#### Deployment Steps
1. Set up Kubernetes clusters in each region
2. Configure global database solution with regional read replicas
3. Configure S3 with cross-region replication
4. Deploy regional components:
   ```bash
   # For each region
   kubectl apply -f kubernetes/multi-region/region-specific/
   ```
5. Configure global load balancing

#### Considerations
- Provides global high availability
- Reduces latency for globally distributed teams
- Complex to set up and maintain
- Requires expertise in distributed systems
- Higher operational costs

## Resource Sizing

### Small Deployment (up to 100 devices)

| Component | CPU | RAM | Storage |
|-----------|-----|-----|---------|
| API | 1 core | 2GB | 10GB |
| Gateway | 1 core | 2GB | 10GB |
| Scheduler | 0.5 core | 1GB | 5GB |
| Frontend | 0.5 core | 1GB | 5GB |
| Database | 1 core | 2GB | 20GB |
| **Total** | **4 cores** | **8GB** | **50GB** |

### Medium Deployment (100-500 devices)

| Component | CPU | RAM | Storage |
|-----------|-----|-----|---------|
| API | 2 cores | 4GB | 20GB |
| Gateway | 2 cores | 4GB | 20GB |
| Scheduler | 1 core | 2GB | 10GB |
| Frontend | 1 core | 2GB | 10GB |
| Database | 2 cores | 4GB | 50GB |
| **Total** | **8 cores** | **16GB** | **110GB** |

### Large Deployment (500+ devices)

| Component | CPU | RAM | Storage |
|-----------|-----|-----|---------|
| API | 4 cores | 8GB | 40GB |
| Gateway | 4 cores | 8GB | 40GB |
| Scheduler | 2 cores | 4GB | 20GB |
| Frontend | 2 cores | 4GB | 20GB |
| Database | 4 cores | 8GB | 100GB |
| **Total** | **16 cores** | **32GB** | **220GB** |

## Storage Options

### Local File Storage

- Simple to set up
- Limited by local disk space
- No built-in redundancy
- Suitable for development and small deployments

Configuration example:
```yaml
storage:
  type: local
  path: /app/data/backups
  backups_to_keep: 100
```

### S3 Compatible Storage

- Scalable and resilient
- Built-in redundancy options
- Works with AWS S3, MinIO, Ceph, etc.
- Recommended for production environments

Configuration example:
```yaml
storage:
  type: s3
  bucket: netraven-backups
  region: us-east-1
  access_key: your-access-key
  secret_key: your-secret-key
  path_prefix: backups/
```

### Database Storage

- Uses PostgreSQL for storing both metadata and small backups
- Limited by database size
- Not recommended for large configurations
- Useful for very small deployments

Configuration example:
```yaml
storage:
  type: database
  max_size_kb: 1024
  compression: true
```

## Database Options

### Bundled PostgreSQL

- Included in Docker Compose setup
- Simple to deploy
- Limited scaling and redundancy
- Suitable for development and small deployments

### Managed PostgreSQL

- Higher reliability and performance
- Automatic backups and maintenance
- Scaling options (vertical and read replicas)
- Recommended for production environments
- Examples: AWS RDS, Azure Database for PostgreSQL, GCP Cloud SQL

### Self-Hosted PostgreSQL Cluster

- Complete control over configuration
- High-availability options with replication
- Requires PostgreSQL expertise
- Suitable for specialized environments
- Examples: PostgreSQL with replication, Patroni, Crunchy Data

## Network Architecture

### Single-Network Deployment

```
                  ┌─────────────┐
                  │   Users     │
                  └──────┬──────┘
                         │
                         ▼
┌─────────────────────────────────────────────┐
│                 NetRaven                    │
│                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Frontend│    │  API    │    │ Gateway │  │
│  └─────────┘    └─────────┘    └─────────┘  │
│                                             │
└─────────────────────────────────────────────┘
                         │
                         ▼
               ┌──────────────────┐
               │ Network Devices  │
               └──────────────────┘
```

### Dual-Network Deployment

```
                  ┌─────────────┐
                  │   Users     │
                  └──────┬──────┘
                         │
                         ▼
┌────────────────────────────────────────┐
│          Management Network             │
│                                         │
│  ┌─────────┐    ┌─────────┐            │
│  │ Frontend│    │  API    │            │
│  └─────────┘    └─────────┘            │
│                      │                  │
└──────────────────────┼──────────────────┘
                       │
┌──────────────────────┼──────────────────┐
│          Device Network                 │
│                      │                  │
│                 ┌────▼────┐             │
│                 │ Gateway │             │
│                 └────┬────┘             │
│                      │                  │
└──────────────────────┼──────────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Network Devices  │
              └──────────────────┘
```

### DMZ Deployment

```
             ┌─────────────┐
             │   Users     │
             └──────┬──────┘
                    │
                    ▼
┌───────────────────────────────────┐
│       Management Network          │
│                                   │
│  ┌─────────┐    ┌─────────┐       │
│  │ Frontend│    │  API    │       │
│  └─────────┘    └─────────┘       │
│                      │            │
└──────────────────────┼────────────┘
                       │
┌──────────────────────┼────────────┐
│              DMZ                  │
│                      │            │
│                 ┌────▼────┐       │
│                 │ Gateway │       │
│                 └────┬────┘       │
│                      │            │
└──────────────────────┼────────────┘
                       │
┌──────────────────────┼────────────┐
│       Device Network              │
│                      │            │
│                      ▼            │
│           ┌──────────────────┐    │
│           │ Network Devices  │    │
│           └──────────────────┘    │
│                                   │
└───────────────────────────────────┘
```

## Security Considerations

### Network Segmentation
- Separate management and device networks
- Implement a DMZ for the Gateway service
- Use VLANs or network segments to isolate traffic

### Access Control
- Implement strict firewall rules
- Limit service exposure to necessary networks
- Use private networks for inter-service communication

### Encryption
- Enable TLS for all services
- Use a reverse proxy for TLS termination
- Configure secure database connections

### Authentication
- Integrate with enterprise authentication systems
- Implement multi-factor authentication
- Use certificate-based authentication for services

## Deployment Comparison

| Feature | Development | Standard Production | High-Availability | Airgapped | Multi-Region |
|---------|------------|---------------------|-------------------|-----------|--------------|
| Complexity | Low | Medium | High | High | Very High |
| Redundancy | None | Limited | High | Configurable | Very High |
| Scalability | Limited | Medium | High | Medium | Very High |
| Setup Time | Minutes | Hours | Days | Days | Weeks |
| Maintenance | Simple | Moderate | Complex | Complex | Very Complex |
| Cost | Low | Medium | High | High | Very High |
| Internet Required | Yes | Yes | Yes | No | Yes |
| Max Devices | ~100 | ~500 | 1000+ | Varies | 1000+ |

## Deployment Checklist

### Pre-Deployment
- [ ] Assess environment requirements
- [ ] Select appropriate deployment model
- [ ] Prepare infrastructure (servers, storage, networking)
- [ ] Install prerequisites (Docker, Kubernetes, etc.)
- [ ] Configure security measures

### Deployment
- [ ] Configure storage backend
- [ ] Set up database
- [ ] Deploy NetRaven services
- [ ] Configure networking and firewall rules
- [ ] Set up SSL/TLS certificates

### Post-Deployment
- [ ] Validate service connectivity
- [ ] Create initial admin user
- [ ] Configure system settings
- [ ] Set up monitoring and alerts
- [ ] Perform backup system test
- [ ] Create deployment documentation

## Related Documentation

- [Installation Guide](../getting-started/installation.md)
- [Docker Deployment](./docker-deployment.md)
- [Kubernetes Deployment](./kubernetes-deployment.md)
- [High Availability Setup](./high-availability.md)
- [Security Configuration](../admin-guide/security.md) 