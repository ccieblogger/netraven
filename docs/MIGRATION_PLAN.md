# Documentation Migration Plan

## Overview

This document outlines the plan for migrating existing NetRaven documentation to the new structure. The goal is to organize the documentation to improve findability, consistency, and completeness.

## Current Documentation

Currently, documentation is spread across:

- Root `README.md`
- Files in the `docs/` directory
- Some inline documentation in code files

## Migration Process

### Step 1: Inventory Existing Documentation

1. List all existing documentation files
2. Categorize each file according to the new structure
3. Identify gaps in current documentation

### Step 2: Map Documentation to New Structure

The following table maps existing documentation to the new structure:

| Existing Document | New Location | Action |
|-------------------|--------------|--------|
| README.md | Keep at root but streamline, pointing to docs/ | Modify |
| docs/INSTALL.md | docs/getting-started/installation.md | Move and format |
| docs/api.md | docs/developer-guide/api-reference.md | Move and enhance |
| docs/backup_storage.md | docs/developer-guide/architecture.md | Extract relevant parts |
| docs/credential_store.md | docs/admin-guide/security.md | Move and enhance |
| docs/current_implementation_plan.md | Archive | No longer needed |
| docs/device_communication.md | docs/developer-guide/architecture.md | Extract relevant parts |
| docs/gateway.md | docs/developer-guide/architecture.md | Extract relevant parts |
| docs/key_rotation.md | docs/admin-guide/security.md | Extract relevant parts |
| docs/logging.md | docs/admin-guide/system-administration.md | Move and format |
| docs/progress_summary.md | Archive | No longer needed |
| docs/project-specs.md | docs/developer-guide/architecture.md | Extract relevant parts |
| docs/testing.md | docs/developer-guide/testing.md | Move and format |
| docs/troubleshooting.md | docs/deployment/troubleshooting.md | Move and format |
| docs/web-frontend-design.md | docs/developer-guide/architecture.md | Extract relevant parts |
| docs/DEVELOPER.md | docs/developer-guide/development-workflow.md | Move and format |
| docs/README_NOTIFICATIONS.md | docs/user-guide/notifications.md | Move and format |
| docs/api_standardization.md | docs/developer-guide/api-standardization.md | Move and format |

### Step 3: Create Missing Documentation

New documentation to be created:

1. **Getting Started**
   - Overview
   - Quick Start
   - Initial Setup

2. **User Guide**
   - UI Overview
   - Managing Devices
   - Backups
   - Tags and Organization

3. **Admin Guide**
   - User Management
   - Monitoring

4. **Reference**
   - Configuration Options
   - Environment Variables
   - Command Line Tools
   - Glossary

### Step 4: Update Cross-References

Update all links and references in documentation to point to the new locations.

### Step 5: Review and Refine

1. Technical review of all migrated and new documentation
2. Editorial review for consistency and style
3. Update navigation and README files

## Migration Timeline

| Week | Tasks |
|------|-------|
| Week 1 | Inventory existing documentation, create new structure |
| Week 2 | Migrate core documentation (Getting Started and User Guide) |
| Week 3 | Migrate technical documentation (Developer and Admin Guides) |
| Week 4 | Create missing documentation, review and finalize |

## Documentation Ownership

This migration will be performed with guidance from the following stakeholders:

- Product Management: User-facing documentation
- Engineering: Technical documentation
- DevOps: Deployment and operations documentation

## Post-Migration Tasks

After the initial migration:

1. Set up a documentation review process
2. Establish governance for ongoing documentation maintenance
3. Schedule regular documentation audits
4. Consider setting up automated documentation testing (e.g., link checking) 