"""
Base page object for all page objects.
"""
from playwright.sync_api import Page, expect
import os
import time
import logging

logger = logging.getLogger(__name__)

class BasePage:
    """Base page object for all page objects."""
    
    def __init__(self, page: Page, app_config: dict):
        """Initialize the base page object.
        
        Args:
            page: The Playwright page object
            app_config: Configuration dictionary with UI settings
        """
        self.page = page
        self.app_config = app_config
        # Use UI URL from container configuration
        self.base_url = app_config.get("ui_url", "http://frontend:8080")
        # Use timeout from container configuration
        self.timeout = app_config.get("test_timeout", 10000)
    
    def navigate(self, path=""):
        """Navigate to a page.
        
        Args:
            path: The path to navigate to, appended to the base URL
        
        Returns:
            The page object for chaining
        """
        url = f"{self.base_url}{path}"
        self.page.goto(url)
        self.page.wait_for_network_idle(timeout=self.timeout)
        return self
    
    def wait_for_selector(self, selector, timeout=None):
        """Wait for a selector to be visible.
        
        Args:
            selector: The selector to wait for
            timeout: The timeout in milliseconds, defaults to configuration timeout
            
        Returns:
            The element that was found
        """
        if timeout is None:
            timeout = self.timeout
        return self.page.wait_for_selector(selector, timeout=timeout)
    
    def fill(self, selector, value):
        """Fill a form field.
        
        Args:
            selector: The selector for the form field
            value: The value to fill in
            
        Returns:
            The page object for chaining
        """
        self.page.fill(selector, value)
        return self
    
    def click(self, selector):
        """Click an element.
        
        Args:
            selector: The selector for the element to click
            
        Returns:
            The page object for chaining
        """
        self.page.click(selector)
        return self
    
    def select_option(self, selector, value):
        """Select an option from a dropdown.
        
        Args:
            selector: The selector for the dropdown
            value: The value to select
            
        Returns:
            The page object for chaining
        """
        self.page.select_option(selector, value)
        return self
    
    def is_visible(self, selector):
        """Check if an element is visible.
        
        Args:
            selector: The selector for the element
            
        Returns:
            True if the element is visible, False otherwise
        """
        return self.page.is_visible(selector)
    
    def get_text(self, selector):
        """Get the text content of an element.
        
        Args:
            selector: The selector for the element
            
        Returns:
            The text content of the element
        """
        return self.page.text_content(selector)
    
    def wait_for_network_idle(self, timeout=5000):
        """Wait for network activity to subside.
        
        Args:
            timeout: The timeout in milliseconds
        
        Returns:
            The page object for chaining
        """
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self
    
    def wait_for_navigation(self, timeout=None):
        """Wait for navigation to complete.
        
        Args:
            timeout: The timeout in milliseconds, defaults to configuration timeout
            
        Returns:
            The page object for chaining
        """
        if timeout is None:
            timeout = self.timeout
        self.page.wait_for_load_state("networkidle", timeout=timeout)
        return self
    
    def take_screenshot(self, name=None):
        """Take a screenshot for debugging purposes.
        
        Args:
            name: Optional name for the screenshot file
            
        Returns:
            The path to the screenshot file
        """
        # Use container paths for screenshots
        if not os.path.exists("/app/test-artifacts"):
            os.makedirs("/app/test-artifacts", exist_ok=True)
            
        if name is None:
            name = f"screenshot_{int(time.time())}"
            
        path = f"/app/test-artifacts/{name}.png"
        self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
        return path
    
    def expect_to_be_visible(self, selector, message=None):
        """Assert that an element is visible.
        
        Args:
            selector: The selector for the element
            message: Optional message for the assertion
            
        Returns:
            The page object for chaining
        """
        expect(self.page.locator(selector)).to_be_visible()
        return self
    
    def expect_to_contain_text(self, selector, text, message=None):
        """Assert that an element contains text.
        
        Args:
            selector: The selector for the element
            text: The text to check for
            message: Optional message for the assertion
            
        Returns:
            The page object for chaining
        """
        expect(self.page.locator(selector)).to_contain_text(text)
        return self
    
    def expect_navigation_to_url(self, url_pattern, timeout=None):
        """Assert that navigation occurs to a URL matching a pattern.
        
        Args:
            url_pattern: The URL pattern to check for
            timeout: The timeout in milliseconds, defaults to configuration timeout
            
        Returns:
            The page object for chaining
        """
        if timeout is None:
            timeout = self.timeout
        self.page.wait_for_url(url_pattern, timeout=timeout)
        return self 