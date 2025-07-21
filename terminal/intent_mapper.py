def get_command(user_input, os_type):
    user_input = user_input.lower()
    mappings = {
        "Windows": {
            "install node": "choco install nodejs",
            "check ip": "ipconfig",
            "disk space": "powershell -Command \"Get-PSDrive -PSProvider 'FileSystem'\"",
            "open browser": "start chrome",
            "make a file": "echo. \u003e hello.txt",
            "create file": "echo. \u003e hello.txt",
            "touch": "echo. \u003e hello.txt",
            "list files": "dir",
            "show files": "dir",
            "current directory": "cd",
            "where am i": "cd",
            "delete file": "del {{filename}}",
            "remove file": "del {{filename}}",
            "make directory": "mkdir {{folder_name}}",
            "create folder": "mkdir {{folder_name}}",
            "system info": "systeminfo",
            "date and time": "date /t \u0026 time /t",
            "network info": "ipconfig /all",
            "task list": "tasklist",
            "kill process": "taskkill /IM {{process_name}} /F",
            "start service": "net start {{service_name}}",
            "stop service": "net stop {{service_name}}",
            "restart service": "net stop {{service_name}} 6 net start {{service_name}}",
            "ping": "ping {{target}}",
            "traceroute": "tracert {{target}}",
            "firewall status": "netsh advfirewall show allprofiles",
            "enable firewall": "netsh advfirewall set allprofiles state on",
            "disable firewall": "netsh advfirewall set allprofiles state off",
            "turn on bluetooth": "enhanced_bluetooth_on",
            "turn off bluetooth": "enhanced_bluetooth_off",
            "enable bluetooth": "enhanced_bluetooth_on",
            "disable bluetooth": "enhanced_bluetooth_off",
            "bluetooth status": "enhanced_bluetooth_status",
            "bluetooth settings": "powershell -Command \"Start-Process 'ms-settings:bluetooth'\"",
            "bluetooth devices": "powershell -Command \"Get-PnpDevice | Where-Object {$_.FriendlyName -like '*Bluetooth*' -or $_.Class -eq 'Bluetooth'} | Select-Object FriendlyName, Status, InstanceId\"",
            "wifi information": "netsh wlan show interfaces",
            "wifi status": "netsh wlan show interfaces",
            "wifi info": "netsh wlan show interfaces",
            "show wifi": "netsh wlan show interfaces",
            "wifi profiles": "netsh wlan show profiles",
            "wifi networks": "netsh wlan show profiles",
            "wifi details": "netsh wlan show interfaces",
            "wifi connection": "netsh wlan show interfaces"
        },
        "Linux": {
            "install node": "sudo apt install nodejs",
            "check ip": "ifconfig",
            "disk space": "df -h",
            "make a file": "touch hello.txt",
            "create file": "touch hello.txt",
            "touch": "touch hello.txt",
            "list files": "ls -la",
            "show files": "ls -la",
            "current directory": "pwd",
            "where am i": "pwd",
            "delete file": "rm hello.txt",
            "remove file": "rm hello.txt",
            "make directory": "mkdir test_folder",
            "create folder": "mkdir test_folder",
            "system info": "uname -a",
            "date and time": "date",
            "network info": "ifconfig -a"
        }
        

    }

    for phrase, command in mappings.get(os_type, {}).items():
        if phrase in user_input:
            return command
    return None
