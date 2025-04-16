"""Worker components for the NetRaven application.

This package contains the components responsible for executing network device operations,
managing connections to devices, handling errors, and processing configuration data.
It includes the core functionality for running jobs against network devices, handling
concurrency, and implementing circuit breaker patterns for resilient operations.

The worker module is responsible for the actual device communication and job execution,
separating these concerns from the API and scheduling layers.
"""
