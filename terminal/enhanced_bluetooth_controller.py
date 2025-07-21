#!/usr/bin/env python3
"""
Enhanced Bluetooth Controller with Gemini API Fallback
This module provides comprehensive Bluetooth control with intelligent fallback mechanisms
"""

import subprocess
import sys
import os
import time
import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from enhanced_command_executor import execute_enhanced_command

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedBluetoothController:
    def __init__(self, gemini_api_key: str = None):
        self.methods = [
            self._method_devcon,
            self._method_powershell_radio,
            self._method_powershell_device,
            self._method_registry,
            self._method_service,
            self._method_wmic,
            self._method_bluetooth_command
        ]
        
        # Initialize Gemini API
        self.gemini_api_key = gemini_api_key or self._get_gemini_api_key()
        self.gemini_client = None
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("Gemini API initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
        
        # Command history for learning
        self.command_history = []
        self.success_patterns = []
        
    def _get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from config"""
        try:
            sys.path.append('config')
            from config.settings import GEMINI_API_KEY
            return GEMINI_API_KEY
        except:
            return os.getenv("GEMINI_API_KEY")
    
    def turn_on_bluetooth(self) -> Dict[str, Any]:
        """Turn on Bluetooth with intelligent fallback"""
        logger.info("🔵 Attempting to turn ON Bluetooth...")
        
        result = {
            "success": False,
            "method_used": None,
            "output": "",
            "attempts": [],
            "gemini_fallback_used": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try all local methods first
        for i, method in enumerate(self.methods, 1):
            try:
                logger.info(f"   Method {i}: {method.__name__.replace('_method_', '').replace('_', ' ').title()}")
                success, output = method(True)
                
                attempt_info = {
                    "method": method.__name__,
                    "success": success,
                    "output": output
                }
                result["attempts"].append(attempt_info)
                
                if success:
                    logger.info("   ✅ Bluetooth turned ON successfully!")
                    result["success"] = True
                    result["method_used"] = method.__name__
                    result["output"] = output
                    self._record_success_pattern(method.__name__, "turn_on", output)
                    return result
                else:
                    logger.info("   ❌ Method failed, trying next...")
                    
            except Exception as e:
                logger.error(f"   ⚠️ Method error: {str(e)}")
                result["attempts"].append({
                    "method": method.__name__,
                    "success": False,
                    "output": str(e)
                })
        
        # All local methods failed, try Gemini API fallback
        logger.info("🤖 All local methods failed. Using Gemini API fallback...")
        gemini_result = self._gemini_bluetooth_fallback("turn on bluetooth", True)
        
        if gemini_result["success"]:
            result.update(gemini_result)
            result["gemini_fallback_used"] = True
            logger.info("✅ Gemini API fallback successful!")
        else:
            logger.error("❌ All methods including Gemini API fallback failed")
            result["output"] = "All methods failed to turn ON Bluetooth"
        
        return result
    
    def turn_off_bluetooth(self) -> Dict[str, Any]:
        """Turn off Bluetooth with intelligent fallback"""
        logger.info("🔵 Attempting to turn OFF Bluetooth...")
        
        result = {
            "success": False,
            "method_used": None,
            "output": "",
            "attempts": [],
            "gemini_fallback_used": False,
            "timestamp": datetime.now().isoformat()
        }
        
        # Try all local methods first
        for i, method in enumerate(self.methods, 1):
            try:
                logger.info(f"   Method {i}: {method.__name__.replace('_method_', '').replace('_', ' ').title()}")
                success, output = method(False)
                
                attempt_info = {
                    "method": method.__name__,
                    "success": success,
                    "output": output
                }
                result["attempts"].append(attempt_info)
                
                if success:
                    logger.info("   ✅ Bluetooth turned OFF successfully!")
                    result["success"] = True
                    result["method_used"] = method.__name__
                    result["output"] = output
                    self._record_success_pattern(method.__name__, "turn_off", output)
                    return result
                else:
                    logger.info("   ❌ Method failed, trying next...")
                    
            except Exception as e:
                logger.error(f"   ⚠️ Method error: {str(e)}")
                result["attempts"].append({
                    "method": method.__name__,
                    "success": False,
                    "output": str(e)
                })
        
        # All local methods failed, try Gemini API fallback
        logger.info("🤖 All local methods failed. Using Gemini API fallback...")
        gemini_result = self._gemini_bluetooth_fallback("turn off bluetooth", False)
        
        if gemini_result["success"]:
            result.update(gemini_result)
            result["gemini_fallback_used"] = True
            logger.info("✅ Gemini API fallback successful!")
        else:
            logger.error("❌ All methods including Gemini API fallback failed")
            result["output"] = "All methods failed to turn OFF Bluetooth"
        
        return result
    
    def _gemini_bluetooth_fallback(self, user_request: str, enable: bool) -> Dict[str, Any]:
        """Use Gemini API to find alternative Bluetooth control methods"""
        if not self.gemini_client:
            return {"success": False, "output": "Gemini API not available"}
        
        try:
            # Get system information for context
            system_info = self._get_system_context()
            
            prompt = f"""You are an expert Windows system administrator. The user wants to {user_request} but all standard methods have failed.

System Context:
{system_info}

Failed Methods:
- DevCon utility
- PowerShell Radio API
- PowerShell Device Management
- Registry modification
- Service management
- WMIC commands
- Bluetooth command line tools

Please provide alternative Windows commands or PowerShell scripts that could {user_request}. Consider:
1. Alternative registry paths
2. Different PowerShell approaches
3. WMI methods
4. Device Manager commands
5. Hardware-specific solutions
6. Windows API calls via PowerShell

Respond with a JSON object containing:
{{
    "commands": ["command1", "command2", "command3"],
    "explanations": ["explanation1", "explanation2", "explanation3"],
    "risk_levels": ["low", "medium", "high"],
    "success_probability": [0.8, 0.6, 0.4],
    "requires_admin": [true, false, true]
}}

Only provide commands that are safe and appropriate for Windows systems."""
            
            response = self.gemini_client.generate_content(prompt)
            gemini_suggestions = self._parse_gemini_response(response.text)
            
            if gemini_suggestions:
                return self._execute_gemini_suggestions(gemini_suggestions, enable)
            else:
                return {"success": False, "output": "No valid suggestions from Gemini API"}
                
        except Exception as e:
            logger.error(f"Gemini API fallback failed: {e}")
            return {"success": False, "output": f"Gemini API error: {str(e)}"}
    
    def _get_system_context(self) -> str:
        """Get system context for Gemini API"""
        context = []
        
        try:
            # Get Windows version
            result = subprocess.run('ver', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                context.append(f"Windows Version: {result.stdout.strip()}")
            
            # Get PowerShell version
            result = subprocess.run('powershell -Command "$PSVersionTable.PSVersion"', 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                context.append(f"PowerShell Version: {result.stdout.strip()}")
            
            # Get Bluetooth adapter info
            result = subprocess.run('powershell -Command "Get-PnpDevice | Where-Object {$_.Class -eq \'Bluetooth\'} | Select-Object FriendlyName, Status"', 
                                  shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                context.append(f"Bluetooth Devices: {result.stdout.strip()}")
            
            # Get current user privileges
            result = subprocess.run('whoami /priv', shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                context.append(f"User Privileges: {result.stdout.strip()[:200]}...")
                
        except Exception as e:
            context.append(f"Error getting system context: {str(e)}")
        
        return "\n".join(context)
    
    def _parse_gemini_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse Gemini API response"""
        try:
            # Handle markdown formatting
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            suggestions = json.loads(response_text)
            
            # Validate response structure
            required_fields = ["commands", "explanations", "risk_levels", "success_probability"]
            if all(field in suggestions for field in required_fields):
                return suggestions
            else:
                logger.error("Invalid Gemini response structure")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing Gemini response: {e}")
            return None
    
    def _execute_gemini_suggestions(self, suggestions: Dict[str, Any], enable: bool) -> Dict[str, Any]:
        """Execute commands suggested by Gemini API"""
        result = {
            "success": False,
            "method_used": "gemini_api",
            "output": "",
            "gemini_attempts": []
        }
        
        commands = suggestions.get("commands", [])
        explanations = suggestions.get("explanations", [])
        risk_levels = suggestions.get("risk_levels", [])
        success_probabilities = suggestions.get("success_probability", [])
        
        # Sort commands by success probability (highest first)
        command_data = list(zip(commands, explanations, risk_levels, success_probabilities))
        command_data.sort(key=lambda x: x[3], reverse=True)
        
        for i, (command, explanation, risk_level, probability) in enumerate(command_data):
            try:
                logger.info(f"🤖 Trying Gemini suggestion {i+1}: {explanation}")
                logger.info(f"   Command: {command}")
                logger.info(f"   Risk Level: {risk_level}, Success Probability: {probability}")
                
                # Execute the command using enhanced command executor
                success, output = execute_enhanced_command(command)
                
                attempt_info = {
                    "command": command,
                    "explanation": explanation,
                    "risk_level": risk_level,
                    "success_probability": probability,
                    "success": success,
                    "output": output
                }
                result["gemini_attempts"].append(attempt_info)
                
                if success:
                    logger.info(f"   ✅ Gemini suggestion successful!")
                    result["success"] = True
                    result["output"] = f"Success with Gemini suggestion: {explanation}\nOutput: {output}"
                    self._record_success_pattern("gemini_api", "turn_on" if enable else "turn_off", command)
                    return result
                else:
                    logger.info(f"   ❌ Gemini suggestion failed: {output}")
                    
                # Wait between attempts
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"   ⚠️ Error executing Gemini suggestion: {str(e)}")
                result["gemini_attempts"].append({
                    "command": command,
                    "explanation": explanation,
                    "success": False,
                    "output": str(e)
                })
        
        result["output"] = "All Gemini API suggestions failed"
        return result
    
    def _record_success_pattern(self, method: str, action: str, details: str):
        """Record successful patterns for future use"""
        pattern = {
            "method": method,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.success_patterns.append(pattern)
        
        # Keep only last 50 patterns
        if len(self.success_patterns) > 50:
            self.success_patterns = self.success_patterns[-50:]
    
    def get_bluetooth_status(self) -> Dict[str, Any]:
        """Get comprehensive Bluetooth status"""
        logger.info("🔵 Checking Bluetooth status...")
        
        status = {
            "service_status": "Unknown",
            "devices": [],
            "radio_state": "Unknown",
            "adapters": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Check service status
        try:
            result = subprocess.run('sc query "bthserv"', shell=True, capture_output=True, text=True)
            if "RUNNING" in result.stdout:
                status["service_status"] = "Running"
            elif "STOPPED" in result.stdout:
                status["service_status"] = "Stopped"
            else:
                status["service_status"] = "Unknown"
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
        
        # Check device status
        try:
            cmd = 'powershell -Command "Get-PnpDevice | Where-Object {$_.Class -eq \'Bluetooth\'} | Select-Object FriendlyName, Status, InstanceId"'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                status["devices"] = result.stdout.strip().split('\n')
        except Exception as e:
            logger.error(f"Error checking device status: {e}")
        
        # Check radio status
        try:
            cmd = '''powershell -Command "Add-Type -AssemblyName System.Runtime.WindowsRuntime; $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]; Function Await($WinRtTask, $ResultType) { $asTask = $asTaskGeneric.MakeGenericMethod($ResultType); $netTask = $asTask.Invoke($null, @($WinRtTask)); $netTask.Wait(-1) | Out-Null; $netTask.Result }; [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]); $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]); $bluetooth = $radios | ? { $_.Kind -eq 'Bluetooth' }; if ($bluetooth) { Write-Host $bluetooth.State } else { Write-Host 'No Bluetooth radio found' }"'''
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.stdout:
                status["radio_state"] = result.stdout.strip()
        except Exception as e:
            logger.error(f"Error checking radio status: {e}")
        
        return status
    
    # Original methods with enhanced error handling
    def _method_devcon(self, enable: bool) -> Tuple[bool, str]:
        """Method 1: Use DevCon utility if available"""
        try:
            devcon_paths = [
                "C:\\Windows\\System32\\devcon.exe",
                "C:\\Windows\\SysWOW64\\devcon.exe",
                "devcon.exe"
            ]
            
            devcon_path = None
            for path in devcon_paths:
                try:
                    result = subprocess.run(f'"{path}" help', shell=True, capture_output=True, timeout=10)
                    if result.returncode == 0:
                        devcon_path = path
                        break
                except:
                    continue
            
            if not devcon_path:
                return False, "DevCon utility not found"
            
            # Find Bluetooth device ID
            result = subprocess.run(f'"{devcon_path}" find *bluetooth*', shell=True, capture_output=True, text=True, timeout=10)
            
            if not result.stdout:
                return False, "No Bluetooth devices found"
            
            lines = result.stdout.strip().split('\n')
            device_id = None
            for line in lines:
                if 'bluetooth' in line.lower():
                    device_id = line.split(':')[0].strip()
                    break
            
            if not device_id:
                return False, "Could not extract Bluetooth device ID"
            
            action = "enable" if enable else "disable"
            result = subprocess.run(f'"{devcon_path}" {action} "{device_id}"', shell=True, capture_output=True, text=True, timeout=30)
            
            return result.returncode == 0, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "DevCon command timed out"
        except Exception as e:
            return False, f"DevCon method failed: {str(e)}"
    
    def _method_powershell_radio(self, enable: bool) -> Tuple[bool, str]:
        """Method 2: PowerShell Windows Runtime Radio API"""
        try:
            state = "On" if enable else "Off"
            cmd = f'''powershell -Command "Add-Type -AssemblyName System.Runtime.WindowsRuntime; $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }})[0]; Function Await($WinRtTask, $ResultType) {{ $asTask = $asTaskGeneric.MakeGenericMethod($ResultType); $netTask = $asTask.Invoke($null, @($WinRtTask)); $netTask.Wait(-1) | Out-Null; $netTask.Result }}; [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus]); $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]]); $bluetooth = $radios | ? {{ $_.Kind -eq 'Bluetooth' }}; if ($bluetooth) {{ [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null; Await ($bluetooth.SetStateAsync('{state}')) ([Windows.Devices.Radios.RadioAccessStatus]); Write-Host 'Success' }} else {{ Write-Host 'No Bluetooth radio found' }}"'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            success = "Success" in result.stdout
            return success, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "PowerShell radio command timed out"
        except Exception as e:
            return False, f"PowerShell radio method failed: {str(e)}"
    
    def _method_powershell_device(self, enable: bool) -> Tuple[bool, str]:
        """Method 3: PowerShell Device Management"""
        try:
            action = "Enable" if enable else "Disable"
            cmd = f'''powershell -Command "$btDevices = Get-PnpDevice | Where-Object {{$_.Class -eq 'Bluetooth'}}; if ($btDevices) {{ foreach ($device in $btDevices) {{ try {{ {action}-PnpDevice -InstanceId $device.InstanceId -Confirm:$false; Write-Host 'Device' $device.FriendlyName '{action.lower()}d' }} catch {{ Write-Host 'Failed to {action.lower()}' $device.FriendlyName }} }}; Write-Host 'Success' }} else {{ Write-Host 'No Bluetooth devices found' }}"'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            success = "Success" in result.stdout
            return success, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "PowerShell device command timed out"
        except Exception as e:
            return False, f"PowerShell device method failed: {str(e)}"
    
    def _method_registry(self, enable: bool) -> Tuple[bool, str]:
        """Method 4: Registry modification (requires admin)"""
        try:
            value = "0" if enable else "1"
            cmd = f'''powershell -Command "try {{ $regPath = 'HKLM:\\SYSTEM\\CurrentControlSet\\Services\\BTHPORT\\Parameters\\Radio Support'; if (Test-Path $regPath) {{ Set-ItemProperty -Path $regPath -Name 'SupportDLL' -Value '{value}'; Write-Host 'Registry updated' }} else {{ Write-Host 'Registry path not found' }} }} catch {{ Write-Host 'Registry access failed' }}"'''
            
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            success = "Registry updated" in result.stdout
            return success, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Registry command timed out"
        except Exception as e:
            return False, f"Registry method failed: {str(e)}"
    
    def _method_service(self, enable: bool) -> Tuple[bool, str]:
        """Method 5: Bluetooth service management"""
        try:
            if enable:
                result1 = subprocess.run('sc start "bthserv"', shell=True, capture_output=True, text=True, timeout=10)
                result2 = subprocess.run('sc start "BthAvctpSvc"', shell=True, capture_output=True, text=True, timeout=10)
                time.sleep(2)
                result3 = subprocess.run('sc query "bthserv"', shell=True, capture_output=True, text=True, timeout=10)
                success = "RUNNING" in result3.stdout
                return success, result3.stdout
            else:
                result1 = subprocess.run('sc stop "bthserv"', shell=True, capture_output=True, text=True, timeout=10)
                result2 = subprocess.run('sc stop "BthAvctpSvc"', shell=True, capture_output=True, text=True, timeout=10)
                time.sleep(2)
                result3 = subprocess.run('sc query "bthserv"', shell=True, capture_output=True, text=True, timeout=10)
                success = "STOPPED" in result3.stdout
                return success, result3.stdout
                
        except subprocess.TimeoutExpired:
            return False, "Service command timed out"
        except Exception as e:
            return False, f"Service method failed: {str(e)}"
    
    def _method_wmic(self, enable: bool) -> Tuple[bool, str]:
        """Method 6: WMIC enable/disable Bluetooth devices"""
        try:
            action = "enable" if enable else "disable"
            cmd = f'wmic path Win32_PnPEntity where "Name like \'%Bluetooth%\'" call {action}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            success = "successful" in result.stdout.lower() or result.returncode == 0
            return success, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "WMIC command timed out"
        except Exception as e:
            return False, f"WMIC method failed: {str(e)}"
    
    def _method_bluetooth_command(self, enable: bool) -> Tuple[bool, str]:
        """Method 7: Use existing Bluetooth command script"""
        try:
            action = "on" if enable else "off"
            cmd = f"python working_bluetooth_control.py {action}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            success = "SUCCESS" in result.stdout
            return success, result.stdout or result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "Bluetooth command script timed out"
        except Exception as e:
            return False, f"Bluetooth command script failed: {str(e)}"

# Global instance
enhanced_bluetooth_controller = EnhancedBluetoothController()

def turn_on_bluetooth_enhanced() -> Dict[str, Any]:
    """Enhanced Bluetooth turn on with Gemini fallback"""
    return enhanced_bluetooth_controller.turn_on_bluetooth()

def turn_off_bluetooth_enhanced() -> Dict[str, Any]:
    """Enhanced Bluetooth turn off with Gemini fallback"""
    return enhanced_bluetooth_controller.turn_off_bluetooth()

def get_bluetooth_status_enhanced() -> Dict[str, Any]:
    """Enhanced Bluetooth status check"""
    return enhanced_bluetooth_controller.get_bluetooth_status()

# Test function
def test_enhanced_bluetooth():
    """Test the enhanced Bluetooth controller"""
    print("🧪 Testing Enhanced Bluetooth Controller with Gemini Fallback")
    print("=" * 60)
    
    # Test status check
    print("\n1. Checking Bluetooth status...")
    status = get_bluetooth_status_enhanced()
    print(json.dumps(status, indent=2))
    
    # Test turning on Bluetooth
    print("\n2. Testing Bluetooth turn ON...")
    result = turn_on_bluetooth_enhanced()
    print(json.dumps(result, indent=2))
    
    print("\n🎉 Enhanced Bluetooth Controller test completed!")

if __name__ == "__main__":
    test_enhanced_bluetooth()
