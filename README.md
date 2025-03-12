# Netbox Updater

A Python-based tool to parse Cisco device configurations and update Netbox inventory accordingly.

## Description

This tool parses full running configuration files from Cisco network devices (routers, switches, firewalls, and WLCs), converts the data into a structured format, and uses it to create, update, or remove device information in a Netbox instance.

## Features

- Parse Cisco device configurations
- Create/Update/Remove devices in Netbox
- Git integration for configuration file retrieval
- Secure credential management
- Comprehensive logging system

## Requirementsoob

- Python 3.10+
- Required Python packages (see requirements.txt)
- Access to a Netbox instance

## Installation

1. Clone the repository:
```bash
git clone [repository-url]
cd netraven
```

2. Create and activate a virtual environment:
```