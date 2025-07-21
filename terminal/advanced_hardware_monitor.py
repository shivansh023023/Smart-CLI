#!/usr/bin/env python3
"""
Advanced Hardware Monitor
Provides comprehensive hardware monitoring capabilities
"""

import psutil
import platform
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

class AdvancedHardwareMonitor:
    """Advanced hardware monitoring with detailed system information"""
    
    def __init__(self):
        self.os_type = platform.system()
        self.monitoring_active = False
        
    def get_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information"""
        try:
            cpu_info = {
                'usage_percent': psutil.cpu_percent(interval=1),
                'usage_per_core': psutil.cpu_percent(interval=1, percpu=True),
                'physical_cores': psutil.cpu_count(logical=False),
                'logical_cores': psutil.cpu_count(logical=True),
                'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                'timestamp': datetime.now().isoformat()
            }
            return cpu_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_info = {
                'virtual_memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'used': memory.used,
                    'percent': memory.percent,
                    'free': memory.free,
                    'active': getattr(memory, 'active', 0),
                    'inactive': getattr(memory, 'inactive', 0),
                    'buffers': getattr(memory, 'buffers', 0),
                    'cached': getattr(memory, 'cached', 0)
                },
                'swap_memory': {
                    'total': swap.total,
                    'used': swap.used,
                    'free': swap.free,
                    'percent': swap.percent,
                    'sin': swap.sin,
                    'sout': swap.sout
                },
                'timestamp': datetime.now().isoformat()
            }
            return memory_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information"""
        try:
            disk_info = {
                'partitions': [],
                'io_counters': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get partition information
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info['partitions'].append({
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100 if usage.total > 0 else 0
                    })
                except PermissionError:
                    continue
            
            return disk_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network interface information"""
        try:
            network_info = {
                'interfaces': {},
                'connections': len(psutil.net_connections()),
                'io_counters': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Get interface information
            for interface, addrs in psutil.net_if_addrs().items():
                stats = psutil.net_if_stats().get(interface)
                network_info['interfaces'][interface] = {
                    'addresses': [addr._asdict() for addr in addrs],
                    'is_up': stats.isup if stats else False,
                    'speed': stats.speed if stats else 0,
                    'mtu': stats.mtu if stats else 0
                }
            
            return network_info
        except Exception as e:
            return {'error': str(e)}
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get process information"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            
            return {
                'total_processes': len(processes),
                'top_cpu_processes': processes[:10],
                'top_memory_processes': sorted(processes, key=lambda x: x.get('memory_percent', 0), reverse=True)[:10],
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get general system information"""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            return {
                'platform': platform.platform(),
                'system': platform.system(),
                'processor': platform.processor(),
                'architecture': platform.architecture(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'boot_time': boot_time.isoformat(),
                'uptime': str(datetime.now() - boot_time),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive hardware report"""
        return {
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'processes': self.get_process_info(),
            'report_timestamp': datetime.now().isoformat()
        }
    
    def monitor_hardware(self, duration: int = 60, interval: int = 5) -> List[Dict[str, Any]]:
        """Monitor hardware for specified duration"""
        monitoring_data = []
        self.monitoring_active = True
        
        start_time = time.time()
        while time.time() - start_time < duration and self.monitoring_active:
            data_point = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if self.os_type != 'Windows' else psutil.disk_usage('C:\\').percent,
                'network_bytes_sent': psutil.net_io_counters().bytes_sent,
                'network_bytes_recv': psutil.net_io_counters().bytes_recv
            }
            monitoring_data.append(data_point)
            time.sleep(interval)
        
        self.monitoring_active = False
        return monitoring_data
    
    def stop_monitoring(self):
        """Stop active monitoring"""
        self.monitoring_active = False
    
    def get_hardware_alerts(self) -> List[Dict[str, Any]]:
        """Get hardware alerts based on thresholds"""
        alerts = []
        
        try:
            # CPU usage alert
            cpu_usage = psutil.cpu_percent(interval=1)
            if cpu_usage > 80:
                alerts.append({
                    'type': 'cpu',
                    'level': 'warning' if cpu_usage < 90 else 'critical',
                    'message': f'High CPU usage: {cpu_usage:.1f}%',
                    'value': cpu_usage,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Memory usage alert
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 85:
                alerts.append({
                    'type': 'memory',
                    'level': 'warning' if memory_usage < 95 else 'critical',
                    'message': f'High memory usage: {memory_usage:.1f}%',
                    'value': memory_usage,
                    'timestamp': datetime.now().isoformat()
                })
            
            # Disk usage alert
            try:
                disk_usage = psutil.disk_usage('C:\\' if self.os_type == 'Windows' else '/').percent
                if disk_usage > 90:
                    alerts.append({
                        'type': 'disk',
                        'level': 'warning' if disk_usage < 95 else 'critical',
                        'message': f'High disk usage: {disk_usage:.1f}%',
                        'value': disk_usage,
                        'timestamp': datetime.now().isoformat()
                    })
            except:
                pass
            
        except Exception as e:
            alerts.append({
                'type': 'system',
                'level': 'error',
                'message': f'Error checking hardware alerts: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
        
        return alerts

# Global instance
hardware_monitor = AdvancedHardwareMonitor()

# Convenience functions
def get_cpu_info() -> Dict[str, Any]:
    """Get CPU information"""
    return hardware_monitor.get_cpu_info()

def get_memory_info() -> Dict[str, Any]:
    """Get memory information"""
    return hardware_monitor.get_memory_info()

def get_hardware_report() -> Dict[str, Any]:
    """Get comprehensive hardware report"""
    return hardware_monitor.get_comprehensive_report()

def get_hardware_alerts() -> List[Dict[str, Any]]:
    """Get hardware alerts"""
    return hardware_monitor.get_hardware_alerts()

# Example usage
if __name__ == "__main__":
    print("🔧 Advanced Hardware Monitor")
    print("=" * 50)
    
    # Get comprehensive report
    report = get_hardware_report()
    
    # Display key metrics
    print(f"CPU Usage: {report['cpu']['usage_percent']:.1f}%")
    print(f"Memory Usage: {report['memory']['virtual_memory']['percent']:.1f}%")
    print(f"System: {report['system']['platform']}")
    print(f"Uptime: {report['system']['uptime']}")
    
    # Check for alerts
    alerts = get_hardware_alerts()
    if alerts:
        print("\n⚠️ Hardware Alerts:")
        for alert in alerts:
            print(f"  {alert['level'].upper()}: {alert['message']}")
    else:
        print("\n✅ No hardware alerts")
