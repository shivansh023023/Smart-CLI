#!/usr/bin/env python3
"""
Desktop Application Controller
Handles launching, managing, and controlling desktop applications across different operating systems
"""

import subprocess
import os
import sys
import platform
import winreg
import json
import psutil
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re

class DesktopAppController:
    """Controls desktop application operations"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.app_cache = {}
        self.common_apps = self._load_common_apps()
        self._scan_installed_apps()
    
    def _load_common_apps(self) -> Dict[str, Dict[str, Any]]:
        """Load common application mappings"""
        return {
            # Microsoft Office
            'word': {
                'names': ['Microsoft Word', 'Word', 'winword.exe'],
                'executable': 'winword.exe',
                'paths': ['Microsoft Office', 'Microsoft Office\\root\\Office16']
            },
            'excel': {
                'names': ['Microsoft Excel', 'Excel', 'excel.exe'],
                'executable': 'excel.exe',
                'paths': ['Microsoft Office', 'Microsoft Office\\root\\Office16']
            },
            'powerpoint': {
                'names': ['Microsoft PowerPoint', 'PowerPoint', 'powerpnt.exe'],
                'executable': 'powerpnt.exe',
                'paths': ['Microsoft Office', 'Microsoft Office\\root\\Office16']
            },
            'outlook': {
                'names': ['Microsoft Outlook', 'Outlook', 'outlook.exe'],
                'executable': 'outlook.exe',
                'paths': ['Microsoft Office', 'Microsoft Office\\root\\Office16']
            },
            
            # Browsers
            'chrome': {
                'names': ['Google Chrome', 'Chrome', 'chrome.exe'],
                'executable': 'chrome.exe',
                'paths': ['Google\\Chrome\\Application']
            },
            'firefox': {
                'names': ['Mozilla Firefox', 'Firefox', 'firefox.exe'],
                'executable': 'firefox.exe',
                'paths': ['Mozilla Firefox']
            },
            'edge': {
                'names': ['Microsoft Edge', 'Edge', 'msedge.exe'],
                'executable': 'msedge.exe',
                'paths': ['Microsoft\\Edge\\Application']
            },
            
            # Development Tools
            'vscode': {
                'names': ['Visual Studio Code', 'VS Code', 'Code.exe'],
                'executable': 'Code.exe',
                'paths': ['Microsoft VS Code']
            },
            'visualstudio': {
                'names': ['Visual Studio', 'devenv.exe'],
                'executable': 'devenv.exe',
                'paths': ['Microsoft Visual Studio']
            },
            'pycharm': {
                'names': ['PyCharm', 'pycharm64.exe'],
                'executable': 'pycharm64.exe',
                'paths': ['JetBrains\\PyCharm']
            },
            
            # Media
            'vlc': {
                'names': ['VLC Media Player', 'VLC', 'vlc.exe'],
                'executable': 'vlc.exe',
                'paths': ['VideoLAN\\VLC']
            },
            'spotify': {
                'names': ['Spotify', 'Spotify.exe'],
                'executable': 'Spotify.exe',
                'paths': ['Spotify']
            },
            
            # Communication
            'discord': {
                'names': ['Discord', 'Discord.exe'],
                'executable': 'Discord.exe',
                'paths': ['Discord']
            },
            'teams': {
                'names': ['Microsoft Teams', 'Teams', 'Teams.exe'],
                'executable': 'Teams.exe',
                'paths': ['Microsoft\\Teams']
            },
            'skype': {
                'names': ['Skype', 'Skype.exe'],
                'executable': 'Skype.exe',
                'paths': ['Microsoft\\Skype for Desktop']
            },
            
            # System Tools
            'notepad': {
                'names': ['Notepad', 'notepad.exe'],
                'executable': 'notepad.exe',
                'paths': ['system32']
            },
            'calculator': {
                'names': ['Calculator', 'calc.exe'],
                'executable': 'calc.exe',
                'paths': ['system32']
            },
            'paint': {
                'names': ['Paint', 'mspaint.exe'],
                'executable': 'mspaint.exe',
                'paths': ['system32']
            },
            'cmd': {
                'names': ['Command Prompt', 'cmd.exe'],
                'executable': 'cmd.exe',
                'paths': ['system32']
            },
            'powershell': {
                'names': ['PowerShell', 'powershell.exe'],
                'executable': 'powershell.exe',
                'paths': ['system32\\WindowsPowerShell\\v1.0']
            },
            
            # Gaming
            'steam': {
                'names': ['Steam', 'Steam.exe'],
                'executable': 'Steam.exe',
                'paths': ['Steam']
            },
            
            # Adobe
            'photoshop': {
                'names': ['Adobe Photoshop', 'Photoshop.exe'],
                'executable': 'Photoshop.exe',
                'paths': ['Adobe']
            },
            'illustrator': {
                'names': ['Adobe Illustrator', 'Illustrator.exe'],
                'executable': 'Illustrator.exe',
                'paths': ['Adobe']
            },
            
            # Other
            'zoom': {
                'names': ['Zoom', 'Zoom.exe'],
                'executable': 'Zoom.exe',
                'paths': ['Zoom']
            },
            'telegram': {
                'names': ['Telegram', 'Telegram.exe'],
                'executable': 'Telegram.exe',
                'paths': ['Telegram Desktop']
            },
            'whatsapp': {
                'names': ['WhatsApp', 'WhatsApp.exe'],
                'executable': 'WhatsApp.exe',
                'paths': ['WhatsApp']
            }
        }
    
    def _scan_installed_apps(self):
        """Scan for installed applications"""
        if self.os_type == 'Windows':
            self._scan_windows_apps()
        elif self.os_type == 'Linux':
            self._scan_linux_apps()
        elif self.os_type == 'Darwin':
            self._scan_mac_apps()
    
    def _scan_windows_apps(self):
        """Scan Windows registry and common paths for installed apps"""
        try:
            # Scan registry for installed programs
            self._scan_windows_registry()
            
            # Scan common installation directories
            self._scan_windows_directories()
            
            # Scan Start Menu
            self._scan_start_menu()
            
        except Exception as e:
            print(f"Error scanning Windows apps: {e}")
    
    def _scan_windows_registry(self):
        """Scan Windows registry for installed applications"""
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for reg_path in registry_paths:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                    
                                    if display_name and install_location:
                                        self.app_cache[display_name.lower()] = {
                                            'name': display_name,
                                            'path': install_location,
                                            'source': 'registry'
                                        }
                                except FileNotFoundError:
                                    continue
                        except Exception:
                            continue
            except Exception:
                continue
    
    def _scan_windows_directories(self):
        """Scan common Windows installation directories"""
        common_dirs = [
            os.environ.get('PROGRAMFILES', ''),
            os.environ.get('PROGRAMFILES(X86)', ''),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs'),
            os.path.join(os.environ.get('APPDATA', ''), 'Programs')
        ]
        
        for base_dir in common_dirs:
            if os.path.exists(base_dir):
                try:
                    for item in os.listdir(base_dir):
                        item_path = os.path.join(base_dir, item)
                        if os.path.isdir(item_path):
                            # Look for executable files in the directory
                            for root, dirs, files in os.walk(item_path):
                                for file in files:
                                    if file.endswith('.exe'):
                                        app_name = item.lower()
                                        if app_name not in self.app_cache:
                                            self.app_cache[app_name] = {
                                                'name': item,
                                                'path': os.path.join(root, file),
                                                'source': 'directory_scan'
                                            }
                                        break
                                break
                except Exception:
                    continue
    
    def _scan_start_menu(self):
        """Scan Start Menu for shortcuts"""
        start_menu_paths = [
            os.path.join(os.environ.get('PROGRAMDATA', ''), 'Microsoft\\Windows\\Start Menu\\Programs'),
            os.path.join(os.environ.get('APPDATA', ''), 'Microsoft\\Windows\\Start Menu\\Programs')
        ]
        
        for menu_path in start_menu_paths:
            if os.path.exists(menu_path):
                try:
                    for root, dirs, files in os.walk(menu_path):
                        for file in files:
                            if file.endswith('.lnk'):
                                shortcut_name = os.path.splitext(file)[0].lower()
                                if shortcut_name not in self.app_cache:
                                    self.app_cache[shortcut_name] = {
                                        'name': os.path.splitext(file)[0],
                                        'path': os.path.join(root, file),
                                        'source': 'start_menu'
                                    }
                except Exception:
                    continue
    
    def _scan_linux_apps(self):
        """Scan Linux desktop files for installed apps"""
        desktop_paths = [
            '/usr/share/applications',
            '/usr/local/share/applications',
            os.path.expanduser('~/.local/share/applications')
        ]
        
        for path in desktop_paths:
            if os.path.exists(path):
                try:
                    for file in os.listdir(path):
                        if file.endswith('.desktop'):
                            app_name = os.path.splitext(file)[0].lower()
                            self.app_cache[app_name] = {
                                'name': os.path.splitext(file)[0],
                                'path': os.path.join(path, file),
                                'source': 'desktop_file'
                            }
                except Exception:
                    continue
    
    def _scan_mac_apps(self):
        """Scan macOS Applications folder"""
        app_paths = ['/Applications', '/System/Applications', os.path.expanduser('~/Applications')]
        
        for path in app_paths:
            if os.path.exists(path):
                try:
                    for item in os.listdir(path):
                        if item.endswith('.app'):
                            app_name = os.path.splitext(item)[0].lower()
                            self.app_cache[app_name] = {
                                'name': os.path.splitext(item)[0],
                                'path': os.path.join(path, item),
                                'source': 'applications_folder'
                            }
                except Exception:
                    continue
    
    def find_app(self, app_name: str) -> Optional[Dict[str, Any]]:
        """Find an application by name"""
        app_name_lower = app_name.lower()
        
        # Check common apps first
        if app_name_lower in self.common_apps:
            app_info = self.common_apps[app_name_lower]
            executable_path = self._find_executable_path(app_info)
            if executable_path:
                return {
                    'name': app_name,
                    'path': executable_path,
                    'source': 'common_apps'
                }
        
        # Check cached apps
        if app_name_lower in self.app_cache:
            return self.app_cache[app_name_lower]
        
        # Search for partial matches
        for cached_name, app_info in self.app_cache.items():
            if app_name_lower in cached_name or cached_name in app_name_lower:
                return app_info
        
        # Try to find by executable name
        if app_name_lower.endswith('.exe'):
            result = self._find_by_executable(app_name_lower)
            if result:
                return result
        
        return None
    
    def _find_executable_path(self, app_info: Dict[str, Any]) -> Optional[str]:
        """Find executable path for common apps"""
        executable = app_info['executable']
        paths = app_info['paths']
        
        # Check system PATH first
        try:
            if self.os_type == 'Windows':
                result = subprocess.run(['where', executable], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        # Check common installation paths
        base_paths = []
        if self.os_type == 'Windows':
            base_paths = [
                os.environ.get('PROGRAMFILES', ''),
                os.environ.get('PROGRAMFILES(X86)', ''),
                os.environ.get('LOCALAPPDATA', ''),
                os.environ.get('WINDIR', '') + '\\system32'
            ]
        
        for base_path in base_paths:
            for rel_path in paths:
                full_path = os.path.join(base_path, rel_path, executable)
                if os.path.exists(full_path):
                    return full_path
        
        return None
    
    def _find_by_executable(self, executable_name: str) -> Optional[Dict[str, Any]]:
        """Find application by executable name"""
        try:
            if self.os_type == 'Windows':
                result = subprocess.run(['where', executable_name], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    path = result.stdout.strip().split('\n')[0]
                    return {
                        'name': executable_name,
                        'path': path,
                        'source': 'executable_search'
                    }
        except:
            pass
        
        return None
    
    def launch_app(self, app_name: str, arguments: str = "") -> Tuple[bool, str]:
        """Launch an application"""
        app_info = self.find_app(app_name)
        
        if not app_info:
            return False, f"Application '{app_name}' not found"
        
        try:
            app_path = app_info['path']
            
            if self.os_type == 'Windows':
                if app_path.endswith('.lnk'):
                    # Handle shortcuts using os.startfile which is more reliable
                    import os
                    os.startfile(app_path)
                else:
                    # Handle executables
                    if arguments:
                        cmd = [app_path] + arguments.split()
                    else:
                        cmd = [app_path]
                    
                    # Use CREATE_NO_WINDOW to avoid command prompt windows
                    subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
            
            elif self.os_type == 'Linux':
                if app_path.endswith('.desktop'):
                    subprocess.Popen(['gtk-launch', os.path.basename(app_path)])
                else:
                    cmd = [app_path] + arguments.split() if arguments else [app_path]
                    subprocess.Popen(cmd)
            
            elif self.os_type == 'Darwin':
                subprocess.Popen(['open', '-a', app_path])
            
            return True, f"Successfully launched {app_info['name']}"
        
        except Exception as e:
            return False, f"Failed to launch {app_name}: {str(e)}"
    
    def get_running_apps(self) -> List[Dict[str, Any]]:
        """Get list of currently running applications"""
        running_apps = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and not proc_info['name'].startswith('System'):
                        running_apps.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline': proc_info['cmdline'],
                            'create_time': proc_info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"Error getting running apps: {e}")
        
        return running_apps
    
    def close_app(self, app_name: str) -> Tuple[bool, str]:
        """Close an application"""
        closed_count = 0
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_info = proc.info
                    if app_name.lower() in proc_info['name'].lower():
                        proc.terminate()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                return True, f"Closed {closed_count} instances of {app_name}"
            else:
                return False, f"No running instances of {app_name} found"
        
        except Exception as e:
            return False, f"Error closing app: {str(e)}"
    
    def get_app_info(self, app_name: str) -> Dict[str, Any]:
        """Get detailed information about an application"""
        app_info = self.find_app(app_name)
        
        if not app_info:
            return {'found': False, 'error': f"Application '{app_name}' not found"}
        
        # Check if app is currently running
        running = False
        running_instances = []
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_info = proc.info
                    if app_name.lower() in proc_info['name'].lower():
                        running = True
                        running_instances.append({
                            'pid': proc_info['pid'],
                            'cmdline': proc_info['cmdline']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            pass
        
        return {
            'found': True,
            'name': app_info['name'],
            'path': app_info['path'],
            'source': app_info['source'],
            'running': running,
            'running_instances': running_instances
        }
    
    def list_installed_apps(self, filter_str: str = "") -> List[Dict[str, Any]]:
        """List installed applications"""
        apps = []
        
        # Add common apps
        for app_name, app_info in self.common_apps.items():
            if not filter_str or filter_str.lower() in app_name.lower():
                executable_path = self._find_executable_path(app_info)
                if executable_path:
                    apps.append({
                        'name': app_name,
                        'path': executable_path,
                        'source': 'common_apps'
                    })
        
        # Add cached apps
        for app_name, app_info in self.app_cache.items():
            if not filter_str or filter_str.lower() in app_name.lower():
                apps.append(app_info)
        
        return sorted(apps, key=lambda x: x['name'])
    
    def refresh_app_cache(self):
        """Refresh the application cache"""
        self.app_cache.clear()
        self._scan_installed_apps()

# Global instance
app_controller = DesktopAppController()

# Convenience functions
def launch_app(app_name: str, arguments: str = "") -> Tuple[bool, str]:
    """Launch an application"""
    return app_controller.launch_app(app_name, arguments)

def find_app(app_name: str) -> Optional[Dict[str, Any]]:
    """Find an application"""
    return app_controller.find_app(app_name)

def get_running_apps() -> List[Dict[str, Any]]:
    """Get running applications"""
    return app_controller.get_running_apps()

def close_app(app_name: str) -> Tuple[bool, str]:
    """Close an application"""
    return app_controller.close_app(app_name)

def get_app_info(app_name: str) -> Dict[str, Any]:
    """Get app information"""
    return app_controller.get_app_info(app_name)

def list_installed_apps(filter_str: str = "") -> List[Dict[str, Any]]:
    """List installed applications"""
    return app_controller.list_installed_apps(filter_str)

def refresh_app_cache():
    """Refresh application cache"""
    app_controller.refresh_app_cache()
