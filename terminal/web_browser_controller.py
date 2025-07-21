#!/usr/bin/env python3
"""
Web Browser Controller
Handles web browser operations including opening URLs, launching browsers, and managing tabs
"""

import subprocess
import os
import sys
import platform
import webbrowser
import json
from typing import Dict, List, Any, Optional, Tuple
import winreg
import psutil

class WebBrowserController:
    """Controls web browser operations"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.supported_browsers = {
            'chrome': {
                'windows': ['chrome.exe', 'Google\\Chrome\\Application\\chrome.exe'],
                'linux': ['google-chrome', 'chromium-browser'],
                'mac': ['Google Chrome']
            },
            'firefox': {
                'windows': ['firefox.exe', 'Mozilla Firefox\\firefox.exe'],
                'linux': ['firefox'],
                'mac': ['Firefox']
            },
            'edge': {
                'windows': ['msedge.exe', 'Microsoft\\Edge\\Application\\msedge.exe'],
                'linux': ['microsoft-edge'],
                'mac': ['Microsoft Edge']
            },
            'safari': {
                'mac': ['Safari']
            }
        }
    
    def find_browser_executable(self, browser_name: str) -> Optional[str]:
        """Find the executable path for a specific browser"""
        if browser_name not in self.supported_browsers:
            return None
        
        browser_info = self.supported_browsers[browser_name]
        
        if self.os_type == 'Windows':
            return self._find_windows_browser(browser_info.get('windows', []))
        elif self.os_type == 'Linux':
            return self._find_linux_browser(browser_info.get('linux', []))
        elif self.os_type == 'Darwin':  # macOS
            return self._find_mac_browser(browser_info.get('mac', []))
        
        return None
    
    def _find_windows_browser(self, possible_names: List[str]) -> Optional[str]:
        """Find browser executable on Windows"""
        # Check common installation paths
        common_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google\\Chrome\\Application\\chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Mozilla Firefox\\firefox.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Mozilla Firefox\\firefox.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Microsoft\\Edge\\Application\\msedge.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Microsoft\\Edge\\Application\\msedge.exe'),
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        # Check PATH
        for name in possible_names:
            try:
                result = subprocess.run(['where', name], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
            except:
                continue
        
        return None
    
    def _find_linux_browser(self, possible_names: List[str]) -> Optional[str]:
        """Find browser executable on Linux"""
        for name in possible_names:
            try:
                result = subprocess.run(['which', name], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
            except:
                continue
        return None
    
    def _find_mac_browser(self, possible_names: List[str]) -> Optional[str]:
        """Find browser executable on macOS"""
        for name in possible_names:
            app_path = f"/Applications/{name}.app"
            if os.path.exists(app_path):
                return app_path
        return None
    
    def open_url(self, url: str, browser: str = 'default') -> Tuple[bool, str]:
        """Open a URL in the specified browser"""
        try:
            # Ensure URL has protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            if browser == 'default':
                # Use system default browser
                webbrowser.open(url)
                return True, f"Opened {url} in default browser"
            else:
                # Use specific browser
                browser_path = self.find_browser_executable(browser)
                if not browser_path:
                    return False, f"Browser '{browser}' not found"
                
                if self.os_type == 'Windows':
                    subprocess.Popen([browser_path, url])
                elif self.os_type == 'Linux':
                    subprocess.Popen([browser_path, url])
                elif self.os_type == 'Darwin':
                    subprocess.Popen(['open', '-a', browser_path, url])
                
                return True, f"Opened {url} in {browser}"
        
        except Exception as e:
            return False, f"Failed to open URL: {str(e)}"
    
    def launch_browser(self, browser: str = 'chrome') -> Tuple[bool, str]:
        """Launch a browser without opening any specific URL"""
        try:
            browser_path = self.find_browser_executable(browser)
            if not browser_path:
                return False, f"Browser '{browser}' not found"
            
            if self.os_type == 'Windows':
                subprocess.Popen([browser_path])
            elif self.os_type == 'Linux':
                subprocess.Popen([browser_path])
            elif self.os_type == 'Darwin':
                subprocess.Popen(['open', '-a', browser_path])
            
            return True, f"Launched {browser} browser"
        
        except Exception as e:
            return False, f"Failed to launch browser: {str(e)}"
    
    def open_youtube(self, browser: str = 'chrome') -> Tuple[bool, str]:
        """Open YouTube in the specified browser"""
        return self.open_url('https://www.youtube.com', browser)
    
    def open_google(self, browser: str = 'chrome') -> Tuple[bool, str]:
        """Open Google in the specified browser"""
        return self.open_url('https://www.google.com', browser)
    
    def search_google(self, query: str, browser: str = 'chrome') -> Tuple[bool, str]:
        """Search Google with the given query"""
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://www.google.com/search?q={encoded_query}"
        return self.open_url(search_url, browser)
    
    def get_running_browsers(self) -> List[Dict[str, Any]]:
        """Get list of currently running browsers"""
        running_browsers = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    name = proc_info['name'].lower()
                    
                    # Check if it's a browser process
                    if any(browser in name for browser in ['chrome', 'firefox', 'edge', 'safari']):
                        running_browsers.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': proc_info['cmdline']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting browser processes: {e}")
        
        return running_browsers
    
    def close_browser(self, browser: str = 'chrome') -> Tuple[bool, str]:
        """Close all instances of the specified browser"""
        closed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if browser.lower() in proc.info['name'].lower():
                        proc.terminate()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                return True, f"Closed {closed_count} {browser} processes"
            else:
                return False, f"No {browser} processes found"
        
        except Exception as e:
            return False, f"Error closing browser: {str(e)}"
    
    def get_browser_info(self) -> Dict[str, Any]:
        """Get information about available browsers"""
        info = {
            'os_type': self.os_type,
            'available_browsers': {},
            'running_browsers': self.get_running_browsers()
        }
        
        for browser_name in self.supported_browsers.keys():
            browser_path = self.find_browser_executable(browser_name)
            info['available_browsers'][browser_name] = {
                'available': browser_path is not None,
                'path': browser_path
            }
        
        return info

# Global instance
browser_controller = WebBrowserController()

# Convenience functions
def open_url(url: str, browser: str = 'default') -> Tuple[bool, str]:
    """Open a URL in the specified browser"""
    return browser_controller.open_url(url, browser)

def launch_browser(browser: str = 'chrome') -> Tuple[bool, str]:
    """Launch a browser"""
    return browser_controller.launch_browser(browser)

def open_youtube(browser: str = 'chrome') -> Tuple[bool, str]:
    """Open YouTube"""
    return browser_controller.open_youtube(browser)

def open_google(browser: str = 'chrome') -> Tuple[bool, str]:
    """Open Google"""
    return browser_controller.open_google(browser)

def search_google(query: str, browser: str = 'chrome') -> Tuple[bool, str]:
    """Search Google"""
    return browser_controller.search_google(query, browser)

def get_browser_info() -> Dict[str, Any]:
    """Get browser information"""
    return browser_controller.get_browser_info()
