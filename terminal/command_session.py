#!/usr/bin/env python3
"""
Command Session Manager with Context Memory
Provides intelligent context-aware command suggestions and session management
"""

import os
import json
import time
import pickle
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re
import threading
import sqlite3

class ContextDatabase:
    """SQLite-based context database for persistent storage"""
    
    def __init__(self, db_path: str = "data/context.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Command history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                command TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                working_directory TEXT,
                success BOOLEAN,
                output TEXT,
                execution_time REAL
            )
        ''')
        
        # Session context table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                timestamp DATETIME NOT NULL
            )
        ''')
        
        # File operations tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                file_path TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                success BOOLEAN
            )
        ''')
        
        # Command patterns for learning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                last_used DATETIME NOT NULL,
                success_rate REAL DEFAULT 1.0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_command_history(self, command: str, working_dir: str, success: bool, output: str, execution_time: float):
        """Add command to history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO command_history (command, timestamp, working_directory, success, output, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (command, datetime.now(), working_dir, success, output, execution_time))
        
        conn.commit()
        conn.close()
    
    def get_command_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent command history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT command, timestamp, working_directory, success, output, execution_time
            FROM command_history
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'command': row[0],
                'timestamp': row[1],
                'working_directory': row[2],
                'success': row[3],
                'output': row[4],
                'execution_time': row[5]
            })
        
        conn.close()
        return results
    
    def update_command_pattern(self, pattern: str):
        """Update command pattern frequency"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO command_patterns (pattern, frequency, last_used)
            VALUES (?, COALESCE((SELECT frequency FROM command_patterns WHERE pattern = ?) + 1, 1), ?)
        ''', (pattern, pattern, datetime.now()))
        
        conn.commit()
        conn.close()
    
    def get_popular_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most popular command patterns"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pattern, frequency, last_used, success_rate
            FROM command_patterns
            ORDER BY frequency DESC, last_used DESC
            LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'pattern': row[0],
                'frequency': row[1],
                'last_used': row[2],
                'success_rate': row[3]
            })
        
        conn.close()
        return results

class CommandSession:
    """Enhanced command session with context awareness and learning"""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.start_time = datetime.now()
        self.working_directory = os.getcwd()
        self.environment_vars = dict(os.environ)
        
        # Context tracking
        self.context = {
            'current_project': None,
            'recent_files': deque(maxlen=20),
            'recent_directories': deque(maxlen=10),
            'active_processes': {},
            'git_status': None,
            'last_errors': deque(maxlen=5),
            'user_preferences': {},
            'command_aliases': {},
            'frequent_commands': defaultdict(int)
        }
        
        # Initialize database
        self.db = ContextDatabase()
        
        # Load session data
        self._load_session_data()
        
        # Pattern learning
        self.command_patterns = []
        self._load_command_patterns()
    
    def _load_session_data(self):
        """Load previous session data"""
        try:
            recent_history = self.db.get_command_history(50)
            for cmd in recent_history:
                if cmd['working_directory']:
                    self.context['recent_directories'].append(cmd['working_directory'])
                
                # Extract file references from commands
                file_refs = self._extract_file_references(cmd['command'])
                for file_ref in file_refs:
                    self.context['recent_files'].append(file_ref)
        except Exception as e:
            print(f"Error loading session data: {e}")
    
    def _load_command_patterns(self):
        """Load learned command patterns"""
        try:
            self.command_patterns = self.db.get_popular_patterns(50)
        except Exception as e:
            print(f"Error loading command patterns: {e}")
    
    def _extract_file_references(self, command: str) -> List[str]:
        """Extract file and directory references from command"""
        # Simple regex patterns for common file references
        patterns = [
            r'([a-zA-Z]:\\[^\s]+)',  # Windows absolute paths
            r'([a-zA-Z]:[^\s]+)',    # Windows drive paths
            r'([^\s]+\.[a-zA-Z0-9]+)',  # Files with extensions
            r'([^\s]+/[^\s]+)',      # Unix-style paths
        ]
        
        files = []
        for pattern in patterns:
            matches = re.findall(pattern, command)
            files.extend(matches)
        
        return files
    
    def update_context(self, command: str, success: bool, output: str, execution_time: float):
        """Update session context based on command execution"""
        # Log to database
        self.db.add_command_history(command, self.working_directory, success, output, execution_time)
        
        # Update context
        self.context['frequent_commands'][command] += 1
        
        # Track errors
        if not success:
            self.context['last_errors'].append({
                'command': command,
                'error': output,
                'timestamp': datetime.now()
            })
        
        # Update file and directory context
        file_refs = self._extract_file_references(command)
        for file_ref in file_refs:
            self.context['recent_files'].append(file_ref)
        
        # Update working directory if changed
        if command.startswith('cd '):
            try:
                new_dir = command[3:].strip()
                if os.path.isdir(new_dir):
                    self.working_directory = os.path.abspath(new_dir)
                    self.context['recent_directories'].append(self.working_directory)
            except:
                pass
        
        # Update git status if git command
        if command.startswith('git '):
            self._update_git_context()
        
        # Learn command patterns
        self._learn_command_pattern(command)
    
    def _update_git_context(self):
        """Update git repository context"""
        try:
            import subprocess
            result = subprocess.run(
                'git status --porcelain',
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.working_directory
            )
            
            if result.returncode == 0:
                self.context['git_status'] = {
                    'is_git_repo': True,
                    'modified_files': [],
                    'untracked_files': [],
                    'staged_files': []
                }
                
                for line in result.stdout.strip().split('\n'):
                    if line:
                        status = line[:2]
                        filename = line[3:]
                        
                        if status == '??':
                            self.context['git_status']['untracked_files'].append(filename)
                        elif status[0] in 'MADRC':
                            self.context['git_status']['staged_files'].append(filename)
                        elif status[1] in 'MADRC':
                            self.context['git_status']['modified_files'].append(filename)
            else:
                self.context['git_status'] = {'is_git_repo': False}
        except:
            self.context['git_status'] = {'is_git_repo': False}
    
    def _learn_command_pattern(self, command: str):
        """Learn patterns from user commands"""
        # Extract command pattern (command type + common parameters)
        parts = command.split()
        if parts:
            base_command = parts[0]
            
            # Create pattern based on command structure
            pattern = base_command
            if len(parts) > 1:
                # Add parameter types
                for part in parts[1:]:
                    if part.startswith('-'):
                        pattern += f" {part}"
                    elif '.' in part:
                        pattern += " <file>"
                    elif part.isdigit():
                        pattern += " <number>"
                    else:
                        pattern += " <param>"
            
            self.db.update_command_pattern(pattern)
    
    def get_command_suggestions(self, partial_command: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get intelligent command suggestions based on context"""
        suggestions = []
        
        # History-based suggestions
        recent_commands = self.db.get_command_history(100)
        for cmd in recent_commands:
            if cmd['command'].startswith(partial_command) and cmd['command'] != partial_command:
                suggestions.append({
                    'command': cmd['command'],
                    'type': 'history',
                    'success_rate': 1.0 if cmd['success'] else 0.5,
                    'last_used': cmd['timestamp']
                })
        
        # Pattern-based suggestions
        for pattern in self.command_patterns:
            if pattern['pattern'].startswith(partial_command):
                suggestions.append({
                    'command': pattern['pattern'],
                    'type': 'pattern',
                    'success_rate': pattern['success_rate'],
                    'frequency': pattern['frequency']
                })
        
        # Context-aware suggestions
        context_suggestions = self._get_context_suggestions(partial_command)
        suggestions.extend(context_suggestions)
        
        # Sort by relevance
        suggestions.sort(key=lambda x: (x.get('success_rate', 0), x.get('frequency', 0)), reverse=True)
        
        return suggestions[:limit]
    
    def _get_context_suggestions(self, partial_command: str) -> List[Dict[str, Any]]:
        """Get context-aware suggestions"""
        suggestions = []
        
        # File-based suggestions
        if any(keyword in partial_command for keyword in ['cat', 'type', 'edit', 'del', 'copy', 'move']):
            for file_path in list(self.context['recent_files'])[-10:]:
                if os.path.exists(file_path):
                    suggestions.append({
                        'command': f"{partial_command} {file_path}",
                        'type': 'file_context',
                        'success_rate': 0.8
                    })
        
        # Directory-based suggestions
        if 'cd' in partial_command:
            for dir_path in list(self.context['recent_directories'])[-5:]:
                if os.path.exists(dir_path):
                    suggestions.append({
                        'command': f"cd {dir_path}",
                        'type': 'directory_context',
                        'success_rate': 0.9
                    })
        
        # Git-specific suggestions
        if partial_command.startswith('git') and self.context['git_status'] and self.context['git_status']['is_git_repo']:
            git_suggestions = self._get_git_suggestions(partial_command)
            suggestions.extend(git_suggestions)
        
        return suggestions
    
    def _get_git_suggestions(self, partial_command: str) -> List[Dict[str, Any]]:
        """Get git-specific suggestions based on repository state"""
        suggestions = []
        git_status = self.context['git_status']
        
        if partial_command == 'git add':
            # Suggest untracked and modified files
            for file_path in git_status.get('untracked_files', []) + git_status.get('modified_files', []):
                suggestions.append({
                    'command': f"git add {file_path}",
                    'type': 'git_context',
                    'success_rate': 0.95
                })
        
        elif partial_command == 'git commit':
            if git_status.get('staged_files'):
                suggestions.append({
                    'command': 'git commit -m "Update files"',
                    'type': 'git_context',
                    'success_rate': 0.9
                })
        
        return suggestions
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive session summary"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time,
            'duration': datetime.now() - self.start_time,
            'working_directory': self.working_directory,
            'commands_executed': sum(self.context['frequent_commands'].values()),
            'unique_commands': len(self.context['frequent_commands']),
            'recent_files': list(self.context['recent_files']),
            'recent_directories': list(self.context['recent_directories']),
            'last_errors': list(self.context['last_errors']),
            'git_status': self.context['git_status'],
            'most_frequent_commands': dict(
                sorted(self.context['frequent_commands'].items(), key=lambda x: x[1], reverse=True)[:10]
            )
        }
    
    def get_working_directory(self) -> str:
        """Get current working directory"""
        return self.working_directory
    
    def set_working_directory(self, path: str) -> bool:
        """Set working directory"""
        try:
            if os.path.isdir(path):
                self.working_directory = os.path.abspath(path)
                self.context['recent_directories'].append(self.working_directory)
                return True
        except:
            pass
        return False
    
    def get_context_info(self, key: str = None) -> Any:
        """Get context information"""
        if key:
            return self.context.get(key)
        return self.context
    
    def set_context_info(self, key: str, value: Any):
        """Set context information"""
        self.context[key] = value
    
    def add_command_alias(self, alias: str, command: str):
        """Add command alias"""
        self.context['command_aliases'][alias] = command
    
    def resolve_alias(self, command: str) -> str:
        """Resolve command alias"""
        parts = command.split()
        if parts and parts[0] in self.context['command_aliases']:
            parts[0] = self.context['command_aliases'][parts[0]]
            return ' '.join(parts)
        return command

# Global session instance
current_session = CommandSession()

def get_current_session() -> CommandSession:
    """Get current command session"""
    return current_session

def update_session_context(command: str, success: bool, output: str, execution_time: float):
    """Update session context"""
    current_session.update_context(command, success, output, execution_time)

def get_command_suggestions(partial_command: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get command suggestions"""
    return current_session.get_command_suggestions(partial_command, limit)

def get_session_summary() -> Dict[str, Any]:
    """Get session summary"""
    return current_session.get_session_summary()
