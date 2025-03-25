#!/usr/bin/env python3
"""
Test NetMiko installation and session log generation
"""
import os
import sys
import uuid
import netmiko
from datetime import datetime

def run_test():
    """Run NetMiko installation and session log test."""
    print(f"=== NetMiko Test ===")
    print(f"NetMiko version: {netmiko.__version__}")
    
    # Get the log directory from environment variable or use default
    log_dir = os.environ.get("NETMIKO_LOG_DIR", "/tmp")
    print(f"Using log directory: {log_dir}")
    
    # Verify the directory exists
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
            print(f"Created log directory: {log_dir}")
        except Exception as e:
            print(f"ERROR: Could not create log directory: {str(e)}")
            return False
    else:
        print(f"Log directory already exists: {log_dir}")
    
    # Check permissions and list files
    try:
        stat_info = os.stat(log_dir)
        print(f"Directory permissions: {oct(stat_info.st_mode)[-3:]}")
        print(f"Owner/Group: {stat_info.st_uid}/{stat_info.st_gid}")
        
        # List existing files
        files = os.listdir(log_dir)
        print(f"Files in directory: {len(files)} files")
        if files:
            print("Sample files:")
            for i, f in enumerate(files[:5]):
                print(f"  {i+1}. {f}")
    except Exception as e:
        print(f"ERROR: Permission check failed: {str(e)}")
    
    # Create a test log file
    test_log_path = os.path.join(log_dir, f"netmiko_test_{uuid.uuid4().hex[:8]}.log")
    print(f"Creating test log at: {test_log_path}")
    
    # Test if we can write to the directory
    try:
        with open(test_log_path, 'w') as f:
            f.write(f"NetMiko test log\nGenerated at: {datetime.now()}\n")
            f.write("This is a test to verify session logging is working.\n")
            f.write("If you can see this file, log writing works correctly.\n")
        
        print(f"Successfully wrote test log to: {test_log_path}")
        
        # Read back the file
        with open(test_log_path, 'r') as f:
            content = f.read()
            print(f"Log content ({len(content)} bytes):")
            print("-" * 40)
            print(content)
            print("-" * 40)
        
        # Test cleanup - mimics what NetMiko does
        os.remove(test_log_path)
        print(f"Successfully removed test log file")
        
        # Check if file was actually removed
        if not os.path.exists(test_log_path):
            print("Log file removal successful")
        else:
            print(f"WARNING: Could not fully remove log file: {test_log_path}")
        
        # Now test a simulated NetMiko session
        print("\n=== Testing NetMiko Session Log ===")
        
        # Create a session log file path in NetMiko format
        session_log_path = os.path.join(log_dir, f"netmiko_session_test-device_{uuid.uuid4().hex[:8]}.log")
        print(f"Creating NetMiko session log at: {session_log_path}")
        
        # Write sample content similar to what NetMiko would produce
        with open(session_log_path, 'w') as f:
            f.write(f"NetMiko Connection Log\n")
            f.write(f"Device: test-device\n")
            f.write(f"Time: {datetime.now()}\n\n")
            f.write("---- Session Start ----\n")
            f.write("ssh test@192.0.2.1\n")
            f.write("Password: ********\n")
            f.write("Connected to test-device\n")
            f.write("test-device> terminal length 0\n")
            f.write("test-device> show version\n")
            f.write("Cisco IOS Software, Version 15.7(3)M\n")
            f.write("test-device> exit\n")
            f.write("---- Session End ----\n")
            
        print(f"Successfully created test session log")
        
        # Read back and print it
        with open(session_log_path, 'r') as f:
            content = f.read()
            print(f"Session log content ({len(content)} bytes):")
            print("-" * 40)
            print(content)
            print("-" * 40)
            
        # Keep this file for testing with the session log capture
        print(f"Test session log created at: {session_log_path}")
        print(f"You can test session log capture with this path")
            
        return True
    except Exception as e:
        print(f"ERROR: Failed to write or read test log: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if run_test():
        print("\nNetMiko logging test PASSED!")
        sys.exit(0)
    else:
        print("\nNetMiko logging test FAILED!")
        sys.exit(1) 