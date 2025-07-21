#!/usr/bin/env python3
"""
AI-Driven Command Suggestion Engine
Provides real-time, context-aware command suggestions and autocomplete
"""

import re
import threading
import time
from typing import List, Dict, Tuple, Optional
from conversation_manager import get_recent_commands, get_context_for_query
from enhanced_llm_parser import EnhancedLLMParser
from config.settings import *
import os
import platform

class AISuggestionEngine:
    def __init__(self, llm_parser: EnhancedLLMParser):
        self.llm_parser = llm_parser
        self.suggestion_cache = {}
        self.last_suggestion_time = 0
        self.suggestion_delay = 0.5  # 500ms delay before suggesting
        self.suggestion_thread = None
        self.current_suggestions = []
        self.suggestion_callback = None
        
        # Common command patterns and their categories
        self.command_patterns = {
            'file_operations': [
                'ls', 'dir', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'find',
                'grep', 'cat', 'head', 'tail', 'less', 'more', 'touch', 'chmod', 'chown'
            ],
            'system_info': [
                'ps', 'top', 'htop', 'df', 'du', 'free', 'uname', 'whoami', 'id',
                'uptime', 'date', 'cal', 'history', 'which', 'where', 'whereis'
            ],
            'network': [
                'ping', 'wget', 'curl', 'ssh', 'scp', 'rsync', 'netstat', 'ifconfig',
                'ip', 'arp', 'route', 'traceroute', 'nslookup', 'dig'
            ],
            'development': [
                'git', 'npm', 'pip', 'python', 'node', 'java', 'gcc', 'make',
                'docker', 'kubectl', 'terraform', 'ansible', 'vagrant'
            ],
            'text_processing': [
                'awk', 'sed', 'sort', 'uniq', 'cut', 'tr', 'wc', 'diff', 'patch'
            ],
            'system_control': [
                'sudo', 'systemctl', 'service', 'crontab', 'at', 'jobs', 'nohup',
                'screen', 'tmux', 'kill', 'killall', 'pkill'
            ]
        }
        
        # Platform-specific commands
        if platform.system() == "Windows":
            self.command_patterns['windows'] = [
                'powershell', 'cmd', 'tasklist', 'taskkill', 'sc', 'net', 'ipconfig',
                'systeminfo', 'wmic', 'reg', 'diskpart', 'sfc', 'chkdsk'
            ]
        
        # Build flat command list for quick lookup
        self.all_commands = []
        for category, commands in self.command_patterns.items():
            self.all_commands.extend(commands)
        
        # Natural language patterns that might need command suggestions
        self.nl_patterns = {
            r'(list|show|display).*(file|folder|director)': ['ls', 'dir', 'find'],
            r'(find|search|locate).*(file|folder)': ['find', 'locate', 'grep'],
            r'(check|show|display).*(process|running)': ['ps', 'top', 'tasklist'],
            r'(copy|move|rename).*(file|folder)': ['cp', 'mv', 'copy', 'move'],
            r'(delete|remove).*(file|folder)': ['rm', 'del', 'rmdir'],
            r'(create|make).*(folder|directory)': ['mkdir', 'md'],
            r'(connect|ssh|remote)': ['ssh', 'telnet', 'rdp'],
            r'(download|get|fetch)': ['wget', 'curl', 'git clone'],
            r'(install|setup|configure)': ['apt install', 'yum install', 'pip install', 'npm install'],
            r'(network|connection|internet)': ['ping', 'netstat', 'ifconfig', 'ipconfig'],
            r'(memory|ram|cpu|system)': ['free', 'top', 'systeminfo', 'htop'],
            r'(disk|storage|space)': ['df', 'du', 'diskpart', 'fdisk'],
            r'(git|version|commit)': ['git status', 'git add', 'git commit', 'git push'],
            r'(docker|container)': ['docker ps', 'docker run', 'docker build'],
            r'(python|run|execute)': ['python', 'python3', 'py'],
            r'(edit|modify|change)': ['nano', 'vim', 'code', 'notepad'],
            r'(compress|archive|zip)': ['tar', 'zip', 'gzip', '7z'],
            r'(permission|access|owner)': ['chmod', 'chown', 'chgrp', 'icacls']
        }
        
    def set_suggestion_callback(self, callback):
        """Set callback function to receive suggestions"""
        self.suggestion_callback = callback
        
    def get_suggestions(self, user_input: str, context: Dict = None) -> List[Dict]:
        """
        Get intelligent suggestions for user input
        Returns list of suggestion dictionaries with type, command, and description
        """
        if not user_input or len(user_input) < 2:
            return []
            
        suggestions = []
        user_input_lower = user_input.lower().strip()
        
        # 1. Direct command matching
        command_suggestions = self._get_command_suggestions(user_input_lower)
        suggestions.extend(command_suggestions)
        
        # 2. Natural language pattern matching
        nl_suggestions = self._get_natural_language_suggestions(user_input_lower)
        suggestions.extend(nl_suggestions)
        
        # 3. Context-aware suggestions from recent history
        context_suggestions = self._get_context_suggestions(user_input_lower, context)
        suggestions.extend(context_suggestions)
        
        # 4. AI-powered suggestions (if available and input is complex enough)
        if self.llm_parser.connected and len(user_input) > 5:
            ai_suggestions = self._get_ai_suggestions(user_input, context)
            suggestions.extend(ai_suggestions)
            
        # Remove duplicates and limit results
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            key = (suggestion['command'], suggestion['type'])
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= 8:  # Limit to 8 suggestions
                    break
                    
        return unique_suggestions
        
    def _get_command_suggestions(self, user_input: str) -> List[Dict]:
        """Get suggestions based on command prefix matching"""
        suggestions = []
        
        # Direct command matching
        for command in self.all_commands:
            if command.startswith(user_input):
                suggestions.append({
                    'type': 'command',
                    'command': command,
                    'description': f'Execute {command} command',
                    'confidence': 0.9 if command == user_input else 0.7
                })
                
        # Fuzzy matching for typos
        if not suggestions:
            for command in self.all_commands:
                if self._fuzzy_match(user_input, command):
                    suggestions.append({
                        'type': 'command_fuzzy',
                        'command': command,
                        'description': f'Did you mean: {command}?',
                        'confidence': 0.6
                    })
                    
        return suggestions[:4]  # Limit command suggestions
        
    def _get_natural_language_suggestions(self, user_input: str) -> List[Dict]:
        """Get suggestions based on natural language patterns"""
        suggestions = []
        
        for pattern, commands in self.nl_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                for command in commands:
                    suggestions.append({
                        'type': 'natural_language',
                        'command': command,
                        'description': f'Based on your request: {command}',
                        'confidence': 0.8
                    })
                    
        return suggestions[:3]  # Limit NL suggestions
        
    def _get_context_suggestions(self, user_input: str, context: Dict = None) -> List[Dict]:
        """Get suggestions based on conversation context and recent commands"""
        suggestions = []
        
        try:
            # Get recent commands from conversation history
            recent_commands = get_recent_commands(limit=10)
            
            # Suggest recently used commands that match input
            for cmd_data in recent_commands:
                command = cmd_data.get('command', '')
                if command and user_input in command.lower():
                    suggestions.append({
                        'type': 'recent',
                        'command': command,
                        'description': f'Recently used: {command}',
                        'confidence': 0.75
                    })
                    
            # Context-aware suggestions based on current directory
            if context:
                current_dir = context.get('current_directory', '')
                if current_dir:
                    # Suggest directory-relevant commands
                    if any(ext in current_dir.lower() for ext in ['.git', 'git']):
                        git_commands = ['git status', 'git add .', 'git commit', 'git push']
                        for cmd in git_commands:
                            if user_input in cmd.lower():
                                suggestions.append({
                                    'type': 'context_git',
                                    'command': cmd,
                                    'description': f'Git repository detected: {cmd}',
                                    'confidence': 0.85
                                })
                                
        except Exception as e:
            pass  # Fail silently for context suggestions
            
        return suggestions[:3]  # Limit context suggestions
        
    def _get_ai_suggestions(self, user_input: str, context: Dict = None) -> List[Dict]:
        """Get AI-powered suggestions using the LLM"""
        suggestions = []
        
        try:
            # Check cache first
            cache_key = f"{user_input}_{context.get('current_directory', '') if context else ''}"
            if cache_key in self.suggestion_cache:
                cache_time, cached_suggestions = self.suggestion_cache[cache_key]
                if time.time() - cache_time < 300:  # Cache for 5 minutes
                    return cached_suggestions
                    
            # Create a prompt for the LLM to suggest commands
            prompt = f"""
Based on the user input: "{user_input}"
Context: {context if context else 'No context'}
Platform: {platform.system()}

Suggest 2-3 relevant commands that the user might want to execute.
Respond with just the commands, one per line, no explanations.
Focus on practical, commonly used commands.
"""
            
            # Get AI suggestions (with timeout)
            result = self.llm_parser.parse_command(prompt, context=context, timeout=3)
            
            if result and result.get('explanation'):
                # Parse the response to extract commands
                lines = result['explanation'].split('\n')
                for line in lines[:3]:  # Max 3 AI suggestions
                    line = line.strip()
                    if line and not line.startswith('#') and not line.startswith('//'):
                        suggestions.append({
                            'type': 'ai_powered',
                            'command': line,
                            'description': f'AI suggestion: {line}',
                            'confidence': 0.7
                        })
                        
            # Cache the results
            self.suggestion_cache[cache_key] = (time.time(), suggestions)
            
        except Exception as e:
            # Fail silently for AI suggestions
            pass
            
        return suggestions
        
    def _fuzzy_match(self, input_str: str, command: str, threshold: float = 0.6) -> bool:
        """Simple fuzzy matching for command suggestions"""
        if len(input_str) < 2:
            return False
            
        # Calculate similarity based on common characters
        common_chars = sum(1 for c in input_str if c in command)
        similarity = common_chars / len(input_str)
        
        return similarity >= threshold
        
    def get_suggestions_async(self, user_input: str, context: Dict = None):
        """Get suggestions asynchronously with debouncing"""
        current_time = time.time()
        self.last_suggestion_time = current_time
        
        def delayed_suggestion():
            # Wait for debounce period
            time.sleep(self.suggestion_delay)
            
            # Check if this is still the latest request
            if self.last_suggestion_time != current_time:
                return
                
            # Get suggestions
            suggestions = self.get_suggestions(user_input, context)
            
            # Call callback if available
            if self.suggestion_callback:
                self.suggestion_callback(suggestions)
                
        # Cancel previous thread if running
        if self.suggestion_thread and self.suggestion_thread.is_alive():
            self.last_suggestion_time = current_time
            
        # Start new thread
        self.suggestion_thread = threading.Thread(target=delayed_suggestion)
        self.suggestion_thread.daemon = True
        self.suggestion_thread.start()
        
    def get_command_completion(self, partial_command: str) -> List[str]:
        """Get command completion suggestions for partial commands"""
        completions = []
        
        if not partial_command:
            return completions
            
        # Split into parts to handle complex commands
        parts = partial_command.split()
        if not parts:
            return completions
            
        base_command = parts[0]
        
        # Get completions for base command
        for command in self.all_commands:
            if command.startswith(base_command):
                completions.append(command)
                
        # Add argument completions for known commands
        if len(parts) == 1 and base_command in self.all_commands:
            completions.extend(self._get_argument_completions(base_command))
            
        return completions[:10]  # Limit completions
        
    def _get_argument_completions(self, command: str) -> List[str]:
        """Get argument completions for specific commands"""
        completions = []
        
        # Common argument patterns
        argument_patterns = {
            'git': ['status', 'add', 'commit', 'push', 'pull', 'checkout', 'branch', 'merge'],
            'docker': ['ps', 'run', 'build', 'pull', 'push', 'exec', 'logs', 'stop'],
            'npm': ['install', 'start', 'run', 'build', 'test', 'update', 'init'],
            'pip': ['install', 'uninstall', 'list', 'show', 'freeze', 'upgrade'],
            'systemctl': ['start', 'stop', 'restart', 'enable', 'disable', 'status'],
            'service': ['start', 'stop', 'restart', 'status'],
            'chmod': ['755', '644', '777', '600', '+x', '-x'],
            'find': ['-name', '-type', '-size', '-mtime', '-exec'],
            'grep': ['-r', '-i', '-n', '-v', '-E', '-F'],
            'tar': ['-xzf', '-czf', '-xvf', '-cvf', '-tzf'],
            'ps': ['aux', '-ef', '-A', '-e', '-f']
        }
        
        if command in argument_patterns:
            for arg in argument_patterns[command]:
                completions.append(f"{command} {arg}")
                
        return completions
        
    def clear_cache(self):
        """Clear the suggestion cache"""
        self.suggestion_cache.clear()
        
    def get_suggestion_stats(self) -> Dict:
        """Get statistics about suggestions"""
        return {
            'cache_size': len(self.suggestion_cache),
            'total_commands': len(self.all_commands),
            'patterns_loaded': len(self.nl_patterns),
            'last_suggestion_time': self.last_suggestion_time
        }
