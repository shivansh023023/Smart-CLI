#!/usr/bin/env python3
"""
Interactive Session Handler
Manages interactive commands like SSH, database connections, and other stateful operations
"""

import subprocess
import threading
import time
import os
import queue
import select
import sys
import signal
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import re
import json

class SessionState(Enum):
    IDLE = "idle"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    EXECUTING = "executing"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class InteractiveSession:
    """Manages a single interactive session"""
    
    def __init__(self, session_id: str, command: str, session_type: str):
        self.session_id = session_id
        self.command = command
        self.session_type = session_type
        self.state = SessionState.IDLE
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        
        # Process management
        self.process = None
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()
        self.error_queue = queue.Queue()
        
        # Session context
        self.context = {
            'working_directory': None,
            'environment': {},
            'connection_info': {},
            'session_log': [],
            'command_history': [],
            'last_prompt': None
        }
        
        # Threading
        self.input_thread = None
        self.output_thread = None
        self.error_thread = None
        self.monitor_thread = None
        
        # Session-specific handlers
        self.prompt_patterns = self._get_prompt_patterns()
        self.connection_patterns = self._get_connection_patterns()
        
    def _get_prompt_patterns(self) -> List[str]:
        """Get prompt patterns for different session types"""
        patterns = {
            'ssh': [
                r'[^@]+@[^:]+:.*\$\s*$',  # user@host:path$
                r'[^@]+@[^:]+:.*#\s*$',   # user@host:path#
                r'.*\$\s*$',              # generic $
                r'.*#\s*$',               # generic #
            ],
            'database': [
                r'.*>\s*$',               # SQL prompt
                r'.*\]\s*$',              # Bracketed prompt
                r'.*:\s*$',               # Colon prompt
            ],
            'python': [
                r'>>>\s*$',               # Python REPL
                r'\.\.\.\s*$',            # Python continuation
            ],
            'node': [
                r'>\s*$',                 # Node.js REPL
                r'\.\.\.\s*$',            # Node continuation
            ],
            'powershell': [
                r'PS\s+.*>\s*$',          # PowerShell
            ],
            'cmd': [
                r'[A-Z]:\\.*>\s*$',       # Command prompt
            ]
        }
        return patterns.get(self.session_type, patterns['ssh'])
    
    def _get_connection_patterns(self) -> Dict[str, List[str]]:
        """Get connection status patterns"""
        return {
            'success': [
                r'connected',
                r'login successful',
                r'welcome',
                r'authenticated',
                r'established'
            ],
            'failure': [
                r'connection refused',
                r'authentication failed',
                r'permission denied',
                r'host unreachable',
                r'timeout'
            ],
            'prompt': [
                r'password:',
                r'passphrase:',
                r'username:',
                r'yes/no\?',
                r'continue\?'
            ]
        }
    
    def start(self) -> bool:
        """Start the interactive session"""
        try:
            self.state = SessionState.CONNECTING
            
            # Start the process
            self.process = subprocess.Popen(
                self.command,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True
            )
            
            # Start monitoring threads
            self._start_threads()
            
            # Wait for initial connection
            if self._wait_for_connection():
                self.state = SessionState.CONNECTED
                return True
            else:
                self.state = SessionState.ERROR
                return False
                
        except Exception as e:
            self.state = SessionState.ERROR
            self.context['last_error'] = str(e)
            return False
    
    def _start_threads(self):
        """Start monitoring threads"""
        self.output_thread = threading.Thread(
            target=self._monitor_output,
            daemon=True
        )
        self.error_thread = threading.Thread(
            target=self._monitor_error,
            daemon=True
        )
        self.monitor_thread = threading.Thread(
            target=self._monitor_session,
            daemon=True
        )
        
        self.output_thread.start()
        self.error_thread.start()
        self.monitor_thread.start()
    
    def _monitor_output(self):
        """Monitor stdout in a separate thread"""
        if not self.process:
            return
            
        try:
            while self.process.poll() is None:
                line = self.process.stdout.readline()
                if line:
                    self.output_queue.put(line)
                    self.last_activity = datetime.now()
                    self.context['session_log'].append({
                        'type': 'output',
                        'content': line.strip(),
                        'timestamp': datetime.now()
                    })
        except Exception as e:
            self.error_queue.put(f"Output monitoring error: {str(e)}")
    
    def _monitor_error(self):
        """Monitor stderr in a separate thread"""
        if not self.process:
            return
            
        try:
            while self.process.poll() is None:
                line = self.process.stderr.readline()
                if line:
                    self.error_queue.put(line)
                    self.last_activity = datetime.now()
                    self.context['session_log'].append({
                        'type': 'error',
                        'content': line.strip(),
                        'timestamp': datetime.now()
                    })
        except Exception as e:
            self.error_queue.put(f"Error monitoring error: {str(e)}")
    
    def _monitor_session(self):
        """Monitor session state and handle timeouts"""
        timeout = 300  # 5 minutes timeout
        
        while self.state in [SessionState.CONNECTING, SessionState.CONNECTED]:
            time.sleep(1)
            
            # Check for timeout
            if (datetime.now() - self.last_activity).seconds > timeout:
                self.state = SessionState.DISCONNECTED
                self.context['disconnect_reason'] = 'timeout'
                break
                
            # Check if process is still alive
            if self.process and self.process.poll() is not None:
                self.state = SessionState.DISCONNECTED
                self.context['disconnect_reason'] = 'process_ended'
                break
    
    def _wait_for_connection(self, timeout: int = 30) -> bool:
        """Wait for initial connection to establish"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check for output indicating connection status
            try:
                while not self.output_queue.empty():
                    line = self.output_queue.get_nowait()
                    
                    # Check for success patterns
                    for pattern in self.connection_patterns['success']:
                        if re.search(pattern, line.lower()):
                            return True
                    
                    # Check for failure patterns
                    for pattern in self.connection_patterns['failure']:
                        if re.search(pattern, line.lower()):
                            self.context['connection_error'] = line
                            return False
                    
                    # Check for prompt patterns
                    for pattern in self.prompt_patterns:
                        if re.search(pattern, line):
                            self.context['last_prompt'] = line
                            return True
                
                # Check error queue
                while not self.error_queue.empty():
                    error = self.error_queue.get_nowait()
                    for pattern in self.connection_patterns['failure']:
                        if re.search(pattern, error.lower()):
                            self.context['connection_error'] = error
                            return False
                
                time.sleep(0.1)
                
            except queue.Empty:
                continue
        
        return False
    
    def send_input(self, input_text: str) -> bool:
        """Send input to the interactive session"""
        if not self.process or self.state != SessionState.CONNECTED:
            return False
        
        try:
            self.process.stdin.write(input_text + '\n')
            self.process.stdin.flush()
            
            self.context['command_history'].append({
                'command': input_text,
                'timestamp': datetime.now()
            })
            
            self.last_activity = datetime.now()
            return True
            
        except Exception as e:
            self.context['last_error'] = str(e)
            return False
    
    def get_output(self, timeout: int = 5) -> List[str]:
        """Get recent output from the session"""
        output_lines = []
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                while not self.output_queue.empty():
                    line = self.output_queue.get_nowait()
                    output_lines.append(line)
                
                # If we have output, return it
                if output_lines:
                    break
                    
                time.sleep(0.1)
                
            except queue.Empty:
                continue
        
        return output_lines
    
    def get_status(self) -> Dict[str, Any]:
        """Get session status"""
        return {
            'session_id': self.session_id,
            'state': self.state.value,
            'session_type': self.session_type,
            'start_time': self.start_time,
            'last_activity': self.last_activity,
            'uptime': datetime.now() - self.start_time,
            'command': self.command,
            'process_id': self.process.pid if self.process else None,
            'context': self.context
        }
    
    def close(self) -> bool:
        """Close the interactive session"""
        try:
            if self.process:
                # Send exit command based on session type
                exit_commands = {
                    'ssh': 'exit',
                    'database': 'quit',
                    'python': 'exit()',
                    'node': '.exit',
                    'powershell': 'exit',
                    'cmd': 'exit'
                }
                
                exit_cmd = exit_commands.get(self.session_type, 'exit')
                self.send_input(exit_cmd)
                
                # Wait for graceful exit
                time.sleep(1)
                
                # Force terminate if still running
                if self.process.poll() is None:
                    self.process.terminate()
                    time.sleep(1)
                    
                    if self.process.poll() is None:
                        self.process.kill()
            
            self.state = SessionState.DISCONNECTED
            return True
            
        except Exception as e:
            self.context['close_error'] = str(e)
            return False

class InteractiveSessionManager:
    """Manages multiple interactive sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, InteractiveSession] = {}
        self.session_counter = 0
    
    def create_session(self, command: str, session_type: str = None) -> str:
        """Create a new interactive session"""
        self.session_counter += 1
        session_id = f"interactive_{self.session_counter}"
        
        # Auto-detect session type if not provided
        if not session_type:
            session_type = self._detect_session_type(command)
        
        session = InteractiveSession(session_id, command, session_type)
        self.sessions[session_id] = session
        
        return session_id
    
    def _detect_session_type(self, command: str) -> str:
        """Auto-detect session type based on command"""
        command_lower = command.lower()
        
        if 'ssh' in command_lower:
            return 'ssh'
        elif any(db in command_lower for db in ['mysql', 'psql', 'sqlite', 'mongo']):
            return 'database'
        elif 'python' in command_lower:
            return 'python'
        elif 'node' in command_lower:
            return 'node'
        elif 'powershell' in command_lower:
            return 'powershell'
        elif 'cmd' in command_lower:
            return 'cmd'
        else:
            return 'generic'
    
    def start_session(self, session_id: str) -> bool:
        """Start a session"""
        if session_id in self.sessions:
            return self.sessions[session_id].start()
        return False
    
    def send_to_session(self, session_id: str, input_text: str) -> bool:
        """Send input to a session"""
        if session_id in self.sessions:
            return self.sessions[session_id].send_input(input_text)
        return False
    
    def get_session_output(self, session_id: str, timeout: int = 5) -> List[str]:
        """Get output from a session"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_output(timeout)
        return []
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session status"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_status()
        return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions"""
        return [session.get_status() for session in self.sessions.values()]
    
    def close_session(self, session_id: str) -> bool:
        """Close a session"""
        if session_id in self.sessions:
            result = self.sessions[session_id].close()
            del self.sessions[session_id]
            return result
        return False
    
    def close_all_sessions(self):
        """Close all sessions"""
        for session_id in list(self.sessions.keys()):
            self.close_session(session_id)
    
    def cleanup_inactive_sessions(self, inactive_timeout: int = 1800):  # 30 minutes
        """Clean up inactive sessions"""
        now = datetime.now()
        inactive_sessions = []
        
        for session_id, session in self.sessions.items():
            if (now - session.last_activity).seconds > inactive_timeout:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            self.close_session(session_id)
            
        return len(inactive_sessions)

# Global session manager
session_manager = InteractiveSessionManager()

def create_interactive_session(command: str, session_type: str = None) -> str:
    """Create a new interactive session"""
    return session_manager.create_session(command, session_type)

def start_interactive_session(session_id: str) -> bool:
    """Start an interactive session"""
    return session_manager.start_session(session_id)

def send_to_interactive_session(session_id: str, input_text: str) -> bool:
    """Send input to an interactive session"""
    return session_manager.send_to_session(session_id, input_text)

def get_interactive_session_output(session_id: str, timeout: int = 5) -> List[str]:
    """Get output from an interactive session"""
    return session_manager.get_session_output(session_id, timeout)

def get_interactive_session_status(session_id: str) -> Optional[Dict[str, Any]]:
    """Get interactive session status"""
    return session_manager.get_session_status(session_id)

def list_interactive_sessions() -> List[Dict[str, Any]]:
    """List all interactive sessions"""
    return session_manager.list_sessions()

def close_interactive_session(session_id: str) -> bool:
    """Close an interactive session"""
    return session_manager.close_session(session_id)

def cleanup_inactive_sessions() -> int:
    """Clean up inactive sessions"""
    return session_manager.cleanup_inactive_sessions()

# Utility functions for common interactive operations
def quick_ssh(hostname: str, username: str = None, port: int = 22) -> str:
    """Create and start SSH session quickly"""
    if username:
        command = f"ssh {username}@{hostname} -p {port}"
    else:
        command = f"ssh {hostname} -p {port}"
    
    session_id = create_interactive_session(command, 'ssh')
    start_interactive_session(session_id)
    return session_id

def quick_database(db_type: str, connection_string: str) -> str:
    """Create and start database session quickly"""
    commands = {
        'mysql': f"mysql {connection_string}",
        'postgres': f"psql {connection_string}",
        'sqlite': f"sqlite3 {connection_string}",
        'mongo': f"mongo {connection_string}"
    }
    
    command = commands.get(db_type.lower(), connection_string)
    session_id = create_interactive_session(command, 'database')
    start_interactive_session(session_id)
    return session_id
