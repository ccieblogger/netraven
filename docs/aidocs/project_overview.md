# NetRaven Project Overview

## Introduction

NetRaven is a specialized platform designed to facilitate the scheduling and execution of jobs that communicate with remote hosts via SSH (with HTTP/REST support planned for future releases). Its primary purpose is to run commands on remote devices, with the initial supported job type focused on retrieving network device configuration files and storing them in a local Git repository. NetRaven provides a secure, scalable, and modular architecture to streamline these operations, making it an essential tool for network administrators and engineers.

## Deployment Model

NetRaven is deployed using a containerized architecture, leveraging Docker and Docker Compose for ease of deployment and scalability. The platform consists of multiple services, each running in its own container, including:
- **PostgreSQL Database**: Stores configuration, logs, and other data.
- **Backend API**: Provides REST API endpoints for managing devices and configurations.
- **Scheduler**: Handles recurring tasks like backups and compliance checks.
- **Device Gateway**: Facilitates secure communication with network devices.
- **Frontend**: A Vue.js-based user interface for managing the platform.

For detailed deployment instructions, refer to the [Deployment Guide](../deployment/deployment-options.md).

## Technologies Used

NetRaven leverages modern technologies to deliver a robust and scalable solution:
- **Backend**: Python, FastAPI
- **Frontend**: Vue.js
- **Database**: PostgreSQL
- **Containerization**: Docker
- **Storage**: Local filesystem, S3-compatible storage
- **Authentication**: Token-based authentication using JWT

## System Design and Architecture

NetRaven is built with modularity and scalability in mind:
- **Frontend**: A Vue.js-based interface for managing devices and schedules. See the [Frontend Documentation](../developer-guide/frontend-overview.md).
- **API**: The central communication layer, enabling interaction between the frontend, scheduler, and gateway components. See the [API Documentation](./api-documentation/api-overview.md).
- **Gateway**: Provides secure communication to network devices. See the [Gateway Documentation](./gateway/gateway-overview.md).
- **Scheduler**: Manages scheduling of tasks and jobs. See the [Scheduler Documentation](./scheduler/scheduler-overview.md).
- **TokenRefresh**: Manages refreshing API and security tokens. See the [TokenRefresh Documentation](./tokenrefresh/tokenrefresh-overview.md).

For a detailed architecture overview, see the [Architecture Documentation](./architecture/architecture-overview.md).

## Key Features

- **Device Inventory**: Add, Edit, Delete, and list devices
- **Device Tagging**: Use tags to group devices
- **Configuration backup**: Backup and diff device configurations.
- **Automation**: Schedule recurring tasks and operations.
- **JobLogging**: Detailed logging of device communication and job status.
- **Authentication**: Robust authentication system using JWT

## 

## Documentation Links

- **TBD**

## Coding Principles

- Always prefer simple solutions.
- Avoid duplication of code whenever possible, which means checking for other areas of the codebase that might already have similar code or functionality and leverage that before introducing something new. 
- only make changes that are requested or related to the change being requested.
- when fixing a bug or issue do not introduce a new pattern or technology without exhausting all options with the existing implementation. If you do need to introduce a new pattern or technology make sure to remove the old implemenation to prevent duplicate logic and legacy code.
- always consider the project deployment model when introducing changes to make sure that those changes are incorporated into the deployment model.
- Always clean up after yourself. If you introduce temporary files or code make sure to remove it when its no longer needed.
- avoid writing scripts in files if possible, especially if its only going to be used once or temporarily.
- avoid having files over 200-300 lines of code. Refactor at that point.
- Mocking data should only be used for tests, never use it for dev or prod.
- Never add stubbing or fake data patterns to code the affects dev or prod.
- Always present a plan that outlines your proposed changes when intially asked to update, enhance, create, or fix an issue and then wait for approval of the plan before proceeding. The plan should be broken into phases so as not to make to many changes all at once.
- Always ask if you can proced before moving on the the next phase of your plan.
- Always git state, commit, and push after every successfull completion of a phase.
- Without being to verbose and inefficient explain what you are doing as you code, test, or make changes so that I can understand what you are doing while you are doing it.