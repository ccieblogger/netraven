#!/usr/bin/env python3
"""
Test NetMiko Session Log Capture

This script directly tests the log_netmiko_session function
with a test session log file.
"""
import os
import sys
import uuid
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_log_capture")

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def setup_test_environment():
    """Set up the test environment with necessary variables."""
    from netraven.jobs.device_logging import start_job_session, register_device
    
    # Start a test job session
    session_id = start_job_session(description="Test NetMiko logging", user_id="admin")
    logger.info(f"Started test job session: {session_id}")
    
    # Register a test device
    device_id = str(uuid.uuid4())
    register_device(
        device_id=device_id,
        hostname="test-device",
        device_type="cisco_ios",
        session_id=session_id
    )
    logger.info(f"Registered test device: {device_id}")
    
    return session_id, device_id

def create_test_session_log():
    """Create a test NetMiko session log file."""
    # Get the log directory from environment variable or use default
    log_dir = os.environ.get("NETMIKO_LOG_DIR", "/tmp/netmiko_logs")
    
    # Ensure directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a session log file path in NetMiko format
    session_log_path = os.path.join(log_dir, f"netmiko_session_test-device_{uuid.uuid4().hex[:8]}.log")
    logger.info(f"Creating test session log at: {session_log_path}")
    
    # Write sample content similar to what NetMiko would produce
    with open(session_log_path, 'w') as f:
        f.write(f"NetMiko Connection Log\n")
        f.write(f"Device: test-device\n")
        f.write(f"Time: {datetime.now()}\n\n")
        f.write("---- Session Start ----\n")
        f.write("ssh test@192.0.2.1\n")
        f.write("Password: test123\n")  # Test password masking
        f.write("Connected to test-device\n")
        f.write("test-device> terminal length 0\n")
        f.write("test-device> show version\n")
        f.write("Cisco IOS Software, Version 15.7(3)M\n")
        f.write("test-device> exit\n")
        f.write("---- Session End ----\n")
    
    return session_log_path

def test_log_capture():
    """Test the log_netmiko_session function."""
    try:
        # Import after setup
        from netraven.jobs.device_logging import log_netmiko_session, end_job_session
        
        # Setup test environment
        session_id, device_id = setup_test_environment()
        
        # Create test session log
        session_log_path = create_test_session_log()
        
        # Call the function under test
        logger.info(f"Testing log_netmiko_session with file: {session_log_path}")
        result = log_netmiko_session(
            device_id=device_id,
            session_log_path=session_log_path,
            username="test",
            session_id=session_id,
            mask_passwords=True
        )
        
        # Check result
        if result:
            logger.info("✓ log_netmiko_session returned SUCCESS")
        else:
            logger.error("✗ log_netmiko_session returned FAILURE")
            
        # End the job session
        end_job_session(session_id=session_id, success=result)
        
        # Check the database for the log entry
        logger.info("Checking database for session log entry...")
        from netraven.core.db import SessionLocal
        from netraven.web.models.job_log import JobLogEntry
        
        db = SessionLocal()
        try:
            # Query for log entries with this session
            entries = db.query(JobLogEntry).filter(
                JobLogEntry.job_log_id == session_id,
                JobLogEntry.category == "device communication"
            ).all()
            
            if entries:
                logger.info(f"✓ Found {len(entries)} matching log entries in database")
                
                # Check if any have session_log_content
                session_logs = [e for e in entries if e.session_log_content is not None]
                if session_logs:
                    logger.info(f"✓ Found {len(session_logs)} entries with session_log_content")
                    
                    # Check the first one
                    log_entry = session_logs[0]
                    log_content = log_entry.session_log_content
                    
                    # Check if it contains masked passwords
                    if "Password: ********" in log_content:
                        logger.info("✓ Password correctly masked in log content")
                    else:
                        logger.warning("! Password not properly masked in log content")
                        
                    # Check if session_log_path is set
                    if log_entry.session_log_path:
                        logger.info(f"✓ session_log_path is set: {log_entry.session_log_path}")
                    else:
                        logger.warning("! session_log_path is not set")
                else:
                    logger.error("✗ No entries with session_log_content found")
            else:
                logger.error("✗ No matching log entries found in database")
                
        finally:
            db.close()
            
        return result
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_log_capture():
        logger.info("TEST PASSED: NetMiko session log capture works correctly")
        sys.exit(0)
    else:
        logger.error("TEST FAILED: NetMiko session log capture has issues")
        sys.exit(1) 