"""
Configuration management module for Netbox Updater.

This module provides functionality to load and manage configuration settings
from both default values and a user-provided configuration file.
"""

import os
from pathlib import Path
import yaml
from typing import Dict, Any, Tuple
from .storage import get_storage_backend, StorageBackend

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Default configuration
DEFAULT_CONFIG = {
    'backup': {
        'storage': {
            'type': 'local',  # 'local' or 's3'
            'local': {
                'directory': str(Path.home() / 'network_backups')
            },
            's3': {
                'bucket': '',
                'prefix': 'network_backups/',
                'region': '',
                'access_key': '',
                'secret_key': '',
                'endpoint_url': None
            }
        },
        'format': '{host}_config.txt',  # Format string for backup files
        'git': {
            'enabled': False,
            'repo_url': None,  # Remote repository URL
            'branch': 'main',  # Branch to push to
            'commit_message': 'Updated configuration for {host}',  # Commit message format
            'author_name': 'Netbox Updater',  # Git author name
            'author_email': 'netbox@example.com'  # Git author email
        }
    },
    'logging': {
        'level': 'INFO',
        'directory': 'logs',
        'filename': 'netraven.log'
    }
}

def init_git_repo(config: Dict[str, Any]) -> None:
    """
    Initialize Git repository for backups if enabled in config.
    
    Args:
        config: Configuration dictionary
    """
    if not config['backup']['git']['enabled']:
        return
        
    try:
        import git
        
        # Only initialize Git for local storage
        if config['backup']['storage']['type'] != 'local':
            print("Git backup only supported with local storage")
            return
            
        backup_dir = Path(config['backup']['storage']['local']['directory']).expanduser().resolve()
        
        # Initialize repository if it doesn't exist
        if not (backup_dir / '.git').exists():
            repo = git.Repo.init(backup_dir)
            
            # Configure Git user
            with repo.config_writer() as git_config:
                git_config.set_value('user', 'name', config['backup']['git']['author_name'])
                git_config.set_value('user', 'email', config['backup']['git']['author_email'])
            
            # Add remote if URL is configured
            if config['backup']['git']['repo_url']:
                try:
                    repo.create_remote('origin', config['backup']['git']['repo_url'])
                except git.GitCommandError:
                    # Remote might already exist
                    pass
                    
            # Create .gitignore to prevent accidental nested repos
            gitignore_path = backup_dir / '.gitignore'
            if not gitignore_path.exists():
                with open(gitignore_path, 'w') as f:
                    f.write("""# NetRaven - Network Configuration Backup
# Ignore nested Git repositories
.git/

# Ignore temporary files
*.tmp
*.bak
*~

# Ignore sensitive data that might be accidentally saved
*.key
*.pem
credentials.yml
secrets.yml

# Ignore logs
*.log
""")
                
                # Add and commit .gitignore
                try:
                    repo.git.add('.gitignore')
                    repo.index.commit('Add initial .gitignore file')
                    print("Created and committed .gitignore file")
                    
                    # Push if remote is configured
                    if config['backup']['git']['repo_url']:
                        try:
                            origin = repo.remote('origin')
                            origin.push(config['backup']['git']['branch'])
                            print(f"Successfully pushed .gitignore to remote: {config['backup']['git']['repo_url']}")
                        except git.GitCommandError as e:
                            print(f"Error pushing .gitignore to remote: {e}")
                except Exception as e:
                    print(f"Error committing .gitignore file: {e}")
                    
    except ImportError:
        print("GitPython package not installed. Git functionality disabled.")
    except Exception as e:
        print(f"Error initializing Git repository: {e}")

def commit_backup(host: str, filepath: str, config: Dict[str, Any]) -> None:
    """
    Commit and push a backup file to Git if enabled.
    
    Args:
        host: Device hostname or IP address
        filepath: Path to the backup file (relative to the backup directory)
        config: Configuration dictionary
    """
    if not config['backup']['git']['enabled']:
        return
        
    # Only commit for local storage
    if config['backup']['storage']['type'] != 'local':
        return
        
    try:
        import git
        
        backup_dir = Path(config['backup']['storage']['local']['directory']).expanduser().resolve()
        repo = git.Repo(backup_dir)
        
        # Log the git commit attempt
        print(f"Committing file {filepath} to git repository at {backup_dir}")
        
        # Stage the file - using just the filename since we're already in the backup directory's repo
        repo.git.add(filepath)
        
        # Create commit
        commit_message = config['backup']['git']['commit_message'].format(host=host)
        repo.index.commit(commit_message)
        print(f"Successfully committed with message: {commit_message}")
        
        # Push if remote is configured
        if config['backup']['git']['repo_url']:
            try:
                origin = repo.remote('origin')
                origin.push(config['backup']['git']['branch'])
                print(f"Successfully pushed to remote: {config['backup']['git']['repo_url']}")
            except git.GitCommandError as e:
                print(f"Error pushing to remote: {e}")
                
    except ImportError:
        print("GitPython package not installed. Git functionality disabled.")
    except Exception as e:
        print(f"Error committing backup: {e}")
        import traceback
        traceback.print_exc()

def load_config(config_file: str = None) -> Tuple[Dict[str, Any], StorageBackend]:
    """
    Load configuration from file, falling back to defaults if not found.
    
    Args:
        config_file: Path to YAML configuration file (optional)
        
    Returns:
        Tuple containing:
        - Dict containing configuration settings
        - StorageBackend instance for handling backups
    """
    config = DEFAULT_CONFIG.copy()
    
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            try:
                with open(config_path) as f:
                    user_config = yaml.safe_load(f)
                if user_config:
                    # Deep update the configuration
                    _deep_update(config, user_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
    
    # Get storage backend
    storage = get_storage_backend(config)
    
    # Initialize Git repository if enabled (only for local storage)
    if config['backup']['storage']['type'] == 'local':
        init_git_repo(config)
    
    return config, storage

def _deep_update(base_dict: Dict, update_dict: Dict) -> None:
    """
    Recursively update a dictionary with another dictionary.
    
    Args:
        base_dict: Base dictionary to update
        update_dict: Dictionary with values to update
    """
    for key, value in update_dict.items():
        if (
            key in base_dict 
            and isinstance(base_dict[key], dict) 
            and isinstance(value, dict)
        ):
            _deep_update(base_dict[key], value)
        else:
            base_dict[key] = value

def get_backup_path(host: str, config: Dict[str, Any]) -> str:
    """
    Get the relative path for a device backup file.
    
    Args:
        host: Device hostname or IP address
        config: Configuration dictionary
        
    Returns:
        str: Relative path for the backup file
    """
    return config['backup']['format'].format(host=host) 