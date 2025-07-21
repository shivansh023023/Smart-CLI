#!/usr/bin/env python3
"""
Enhanced Command Executor with Advanced Features
Supports pipes, conditionals, background processes, and command chaining
"""

import subprocess
import threading
import time
import os
import json
import queue
import signal
import sys
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

class ProcessManager:
    """Manages background processes and long-running tasks"""
    
    def __init__(self):
        self.running_processes = {}
        self.process_counter = 0
        self.process_queue = queue.Queue()
        
    def start_background_process(self, command: str, process_id: str = None) -> str:
        """Start a command in the background and return process ID"""
        if not process_id:
            self.process_counter += 1
            process_id = f"bg_{self.process_counter}"
        
        try:
            # Start process in background
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            
            self.running_processes[process_id] = {
                'process': process,
                'command': command,
                'start_time': datetime.now(),
                'status': 'running'
            }
            
            # Monitor process in separate thread
            monitor_thread = threading.Thread(
                target=self._monitor_process,
                args=(process_id, process),
                daemon=True
            )
            monitor_thread.start()
            
            return process_id
            
        except Exception as e:
            return f"Error starting background process: {str(e)}"
    
    def _monitor_process(self, process_id: str, process: subprocess.Popen):
        """Monitor a background process"""
        try:
            stdout, stderr = process.communicate()
            
            self.running_processes[process_id].update({
                'status': 'completed' if process.returncode == 0 else 'failed',
                'return_code': process.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'end_time': datetime.now()
            })
            
        except Exception as e:
            self.running_processes[process_id].update({
                'status': 'error',
                'error': str(e),
                'end_time': datetime.now()
            })
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Get status of a background process"""
        return self.running_processes.get(process_id, {'status': 'not_found'})
    
    def list_processes(self) -> Dict[str, Dict[str, Any]]:
        """List all background processes"""
        return self.running_processes
    
    def kill_process(self, process_id: str) -> bool:
        """Kill a background process"""
        if process_id in self.running_processes:
            try:
                process = self.running_processes[process_id]['process']
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:  # Still running, force kill
                        process.kill()
                
                self.running_processes[process_id]['status'] = 'killed'
                return True
            except Exception as e:
                print(f"Error killing process {process_id}: {str(e)}")
                return False
        return False

class CommandChainExecutor:
    """Executes complex command chains with pipes, conditionals, and parallel execution"""
    
    def __init__(self):
        self.process_manager = ProcessManager()
        self.last_exit_code = 0
        self.command_history = []
    
    def execute_command_chain(self, command_chain: str) -> Tuple[bool, str]:
        """
        Execute a complex command chain with support for:
        - Pipes: command1 | command2
        - Conditionals: command1 && command2, command1 || command2
        - Sequential: command1; command2
        - Background: command1 & command2
        """
        try:
            # Log the command
            self.command_history.append({
                'command': command_chain,
                'timestamp': datetime.now(),
                'type': 'chain'
            })
            
            # Parse and execute the command chain
            result = self._parse_and_execute(command_chain)
            return result
            
        except Exception as e:
            return False, f"Command chain execution error: {str(e)}"
    
    def _parse_and_execute(self, command_chain: str) -> Tuple[bool, str]:
        """Parse and execute command chain based on operators"""
        command_chain = command_chain.strip()
        
        # Handle background execution (&)
        if command_chain.endswith(' &'):
            return self._execute_background(command_chain[:-1].strip())
        
        # Handle sequential execution (;)
        if ';' in command_chain:
            return self._execute_sequential(command_chain)
        
        # Handle conditional OR (||)
        if '||' in command_chain:
            return self._execute_conditional_or(command_chain)
        
        # Handle conditional AND (&&)
        if '&&' in command_chain:
            return self._execute_conditional_and(command_chain)
        
        # Handle pipes (|)
        if '|' in command_chain:
            return self._execute_pipe(command_chain)
        
        # Single command
        return self._execute_single_command(command_chain)
    
    def _execute_background(self, command: str) -> Tuple[bool, str]:
        """Execute command in background"""
        process_id = self.process_manager.start_background_process(command)
        return True, f"Started background process: {process_id}"
    
    def _execute_sequential(self, command_chain: str) -> Tuple[bool, str]:
        """Execute commands sequentially (command1; command2)"""
        commands = [cmd.strip() for cmd in command_chain.split(';')]
        results = []
        
        for cmd in commands:
            if cmd:
                success, output = self._parse_and_execute(cmd)
                results.append(f"[{cmd}] -> {output}")
                # Continue regardless of success/failure
        
        return True, "\n".join(results)
    
    def _execute_conditional_and(self, command_chain: str) -> Tuple[bool, str]:
        """Execute conditional AND (command1 && command2)"""
        commands = [cmd.strip() for cmd in command_chain.split('&&')]
        results = []
        
        for cmd in commands:
            if cmd:
                success, output = self._parse_and_execute(cmd)
                results.append(f"[{cmd}] -> {output}")
                if not success:
                    return False, "\n".join(results) + "\n(Chain stopped due to failure)"
        
        return True, "\n".join(results)
    
    def _execute_conditional_or(self, command_chain: str) -> Tuple[bool, str]:
        """Execute conditional OR (command1 || command2)"""
        commands = [cmd.strip() for cmd in command_chain.split('||')]
        results = []
        
        for cmd in commands:
            if cmd:
                success, output = self._parse_and_execute(cmd)
                results.append(f"[{cmd}] -> {output}")
                if success:
                    return True, "\n".join(results) + "\n(Chain succeeded)"
        
        return False, "\n".join(results) + "\n(All commands failed)"
    
    def _execute_pipe(self, command_chain: str) -> Tuple[bool, str]:
        """Execute piped commands (command1 | command2)"""
        commands = [cmd.strip() for cmd in command_chain.split('|')]
        
        try:
            # Create process chain
            processes = []
            
            for i, cmd in enumerate(commands):
                if i == 0:
                    # First command
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    # Subsequent commands - pipe from previous
                    process = subprocess.Popen(
                        cmd,
                        shell=True,
                        stdin=processes[-1].stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    processes[-1].stdout.close()  # Close previous stdout
                
                processes.append(process)
            
            # Get final output
            stdout, stderr = processes[-1].communicate()
            
            # Check if all processes succeeded
            success = all(p.wait() == 0 for p in processes)
            
            return success, stdout.strip() if stdout else stderr.strip()
            
        except Exception as e:
            return False, f"Pipe execution error: {str(e)}"
    
    def _execute_single_command(self, command: str) -> Tuple[bool, str]:
        """Execute a single command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            self.last_exit_code = result.returncode
            output = result.stdout.strip() or result.stderr.strip()
            
            return result.returncode == 0, output
            
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds"
        except Exception as e:
            return False, f"Command execution error: {str(e)}"
    
    def get_command_history(self) -> List[Dict[str, Any]]:
        """Get command execution history"""
        return self.command_history
    
    def get_background_processes(self) -> Dict[str, Dict[str, Any]]:
        """Get all background processes"""
        return self.process_manager.list_processes()
    
    def kill_background_process(self, process_id: str) -> bool:
        """Kill a background process"""
        return self.process_manager.kill_process(process_id)
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Get status of a background process"""
        return self.process_manager.get_process_status(process_id)

# Global instance
enhanced_executor = CommandChainExecutor()

def execute_enhanced_command(command: str) -> Tuple[bool, str]:
    """Main entry point for enhanced command execution"""
    # Check for special Bluetooth commands
    if command == "enhanced_bluetooth_on":
        try:
            from enhanced_bluetooth_controller import turn_on_bluetooth_enhanced
            result = turn_on_bluetooth_enhanced()
            return result["success"], result["output"]
        except Exception as e:
            return False, f"Enhanced Bluetooth control failed: {str(e)}"
    
    elif command == "enhanced_bluetooth_off":
        try:
            from enhanced_bluetooth_controller import turn_off_bluetooth_enhanced
            result = turn_off_bluetooth_enhanced()
            return result["success"], result["output"]
        except Exception as e:
            return False, f"Enhanced Bluetooth control failed: {str(e)}"
    
    elif command == "enhanced_bluetooth_status":
        try:
            from enhanced_bluetooth_controller import get_bluetooth_status_enhanced
            result = get_bluetooth_status_enhanced()
            status_text = f"Service Status: {result['service_status']}\n"
            status_text += f"Radio State: {result['radio_state']}\n"
            if result['devices']:
                status_text += f"Devices: {len(result['devices'])} found\n"
            return True, status_text
        except Exception as e:
            return False, f"Enhanced Bluetooth status check failed: {str(e)}"
    
    # Check for web browser commands
    elif command.startswith("open_url:"):
        try:
            from web_browser_controller import open_url
            url = command.split(":", 1)[1]
            return open_url(url)
        except Exception as e:
            return False, f"Failed to open URL: {str(e)}"
    
    elif command.startswith("launch_browser:"):
        try:
            from web_browser_controller import launch_browser
            browser = command.split(":", 1)[1] if ":" in command else "chrome"
            return launch_browser(browser)
        except Exception as e:
            return False, f"Failed to launch browser: {str(e)}"
    
    elif command == "open_youtube":
        try:
            from web_browser_controller import open_youtube
            return open_youtube()
        except Exception as e:
            return False, f"Failed to open YouTube: {str(e)}"
    
    elif command == "open_google":
        try:
            from web_browser_controller import open_google
            return open_google()
        except Exception as e:
            return False, f"Failed to open Google: {str(e)}"
    
    elif command.startswith("search_google:"):
        try:
            from web_browser_controller import search_google
            query = command.split(":", 1)[1]
            return search_google(query)
        except Exception as e:
            return False, f"Failed to search Google: {str(e)}"
    
    # Check for desktop app commands
    elif command.startswith("launch_app:"):
        try:
            from desktop_app_controller import launch_app
            app_name = command.split(":", 1)[1]
            return launch_app(app_name)
        except Exception as e:
            return False, f"Failed to launch app: {str(e)}"
    
    elif command.startswith("close_app:"):
        try:
            from desktop_app_controller import close_app
            app_name = command.split(":", 1)[1]
            return close_app(app_name)
        except Exception as e:
            return False, f"Failed to close app: {str(e)}"
    
    elif command == "list_apps":
        try:
            from desktop_app_controller import list_installed_apps
            apps = list_installed_apps()
            if apps:
                app_list = "\n".join([f"• {app['name']} ({app['source']})" for app in apps[:20]])
                if len(apps) > 20:
                    app_list += f"\n... and {len(apps) - 20} more apps"
                return True, f"Installed Applications:\n{app_list}"
            else:
                return False, "No applications found"
        except Exception as e:
            return False, f"Failed to list apps: {str(e)}"
    
    elif command.startswith("app_info:"):
        try:
            from desktop_app_controller import get_app_info
            app_name = command.split(":", 1)[1]
            info = get_app_info(app_name)
            if info['found']:
                status = "Running" if info['running'] else "Not running"
                return True, f"App: {info['name']}\nPath: {info['path']}\nSource: {info['source']}\nStatus: {status}"
            else:
                return False, info['error']
        except Exception as e:
            return False, f"Failed to get app info: {str(e)}"
    
    # For regular commands, use the original executor
    return enhanced_executor.execute_command_chain(command)

def get_background_processes() -> Dict[str, Dict[str, Any]]:
    """Get all background processes"""
    return enhanced_executor.get_background_processes()

def kill_background_process(process_id: str) -> bool:
    """Kill a background process"""
    return enhanced_executor.kill_background_process(process_id)

def get_command_history() -> List[Dict[str, Any]]:
    """Get command execution history"""
    return enhanced_executor.get_command_history()

def create_test_background_process() -> str:
    """Create a test background process for debugging"""
    test_command = "ping 8.8.8.8 -t" if sys.platform == "win32" else "ping 8.8.8.8"
    process_id = enhanced_executor.process_manager.start_background_process(test_command)
    return process_id

def test_background_functionality():
    """Test background process functionality"""
    try:
        # Create a test process
        process_id = create_test_background_process()
        print(f"Created test process: {process_id}")
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Get processes
        processes = get_background_processes()
        print(f"Background processes: {processes}")
        
        # Kill test process
        if process_id in processes:
            kill_background_process(process_id)
            print(f"Killed test process: {process_id}")
        
        return True
    except Exception as e:
        print(f"Test failed: {str(e)}")
        return False
