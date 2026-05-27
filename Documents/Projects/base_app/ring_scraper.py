import requests
from typing import Dict, List, Optional, Any
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json


class RingAPI:
    """Client for Ring.com web scraping"""
    
    def __init__(self, username: str, password: str, url: str = "https://ring.com"):
        """
        Initialize Ring scraper client
        
        Args:
            username: Ring account email
            password: Ring account password
            url: Ring URL (default: https://ring.com)
        """
        self.username = username
        self.password = password
        self.url = url.rstrip('/')
        self.driver = None
        
    def _init_driver(self):
        """Initialize Chrome WebDriver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use Chromium binary from environment or default
        chrome_binary = os.getenv('CHROME_BIN', '/usr/bin/chromium')
        if os.path.exists(chrome_binary):
            chrome_options.binary_location = chrome_binary
        
        # Set ChromeDriver path
        service = None
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
        if os.path.exists(chromedriver_path):
            service = Service(executable_path=chromedriver_path)
        
        try:
            if service:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Remove automation flags
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            print(f"Failed to initialize Chrome driver: {str(e)}")
            raise
        
    def _cleanup(self):
        """Close and cleanup WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def login(self) -> bool:
        """
        Login to Ring.com
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            if not self.driver:
                self._init_driver()
            
            print(f"Navigating to {self.url}/users/sign_in")
            # Navigate to Ring login page
            self.driver.get(f"{self.url}/users/sign_in")
            
            # Wait for page to load fully
            time.sleep(5)
            
            print(f"Page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")
            
            # Take screenshot for debugging
            try:
                self.driver.save_screenshot('/tmp/ring_login_page.png')
                print("Login page screenshot saved to /tmp/ring_login_page.png")
            except:
                pass
            
            # STEP 1: Enter email and click Continue
            # Try multiple strategies for finding email field
            email_field = None
            email_selectors = [
                "#user_email",
                "input[type='email']",
                "input[name='user[email]']",
                "input[name='email']",
                "input[id*='email']",
                "input[placeholder*='email']",
                "input[placeholder*='Email']"
            ]
            
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_field:
                        print(f"Found email field with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                print("Could not find email field")
                return False
            
            email_field.clear()
            email_field.send_keys(self.username)
            print(f"Entered email: {self.username}")
            time.sleep(1)
            
            # Look for Continue button (Ring's two-step login)
            continue_button = None
            continue_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[name='commit']",
                "input[name='commit']",
                "button:contains('Continue')",
                "input[value='Continue']",
                ".btn-primary",
                ".submit-button"
            ]
            
            for selector in continue_selectors:
                try:
                    if 'contains' in selector:
                        # Skip XPath selectors for now
                        continue
                    continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if continue_button:
                        print(f"Found continue button with selector: {selector}")
                        break
                except:
                    continue
            
            if not continue_button:
                print("Could not find continue button")
                return False
            
            continue_button.click()
            print("Clicked continue button")
            time.sleep(3)
            
            # STEP 2: Enter password on next page
            print("Looking for password field...")
            try:
                self.driver.save_screenshot('/tmp/ring_password_page.png')
                print("Password page screenshot saved")
            except:
                pass
            
            for selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_field:
                        print(f"Found email field with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_field:
                print("Could not find email field")
                return False
            
            email_field.clear()
            email_field.send_keys(self.username)
            print(f"Entered email: {self.username}")
            time.sleep(1)
            
            # Look for Continue button (Ring's two-step login)
            continue_button = None
            continue_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[name='commit']",
                "input[name='commit']",
                "button:contains('Continue')",
                "input[value='Continue']",
                ".btn-primary",
                ".submit-button"
            ]
            
            for selector in continue_selectors:
                try:
                    if 'contains' in selector:
                        # Skip XPath selectors for now
                        continue
                    continue_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if continue_button:
                        print(f"Found continue button with selector: {selector}")
                        break
                except:
                    continue
            
            if not continue_button:
                print("Could not find continue button")
                return False
            
            continue_button.click()
            print("Clicked continue button")
            time.sleep(3)
            
            # STEP 2: Enter password on next page
            print("Looking for password field...")
            try:
                self.driver.save_screenshot('/tmp/ring_password_page.png')
                print("Password page screenshot saved")
            except:
                pass
            
            # Find password field
            password_field = None
            password_selectors = ["#user_password", "input[type='password']", "input[name='user[password]']", "input[name='password']"]
            
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_field:
                        print(f"Found password field with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_field:
                print("Could not find password field")
                return False
            
            password_field.clear()
            password_field.send_keys(self.password)
            print("Entered password")
            time.sleep(1)
            
            # Click sign in button (final step)
            sign_in_button = None
            button_selectors = [
                "input[name='commit']",
                "button[type='submit']",
                "input[type='submit']",
                "button[name='commit']",
                ".btn-primary",
                ".submit-button"
            ]
            
            for selector in button_selectors:
                try:
                    sign_in_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if sign_in_button:
                        print(f"Found sign in button with selector: {selector}")
                        break
                except:
                    continue
            
            if not sign_in_button:
                print("Could not find sign in button")
                return False
            
            sign_in_button.click()
            print("Clicked sign in button")
            
            # Wait longer for dashboard or 2FA
            time.sleep(8)
            
            current_url = self.driver.current_url
            print(f"After login, URL: {current_url}")
            print(f"Page title: {self.driver.title}")
            
            # Check if we're at dashboard or if 2FA is required
            if 'dashboard' in current_url or 'app' in current_url:
                print("Login successful - reached dashboard")
                return True
            elif 'verification' in current_url or '2fa' in current_url or 'code' in current_url:
                print("2FA/verification required - cannot proceed automatically")
                return False
            elif 'sign_in' in current_url:
                print("Still on sign in page - login may have failed")
                # Save screenshot for debugging
                try:
                    self.driver.save_screenshot('/tmp/ring_login_failed.png')
                    print("Screenshot saved to /tmp/ring_login_failed.png")
                except:
                    pass
                return False
            else:
                # Try to navigate to dashboard
                print("Attempting to navigate to dashboard...")
                self.driver.get(f"{self.url}/dashboard")
                time.sleep(5)
                if 'dashboard' in self.driver.current_url:
                    print("Successfully navigated to dashboard")
                    return True
                else:
                    print(f"Could not reach dashboard, at: {self.driver.current_url}")
                    return False
            
        except TimeoutException:
            print("Login timeout - page elements not found")
            return False
        except Exception as e:
            print(f"Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_devices(self) -> List[Dict[str, Any]]:
        """
        Fetch list of Ring cameras from dashboard
        
        Returns:
            List of device dictionaries with structure:
            [
                {
                    'id': str,
                    'name': str,
                    'displayName': str,
                    'type': str (e.g., 'camera', 'doorbell'),
                    'status': str (e.g., 'online', 'offline'),
                    'system_status': str (e.g., 'away', 'home', 'disarmed')
                }
            ]
        """
        try:
            if not self.driver:
                if not self.login():
                    return []
            
            # Navigate to dashboard
            self.driver.get(f"{self.url}/dashboard")
            
            # Wait for dashboard to load
            time.sleep(5)  # Give more time for dynamic content to load
            
            devices = []
            system_status = "unknown"
            
            # Try to get system status (Disarmed, Home mode, Away mode)
            try:
                page_text = self.driver.page_source.lower()
                if 'away mode' in page_text or 'in away mode' in page_text:
                    system_status = 'away'
                elif 'home mode' in page_text or 'in home mode' in page_text:
                    system_status = 'home'
                elif 'disarmed' in page_text:
                    system_status = 'disarmed'
                print(f"Ring system status: {system_status}")
            except Exception as e:
                print(f"Could not determine system status: {str(e)}")
            
            # Look for camera cards - Ring uses various class names
            camera_selectors = [
                "[data-testid*='camera']",
                "[class*='CameraCard']",
                "[class*='camera-card']",
                "[class*='device-card']",
                ".device-tile",
                "[data-cy*='camera']",
                "article",
                "[role='article']"
            ]
            
            camera_elements = []
            for selector in camera_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Filter to only elements that likely contain camera info
                        camera_elements = [el for el in elements if el.text and len(el.text) > 0]
                        if camera_elements:
                            print(f"Found {len(camera_elements)} potential camera elements with selector: {selector}")
                            break
                except:
                    continue
            
            # If no camera elements found, try looking for any text matching camera pattern
            if not camera_elements:
                print("No camera elements found with standard selectors, trying text search...")
                # Look for the "Cameras" heading and get elements after it
                try:
                    page_source = self.driver.page_source
                    # Try to find camera names in the page
                    import re
                    # Look for potential camera names (words with "cam", "camera", "view", etc.)
                    potential_cameras = re.findall(r'["\']([^"\']{3,50}(?:view|cam|camera|doorbell|ring)[^"\']{0,20})["\']', page_source, re.IGNORECASE)
                    
                    if potential_cameras:
                        print(f"Found potential camera names in source: {potential_cameras[:5]}")
                        for idx, camera_name in enumerate(set(potential_cameras[:20])):
                            if len(camera_name) > 3 and len(camera_name) < 50:
                                devices.append({
                                    'id': f"ring_camera_{idx}",
                                    'name': camera_name,
                                    'displayName': camera_name,
                                    'type': 'doorbell' if 'doorbell' in camera_name.lower() else 'camera',
                                    'status': 'online',
                                    'system_status': system_status
                                })
                except Exception as e:
                    print(f"Text search error: {str(e)}")
            else:
                # Parse camera elements
                for idx, element in enumerate(camera_elements[:20]):
                    try:
                        element_text = element.text.strip()
                        element_html = element.get_attribute('outerHTML')
                        
                        # Skip if no useful text
                        if not element_text or len(element_text) < 2:
                            continue
                        
                        # Skip common non-camera texts
                        skip_texts = ['cameras', 'settings', 'history', 'dashboard', 'notifications', 'live view']
                        if any(skip in element_text.lower() for skip in skip_texts) and len(element_text) < 15:
                            continue
                        
                        # Extract camera name (first line of text usually)
                        camera_name = element_text.split('\n')[0].strip()
                        
                        # Skip if name is too short or too long
                        if len(camera_name) < 3 or len(camera_name) > 50:
                            continue
                        
                        # Determine device type
                        device_type = 'camera'
                        element_lower = (element_text + element_html).lower()
                        if 'doorbell' in element_lower:
                            device_type = 'doorbell'
                        elif 'spotlight' in element_lower:
                            device_type = 'spotlight_cam'
                        elif 'floodlight' in element_lower:
                            device_type = 'floodlight_cam'
                        
                        # Determine online status
                        device_status = 'online'
                        if 'offline' in element_lower:
                            device_status = 'offline'
                        
                        print(f"Found camera: {camera_name} (type: {device_type})")
                        
                        devices.append({
                            'id': f"ring_camera_{idx}",
                            'name': camera_name,
                            'displayName': camera_name,
                            'type': device_type,
                            'status': device_status,
                            'system_status': system_status
                        })
                        
                    except Exception as e:
                        print(f"Error parsing camera element {idx}: {str(e)}")
                        continue
            
            # If still no devices, save a screenshot for debugging
            if not devices:
                try:
                    screenshot_path = '/tmp/ring_dashboard.png'
                    self.driver.save_screenshot(screenshot_path)
                    print(f"No cameras found. Screenshot saved to {screenshot_path}")
                    print(f"Page title: {self.driver.title}")
                    print(f"Current URL: {self.driver.current_url}")
                except:
                    pass
            
            return devices
            
        except Exception as e:
            print(f"Error fetching devices: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
        finally:
            self._cleanup()
    
    def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Convenience method that logs in and gets devices
        
        Returns:
            List of device dictionaries
        """
        if self.login():
            return self.get_devices()
        return []
