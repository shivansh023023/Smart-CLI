#!/usr/bin/env python3
"""
Working Bluetooth Control Script
Simple command-line Bluetooth control for Windows
"""

import sys
import subprocess
import time

def turn_on_bluetooth():
    """Turn on Bluetooth"""
    try:
        # Method 1: PowerShell Radio API
        cmd = '''powershell -Command "
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
        Function Await($WinRtTask, $ResultType) {
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait(-1) | Out-Null
            $netTask.Result
        }
        [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
        [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
        Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
        $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
        $bluetooth = $radios | ? { $_.Kind -eq 'Bluetooth' }
        if ($bluetooth) {
            [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            Await ($bluetooth.SetStateAsync('On')) ([Windows.Devices.Radios.RadioAccessStatus])
            Write-Host 'Bluetooth turned ON'
        } else {
            Write-Host 'No Bluetooth radio found'
        }
        "'''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "Bluetooth turned ON" in result.stdout:
            print("✅ Bluetooth turned ON successfully")
            return True
        else:
            print("❌ Failed to turn ON Bluetooth")
            return False
    except Exception as e:
        print(f"❌ Error turning ON Bluetooth: {str(e)}")
        return False

def turn_off_bluetooth():
    """Turn off Bluetooth"""
    try:
        # Method 1: PowerShell Radio API
        cmd = '''powershell -Command "
        Add-Type -AssemblyName System.Runtime.WindowsRuntime
        $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | ? { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
        Function Await($WinRtTask, $ResultType) {
            $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
            $netTask = $asTask.Invoke($null, @($WinRtTask))
            $netTask.Wait(-1) | Out-Null
            $netTask.Result
        }
        [Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
        [Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
        Await ([Windows.Devices.Radios.Radio]::RequestAccessAsync()) ([Windows.Devices.Radios.RadioAccessStatus])
        $radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
        $bluetooth = $radios | ? { $_.Kind -eq 'Bluetooth' }
        if ($bluetooth) {
            [Windows.Devices.Radios.RadioState,Windows.System.Devices,ContentType=WindowsRuntime] | Out-Null
            Await ($bluetooth.SetStateAsync('Off')) ([Windows.Devices.Radios.RadioAccessStatus])
            Write-Host 'Bluetooth turned OFF'
        } else {
            Write-Host 'No Bluetooth radio found'
        }
        "'''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if "Bluetooth turned OFF" in result.stdout:
            print("✅ Bluetooth turned OFF successfully")
            return True
        else:
            print("❌ Failed to turn OFF Bluetooth")
            return False
    except Exception as e:
        print(f"❌ Error turning OFF Bluetooth: {str(e)}")
        return False

def get_bluetooth_status():
    """Get Bluetooth status"""
    try:
        # Check service status
        result = subprocess.run('sc query "bthserv"', shell=True, capture_output=True, text=True)
        if "RUNNING" in result.stdout:
            print("📡 Bluetooth service is running")
        else:
            print("📴 Bluetooth service is stopped")
        
        # Check device status
        cmd = '''powershell -Command "Get-PnpDevice | Where-Object {$_.FriendlyName -like '*Bluetooth*' -and $_.Class -eq 'Bluetooth'} | Select-Object FriendlyName, Status"'''
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print("📋 Bluetooth devices:")
            print(result.stdout)
        
        return True
    except Exception as e:
        print(f"❌ Error getting Bluetooth status: {str(e)}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python working_bluetooth_control.py [on|off|status]")
        return
    
    command = sys.argv[1].lower()
    
    if command in ["on", "enable", "start"]:
        turn_on_bluetooth()
    elif command in ["off", "disable", "stop"]:
        turn_off_bluetooth()
    elif command in ["status", "check"]:
        get_bluetooth_status()
    else:
        print("Invalid command. Use: on, off, or status")

if __name__ == "__main__":
    main()
