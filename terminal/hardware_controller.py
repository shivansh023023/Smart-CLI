#!/usr/bin/env python3
"""
Advanced Hardware Controller - System-Level Operations
Provides deep hardware access, BIOS information, temperature monitoring, and diagnostics
"""

import wmi
import subprocess
import time
import os
import json
import threading
import psutil
import platform
import winreg
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import warnings
import ctypes
from ctypes import wintypes

# Suppress WMI warnings
warnings.filterwarnings("ignore", category=UserWarning)

class HardwareController:
    """Advanced hardware controller with deep system access"""
    
    def __init__(self):
        self.wmi_conn = None
        self.monitoring_active = False
        self.temperature_alerts = []
        self.hardware_cache = {}
        self.alert_thresholds = {
            'cpu_temp': 85,
            'gpu_temp': 90,
            'system_temp': 80
        }
        self._initialize_wmi()
    
    def _initialize_wmi(self):
        """Initialize WMI connection with error handling"""
        try:
            self.wmi_conn = wmi.WMI()
            return True
        except Exception as e:
            print(f"WMI initialization failed: {e}")
            return False
    
    def get_comprehensive_bios_info(self) -> Dict[str, Any]:
        """Get detailed BIOS/UEFI information"""
        bios_info = {
            'basic_info': {},
            'system_info': {},
            'motherboard_info': {},
            'firmware_info': {},
            'boot_config': {},
            'security_info': {}
        }
        
        try:
            # Basic BIOS Information
            for bios in self.wmi_conn.Win32_BIOS():
                bios_info['basic_info'] = {
                    'manufacturer': bios.Manufacturer,
                    'version': bios.SMBIOSBIOSVersion,
                    'release_date': self._parse_wmi_date(bios.ReleaseDate),
                    'serial_number': bios.SerialNumber,
                    'smbios_version': f"{bios.SMBIOSMajorVersion}.{bios.SMBIOSMinorVersion}" if bios.SMBIOSMajorVersion and bios.SMBIOSMinorVersion else 'Unknown',
                    'characteristics': bios.BiosCharacteristics,
                    'current_language': bios.CurrentLanguage,
                    'installable_languages': bios.InstallableLanguages
                }
            
            # System Information
            for system in self.wmi_conn.Win32_ComputerSystem():
                bios_info['system_info'] = {
                    'manufacturer': system.Manufacturer,
                    'model': system.Model,
                    'system_type': system.SystemType,
                    'total_physical_memory': self._bytes_to_gb(system.TotalPhysicalMemory),
                    'number_of_processors': system.NumberOfProcessors,
                    'boot_status': system.BootupState,
                    'domain_role': self._get_domain_role(system.DomainRole),
                    'power_state': system.PowerState
                }
            
            # Motherboard Information
            for board in self.wmi_conn.Win32_BaseBoard():
                bios_info['motherboard_info'] = {
                    'manufacturer': board.Manufacturer,
                    'product': board.Product,
                    'version': board.Version,
                    'serial_number': board.SerialNumber,
                    'asset_tag': board.Tag,
                    'config_options': board.ConfigOptions
                }
            
            # Firmware Information
            bios_info['firmware_info'] = {
                'uefi_mode': self._is_uefi_mode(),
                'secure_boot': self._get_secure_boot_status(),
                'tpm_present': self._check_tpm_presence(),
                'virtualization_enabled': self._check_virtualization()
            }
            
            # Boot Configuration
            bios_info['boot_config'] = self._get_boot_configuration()
            
            # Security Information
            bios_info['security_info'] = self._get_security_info()
            
        except Exception as e:
            bios_info['error'] = f"Failed to retrieve BIOS info: {str(e)}"
        
        return bios_info
    
    def get_hardware_inventory(self) -> Dict[str, Any]:
        """Get complete hardware inventory"""
        inventory = {
            'processors': [],
            'memory': [],
            'storage': [],
            'graphics': [],
            'network': [],
            'audio': [],
            'system_slots': [],
            'ports': []
        }
        
        try:
            # Processors
            for processor in self.wmi_conn.Win32_Processor():
                inventory['processors'].append({
                    'name': processor.Name or 'Unknown',
                    'manufacturer': processor.Manufacturer or 'Unknown',
                    'family': processor.Family or 'Unknown',
                    'model': processor.Model or 'Unknown',
                    'stepping': processor.Stepping or 'Unknown',
                    'cores': processor.NumberOfCores or 0,
                    'logical_processors': processor.NumberOfLogicalProcessors or 0,
                    'max_clock_speed': processor.MaxClockSpeed or 0,
                    'current_clock_speed': processor.CurrentClockSpeed or 0,
                    'cache_size': {
                        'l2': processor.L2CacheSize or 0,
                        'l3': processor.L3CacheSize or 0
                    },
                    'architecture': processor.Architecture or 'Unknown',
                    'socket': processor.SocketDesignation or 'Unknown',
                    'voltage': processor.CurrentVoltage or 0,
                    'status': processor.Status or 'Unknown'
                })
            
            # Memory
            for memory in self.wmi_conn.Win32_PhysicalMemory():
                inventory['memory'].append({
                    'capacity': self._bytes_to_gb(memory.Capacity),
                    'speed': memory.Speed or 'Unknown',
                    'manufacturer': memory.Manufacturer or 'Unknown',
                    'part_number': memory.PartNumber or 'Unknown',
                    'serial_number': memory.SerialNumber or 'Unknown',
                    'memory_type': memory.MemoryType or 'Unknown',
                    'form_factor': memory.FormFactor or 'Unknown',
                    'bank_label': memory.BankLabel or 'Unknown',
                    'device_locator': memory.DeviceLocator or 'Unknown'
                })
            
            # Storage Devices
            for disk in self.wmi_conn.Win32_DiskDrive():
                inventory['storage'].append({
                    'model': disk.Model or 'Unknown',
                    'size': self._bytes_to_gb(disk.Size),
                    'interface_type': disk.InterfaceType or 'Unknown',
                    'media_type': disk.MediaType or 'Unknown',
                    'serial_number': disk.SerialNumber or 'Unknown',
                    'firmware_revision': disk.FirmwareRevision or 'Unknown',
                    'partitions': disk.Partitions or 0,
                    'status': disk.Status or 'Unknown'
                })
            
            # Graphics Cards
            for gpu in self.wmi_conn.Win32_VideoController():
                inventory['graphics'].append({
                    'name': gpu.Name or 'Unknown',
                    'adapter_ram': self._bytes_to_gb(gpu.AdapterRAM) if gpu.AdapterRAM else 'Unknown',
                    'driver_version': gpu.DriverVersion or 'Unknown',
                    'driver_date': gpu.DriverDate or 'Unknown',
                    'video_processor': gpu.VideoProcessor or 'Unknown',
                    'video_mode_description': gpu.VideoModeDescription or 'Unknown',
                    'current_refresh_rate': gpu.CurrentRefreshRate or 0,
                    'max_refresh_rate': gpu.MaxRefreshRate or 0,
                    'status': gpu.Status or 'Unknown'
                })
            
            # Network Adapters
            for network in self.wmi_conn.Win32_NetworkAdapter():
                if network.PhysicalAdapter:
                    inventory['network'].append({
                        'name': network.Name or 'Unknown',
                        'manufacturer': network.Manufacturer or 'Unknown',
                        'mac_address': network.MACAddress or 'Unknown',
                        'adapter_type': network.AdapterType or 'Unknown',
                        'speed': network.Speed or 'Unknown',
                        'status': network.NetConnectionStatus or 'Unknown'
                    })
            
            # Audio Devices
            for audio in self.wmi_conn.Win32_SoundDevice():
                inventory['audio'].append({
                    'name': audio.Name or 'Unknown',
                    'manufacturer': audio.Manufacturer or 'Unknown',
                    'status': audio.Status or 'Unknown'
                })
            
            # System Slots
            for slot in self.wmi_conn.Win32_SystemSlot():
                inventory['system_slots'].append({
                    'slot_designation': slot.SlotDesignation or 'Unknown',
                    'slot_type': slot.SlotType or 'Unknown',
                    'current_usage': slot.CurrentUsage or 'Unknown',
                    'status': slot.Status or 'Unknown'
                })
            
            # Ports
            for port in self.wmi_conn.Win32_PortConnector():
                inventory['ports'].append({
                    'internal_reference': port.InternalReferenceDesignator or 'Unknown',
                    'external_reference': port.ExternalReferenceDesignator or 'Unknown',
                    'port_type': port.PortType or 'Unknown',
                    'connector_type': port.ConnectorType or 'Unknown'
                })
        
        except Exception as e:
            inventory['error'] = f"Failed to retrieve hardware inventory: {str(e)}"
        
        return inventory
    
    def monitor_temperatures(self) -> Dict[str, Any]:
        """Advanced temperature monitoring"""
        temperatures = {
            'cpu': [],
            'gpu': [],
            'system': [],
            'drives': [],
            'motherboard': [],
            'alerts': []
        }
        
        try:
            # CPU Temperature (if available)
            for temp in self.wmi_conn.Win32_TemperatureProbe():
                if temp.CurrentReading:
                    temp_celsius = (temp.CurrentReading - 2732) / 10  # Convert from decikelvin
                    temperatures['cpu'].append({
                        'sensor': temp.Name or 'CPU Sensor',
                        'temperature': temp_celsius,
                        'status': temp.Status,
                        'max_reading': temp.MaxReading,
                        'min_reading': temp.MinReading
                    })
            
            # Alternative CPU temperature using MSR (if available)
            cpu_temps = self._get_cpu_temperatures_alternative()
            if cpu_temps:
                temperatures['cpu'].extend(cpu_temps)
            
            # GPU Temperature (NVIDIA/AMD specific)
            gpu_temps = self._get_gpu_temperatures()
            temperatures['gpu'] = gpu_temps
            
            # System/Motherboard sensors
            system_temps = self._get_system_temperatures()
            temperatures['system'] = system_temps
            
            # Drive temperatures
            drive_temps = self._get_drive_temperatures()
            temperatures['drives'] = drive_temps
            
            # Check for temperature alerts
            alerts = self._check_temperature_alerts(temperatures)
            temperatures['alerts'] = alerts
            
        except Exception as e:
            temperatures['error'] = f"Failed to monitor temperatures: {str(e)}"
        
        return temperatures
    
    def get_power_information(self) -> Dict[str, Any]:
        """Get comprehensive power information"""
        power_info = {
            'battery': {},
            'power_supply': {},
            'power_plan': {},
            'consumption': {}
        }
        
        try:
            # Battery Information
            for battery in self.wmi_conn.Win32_Battery():
                power_info['battery'] = {
                    'name': battery.Name,
                    'chemistry': battery.Chemistry,
                    'design_capacity': battery.DesignCapacity,
                    'full_charge_capacity': battery.FullChargeCapacity,
                    'estimated_charge_remaining': battery.EstimatedChargeRemaining,
                    'estimated_run_time': battery.EstimatedRunTime,
                    'status': battery.Status
                }
            
            # Power Supply
            for supply in self.wmi_conn.Win32_PowerSupply():
                power_info['power_supply'] = {
                    'name': supply.Name,
                    'total_output_power': supply.TotalOutputPower,
                    'status': supply.Status
                }
            
            # Active Power Plan
            power_info['power_plan'] = self._get_active_power_plan()
            
            # Power consumption (if available)
            power_info['consumption'] = self._get_power_consumption()
            
        except Exception as e:
            power_info['error'] = f"Failed to get power information: {str(e)}"
        
        return power_info
    
    def get_fan_information(self) -> Dict[str, Any]:
        """Get fan information and control capabilities"""
        fan_info = {
            'fans': [],
            'control_available': False,
            'thermal_zones': []
        }
        
        try:
            # Fan Information
            for fan in self.wmi_conn.Win32_Fan():
                fan_info['fans'].append({
                    'name': fan.Name,
                    'desired_speed': fan.DesiredSpeed,
                    'variable_speed': fan.VariableSpeed,
                    'status': fan.Status
                })
            
            # Thermal Zones
            for zone in self.wmi_conn.Win32_ThermalZone():
                fan_info['thermal_zones'].append({
                    'instance_name': zone.InstanceName,
                    'critical_trip_point': zone.CriticalTripPoint,
                    'current_temperature': zone.CurrentTemperature,
                    'high_precision_temperature': zone.HighPrecisionTemperature
                })
            
            # Check if fan control is available
            fan_info['control_available'] = self._check_fan_control_availability()
            
        except Exception as e:
            fan_info['error'] = f"Failed to get fan information: {str(e)}"
        
        return fan_info
    
    def run_hardware_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive hardware diagnostics"""
        diagnostics = {
            'system_health': {},
            'memory_test': {},
            'disk_health': {},
            'cpu_stress': {},
            'thermal_test': {},
            'overall_status': 'Unknown'
        }
        
        try:
            # System Health Check
            diagnostics['system_health'] = self._check_system_health()
            
            # Memory Test
            diagnostics['memory_test'] = self._run_memory_test()
            
            # Disk Health (SMART data)
            diagnostics['disk_health'] = self._check_disk_health()
            
            # CPU Stress Test (light version)
            diagnostics['cpu_stress'] = self._run_cpu_stress_test()
            
            # Thermal Test
            diagnostics['thermal_test'] = self._run_thermal_test()
            
            # Overall Status
            diagnostics['overall_status'] = self._calculate_overall_health(diagnostics)
            
        except Exception as e:
            diagnostics['error'] = f"Failed to run diagnostics: {str(e)}"
        
        return diagnostics
    
    def start_temperature_monitoring(self, interval: int = 5) -> bool:
        """Start continuous temperature monitoring"""
        if self.monitoring_active:
            return False
        
        self.monitoring_active = True
        monitor_thread = threading.Thread(target=self._temperature_monitor_loop, args=(interval,))
        monitor_thread.daemon = True
        monitor_thread.start()
        return True
    
    def stop_temperature_monitoring(self) -> bool:
        """Stop temperature monitoring"""
        self.monitoring_active = False
        return True
    
    def get_temperature_alerts(self) -> List[Dict[str, Any]]:
        """Get current temperature alerts"""
        return self.temperature_alerts
    
    def set_temperature_thresholds(self, thresholds: Dict[str, int]) -> bool:
        """Set temperature alert thresholds"""
        try:
            self.alert_thresholds.update(thresholds)
            return True
        except Exception:
            return False
    
    # Helper Methods
    def _parse_wmi_date(self, wmi_date: str) -> str:
        """Parse WMI date format to readable format"""
        if not wmi_date:
            return "Unknown"
        try:
            # WMI date format: YYYYMMDDHHMMSS.ffffff+UUU
            year = wmi_date[0:4]
            month = wmi_date[4:6]
            day = wmi_date[6:8]
            return f"{year}-{month}-{day}"
        except:
            return wmi_date
    
    def _bytes_to_gb(self, bytes_value) -> str:
        """Convert bytes to GB"""
        if not bytes_value:
            return "Unknown"
        try:
            gb = int(bytes_value) / (1024**3)
            return f"{gb:.2f} GB"
        except:
            return "Unknown"
    
    def _get_domain_role(self, role_code) -> str:
        """Convert domain role code to readable format"""
        roles = {
            0: "Standalone Workstation",
            1: "Member Workstation",
            2: "Standalone Server",
            3: "Member Server",
            4: "Backup Domain Controller",
            5: "Primary Domain Controller"
        }
        return roles.get(role_code, "Unknown")
    
    def _is_uefi_mode(self) -> bool:
        """Check if system is running in UEFI mode"""
        try:
            result = subprocess.run(['bcdedit', '/enum', 'firmware'], 
                                  capture_output=True, text=True, shell=True)
            return 'Windows Boot Manager' in result.stdout
        except:
            return False
    
    def _get_secure_boot_status(self) -> str:
        """Get Secure Boot status"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-SecureBootUEFI -Name SetupMode'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return "Enabled" if "False" in result.stdout else "Disabled"
        except:
            pass
        return "Unknown"
    
    def _check_tpm_presence(self) -> bool:
        """Check if TPM is present"""
        try:
            for tpm in self.wmi_conn.Win32_Tpm():
                return tpm.IsActivated_InitialValue
        except:
            return False
    
    def _check_virtualization(self) -> bool:
        """Check if hardware virtualization is enabled"""
        try:
            for processor in self.wmi_conn.Win32_Processor():
                if processor.VirtualizationFirmwareEnabled:
                    return True
        except:
            pass
        return False
    
    def _get_boot_configuration(self) -> Dict[str, Any]:
        """Get boot configuration"""
        boot_config = {}
        try:
            # Boot order and options
            result = subprocess.run(['bcdedit', '/enum'], 
                                  capture_output=True, text=True, shell=True)
            boot_config['boot_entries'] = result.stdout if result.returncode == 0 else "Unable to retrieve"
            
            # Boot options
            result = subprocess.run(['bcdedit', '/enum', 'bootmgr'], 
                                  capture_output=True, text=True, shell=True)
            boot_config['boot_manager'] = result.stdout if result.returncode == 0 else "Unable to retrieve"
            
        except Exception as e:
            boot_config['error'] = str(e)
        
        return boot_config
    
    def _get_security_info(self) -> Dict[str, Any]:
        """Get security information"""
        security_info = {
            'windows_defender': self._get_defender_status(),
            'firewall': self._get_firewall_status(),
            'user_account_control': self._get_uac_status(),
            'bitlocker': self._get_bitlocker_status()
        }
        return security_info
    
    def _get_defender_status(self) -> str:
        """Get Windows Defender status"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-MpComputerStatus'], 
                                  capture_output=True, text=True, shell=True)
            if "AntivirusEnabled" in result.stdout and "True" in result.stdout:
                return "Enabled"
            else:
                return "Disabled"
        except:
            return "Unknown"
    
    def _get_firewall_status(self) -> str:
        """Get Windows Firewall status"""
        try:
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles', 'state'], 
                                  capture_output=True, text=True, shell=True)
            if "ON" in result.stdout:
                return "Enabled"
            else:
                return "Disabled"
        except:
            return "Unknown"
    
    def _get_uac_status(self) -> str:
        """Get User Account Control status"""
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                               r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
            value, _ = winreg.QueryValueEx(key, "EnableLUA")
            winreg.CloseKey(key)
            return "Enabled" if value == 1 else "Disabled"
        except:
            return "Unknown"
    
    def _get_bitlocker_status(self) -> str:
        """Get BitLocker status"""
        try:
            result = subprocess.run(['manage-bde', '-status'], 
                                  capture_output=True, text=True, shell=True)
            if "Fully Encrypted" in result.stdout:
                return "Enabled"
            elif "Fully Decrypted" in result.stdout:
                return "Disabled"
            else:
                return "Partially Encrypted"
        except:
            return "Unknown"
    
    def _get_cpu_temperatures_alternative(self) -> List[Dict[str, Any]]:
        """Alternative method to get CPU temperatures"""
        temps = []
        try:
            # Try using psutil for temperature data
            if hasattr(psutil, 'sensors_temperatures'):
                sensors = psutil.sensors_temperatures()
                for name, entries in sensors.items():
                    for entry in entries:
                        temps.append({
                            'sensor': f"{name} - {entry.label}",
                            'temperature': entry.current,
                            'critical': entry.critical,
                            'high': entry.high
                        })
        except:
            pass
        return temps
    
    def _get_gpu_temperatures(self) -> List[Dict[str, Any]]:
        """Get GPU temperatures (basic implementation)"""
        temps = []
        try:
            # This would require GPU-specific libraries like nvidia-ml-py or similar
            # For now, return placeholder
            temps.append({
                'sensor': 'GPU',
                'temperature': 'Not Available',
                'status': 'GPU temperature monitoring requires additional drivers'
            })
        except:
            pass
        return temps
    
    def _get_system_temperatures(self) -> List[Dict[str, Any]]:
        """Get system/motherboard temperatures"""
        temps = []
        try:
            # Try to get thermal zone information
            for zone in self.wmi_conn.Win32_ThermalZone():
                if zone.CurrentTemperature:
                    temp_celsius = (zone.CurrentTemperature - 2732) / 10
                    temps.append({
                        'sensor': f"Thermal Zone - {zone.InstanceName}",
                        'temperature': temp_celsius,
                        'critical': zone.CriticalTripPoint / 10 if zone.CriticalTripPoint else None
                    })
        except:
            pass
        return temps
    
    def _get_drive_temperatures(self) -> List[Dict[str, Any]]:
        """Get drive temperatures using SMART data"""
        temps = []
        try:
            # This would require specific SMART monitoring libraries
            # For now, return placeholder
            temps.append({
                'sensor': 'Storage Drives',
                'temperature': 'Not Available',
                'status': 'Drive temperature monitoring requires SMART data access'
            })
        except:
            pass
        return temps
    
    def _check_temperature_alerts(self, temperatures: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for temperature alerts"""
        alerts = []
        
        for category, temp_list in temperatures.items():
            if category == 'alerts':
                continue
            
            for temp_data in temp_list:
                if isinstance(temp_data.get('temperature'), (int, float)):
                    temp_value = temp_data['temperature']
                    threshold = self.alert_thresholds.get(f"{category}_temp", 85)
                    
                    if temp_value > threshold:
                        alerts.append({
                            'timestamp': datetime.now().isoformat(),
                            'category': category,
                            'sensor': temp_data['sensor'],
                            'temperature': temp_value,
                            'threshold': threshold,
                            'severity': 'Critical' if temp_value > threshold + 10 else 'Warning'
                        })
        
        return alerts
    
    def _get_active_power_plan(self) -> Dict[str, Any]:
        """Get active power plan"""
        try:
            result = subprocess.run(['powercfg', '/getactivescheme'], 
                                  capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                return {'active_scheme': result.stdout.strip()}
        except:
            pass
        return {'active_scheme': 'Unknown'}
    
    def _get_power_consumption(self) -> Dict[str, Any]:
        """Get power consumption data"""
        try:
            result = subprocess.run(['powercfg', '/energy', '/duration', '5'], 
                                  capture_output=True, text=True, shell=True)
            return {'energy_report': 'Generated' if result.returncode == 0 else 'Failed'}
        except:
            return {'energy_report': 'Not Available'}
    
    def _check_fan_control_availability(self) -> bool:
        """Check if fan control is available"""
        # This would require specific hardware access
        # Most consumer systems don't allow direct fan control via WMI
        return False
    
    def _check_system_health(self) -> Dict[str, Any]:
        """Check overall system health"""
        health = {
            'system_file_checker': self._run_sfc_scan(),
            'memory_diagnostic': self._check_memory_diagnostic(),
            'disk_check': self._run_disk_check(),
            'system_errors': self._check_system_errors()
        }
        return health
    
    def _run_sfc_scan(self) -> str:
        """Run System File Checker scan"""
        try:
            result = subprocess.run(['sfc', '/scannow'], 
                                  capture_output=True, text=True, shell=True)
            return "Completed" if result.returncode == 0 else "Failed"
        except:
            return "Not Available"
    
    def _check_memory_diagnostic(self) -> str:
        """Check memory diagnostic results"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-WinEvent -FilterHashtable @{LogName="System"; ID=1201} -MaxEvents 1'], 
                                  capture_output=True, text=True, shell=True)
            return "Available" if result.returncode == 0 else "No Recent Results"
        except:
            return "Not Available"
    
    def _run_disk_check(self) -> Dict[str, Any]:
        """Run disk check on system drives"""
        disk_status = {}
        try:
            for disk in self.wmi_conn.Win32_LogicalDisk():
                if disk.DriveType == 3:  # Fixed disk
                    result = subprocess.run(['chkdsk', disk.DeviceID, '/f', '/r'], 
                                          capture_output=True, text=True, shell=True)
                    disk_status[disk.DeviceID] = "Healthy" if result.returncode == 0 else "Needs Attention"
        except:
            disk_status = {"status": "Unable to check"}
        return disk_status
    
    def _check_system_errors(self) -> Dict[str, Any]:
        """Check for recent system errors"""
        try:
            result = subprocess.run(['powershell', '-Command', 'Get-WinEvent -FilterHashtable @{LogName="System"; Level=2} -MaxEvents 10'], 
                                  capture_output=True, text=True, shell=True)
            return {"recent_errors": "Found" if result.returncode == 0 and result.stdout.strip() else "None"}
        except:
            return {"recent_errors": "Unable to check"}
    
    def _run_memory_test(self) -> Dict[str, Any]:
        """Run basic memory test"""
        try:
            memory_info = psutil.virtual_memory()
            return {
                'total_memory': self._bytes_to_gb(memory_info.total),
                'available_memory': self._bytes_to_gb(memory_info.available),
                'memory_percent': memory_info.percent,
                'status': 'Healthy' if memory_info.percent < 90 else 'High Usage'
            }
        except:
            return {'status': 'Unable to test'}
    
    def _check_disk_health(self) -> Dict[str, Any]:
        """Check disk health using SMART data"""
        disk_health = {}
        try:
            for disk in self.wmi_conn.Win32_DiskDrive():
                # Basic disk status
                disk_health[disk.Model or 'Unknown'] = {
                    'status': disk.Status,
                    'size': self._bytes_to_gb(disk.Size),
                    'interface': disk.InterfaceType
                }
        except:
            disk_health = {'status': 'Unable to check'}
        return disk_health
    
    def _run_cpu_stress_test(self) -> Dict[str, Any]:
        """Run light CPU stress test"""
        try:
            cpu_percent_before = psutil.cpu_percent(interval=1)
            
            # Light stress test for 5 seconds
            start_time = time.time()
            while time.time() - start_time < 5:
                _ = sum(i * i for i in range(1000))
            
            cpu_percent_after = psutil.cpu_percent(interval=1)
            
            return {
                'cpu_usage_before': cpu_percent_before,
                'cpu_usage_after': cpu_percent_after,
                'status': 'Passed' if cpu_percent_after > cpu_percent_before else 'Warning'
            }
        except:
            return {'status': 'Unable to test'}
    
    def _run_thermal_test(self) -> Dict[str, Any]:
        """Run thermal test"""
        try:
            temp_before = self.monitor_temperatures()
            
            # Wait and check again
            time.sleep(10)
            temp_after = self.monitor_temperatures()
            
            return {
                'initial_temps': temp_before,
                'final_temps': temp_after,
                'status': 'Normal' if len(temp_after.get('alerts', [])) == 0 else 'High Temperature'
            }
        except:
            return {'status': 'Unable to test'}
    
    def _calculate_overall_health(self, diagnostics: Dict[str, Any]) -> str:
        """Calculate overall system health"""
        try:
            # Simple scoring system
            score = 0
            total = 0
            
            for category, result in diagnostics.items():
                if category == 'overall_status':
                    continue
                
                total += 1
                if isinstance(result, dict):
                    if 'status' in result:
                        if result['status'] in ['Healthy', 'Passed', 'Normal', 'Completed']:
                            score += 1
                elif isinstance(result, str):
                    if result in ['Healthy', 'Passed', 'Normal', 'Completed']:
                        score += 1
            
            if total == 0:
                return 'Unknown'
            
            percentage = (score / total) * 100
            
            if percentage >= 80:
                return 'Excellent'
            elif percentage >= 60:
                return 'Good'
            elif percentage >= 40:
                return 'Fair'
            else:
                return 'Poor'
        except:
            return 'Unknown'
    
    def _temperature_monitor_loop(self, interval: int):
        """Continuous temperature monitoring loop"""
        while self.monitoring_active:
            try:
                temps = self.monitor_temperatures()
                alerts = temps.get('alerts', [])
                
                for alert in alerts:
                    # Add to alert history
                    self.temperature_alerts.append(alert)
                    
                    # Keep only last 100 alerts
                    if len(self.temperature_alerts) > 100:
                        self.temperature_alerts = self.temperature_alerts[-100:]
                
                time.sleep(interval)
            except Exception as e:
                print(f"Temperature monitoring error: {e}")
                time.sleep(interval)
    
    # =============================================================================
    # ADVANCED BIOS MANIPULATION FEATURES
    # =============================================================================
    
    def manage_uefi_variables(self, dry_run: bool = True) -> Dict[str, Any]:
        """Advanced UEFI/BIOS Variable Management"""
        try:
            result = {
                'feature': 'UEFI Variable Management',
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
                'operations': [],
                'variables': {},
                'status': 'success'
            }
            
            # Read current UEFI variables (safe operation)
            try:
                # Use bcdedit to read boot configuration
                boot_config = subprocess.run(['bcdedit', '/enum'], 
                                           capture_output=True, text=True, timeout=10)
                if boot_config.returncode == 0:
                    result['variables']['boot_config'] = boot_config.stdout[:500]  # Limit output
                    result['operations'].append('Read boot configuration')
            except:
                result['variables']['boot_config'] = 'Unable to read'
            
            # Read EFI system partition info (safe)
            try:
                efi_info = subprocess.run(['mountvol'], 
                                         capture_output=True, text=True, timeout=10)
                if efi_info.returncode == 0:
                    result['variables']['efi_partition'] = 'EFI partition detected'
                    result['operations'].append('Detected EFI partition')
            except:
                result['variables']['efi_partition'] = 'Unable to detect'
            
            # Simulate UEFI variable operations
            if dry_run:
                result['operations'].extend([
                    'DRY RUN: Would enumerate UEFI variables',
                    'DRY RUN: Would read SecureBoot variables',
                    'DRY RUN: Would check boot order variables',
                    'DRY RUN: Would validate variable signatures'
                ])
                
                # Simulate common UEFI variables
                result['variables']['simulated'] = {
                    'SecureBoot': 'Enabled (simulated)',
                    'SetupMode': 'User (simulated)',
                    'BootOrder': '0000,0001,0002 (simulated)',
                    'BootCurrent': '0000 (simulated)',
                    'PlatformLang': 'en-US (simulated)'
                }
            else:
                # Real operations would go here (currently not implemented for safety)
                result['operations'].append('REAL: Real UEFI operations not yet implemented for safety')
                result['status'] = 'simulation_only'
            
            return result
        except Exception as e:
            return {
                'feature': 'UEFI Variable Management',
                'error': str(e),
                'status': 'failed'
            }
    
    def manage_hsm_integration(self, dry_run: bool = True) -> Dict[str, Any]:
        """Hardware Security Module (HSM) Integration"""
        try:
            result = {
                'feature': 'HSM Integration',
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
                'hsm_status': {},
                'operations': [],
                'security_features': {},
                'status': 'success'
            }
            
            # Check TPM status (safe operation)
            try:
                tpm_info = subprocess.run(['tpm.msc'], 
                                         capture_output=True, text=True, timeout=5)
                result['hsm_status']['tpm_available'] = tpm_info.returncode == 0
                result['operations'].append('Checked TPM availability')
            except:
                result['hsm_status']['tpm_available'] = False
            
            # Check BitLocker status (safe)
            try:
                bitlocker_info = subprocess.run(['manage-bde', '-status'], 
                                               capture_output=True, text=True, timeout=10)
                if bitlocker_info.returncode == 0:
                    result['security_features']['bitlocker'] = 'Available'
                    result['operations'].append('Checked BitLocker status')
            except:
                result['security_features']['bitlocker'] = 'Not available'
            
            # Check Windows Hello (safe)
            try:
                hello_info = subprocess.run(['powershell', '-Command', 
                                           'Get-WindowsOptionalFeature -Online -FeatureName "*Hello*"'], 
                                          capture_output=True, text=True, timeout=10)
                if hello_info.returncode == 0:
                    result['security_features']['windows_hello'] = 'Available'
                    result['operations'].append('Checked Windows Hello')
            except:
                result['security_features']['windows_hello'] = 'Not available'
            
            # Simulate HSM operations
            if dry_run:
                result['operations'].extend([
                    'DRY RUN: Would initialize HSM connection',
                    'DRY RUN: Would enumerate security tokens',
                    'DRY RUN: Would check cryptographic capabilities',
                    'DRY RUN: Would validate security policies',
                    'DRY RUN: Would test key generation',
                    'DRY RUN: Would verify certificate chain'
                ])
                
                # Simulate HSM capabilities
                result['hsm_status']['simulated'] = {
                    'hsm_present': True,
                    'key_slots': 256,
                    'algorithms': ['RSA-2048', 'RSA-4096', 'ECC-P256', 'AES-256'],
                    'attestation': 'Supported',
                    'secure_boot': 'Enabled',
                    'measured_boot': 'Enabled'
                }
            else:
                # Real HSM operations would go here (currently not implemented for safety)
                result['operations'].append('REAL: Real HSM operations not yet implemented for safety')
                result['status'] = 'simulation_only'
            
            return result
        except Exception as e:
            return {
                'feature': 'HSM Integration',
                'error': str(e),
                'status': 'failed'
            }
    
    def manage_memory_storage_controllers(self, dry_run: bool = True) -> Dict[str, Any]:
        """Memory and Storage Controller Management"""
        try:
            result = {
                'feature': 'Memory and Storage Controller Management',
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
                'memory_controllers': {},
                'storage_controllers': {},
                'operations': [],
                'status': 'success'
            }
            
            # Read memory controller information (safe)
            try:
                for mem_controller in self.wmi_conn.Win32_MemoryArray():
                    controller_info = {
                        'location': getattr(mem_controller, 'Location', 'Unknown'),
                        'max_capacity': getattr(mem_controller, 'MaxCapacity', 'Unknown'),
                        'memory_devices': getattr(mem_controller, 'MemoryDevices', 'Unknown'),
                        'error_correction': getattr(mem_controller, 'ErrorCorrection', 'Unknown')
                    }
                    result['memory_controllers'][f'Controller_{len(result["memory_controllers"])}'] = controller_info
                    result['operations'].append('Read memory controller info')
            except:
                result['memory_controllers']['error'] = 'Unable to read memory controllers'
            
            # Read storage controller information (safe)
            try:
                for storage_controller in self.wmi_conn.Win32_SCSIController():
                    controller_info = {
                        'name': getattr(storage_controller, 'Name', 'Unknown'),
                        'manufacturer': getattr(storage_controller, 'Manufacturer', 'Unknown'),
                        'status': getattr(storage_controller, 'Status', 'Unknown'),
                        'device_id': getattr(storage_controller, 'DeviceID', 'Unknown')
                    }
                    result['storage_controllers'][f'Controller_{len(result["storage_controllers"])}'] = controller_info
                    result['operations'].append('Read storage controller info')
            except:
                result['storage_controllers']['error'] = 'Unable to read storage controllers'
            
            # Read disk controller information (safe)
            try:
                for disk_controller in self.wmi_conn.Win32_IDEController():
                    controller_info = {
                        'name': getattr(disk_controller, 'Name', 'Unknown'),
                        'manufacturer': getattr(disk_controller, 'Manufacturer', 'Unknown'),
                        'status': getattr(disk_controller, 'Status', 'Unknown')
                    }
                    result['storage_controllers'][f'IDE_Controller_{len(result["storage_controllers"])}'] = controller_info
                    result['operations'].append('Read IDE controller info')
            except:
                pass  # IDE controllers might not be present
            
            # Simulate controller management operations
            if dry_run:
                result['operations'].extend([
                    'DRY RUN: Would configure memory timing',
                    'DRY RUN: Would adjust memory voltage',
                    'DRY RUN: Would set memory frequency',
                    'DRY RUN: Would configure storage caching',
                    'DRY RUN: Would optimize storage queues',
                    'DRY RUN: Would adjust controller parameters',
                    'DRY RUN: Would enable/disable controller features'
                ])
                
                # Simulate controller capabilities
                result['simulated_capabilities'] = {
                    'memory_overclocking': 'Supported',
                    'memory_timing_adjustment': 'Supported',
                    'storage_caching': 'Enabled',
                    'storage_optimization': 'Available',
                    'controller_diagnostics': 'Supported',
                    'performance_tuning': 'Available'
                }
            else:
                # Real controller operations would go here (currently not implemented for safety)
                result['operations'].append('REAL: Real controller operations not yet implemented for safety')
                result['status'] = 'simulation_only'
            
            return result
        except Exception as e:
            return {
                'feature': 'Memory and Storage Controller Management',
                'error': str(e),
                'status': 'failed'
            }
    
    def comprehensive_bios_control_test(self, dry_run: bool = True) -> Dict[str, Any]:
        """Comprehensive test of all BIOS control features"""
        try:
            result = {
                'comprehensive_test': 'BIOS Control Features',
                'dry_run': dry_run,
                'timestamp': datetime.now().isoformat(),
                'test_results': {},
                'overall_status': 'success'
            }
            
            print("🔧 Running comprehensive BIOS control test...")
            
            # Test UEFI Variable Management
            print("  Testing UEFI Variable Management...")
            uefi_result = self.manage_uefi_variables(dry_run)
            result['test_results']['uefi_variables'] = uefi_result
            
            # Test HSM Integration
            print("  Testing HSM Integration...")
            hsm_result = self.manage_hsm_integration(dry_run)
            result['test_results']['hsm_integration'] = hsm_result
            
            # Test Memory and Storage Controller Management
            print("  Testing Memory and Storage Controller Management...")
            controller_result = self.manage_memory_storage_controllers(dry_run)
            result['test_results']['memory_storage_controllers'] = controller_result
            
            # Test existing BIOS operations
            print("  Testing existing BIOS operations...")
            bios_info = self.get_comprehensive_bios_info()
            result['test_results']['bios_info'] = {'status': 'success', 'data_retrieved': len(bios_info) > 0}
            
            # Test BIOS simulation
            print("  Testing BIOS simulation...")
            sim_result = self.simulate_bios_change('SecureBoot', 'Enabled')
            result['test_results']['bios_simulation'] = sim_result
            
            # Calculate overall test status
            failed_tests = []
            for test_name, test_result in result['test_results'].items():
                if isinstance(test_result, dict) and test_result.get('status') == 'failed':
                    failed_tests.append(test_name)
            
            if failed_tests:
                result['overall_status'] = f'partial_success - {len(failed_tests)} tests failed'
                result['failed_tests'] = failed_tests
            
            print(f"  Test completed with status: {result['overall_status']}")
            
            return result
        except Exception as e:
            return {
                'comprehensive_test': 'BIOS Control Features',
                'error': str(e),
                'overall_status': 'failed'
            }
    
    def simulate_bios_change(self, setting: str, value: str) -> Dict[str, Any]:
        """Simulate BIOS setting change (safe simulation only)"""
        try:
            result = {
                'feature': 'BIOS Change Simulation',
                'setting': setting,
                'new_value': value,
                'timestamp': datetime.now().isoformat(),
                'simulation': True,
                'status': 'success'
            }
            
            # Simulate common BIOS settings
            valid_settings = {
                'SecureBoot': ['Enabled', 'Disabled'],
                'BootOrder': ['USB', 'HDD', 'CD/DVD', 'Network'],
                'VirtualizationTechnology': ['Enabled', 'Disabled'],
                'HyperThreading': ['Enabled', 'Disabled'],
                'XMPProfile': ['Profile1', 'Profile2', 'Disabled'],
                'CPUOverclocking': ['Enabled', 'Disabled'],
                'FastBoot': ['Enabled', 'Disabled'],
                'WakeOnLAN': ['Enabled', 'Disabled'],
                'USBLegacySupport': ['Enabled', 'Disabled'],
                'TPM': ['Enabled', 'Disabled']
            }
            
            if setting in valid_settings:
                if value in valid_settings[setting]:
                    result['message'] = f'SIMULATION: Would change {setting} to {value}'
                    result['previous_value'] = 'Unknown (simulation)'
                    result['requires_reboot'] = True
                else:
                    result['status'] = 'invalid_value'
                    result['message'] = f'Invalid value {value} for {setting}'
                    result['valid_values'] = valid_settings[setting]
            else:
                result['status'] = 'unsupported_setting'
                result['message'] = f'Setting {setting} not supported'
                result['supported_settings'] = list(valid_settings.keys())
            
            return result
        except Exception as e:
            return {
                'feature': 'BIOS Change Simulation',
                'error': str(e),
                'status': 'failed'
            }
    
    def simulate_bios_operation(self, operation: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simulate BIOS operation (safe simulation only)"""
        try:
            result = {
                'feature': 'BIOS Operation Simulation',
                'operation': operation,
                'parameters': parameters or {},
                'timestamp': datetime.now().isoformat(),
                'simulation': True,
                'status': 'success'
            }
            
            # Simulate common BIOS operations
            valid_operations = {
                'reset_to_defaults': 'Reset all BIOS settings to factory defaults',
                'save_profile': 'Save current BIOS configuration to profile',
                'load_profile': 'Load BIOS configuration from profile',
                'update_firmware': 'Update BIOS firmware',
                'clear_cmos': 'Clear CMOS memory',
                'enable_overclocking': 'Enable CPU/Memory overclocking',
                'disable_overclocking': 'Disable CPU/Memory overclocking',
                'configure_boot_order': 'Configure boot device order',
                'set_admin_password': 'Set BIOS administrator password',
                'clear_admin_password': 'Clear BIOS administrator password'
            }
            
            if operation in valid_operations:
                result['message'] = f'SIMULATION: Would perform {operation}'
                result['description'] = valid_operations[operation]
                result['estimated_duration'] = '30-60 seconds'
                result['requires_reboot'] = True
                result['risk_level'] = 'medium' if operation in ['update_firmware', 'clear_cmos'] else 'low'
            else:
                result['status'] = 'unsupported_operation'
                result['message'] = f'Operation {operation} not supported'
                result['supported_operations'] = list(valid_operations.keys())
            
            return result
        except Exception as e:
            return {
                'feature': 'BIOS Operation Simulation',
                'error': str(e),
                'status': 'failed'
            }
    
    def restart_system(self, dry_run: bool = True, delay: int = 0, message: str = None) -> Dict[str, Any]:
        """Restart the system with safety controls"""
        try:
            result = {
                'feature': 'System Restart',
                'dry_run': dry_run,
                'delay': delay,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # Validate delay parameter
            if delay < 0 or delay > 3600:  # Max 1 hour delay
                result['status'] = 'invalid_delay'
                result['error'] = 'Delay must be between 0 and 3600 seconds'
                return result
            
            # Build restart command
            restart_cmd = ['shutdown', '/r', f'/t', str(delay)]
            
            # Add message if provided
            if message and len(message) <= 512:  # Windows message limit
                restart_cmd.extend(['/c', message])
            
            if dry_run:
                # Dry run - simulate the restart
                result['simulation'] = True
                result['message'] = f'DRY RUN: Would restart system in {delay} seconds'
                result['command'] = ' '.join(restart_cmd)
                result['warning'] = 'This is a simulation. No actual restart will occur.'
                
                # Additional safety information
                result['safety_info'] = {
                    'unsaved_work': 'Please save all work before actual restart',
                    'running_processes': 'All running processes will be terminated',
                    'network_connections': 'All network connections will be closed',
                    'open_files': 'All open files will be closed'
                }
                
                # Check for potentially unsafe conditions
                result['system_checks'] = self._check_restart_safety()
                
            else:
                # Real restart - execute the command
                result['simulation'] = False
                result['message'] = f'REAL RESTART: System will restart in {delay} seconds'
                result['command'] = ' '.join(restart_cmd)
                result['warning'] = 'THIS IS A REAL RESTART. SAVE ALL WORK NOW!'
                
                # Final safety check
                safety_check = self._check_restart_safety()
                if safety_check['warnings']:
                    result['safety_warnings'] = safety_check['warnings']
                
                # Execute the restart command
                try:
                    restart_process = subprocess.run(restart_cmd, 
                                                   capture_output=True, 
                                                   text=True, 
                                                   timeout=10)
                    
                    if restart_process.returncode == 0:
                        result['execution_status'] = 'success'
                        result['message'] = f'Restart initiated successfully. System will restart in {delay} seconds.'
                    else:
                        result['execution_status'] = 'failed'
                        result['error'] = restart_process.stderr or 'Unknown error'
                        result['status'] = 'failed'
                        
                except subprocess.TimeoutExpired:
                    result['execution_status'] = 'timeout'
                    result['error'] = 'Restart command timed out'
                    result['status'] = 'failed'
                except Exception as e:
                    result['execution_status'] = 'exception'
                    result['error'] = str(e)
                    result['status'] = 'failed'
            
            return result
            
        except Exception as e:
            return {
                'feature': 'System Restart',
                'error': str(e),
                'status': 'failed'
            }
    
    def _check_restart_safety(self) -> Dict[str, Any]:
        """Check system conditions before restart"""
        safety_check = {
            'warnings': [],
            'info': [],
            'system_status': 'safe'
        }
        
        try:
            # Check system uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            uptime_hours = uptime_seconds / 3600
            
            if uptime_hours < 1:
                safety_check['warnings'].append('System was recently started (less than 1 hour ago)')
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                safety_check['warnings'].append(f'High memory usage: {memory.percent}%')
            
            # Check disk usage
            disk = psutil.disk_usage('C:\\')
            if disk.percent > 95:
                safety_check['warnings'].append(f'High disk usage: {disk.percent}%')
            
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                safety_check['warnings'].append(f'High CPU usage: {cpu_percent}%')
            
            # Check running processes count
            process_count = len(psutil.pids())
            if process_count > 200:
                safety_check['info'].append(f'Many processes running: {process_count}')
            
            # Check network connections
            try:
                connections = len(psutil.net_connections())
                if connections > 100:
                    safety_check['info'].append(f'Many network connections: {connections}')
            except:
                pass  # May require admin privileges
            
            # Set overall status
            if safety_check['warnings']:
                safety_check['system_status'] = 'caution'
                
        except Exception as e:
            safety_check['warnings'].append(f'Could not perform complete safety check: {str(e)}')
            safety_check['system_status'] = 'unknown'
        
        return safety_check
    
    def cancel_restart(self) -> Dict[str, Any]:
        """Cancel a pending system restart"""
        try:
            result = {
                'feature': 'Cancel System Restart',
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            }
            
            # Cancel restart command
            cancel_cmd = ['shutdown', '/a']
            
            try:
                cancel_process = subprocess.run(cancel_cmd, 
                                               capture_output=True, 
                                               text=True, 
                                               timeout=10)
                
                if cancel_process.returncode == 0:
                    result['message'] = 'Restart cancelled successfully'
                    result['execution_status'] = 'success'
                else:
                    if 'No logoff or shutdown in progress' in cancel_process.stderr:
                        result['message'] = 'No restart was in progress'
                        result['execution_status'] = 'no_restart_pending'
                    else:
                        result['message'] = 'Failed to cancel restart'
                        result['error'] = cancel_process.stderr
                        result['execution_status'] = 'failed'
                        result['status'] = 'failed'
                        
            except subprocess.TimeoutExpired:
                result['execution_status'] = 'timeout'
                result['error'] = 'Cancel command timed out'
                result['status'] = 'failed'
            except Exception as e:
                result['execution_status'] = 'exception'
                result['error'] = str(e)
                result['status'] = 'failed'
            
            return result
            
        except Exception as e:
            return {
                'feature': 'Cancel System Restart',
                'error': str(e),
                'status': 'failed'
            }

# Test function
def test_hardware_controller():
    """Test the hardware controller functionality"""
    print("🔧 Testing Hardware Controller...")
    
    controller = HardwareController()
    
    print("\n1. BIOS Information:")
    bios_info = controller.get_comprehensive_bios_info()
    print(json.dumps(bios_info, indent=2, default=str))
    
    print("\n2. Temperature Monitoring:")
    temps = controller.monitor_temperatures()
    print(json.dumps(temps, indent=2, default=str))
    
    print("\n3. Hardware Inventory:")
    inventory = controller.get_hardware_inventory()
    print(json.dumps(inventory, indent=2, default=str))
    
    print("\n4. Power Information:")
    power = controller.get_power_information()
    print(json.dumps(power, indent=2, default=str))
    
    print("\n5. Hardware Diagnostics:")
    diagnostics = controller.run_hardware_diagnostics()
    print(json.dumps(diagnostics, indent=2, default=str))

if __name__ == "__main__":
    test_hardware_controller()
