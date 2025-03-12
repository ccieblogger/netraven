from setuptools import setup, find_packages

setup(
    name="netraven",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "netmiko>=4.3.0",
        "textfsm>=1.1.3",
        "pynetbox>=7.3.2",
        "pyyaml>=6.0.1",
        "gitpython>=3.1.42",
        "boto3>=1.34.34",
        "argparse>=1.4.0",
    ],
    python_requires=">=3.8",
) 