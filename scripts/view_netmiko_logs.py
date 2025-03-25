#!/usr/bin/env python3
"""
NetMiko Log Viewer and Manager

This script provides utilities for viewing, analyzing, and managing NetMiko logs.
It's designed to work with the NetRaven application's log volume mount.
"""

import os
import sys
import glob
import argparse
import time
from datetime import datetime

def get_log_dir():
    """Get the NetMiko logs directory from environment or default."""
    return os.environ.get("NETMIKO_LOG_DIR", "/tmp/netmiko_logs")

def list_logs(args):
    """List all NetMiko logs in the directory."""
    log_dir = get_log_dir()
    if not os.path.exists(log_dir):
        print(f"Log directory {log_dir} does not exist.")
        return
    
    pattern = os.path.join(log_dir, "netmiko_session_*.log")
    log_files = glob.glob(pattern)
    
    if not log_files:
        print(f"No NetMiko log files found in {log_dir}")
        return
    
    print(f"Found {len(log_files)} NetMiko log files in {log_dir}:")
    print("-" * 80)
    
    # Sort by modification time (newest first)
    log_files.sort(key=os.path.getmtime, reverse=True)
    
    for i, log_file in enumerate(log_files):
        filename = os.path.basename(log_file)
        size = os.path.getsize(log_file)
        mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
        
        # Extract host from filename if possible
        try:
            # Format is typically netmiko_session_HOST_UUID.log
            host = filename.split("_")[2]
        except:
            host = "unknown"
            
        # Print limited number if requested
        if args.limit and i >= args.limit:
            print(f"... and {len(log_files) - args.limit} more log files")
            break
            
        print(f"{i+1}. {filename}")
        print(f"   Host: {host}")
        print(f"   Size: {size} bytes")
        print(f"   Time: {mtime}")
        
        if args.show_content:
            with open(log_file, 'r') as f:
                content = f.read()
                if len(content) > 500:
                    content = content[:250] + "\n...\n" + content[-250:]
                print("   Preview:")
                print("   " + content.replace("\n", "\n   "))
        print("-" * 80)

def view_log(args):
    """View a specific NetMiko log file."""
    log_dir = get_log_dir()
    pattern = os.path.join(log_dir, "netmiko_session_*.log")
    log_files = glob.glob(pattern)
    
    if not log_files:
        print(f"No NetMiko log files found in {log_dir}")
        return
    
    # Sort by modification time (newest first)
    log_files.sort(key=os.path.getmtime, reverse=True)
    
    if args.index is not None:
        # View by index
        if args.index < 1 or args.index > len(log_files):
            print(f"Invalid index. Please specify a value between 1 and {len(log_files)}")
            return
        
        log_file = log_files[args.index - 1]
    elif args.file:
        # View by filename
        log_file = os.path.join(log_dir, args.file)
        if not os.path.exists(log_file):
            print(f"Log file {log_file} does not exist.")
            return
    else:
        # View most recent log
        log_file = log_files[0]
    
    # Display log file information
    filename = os.path.basename(log_file)
    size = os.path.getsize(log_file)
    mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
    
    print(f"Log File: {filename}")
    print(f"Size: {size} bytes")
    print(f"Modified: {mtime}")
    print("-" * 80)
    
    # Display log content
    with open(log_file, 'r') as f:
        content = f.read()
        print(content)

def cleanup(args):
    """Cleanup old NetMiko log files."""
    log_dir = get_log_dir()
    pattern = os.path.join(log_dir, "netmiko_session_*.log")
    log_files = glob.glob(pattern)
    
    if not log_files:
        print(f"No NetMiko log files found in {log_dir}")
        return
    
    # Get current time
    now = time.time()
    
    # Define age threshold
    age_seconds = args.days * 86400
    
    # Find old logs
    old_logs = []
    for log_file in log_files:
        mtime = os.path.getmtime(log_file)
        age = now - mtime
        
        if age > age_seconds:
            old_logs.append(log_file)
    
    if not old_logs:
        print(f"No logs older than {args.days} days found.")
        return
    
    if args.dry_run:
        print(f"Would delete {len(old_logs)} logs older than {args.days} days:")
        for log in old_logs:
            print(f"  {os.path.basename(log)}")
    else:
        print(f"Deleting {len(old_logs)} logs older than {args.days} days...")
        for log in old_logs:
            try:
                os.remove(log)
                print(f"  Deleted {os.path.basename(log)}")
            except Exception as e:
                print(f"  Failed to delete {os.path.basename(log)}: {str(e)}")

def debug_logs(args):
    """Debug NetMiko logging - scan entire tmp directory."""
    print("==== NetMiko Log Debugging ====")
    print(f"1. Environment variable NETMIKO_LOG_DIR: {os.environ.get('NETMIKO_LOG_DIR', 'not set')}")
    
    # Check /tmp directory
    print("\n2. Checking /tmp directory for any NetMiko logs:")
    tmp_files = glob.glob("/tmp/netmiko*") + glob.glob("/tmp/*/netmiko*")
    if tmp_files:
        print(f"Found {len(tmp_files)} matching files in /tmp:")
        for i, file in enumerate(tmp_files):
            size = os.path.getsize(file) if os.path.exists(file) else 0
            print(f"  {i+1}. {file} ({size} bytes)")
    else:
        print("No netmiko files found in /tmp")
    
    # Check configured log directory
    log_dir = get_log_dir()
    print(f"\n3. Checking configured log directory: {log_dir}")
    if os.path.exists(log_dir):
        print(f"Directory exists: {log_dir}")
        all_files = glob.glob(f"{log_dir}/*")
        print(f"Total files in directory: {len(all_files)}")
        for i, file in enumerate(all_files[:10]):  # Show first 10 files
            size = os.path.getsize(file) if os.path.exists(file) else 0
            print(f"  {i+1}. {os.path.basename(file)} ({size} bytes)")
        if len(all_files) > 10:
            print(f"  ... and {len(all_files) - 10} more files")
    else:
        print(f"Directory does not exist: {log_dir}")
    
    # Check volume mounting
    print("\n4. Check Docker volume:")
    print("To inspect the Docker volume, run the following command:")
    print("  docker volume inspect netmiko_logs")
    print("To see if it's properly mounted, run:")
    print("  docker exec device_gateway ls -la /tmp/netmiko_logs")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="NetMiko Log Viewer and Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List logs command
    list_parser = subparsers.add_parser("list", help="List NetMiko log files")
    list_parser.add_argument("--limit", type=int, help="Limit the number of logs displayed")
    list_parser.add_argument("--show-content", action="store_true", help="Show log content preview")
    
    # View log command
    view_parser = subparsers.add_parser("view", help="View a NetMiko log file")
    view_parser.add_argument("--index", type=int, help="Index of the log file to view (from list command)")
    view_parser.add_argument("--file", help="Filename of the log to view")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup old NetMiko log files")
    cleanup_parser.add_argument("--days", type=int, default=7, help="Delete logs older than this many days")
    cleanup_parser.add_argument("--dry-run", action="store_true", help="Don't actually delete files, just show what would be deleted")
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug NetMiko logging")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_logs(args)
    elif args.command == "view":
        view_log(args)
    elif args.command == "cleanup":
        cleanup(args)
    elif args.command == "debug":
        debug_logs(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 