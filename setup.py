from setuptools import setup, find_packages

setup(
    name="netraven",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Core dependencies
        "netmiko>=4.3.0",
        "textfsm>=1.1.3",
        "pynetbox>=7.3.2",
        "pyyaml>=6.0.1",
        "gitpython>=3.1.42",
        "boto3>=1.34.34",
        "argparse>=1.4.0",
        "schedule>=1.2.0",
        # Web backend dependencies
        "fastapi>=0.104.0",
        "uvicorn>=0.23.2",
        "sqlalchemy>=2.0.23",
        "alembic>=1.12.1",
        "pydantic>=2.4.2",
        "pydantic-settings>=2.0.3",
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "python-multipart>=0.0.6",
        "psycopg2-binary>=2.9.9",
        "email-validator>=2.0.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.24.0",
        ],
        "web": [
            # "email-validator>=2.0.0",  # Moved to main dependencies
        ],
    },
    python_requires=">=3.10",
    description="Network device configuration backup management system",
    author="Brian Larson",
    entry_points={
        "console_scripts": [
            "netraven=netraven.cli:main",
        ],
    },
    package_data={
        "netraven": ["templates/*.j2", "static/*", "web/static/*", "web/templates/*.html"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Networking",
        "Topic :: System :: Systems Administration",
    ],
    license="MIT",
    keywords="network backup configuration cisco juniper",
    url="https://github.com/yourusername/netraven",
) 