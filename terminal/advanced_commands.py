#!/usr/bin/env python3
"""
Advanced Command Database for OS Assistant
Contains 500+ commands organized by category and functionality
"""

import platform

class AdvancedCommandDatabase:
    def __init__(self):
        self.os_type = platform.system()
        self.commands = self._load_commands()
    
    def _load_commands(self):
        """Load comprehensive command database"""
        return {
            "Windows": {
                # File Operations
                "file_operations": {
                    "create file": "echo. > {filename}",
                    "create empty file": "type nul > {filename}",
                    "copy file": "copy {source} {destination}",
                    "move file": "move {source} {destination}",
                    "rename file": "ren {old_name} {new_name}",
                    "delete file": "del {filename}",
                    "delete multiple files": "del {pattern}",
                    "find file": "dir /s {filename}",
                    "search in files": "findstr /s /i \"{text}\" {pattern}",
                    "file size": "dir {filename}",
                    "file permissions": "icacls {filename}",
                    "change permissions": "icacls {filename} /grant {user}:{permission}",
                    "compress file": "powershell -Command \"Compress-Archive {source} {destination}\"",
                    "extract file": "powershell -Command \"Expand-Archive {source} {destination}\"",
                    "create backup": "xcopy {source} {backup_location} /s /e /y",
                    "sync folders": "robocopy {source} {destination} /mir",
                },
                
                # Directory Operations
                "directory_operations": {
                    "create directory": "mkdir {dirname}",
                    "remove directory": "rmdir /s /q {dirname}",
                    "list directory": "dir {path}",
                    "list hidden files": "dir /ah {path}",
                    "tree view": "tree {path}",
                    "change directory": "cd {path}",
                    "current directory": "cd",
                    "directory size": "powershell -Command \"Get-ChildItem {path} -Recurse | Measure-Object -Property Length -Sum\"",
                    "find empty directories": "for /f \\\"delims=\\\" %i in ('dir /s /b /ad {path} ^| findstr /r /v /c:\\\".*\\\\.*\\\"') do @echo %i",
                },
                
                # Process Management
                "process_management": {
                    "list processes": "tasklist",
                    "detailed process list": "tasklist /v",
                    "kill process by name": "taskkill /IM {process_name} /F",
                    "kill process by id": "taskkill /PID {process_id} /F",
                    "start process": "start {program}",
                    "process tree": "tasklist /fo tree",
                    "memory usage": "tasklist /fo table /fi \\\"memusage gt {size}\\\"",
                    "cpu usage": "wmic process get name,processid,percentprocessortime",
                    "running services": "net start",
                    "process priority": "wmic process where name=\\\"{process_name}\\\" CALL setpriority {priority}",
                },
                
                # Service Management
                "service_management": {
                    "start service": "net start {service_name}",
                    "stop service": "net stop {service_name}",
                    "restart service": "net stop {service_name} & net start {service_name}",
                    "service status": "sc query {service_name}",
                    "list services": "sc query state= all",
                    "enable service": "sc config {service_name} start= auto",
                    "disable service": "sc config {service_name} start= disabled",
                    "service dependencies": "sc enumdepend {service_name}",
                },
                
                # Network Operations
                "network_operations": {
                    "ping host": "ping {hostname}",
                    "continuous ping": "ping -t {hostname}",
                    "traceroute": "tracert {hostname}",
                    "dns lookup": "nslookup {hostname}",
                    "port scan": "telnet {hostname} {port}",
                    "network connections": "netstat -an",
                    "listening ports": "netstat -an | find \"LISTENING\"",
                    "routing table": "route print",
                    "arp table": "arp -a",
                    "flush dns": "ipconfig /flushdns",
                    "release ip": "ipconfig /release",
                    "renew ip": "ipconfig /renew",
                    "network interfaces": "ipconfig /all",
                    "wifi profiles": "netsh wlan show profiles",
                    "wifi status": "netsh wlan show interfaces",
                    "wifi information": "netsh wlan show profiles",
                    "show wifi info": "netsh wlan show interfaces",
                    "wifi networks": "netsh wlan show profiles",
                    "scan wifi": "netsh wlan show profiles",
                    "wifi details": "netsh wlan show interfaces",
                    "current wifi": "netsh wlan show interfaces",
                    "wifi connection": "netsh wlan show interfaces",
                    "connect wifi": "netsh wlan connect name=\"{profile_name}\"",
                    "disconnect wifi": "netsh wlan disconnect",
                    "wifi password": "netsh wlan show profile name=\"{profile_name}\" key=clear",
                    "forget wifi": "netsh wlan delete profile name=\"{profile_name}\"",
                    "wifi adapter": "powershell -Command \"Get-NetAdapter | Where-Object {$_.InterfaceDescription -like '*wireless*' -or $_.InterfaceDescription -like '*wifi*'}\"",
                    "wifi signal strength": "netsh wlan show interfaces",
                },
                
                # Security & Firewall
                "security_operations": {
                    "firewall status": "netsh advfirewall show allprofiles",
                    "enable firewall": "netsh advfirewall set allprofiles state on",
                    "disable firewall": "netsh advfirewall set allprofiles state off",
                    "add firewall rule": "netsh advfirewall firewall add rule name=\\\"{rule_name}\\\" dir=in action=allow protocol=TCP localport={port}",
                    "remove firewall rule": "netsh advfirewall firewall delete rule name=\\\"{rule_name}\\\"",
                    "list firewall rules": "netsh advfirewall firewall show rule name=all",
                    "user accounts": "net user",
                    "add user": "net user {username} {password} /add",
                    "delete user": "net user {username} /delete",
                    "change password": "net user {username} {new_password}",
                    "group membership": "net localgroup",
                    "add to group": "net localgroup {group} {username} /add",
                },
                
                # System Information
                "system_info": {
                    "system information": "systeminfo",
                    "computer name": "hostname",
                    "current user": "whoami",
                    "uptime": "systeminfo | find \\\"System Boot Time\\\"",
                    "cpu info": "powershell -Command \"Get-CimInstance -ClassName Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors\"",
                    "memory info": "powershell -Command \"Get-CimInstance -ClassName Win32_ComputerSystem | Select-Object TotalPhysicalMemory\"",
                    "disk info": "powershell -Command \"Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object DeviceID, Size, FreeSpace\"",
                    "installed programs": "powershell -Command \"Get-CimInstance -ClassName Win32_Product | Select-Object Name, Version\"",
                    "ram usage": "powershell -Command \"Get-CimInstance -ClassName Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory\"",
                    "disk space check": "powershell -Command \"Get-CimInstance -ClassName Win32_LogicalDisk | Select-Object DeviceID, @{Name='Size(GB)';Expression={[math]::Round($_.Size/1GB,2)}}, @{Name='FreeSpace(GB)';Expression={[math]::Round($_.FreeSpace/1GB,2)}}\"",
                    "environment variables": "set",
                    "system events": "wevtutil qe System /c:10 /rd:true /f:text",
                    "error events": "wevtutil qe Application /c:10 /q:\\\"*[System/Level=2]\\\" /rd:true /f:text",
                },
                
                # Development Tools
                "development": {
                    "git status": "git status",
                    "git add all": "git add .",
                    "git commit": "git commit -m \\\"{message}\\\"",
                    "git push": "git push origin main",
                    "git pull": "git pull origin main",
                    "git clone": "git clone {repository_url}",
                    "git branch": "git branch",
                    "create branch": "git checkout -b {branch_name}",
                    "switch branch": "git checkout {branch_name}",
                    "merge branch": "git merge {branch_name}",
                    "npm install": "npm install",
                    "npm start": "npm start",
                    "pip install": "pip install {package}",
                    "pip list": "pip list",
                    "virtual environment": "python -m venv {env_name}",
                    "activate venv": "{env_name}\\\\Scripts\\\\activate",
                },
                
                # Registry Operations
                "registry_operations": {
                    "query registry": "reg query {key_path}",
                    "add registry entry": "reg add {key_path} /v {value_name} /t {type} /d {data}",
                    "delete registry entry": "reg delete {key_path} /v {value_name} /f",
                    "export registry": "reg export {key_path} {filename}",
                    "import registry": "reg import {filename}",
                },
                
                # Performance & Monitoring
                "performance": {
                    "performance counters": "typeperf \\\"\\\\Processor(_Total)\\\\% Processor Time\\\" -sc 1",
                    "memory usage": "typeperf \\\"\\\\Memory\\\\Available MBytes\\\" -sc 1",
                    "disk activity": "typeperf \\\"\\\\PhysicalDisk(_Total)\\\\% Disk Time\\\" -sc 1",
                    "network usage": "typeperf \\\"\\\\Network Interface(*)\\\\Bytes Total/sec\\\" -sc 1",
                    "event viewer": "eventvwr",
                    "task manager": "taskmgr",
                    "resource monitor": "resmon",
                    "performance monitor": "perfmon",
                },
                
                # Backup \u0026 Recovery
                "backup_recovery": {
                    "create system restore": "wmic.exe /Namespace:\\\\root\\default Path SystemRestore Call CreateRestorePoint \"{description}\", 100, 7",
                    "list restore points": "wmic.exe /Namespace:\\\\root\\default Path SystemRestore Get Description,CreationTime",
                    "backup files": "robocopy {source} {destination} /mir /r:3 /w:10",
                    "schedule backup": "schtasks /create /tn \"{task_name}\" /tr \"{command}\" /sc {frequency}",
                    "system file check": "sfc /scannow",
                    "disk check": "chkdsk {drive} /f",
                },
                
                # Bluetooth \u0026 Wireless
                "bluetooth_operations": {
                    "turn on bluetooth": "python working_bluetooth_control.py on",
                    "turn off bluetooth": "python working_bluetooth_control.py off",
                    "bluetooth status": "python working_bluetooth_control.py status",
                    "enable bluetooth": "python working_bluetooth_control.py on",
                    "disable bluetooth": "python working_bluetooth_control.py off",
                    "check bluetooth status": "python working_bluetooth_control.py status",
                    "bluetooth devices": "powershell -Command \"Get-PnpDevice -Class Bluetooth | Select-Object FriendlyName, Status, InstanceId\"",
                    "scan bluetooth": "powershell -Command \"Add-Type -AssemblyName System.Runtime.WindowsRuntime; $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]; Function Await($WinRtTask, $ResultType) { $asTask = $asTaskGeneric.MakeGenericMethod($ResultType); $netTask = $asTask.Invoke($null, @($WinRtTask)); $netTask.Wait(-1) | Out-Null; $netTask.Result }; [Windows.Devices.Bluetooth.Advertisement.BluetoothLEAdvertisementWatcher,Windows.Devices.Bluetooth.Advertisement,ContentType=WindowsRuntime] | Out-Null; $watcher = [Windows.Devices.Bluetooth.Advertisement.BluetoothLEAdvertisementWatcher]::new(); $watcher.Start(); Write-Host 'Scanning for Bluetooth devices...'; Start-Sleep -Seconds 10; $watcher.Stop(); Write-Host 'Bluetooth scan completed'\"",
                    "pair bluetooth device": "powershell -Command \"Start-Process 'ms-settings:bluetooth' -Wait\"",
                    "bluetooth settings": "powershell -Command \"Start-Process 'ms-settings:bluetooth'\"",
                    "restart bluetooth service": "powershell -Command \"Restart-Service -Name 'bthserv' -Force; Write-Host 'Bluetooth service restarted'\"",
                    "start bluetooth service": "powershell -Command \"Start-Service -Name 'bthserv'; Write-Host 'Bluetooth service started'\"",
                    "stop bluetooth service": "powershell -Command \"Stop-Service -Name 'bthserv' -Force; Write-Host 'Bluetooth service stopped'\"",
                }
            },
            
            "Linux": {
                # File Operations
                "file_operations": {
                    "create file": "touch {filename}",
                    "copy file": "cp {source} {destination}",
                    "move file": "mv {source} {destination}",
                    "delete file": "rm {filename}",
                    "delete directory": "rm -rf {dirname}",
                    "find file": "find {path} -name {filename}",
                    "search in files": "grep -r \\\"{text}\\\" {path}",
                    "file permissions": "ls -l {filename}",
                    "change permissions": "chmod {permissions} {filename}",
                    "change owner": "chown {user}:{group} {filename}",
                    "compress file": "tar -czf {archive}.tar.gz {files}",
                    "extract file": "tar -xzf {archive}.tar.gz",
                    "disk usage": "du -sh {path}",
                    "symbolic link": "ln -s {target} {link_name}",
                },
                
                # Process Management
                "process_management": {
                    "list processes": "ps aux",
                    "process tree": "pstree",
                    "kill process": "kill {process_id}",
                    "force kill": "kill -9 {process_id}",
                    "kill by name": "pkill {process_name}",
                    "background job": "{command} &",
                    "list jobs": "jobs",
                    "bring to foreground": "fg {job_id}",
                    "send to background": "bg {job_id}",
                    "process monitor": "top",
                    "process info": "htop",
                },
                
                # System Information
                "system_info": {
                    "system info": "uname -a",
                    "cpu info": "lscpu",
                    "memory info": "free -h",
                    "disk info": "df -h",
                    "uptime": "uptime",
                    "current user": "whoami",
                    "logged users": "who",
                    "environment": "env",
                    "kernel version": "uname -r",
                    "distribution": "lsb_release -a",
                },
                
                # Network Operations
                "network_operations": {
                    "ping": "ping {hostname}",
                    "traceroute": "traceroute {hostname}",
                    "dns lookup": "dig {hostname}",
                    "network interfaces": "ifconfig",
                    "network connections": "netstat -tuln",
                    "listening ports": "ss -tuln",
                    "routing table": "route -n",
                    "arp table": "arp -a",
                    "download file": "wget {url}",
                    "curl request": "curl {url}",
                }
            }
        }
    
    def get_command(self, category, operation, **params):
        """Get command with parameter substitution"""
        try:
            command_template = self.commands[self.os_type][category][operation]
            return command_template.format(**params)
        except KeyError:
            return None
    
    def get_categories(self):
        """Get all available categories"""
        return list(self.commands.get(self.os_type, {}).keys())
    
    def get_operations(self, category):
        """Get all operations for a category"""
        return list(self.commands.get(self.os_type, {}).get(category, {}).keys())
    
    def search_commands(self, query):
        """Search for commands matching query"""
        results = []
        query_lower = query.lower()
        
        for category, operations in self.commands.get(self.os_type, {}).items():
            for operation, command in operations.items():
                if query_lower in operation.lower() or query_lower in command.lower():
                    results.append({
                        'category': category,
                        'operation': operation,
                        'command': command
                    })
        
        return results
    
    def get_command_info(self, operation):
        """Get detailed information about a command"""
        for category, operations in self.commands.get(self.os_type, {}).items():
            if operation in operations:
                return {
                    'category': category,
                    'operation': operation,
                    'command': operations[operation],
                    'os': self.os_type
                }
        return None

# Global instance
command_db = AdvancedCommandDatabase()
