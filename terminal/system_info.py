import psutil
import subprocess
import wmi
import json
import warnings
from typing import Dict, Any, List
from datetime import datetime

# Suppress WMI warnings
warnings.filterwarnings("ignore", category=UserWarning)

class SystemInfo:
    def __init__(self):
        try:
            self.wmi_connection = wmi.WMI()
            self.wmi_available = True
        except Exception as e:
            print(f"WMI initialization failed: {e}")
            self.wmi_available = False

    def get_power_management_info(self) -> Dict[str, Any]:
        """Retrieve comprehensive power management information"""
        power_info = {
            'battery': {},
            'power_supply': {},
            'power_plan': {},
            'power_consumption': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.wmi_available:
                # Battery information
                for battery in self.wmi_connection.Win32_Battery():
                    power_info['battery'] = {
                        'name': battery.Name or 'Unknown',
                        'status': self._get_battery_status(battery.BatteryStatus),
                        'chemistry': battery.Chemistry or 'Unknown',
                        'design_capacity': battery.DesignCapacity or 'Unknown',
                        'full_charge_capacity': battery.FullChargeCapacity or 'Unknown',
                        'estimated_charge_remaining': battery.EstimatedChargeRemaining or 'Unknown',
                        'estimated_run_time': battery.EstimatedRunTime or 'Unknown'
                    }
                    break
                
                # Power supply information
                for supply in self.wmi_connection.Win32_PowerSupply():
                    power_info['power_supply'] = {
                        'name': supply.Name or 'Unknown',
                        'status': supply.Status or 'Unknown',
                        'total_output_power': supply.TotalOutputPower or 'Unknown'
                    }
                    break
            
            # Active power plan
            try:
                result = subprocess.run(['powercfg', '/getactivescheme'], 
                                      capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    power_info['power_plan']['active_scheme'] = result.stdout.strip()
                else:
                    power_info['power_plan']['active_scheme'] = 'Unknown'
            except:
                power_info['power_plan']['active_scheme'] = 'Unable to retrieve'
            
            # Power consumption (basic)
            try:
                power_info['power_consumption'] = {
                    'cpu_usage': psutil.cpu_percent(interval=1),
                    'memory_usage': psutil.virtual_memory().percent,
                    'disk_usage': psutil.disk_usage('C:\\').percent if psutil.disk_usage('C:\\') else 'Unknown'
                }
            except:
                power_info['power_consumption'] = {'status': 'Unable to retrieve'}
                
        except Exception as e:
            power_info['error'] = str(e)

        return power_info
    
    def _get_battery_status(self, status_code):
        """Convert battery status code to readable format"""
        status_map = {
            1: 'Discharging',
            2: 'On AC Power',
            3: 'Fully Charged',
            4: 'Low',
            5: 'Critical',
            6: 'Charging',
            7: 'Charging and High',
            8: 'Charging and Low',
            9: 'Charging and Critical',
            10: 'Undefined',
            11: 'Partially Charged'
        }
        return status_map.get(status_code, f'Unknown ({status_code})')

    def get_peripheral_devices(self) -> Dict[str, Any]:
        """List all connected USB and Bluetooth devices"""
        peripherals = {
            'usb_devices': [],
            'bluetooth_devices': [],
            'audio_devices': [],
            'input_devices': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.wmi_available:
                # USB devices
                for usb in self.wmi_connection.Win32_USBControllerDevice():
                    try:
                        device = usb.Dependent
                        if device and hasattr(device, 'Description') and device.Description:
                            peripherals['usb_devices'].append({
                                'device_id': device.DeviceID or 'Unknown',
                                'description': device.Description or 'Unknown',
                                'manufacturer': getattr(device, 'Manufacturer', 'Unknown'),
                                'status': getattr(device, 'Status', 'Unknown')
                            })
                    except:
                        continue
                
                # Bluetooth devices
                for bt in self.wmi_connection.Win32_PnPEntity():
                    try:
                        if bt.DeviceID and 'BTH' in bt.DeviceID:
                            peripherals['bluetooth_devices'].append({
                                'device_id': bt.DeviceID or 'Unknown',
                                'description': bt.Description or 'Unknown',
                                'manufacturer': getattr(bt, 'Manufacturer', 'Unknown'),
                                'status': getattr(bt, 'Status', 'Unknown')
                            })
                    except:
                        continue
                
                # Audio devices
                for audio in self.wmi_connection.Win32_SoundDevice():
                    peripherals['audio_devices'].append({
                        'name': audio.Name or 'Unknown',
                        'manufacturer': audio.Manufacturer or 'Unknown',
                        'status': audio.Status or 'Unknown'
                    })
                
                # Input devices (keyboards, mice)
                for input_dev in self.wmi_connection.Win32_PointingDevice():
                    peripherals['input_devices'].append({
                        'name': input_dev.Name or 'Unknown',
                        'manufacturer': input_dev.Manufacturer or 'Unknown',
                        'status': input_dev.Status or 'Unknown',
                        'type': 'Pointing Device'
                    })
                
                for keyboard in self.wmi_connection.Win32_Keyboard():
                    peripherals['input_devices'].append({
                        'name': keyboard.Name or 'Unknown',
                        'description': keyboard.Description or 'Unknown',
                        'status': keyboard.Status or 'Unknown',
                        'type': 'Keyboard'
                    })
                    
        except Exception as e:
            peripherals['error'] = str(e)

        return peripherals

    def get_active_drivers(self) -> Dict[str, Any]:
        """List active drivers loaded in the system"""
        drivers_info = {
            'system_drivers': [],
            'plug_and_play_drivers': [],
            'summary': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            if self.wmi_available:
                # System drivers
                running_count = 0
                stopped_count = 0
                
                for driver in self.wmi_connection.Win32_SystemDriver():
                    driver_data = {
                        'name': driver.Name or 'Unknown',
                        'display_name': driver.DisplayName or 'Unknown',
                        'state': driver.State or 'Unknown',
                        'started': driver.Started or False,
                        'start_mode': driver.StartMode or 'Unknown',
                        'path_name': driver.PathName or 'Unknown'
                    }
                    drivers_info['system_drivers'].append(driver_data)
                    
                    if driver.Started:
                        running_count += 1
                    else:
                        stopped_count += 1
                
                # Plug and Play drivers
                for pnp_driver in self.wmi_connection.Win32_PnPSignedDriver():
                    if pnp_driver.DeviceName:
                        drivers_info['plug_and_play_drivers'].append({
                            'device_name': pnp_driver.DeviceName or 'Unknown',
                            'driver_version': pnp_driver.DriverVersion or 'Unknown',
                            'driver_date': pnp_driver.DriverDate or 'Unknown',
                            'manufacturer': pnp_driver.Manufacturer or 'Unknown',
                            'is_signed': pnp_driver.IsSigned or False
                        })
                
                drivers_info['summary'] = {
                    'total_system_drivers': len(drivers_info['system_drivers']),
                    'running_drivers': running_count,
                    'stopped_drivers': stopped_count,
                    'total_pnp_drivers': len(drivers_info['plug_and_play_drivers'])
                }
                
        except Exception as e:
            drivers_info['error'] = str(e)

        return drivers_info

    def get_network_connectivity(self) -> Dict[str, Any]:
        """Show active network connections and network interface information"""
        network_info = {
            'active_connections': [],
            'network_interfaces': [],
            'network_statistics': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Active network connections
            try:
                net_conns = psutil.net_connections(kind='inet')
                for conn in net_conns:
                    if conn.laddr and conn.raddr:  # Only show established connections
                        network_info['active_connections'].append({
                            'local_address': f"{conn.laddr.ip}:{conn.laddr.port}",
                            'remote_address': f"{conn.raddr.ip}:{conn.raddr.port}",
                            'status': conn.status,
                            'family': 'IPv4' if conn.family == 2 else 'IPv6',
                            'type': 'TCP' if conn.type == 1 else 'UDP',
                            'pid': conn.pid
                        })
            except PermissionError:
                network_info['active_connections'].append({'error': 'Permission denied - requires admin privileges'})
            
            # Network interfaces
            interfaces = psutil.net_if_addrs()
            interface_stats = psutil.net_if_stats()
            
            for interface_name, addresses in interfaces.items():
                interface_info = {
                    'name': interface_name,
                    'addresses': [],
                    'is_up': False,
                    'speed': 0,
                    'mtu': 0
                }
                
                # Get interface addresses
                for addr in addresses:
                    if addr.family == 2:  # IPv4
                        interface_info['addresses'].append({
                            'type': 'IPv4',
                            'address': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        })
                    elif addr.family == 23:  # IPv6
                        interface_info['addresses'].append({
                            'type': 'IPv6',
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
                
                # Get interface statistics
                if interface_name in interface_stats:
                    stats = interface_stats[interface_name]
                    interface_info['is_up'] = stats.isup
                    interface_info['speed'] = stats.speed
                    interface_info['mtu'] = stats.mtu
                
                network_info['network_interfaces'].append(interface_info)
            
            # Network I/O statistics
            net_io = psutil.net_io_counters()
            network_info['network_statistics'] = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errin': net_io.errin,
                'errout': net_io.errout,
                'dropin': net_io.dropin,
                'dropout': net_io.dropout
            }
            
        except Exception as e:
            network_info['error'] = str(e)

        return network_info

    def get_firewall_status(self) -> Dict[str, Any]:
        """Display comprehensive Windows Firewall status"""
        firewall_info = {
            'profiles': {},
            'overall_status': 'Unknown',
            'windows_defender': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Get firewall status for all profiles
            result = subprocess.run(['netsh', 'advfirewall', 'show', 'allprofiles'], 
                                  capture_output=True, text=True, shell=True)
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse profiles
                current_profile = None
                for line in output.split('\n'):
                    line = line.strip()
                    if 'Profile Settings' in line:
                        if 'Domain' in line:
                            current_profile = 'Domain'
                        elif 'Private' in line:
                            current_profile = 'Private'
                        elif 'Public' in line:
                            current_profile = 'Public'
                        
                        if current_profile:
                            firewall_info['profiles'][current_profile] = {}
                    
                    elif current_profile and 'State' in line and 'ON' in line:
                        firewall_info['profiles'][current_profile]['state'] = 'ON'
                    elif current_profile and 'State' in line and 'OFF' in line:
                        firewall_info['profiles'][current_profile]['state'] = 'OFF'
                    elif current_profile and 'Firewall Policy' in line:
                        policy = line.split('Firewall Policy')[1].strip()
                        firewall_info['profiles'][current_profile]['policy'] = policy
                
                # Determine overall status
                enabled_profiles = [p for p in firewall_info['profiles'].values() 
                                  if p.get('state') == 'ON']
                firewall_info['overall_status'] = 'Enabled' if enabled_profiles else 'Disabled'
            
            # Get Windows Defender status
            try:
                defender_result = subprocess.run(['powershell', '-Command', 
                                                'Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled'], 
                                               capture_output=True, text=True, shell=True)
                
                if defender_result.returncode == 0:
                    defender_output = defender_result.stdout
                    firewall_info['windows_defender'] = {
                        'antivirus_enabled': 'True' in defender_output,
                        'real_time_protection': 'True' in defender_output
                    }
                else:
                    firewall_info['windows_defender'] = {'status': 'Unable to retrieve'}
            except:
                firewall_info['windows_defender'] = {'status': 'Unable to retrieve'}
                
        except Exception as e:
            firewall_info['error'] = str(e)

        return firewall_info

    def monitor_temperatures(self) -> Dict[str, Any]:
        """Get comprehensive temperature readings from all available sensors"""
        temperatures = {
            'cpu': [],
            'gpu': [],
            'system': [],
            'drives': [],
            'fans': [],
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Try multiple methods to get temperature data
            temp_found = False
            
            # Method 1: CPU temperature using psutil
            try:
                if hasattr(psutil, 'sensors_temperatures'):
                    temps = psutil.sensors_temperatures()
                    if temps:  # Check if we got any results
                        for name, entries in temps.items():
                            for entry in entries:
                                if 'core' in name.lower() or 'cpu' in name.lower():
                                    temp_data = {
                                        'label': entry.label or f'CPU {name}',
                                        'current': entry.current,
                                        'high': entry.high,
                                        'critical': entry.critical
                                    }
                                    temperatures['cpu'].append(temp_data)
                                    temp_found = True
                                    
                                    # Check for alerts
                                    if entry.critical and entry.current > entry.critical:
                                        temperatures['alerts'].append({
                                            'level': 'Critical',
                                            'sensor': temp_data['label'],
                                            'current': entry.current,
                                            'threshold': entry.critical
                                        })
                                    elif entry.high and entry.current > entry.high:
                                        temperatures['alerts'].append({
                                            'level': 'Warning',
                                            'sensor': temp_data['label'],
                                            'current': entry.current,
                                            'threshold': entry.high
                                        })
            except:
                pass
            
            # Method 2: Try WMI for additional temperature sensors
            if self.wmi_available:
                try:
                    # CPU temperature via WMI
                    for temp_probe in self.wmi_connection.Win32_TemperatureProbe():
                        if temp_probe.CurrentReading and temp_probe.CurrentReading > 0:
                            temp_celsius = (temp_probe.CurrentReading - 2732) / 10  # Convert from decikelvin
                            if temp_celsius > 0 and temp_celsius < 150:  # Sanity check
                                temperatures['cpu'].append({
                                    'label': temp_probe.Name or 'CPU Sensor',
                                    'current': temp_celsius,
                                    'high': None,
                                    'critical': None
                                })
                                temp_found = True
                    
                    # Thermal zones
                    for zone in self.wmi_connection.Win32_ThermalZone():
                        if zone.CurrentTemperature and zone.CurrentTemperature > 0:
                            temp_celsius = (zone.CurrentTemperature - 2732) / 10
                            if temp_celsius > 0 and temp_celsius < 150:  # Sanity check
                                temperatures['system'].append({
                                    'label': f'Thermal Zone - {zone.InstanceName}',
                                    'current': temp_celsius,
                                    'critical': zone.CriticalTripPoint / 10 if zone.CriticalTripPoint else None
                                })
                                temp_found = True
                    
                    # Fan information
                    for fan in self.wmi_connection.Win32_Fan():
                        if fan.DesiredSpeed:
                            temperatures['fans'].append({
                                'name': fan.Name or 'System Fan',
                                'speed': fan.DesiredSpeed,
                                'variable_speed': fan.VariableSpeed,
                                'status': fan.Status
                            })
                    
                    # Hard drive temperatures (basic)
                    for disk in self.wmi_connection.Win32_DiskDrive():
                        temperatures['drives'].append({
                            'model': disk.Model or 'Unknown',
                            'size': disk.Size,
                            'temperature': 'N/A',  # Would need SMART data
                            'status': disk.Status
                        })
                        
                except Exception as e:
                    temperatures['wmi_error'] = str(e)
            
            # Method 3: Try PowerShell for temperature readings
            if not temp_found:
                try:
                    # Try to get temperature via PowerShell and WMI
                    ps_command = 'Get-WmiObject -Namespace "root/wmi" -Class MSAcpi_ThermalZoneTemperature | Select-Object CurrentTemperature'
                    result = subprocess.run(['powershell', '-Command', ps_command], 
                                          capture_output=True, text=True, shell=True, timeout=10)
                    
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if line.strip() and line.strip().isdigit():
                                # Convert from decikelvin to celsius
                                temp_celsius = (int(line.strip()) - 2732) / 10
                                if temp_celsius > 0 and temp_celsius < 150:  # Sanity check
                                    temperatures['cpu'].append({
                                        'label': 'CPU (PowerShell)',
                                        'current': temp_celsius,
                                        'high': None,
                                        'critical': None
                                    })
                                    temp_found = True
                                    break
                except:
                    pass
            
            # Method 4: Try simulated temperature based on CPU usage (fallback)
            if not temp_found:
                try:
                    cpu_usage = psutil.cpu_percent(interval=1)
                    # Simulate temperature based on CPU usage (very rough approximation)
                    base_temp = 35  # Base temperature
                    usage_temp = cpu_usage * 0.3  # Rough scaling
                    estimated_temp = base_temp + usage_temp
                    
                    temperatures['cpu'].append({
                        'label': 'CPU (Estimated)',
                        'current': round(estimated_temp, 1),
                        'high': 70,
                        'critical': 85,
                        'note': 'Estimated based on CPU usage - not actual sensor data'
                    })
                    temp_found = True
                    
                    # Add warning for estimated temperature
                    temperatures['alerts'].append({
                        'level': 'Info',
                        'sensor': 'Temperature Monitoring',
                        'message': 'No hardware sensors available - showing estimated values'
                    })
                    
                except:
                    pass
            
            # Method 5: Try Open Hardware Monitor / LibreHardwareMonitor via WMI
            if not temp_found:
                try:
                    # Try LibreHardwareMonitor WMI namespace
                    ohm_command = 'Get-WmiObject -Namespace "root/LibreHardwareMonitor" -Class Sensor | Where-Object {$_.SensorType -eq "Temperature"} | Select-Object Name, Value'
                    result = subprocess.run(['powershell', '-Command', ohm_command], 
                                          capture_output=True, text=True, shell=True, timeout=10)
                    
                    if result.returncode == 0 and 'Value' in result.stdout:
                        lines = result.stdout.strip().split('\n')
                        for line in lines:
                            if 'CPU' in line or 'Core' in line:
                                try:
                                    # Extract temperature value
                                    import re
                                    temp_match = re.search(r'\d+(?:\.\d+)?', line)
                                    if temp_match:
                                        temp_value = float(temp_match.group())
                                        if 20 <= temp_value <= 120:  # Reasonable range
                                            temperatures['cpu'].append({
                                                'label': 'CPU (LibreHardwareMonitor)',
                                                'current': temp_value,
                                                'high': 70,
                                                'critical': 85
                                            })
                                            temp_found = True
                                            break
                                except:
                                    continue
                except:
                    pass
            
            # GPU temperature (placeholder - would need vendor-specific libraries)
            temperatures['gpu'].append({
                'label': 'GPU',
                'current': 'N/A',
                'note': 'GPU temperature monitoring requires vendor-specific drivers/libraries (NVIDIA-ML, AMD ADL, etc.)'
            })
            
            
            # Add informational message about Windows temperature monitoring
            if not temp_found:
                temperatures['info'] = {
                    'message': 'Windows temperature monitoring is limited by hardware/driver support',
                    'suggestions': [
                        'Install Open Hardware Monitor or HWiNFO for better sensor access',
                        'Check if your motherboard manufacturer provides sensor software',
                        'Some laptops may have temperature sensors disabled in BIOS'
                    ]
                }
            
        except Exception as e:
            temperatures['error'] = str(e)

        return temperatures
    
    def get_comprehensive_system_info(self) -> Dict[str, Any]:
        """Get all system information in one comprehensive call"""
        system_info = {
            'timestamp': datetime.now().isoformat(),
            'power_management': self.get_power_management_info(),
            'peripheral_devices': self.get_peripheral_devices(),
            'active_drivers': self.get_active_drivers(),
            'network_connectivity': self.get_network_connectivity(),
            'firewall_status': self.get_firewall_status(),
            'temperatures': self.monitor_temperatures()
        }
        
        return system_info


# Demo/Test function
def test_system_info():
    """Test all SystemInfo features"""
    print("🔧 Testing SystemInfo features...")
    
    sys_info = SystemInfo()
    
    print("\n1. Power Management Info:")
    power_info = sys_info.get_power_management_info()
    print(json.dumps(power_info, indent=2, default=str))
    
    print("\n2. Peripheral Devices:")
    peripherals = sys_info.get_peripheral_devices()
    print(json.dumps(peripherals, indent=2, default=str))
    
    print("\n3. Active Drivers:")
    drivers = sys_info.get_active_drivers()
    print(json.dumps(drivers, indent=2, default=str))
    
    print("\n4. Network Connectivity:")
    network = sys_info.get_network_connectivity()
    print(json.dumps(network, indent=2, default=str))
    
    print("\n5. Firewall Status:")
    firewall = sys_info.get_firewall_status()
    print(json.dumps(firewall, indent=2, default=str))
    
    print("\n6. Temperature Monitoring:")
    temperatures = sys_info.monitor_temperatures()
    print(json.dumps(temperatures, indent=2, default=str))
    
    print("\n7. Comprehensive System Info:")
    comprehensive = sys_info.get_comprehensive_system_info()
    print("Comprehensive system info generated successfully!")
    print(f"Total data keys: {len(comprehensive.keys())}")
    
    print("\n✅ All SystemInfo features tested successfully!")


if __name__ == "__main__":
    test_system_info()
