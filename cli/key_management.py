"""
CLI tool for managing NetRaven encryption keys.

This module provides command-line tools for managing encryption keys
used for credential encryption, including key rotation, backup, and restore.
"""

import os
import sys
import argparse
import getpass
from datetime import datetime, timedelta
import json

from netraven.core.credential_store import CredentialStore
from netraven.core.key_rotation import KeyRotationManager
from netraven.core.logging import get_logger

logger = get_logger("cli.key_management")

def setup_argparse():
    """Set up argument parser for key management tool."""
    parser = argparse.ArgumentParser(
        description="NetRaven Encryption Key Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Create a new key:              key-mgmt create\n"
            "  Rotate keys:                   key-mgmt rotate\n"
            "  List all keys:                 key-mgmt list\n"
            "  Export a key backup:           key-mgmt backup -o backup.json\n"
            "  Import keys from backup:       key-mgmt restore -i backup.json\n"
            "  Get key information:           key-mgmt info -k key_12345678\n"
        )
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new encryption key')
    
    # Rotate command
    rotate_parser = subparsers.add_parser('rotate', help='Rotate encryption keys')
    rotate_parser.add_argument('--force', action='store_true', help='Force key rotation even if not needed')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all encryption keys')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Get information about an encryption key')
    info_parser.add_argument('-k', '--key', required=True, help='Key ID to get information for')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create an encrypted backup of keys')
    backup_parser.add_argument('-k', '--key', help='Specific key ID to backup (default: all keys)')
    backup_parser.add_argument('-o', '--output', required=True, help='Output file for the backup')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore keys from a backup')
    restore_parser.add_argument('-i', '--input', required=True, help='Input backup file')
    
    # Set active key command
    activate_parser = subparsers.add_parser('activate', help='Set the active encryption key')
    activate_parser.add_argument('-k', '--key', required=True, help='Key ID to set as active')
    
    return parser

def create_key(args, key_manager):
    """Create a new encryption key."""
    try:
        key_id = key_manager.create_new_key()
        print(f"Successfully created new encryption key: {key_id}")
        return 0
    except Exception as e:
        logger.error(f"Error creating encryption key: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def rotate_keys(args, key_manager, credential_store):
    """Rotate encryption keys."""
    try:
        new_key_id = key_manager.rotate_keys(force=args.force)
        if new_key_id:
            print(f"Successfully rotated encryption keys. New active key: {new_key_id}")
            
            # Re-encrypt all credentials with the new key
            count = credential_store.reencrypt_all_credentials(new_key_id)
            print(f"Re-encrypted {count} credentials with the new key.")
            return 0
        else:
            print("Key rotation not needed or failed.")
            return 1
    except Exception as e:
        logger.error(f"Error rotating encryption keys: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def list_keys(args, key_manager):
    """List all encryption keys."""
    try:
        with key_manager._lock:
            if not key_manager._key_metadata:
                print("No encryption keys found.")
                return 0
            
            print("\nEncryption Keys:")
            print("-" * 80)
            print(f"{'Key ID':<20} {'Created':<20} {'Source':<15} {'Active':<8}")
            print("-" * 80)
            
            for key_id, meta in key_manager._key_metadata.items():
                created_at = meta.get("created_at", "Unknown")
                if created_at and created_at != "Unknown":
                    try:
                        dt = datetime.fromisoformat(created_at)
                        created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                
                source = meta.get("source", "Unknown")
                active = "Yes" if meta.get("active", False) else "No"
                
                print(f"{key_id:<20} {created_at:<20} {source:<15} {active:<8}")
            
            print("-" * 80)
            return 0
    except Exception as e:
        logger.error(f"Error listing encryption keys: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def get_key_info(args, key_manager):
    """Get information about a specific encryption key."""
    try:
        with key_manager._lock:
            key_id = args.key
            if key_id not in key_manager._key_metadata:
                print(f"Key not found: {key_id}")
                return 1
            
            meta = key_manager._key_metadata[key_id]
            
            print("\nKey Information:")
            print("-" * 50)
            print(f"Key ID:        {key_id}")
            
            created_at = meta.get("created_at", "Unknown")
            if created_at and created_at != "Unknown":
                try:
                    dt = datetime.fromisoformat(created_at)
                    print(f"Created:       {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Calculate age
                    age = datetime.utcnow() - dt
                    print(f"Age:           {age.days} days")
                except ValueError:
                    print(f"Created:       {created_at}")
            
            print(f"Source:        {meta.get('source', 'Unknown')}")
            print(f"Active:        {'Yes' if meta.get('active', False) else 'No'}")
            
            if meta.get("imported_at"):
                try:
                    dt = datetime.fromisoformat(meta.get("imported_at"))
                    print(f"Imported:      {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                except ValueError:
                    print(f"Imported:      {meta.get('imported_at')}")
            
            print("-" * 50)
            return 0
    except Exception as e:
        logger.error(f"Error getting key information: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def backup_keys(args, key_manager):
    """Create an encrypted backup of keys."""
    try:
        # Get password for encryption
        password = getpass.getpass("Enter password for encryption: ")
        confirm = getpass.getpass("Confirm password: ")
        
        if password != confirm:
            print("Error: Passwords do not match.")
            return 1
        
        if len(password) < 8:
            print("Error: Password must be at least 8 characters.")
            return 1
        
        # Create backup
        backup_data = key_manager.export_key_backup(password, args.key)
        
        # Save to file
        with open(args.output, "w") as f:
            f.write(backup_data)
        
        print(f"Successfully created key backup: {args.output}")
        return 0
    except Exception as e:
        logger.error(f"Error creating key backup: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def restore_keys(args, key_manager):
    """Restore keys from a backup."""
    try:
        # Read backup data
        with open(args.input, "r") as f:
            backup_data = f.read()
        
        # Get password for decryption
        password = getpass.getpass("Enter password for decryption: ")
        
        # Restore keys
        imported_keys = key_manager.import_key_backup(backup_data, password)
        
        print(f"Successfully imported {len(imported_keys)} keys from backup:")
        for key_id in imported_keys:
            print(f"  - {key_id}")
        
        return 0
    except Exception as e:
        logger.error(f"Error restoring keys: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def activate_key(args, key_manager):
    """Set the active encryption key."""
    try:
        key_id = args.key
        success = key_manager.activate_key(key_id)
        
        if success:
            print(f"Successfully set active encryption key to: {key_id}")
            return 0
        else:
            print(f"Failed to set active key: {key_id}")
            return 1
    except Exception as e:
        logger.error(f"Error setting active key: {str(e)}")
        print(f"Error: {str(e)}")
        return 1

def main():
    """Main entry point for the key management tool."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Create credential store and key manager
    try:
        credential_store = CredentialStore()
        key_manager = KeyRotationManager(credential_store=credential_store)
        credential_store.set_key_manager(key_manager)
    except Exception as e:
        logger.error(f"Error initializing key management: {str(e)}")
        print(f"Error: {str(e)}")
        return 1
    
    # Execute appropriate command
    if args.command == 'create':
        return create_key(args, key_manager)
    elif args.command == 'rotate':
        return rotate_keys(args, key_manager, credential_store)
    elif args.command == 'list':
        return list_keys(args, key_manager)
    elif args.command == 'info':
        return get_key_info(args, key_manager)
    elif args.command == 'backup':
        return backup_keys(args, key_manager)
    elif args.command == 'restore':
        return restore_keys(args, key_manager)
    elif args.command == 'activate':
        return activate_key(args, key_manager)
    else:
        parser.print_help()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 