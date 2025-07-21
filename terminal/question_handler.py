#!/usr/bin/env python3
"""
Question Handler for Terminal Assistant
Handles informational questions about capabilities and features
"""

import json
import re
from typing import Dict, Any, List
from advanced_commands import command_db
import platform
import google.generativeai as genai
import os
import sys
from datetime import datetime, timedelta
import logging
import hashlib
import time
from functools import wraps

class QuestionHandler:
    def __init__(self):
        """Initialize the Question Handler"""
        self.command_db = command_db
        self.os_type = platform.system()
        
        # Initialize response cache
        self.response_cache = {}
        self.cache_max_size = 100
        self.cache_ttl = 3600  # 1 hour TTL
        
        # Session context for enhanced responses
        self.session_context = {
            'start_time': datetime.now(),
            'recent_questions': [],
            'user_interests': set(),
            'command_history': []
        }
        
        # Initialize Gemini API client
        self.gemini_client = None
        self.gemini_api_key = self._get_gemini_api_key()
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                logging.info("Question Handler initialized with Gemini API")
            except Exception as e:
                logging.error(f"Failed to initialize Gemini API: {e}")
                self.gemini_client = None
        
        # Define question patterns and their handlers
        self.question_patterns = {
            'capabilities': {
                'patterns': [
                    r'what.*can.*you.*do',
                    r'what.*operations.*can.*you.*perform',
                    r'what.*are.*your.*capabilities',
                    r'what.*features.*do.*you.*have',
                    r'list.*your.*capabilities',
                    r'show.*me.*what.*you.*can.*do'
                ],
                'handler': self._handle_capabilities_question
            },
            'bios_operations': {
                'patterns': [
                    r'what.*bios.*operations.*can.*you.*do',
                    r'what.*bios.*related.*operations',
                    r'what.*bios.*commands.*do.*you.*support',
                    r'bios.*capabilities',
                    r'what.*can.*you.*do.*with.*bios',
                    r'bios.*operations.*available'
                ],
                'handler': self._handle_bios_question
            },
            'hardware_operations': {
                'patterns': [
                    r'what.*hardware.*operations',
                    r'what.*hardware.*commands',
                    r'hardware.*capabilities',
                    r'what.*can.*you.*do.*with.*hardware'
                ],
                'handler': self._handle_hardware_question
            },
            'network_operations': {
                'patterns': [
                    r'what.*network.*operations',
                    r'what.*network.*commands',
                    r'network.*capabilities',
                    r'what.*can.*you.*do.*with.*network'
                ],
                'handler': self._handle_network_question
            },
            'file_operations': {
                'patterns': [
                    r'what.*file.*operations',
                    r'what.*file.*commands',
                    r'file.*capabilities',
                    r'what.*can.*you.*do.*with.*files'
                ],
                'handler': self._handle_file_question
            },
            'help': {
                'patterns': [
                    r'^help$',
                    r'^help.*me$',
                    r'how.*do.*i.*use.*this',
                    r'what.*commands.*are.*available',
                    r'show.*me.*commands',
                    r'list.*commands'
                ],
                'handler': self._handle_help_question
            },
            'categories': {
                'patterns': [
                    r'what.*categories.*do.*you.*support',
                    r'list.*categories',
                    r'show.*me.*categories',
                    r'what.*types.*of.*operations'
                ],
                'handler': self._handle_categories_question
            },
            'ssh': {
                'patterns': [
                    r'.*ssh.*',
                    r'tell.*me.*about.*ssh',
                    r'what.*is.*ssh',
                    r'explain.*ssh',
                    r'how.*does.*ssh.*work',
                    r'secure.*shell.*'
                ],
                'handler': self._handle_ssh_question
            },
            'terminal_concepts': {
                'patterns': [
                    r'tell.*me.*about.*terminal',
                    r'what.*is.*terminal',
                    r'explain.*terminal',
                    r'command.*line.*interface',
                    r'what.*is.*cli',
                    r'tell.*me.*about.*command.*line'
                ],
                'handler': self._handle_terminal_concepts_question
            },
            'linux_concepts': {
                'patterns': [
                    r'tell.*me.*about.*linux',
                    r'what.*is.*linux',
                    r'explain.*linux',
                    r'unix.*system',
                    r'what.*is.*unix'
                ],
                'handler': self._handle_linux_concepts_question
            },
            'networking_concepts': {
                'patterns': [
                    r'tell.*me.*about.*networking',
                    r'what.*is.*tcp.*ip',
                    r'explain.*networking',
                    r'how.*does.*internet.*work',
                    r'what.*is.*dns',
                    r'explain.*dns'
                ],
                'handler': self._handle_networking_concepts_question
            },
            'security_concepts': {
                'patterns': [
                    r'tell.*me.*about.*security',
                    r'what.*is.*cybersecurity',
                    r'explain.*security',
                    r'what.*is.*encryption',
                    r'tell.*me.*about.*encryption'
                ],
                'handler': self._handle_security_concepts_question
            }
        }
    
    def _get_gemini_api_key(self) -> str:
        """Get Gemini API key from config"""
        try:
            sys.path.append('config')
            from config.settings import GEMINI_API_KEY
            return GEMINI_API_KEY
        except Exception as e:
            logging.error(f"Error loading Gemini API key: {e}")
            return os.getenv("GEMINI_API_KEY", "")
    
    def is_question(self, user_input: str) -> bool:
        """Determine if user input is a question rather than a command"""
        user_lower = user_input.lower().strip()
        
        # Command indicators that should NOT be treated as questions
        command_indicators = [
            'show me the', 'display the', 'get the', 'check the', 'run',
            'execute', 'start', 'stop', 'enable', 'disable', 'turn on', 'turn off',
            'connect', 'disconnect', 'install', 'uninstall', 'delete', 'remove',
            'create', 'make', 'copy', 'move', 'rename', 'list files', 'list directory'
        ]
        
        # If it starts with command indicators, it's likely a command
        for indicator in command_indicators:
            if user_lower.startswith(indicator):
                return False
        
        # Question words/phrases that indicate informational queries about capabilities
        question_indicators = [
            'what can you', 'what do you', 'what are your', 'what features',
            'what operations', 'what commands', 'what categories',
            'how do i use', 'how does this work', 'help me with',
            'explain', 'tell me about', 'describe'
        ]
        
        # Check if input starts with question indicators
        for indicator in question_indicators:
            if user_lower.startswith(indicator):
                return True
        
        # Check for question marks
        if '?' in user_input:
            return True
        
        # Check for specific question patterns
        for question_type, config in self.question_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, user_lower):
                    return True
        
        # Check for help command
        if user_lower == 'help' or user_lower.startswith('help '):
            return True
        
        return False
    
    def handle_question(self, user_input: str) -> Dict[str, Any]:
        """Handle informational questions"""
        user_lower = user_input.lower().strip()
        
        # PRIORITY: Use Gemini API for ALL questions if available
        if self.gemini_client:
            return self._handle_dynamic_question(user_input)
        
        # FALLBACK: Use predefined patterns only if Gemini API is not available
        for question_type, config in self.question_patterns.items():
            for pattern in config['patterns']:
                if re.search(pattern, user_lower):
                    return config['handler']()
        
        # Final fallback to general question handler
        return self._handle_general_question(user_input)

    def _handle_dynamic_question(self, user_input: str) -> Dict[str, Any]:
        """Fetch answer dynamically using the Gemini API with caching"""
        if not self.gemini_client:
            # Fallback to general question handler if Gemini is not available
            return self._handle_general_question(user_input)
        
        # Check cache first
        cached_response = self._get_cached_response(user_input)
        if cached_response:
            return cached_response
        
        try:
            # Create a specialized prompt for terminal-related questions
            prompt = self._create_terminal_question_prompt(user_input)
            
            # Get response from Gemini API
            response = self.gemini_client.generate_content(prompt)
            content = response.text.strip()
            
            # Parse the response
            parsed_response = self._parse_gemini_response(content)
            
            if parsed_response:
                result = {
                    "response_type": "dynamic_information", 
                    "content": parsed_response["content"],
                    "category": "dynamic",
                    "suggestions": parsed_response.get("suggestions", [])
                }
            else:
                # If parsing fails, return raw response
                result = {
                    "response_type": "dynamic_information",
                    "content": content,
                    "category": "dynamic",
                    "suggestions": ["what can you do?", "help"]
                }
            
            # Cache the successful response
            self._cache_response(user_input, result)
            
            # Update session context
            self._update_session_context(user_input, "dynamic")
            
            return result
                
        except Exception as e:
            logging.error(f"Error in dynamic question handling: {e}")
            error_result = {
                "response_type": "dynamic_information",
                "content": f"🤖 **I encountered an error while processing your question.**\n\nError: {str(e)}\n\nPlease try asking a different question or use one of the predefined patterns like 'what can you do?' or 'help'.",
                "category": "error",
                "suggestions": ["what can you do?", "help", "tell me about SSH"]
            }
            
            # Update session context even for errors
            self._update_session_context(user_input, "error")
            
            return error_result
    
    def _create_terminal_question_prompt(self, user_input: str) -> str:
        """Create a specialized prompt for terminal-related questions"""
        categories = self.command_db.get_categories()
        categories_str = ", ".join(categories)
        
        prompt = f"""You are an expert system administrator and terminal assistant specializing in {self.os_type} systems. You provide comprehensive, accurate, and helpful answers to technical questions.

User Question: "{user_input}"

System Context:
- Operating System: {self.os_type}
- Available command categories: {categories_str}
- Terminal Assistant with 144+ operations available
- Focus: Terminal operations, system administration, networking, security, hardware, file operations

Response Guidelines:
1. Provide detailed, accurate technical information
2. Include practical examples and command-line demonstrations when relevant
3. Use professional language with appropriate emojis for readability
4. Focus on terminal, command-line, and system administration topics
5. If the question is general tech (Docker, Git, APIs, etc.), explain it with terminal/command-line context
6. Include relevant {self.os_type} commands and examples where applicable
7. Provide educational content that helps users learn

Response Format (JSON):
{{
    "content": "Your comprehensive answer with emojis, technical details, examples, and formatting. Use markdown-style formatting for better readability.",
    "suggestions": ["related question 1", "related question 2", "related question 3"]
}}

For questions about:
- System administration: Include {self.os_type} commands and best practices
- Development tools: Show terminal usage and command examples
- Networking: Include relevant network commands and diagnostics
- Security: Focus on command-line security tools and practices
- General tech topics: Explain with terminal/system administration context

Provide expert-level, comprehensive responses that educate and inform users about terminal and system administration topics."""
        
        return prompt
    
    def _get_cache_key(self, question: str) -> str:
        """Generate a cache key for the question"""
        return hashlib.md5(question.lower().strip().encode()).hexdigest()
    
    def _get_cached_response(self, question: str) -> Dict[str, Any]:
        """Get cached response if available and not expired"""
        cache_key = self._get_cache_key(question)
        
        if cache_key in self.response_cache:
            cached_item = self.response_cache[cache_key]
            
            # Check if cache item is still valid (not expired)
            if datetime.now() - cached_item['timestamp'] < timedelta(seconds=self.cache_ttl):
                logging.info(f"Cache hit for question: {question[:50]}...")
                return cached_item['response']
            else:
                # Remove expired cache item
                del self.response_cache[cache_key]
                logging.info(f"Cache expired for question: {question[:50]}...")
        
        return None
    
    def _cache_response(self, question: str, response: Dict[str, Any]) -> None:
        """Cache a response for future use"""
        cache_key = self._get_cache_key(question)
        
        # Implement LRU cache by removing oldest items if cache is full
        if len(self.response_cache) >= self.cache_max_size:
            # Remove oldest item
            oldest_key = min(self.response_cache.keys(), 
                           key=lambda k: self.response_cache[k]['timestamp'])
            del self.response_cache[oldest_key]
            logging.info(f"Cache evicted oldest item: {oldest_key}")
        
        self.response_cache[cache_key] = {
            'timestamp': datetime.now(),
            'response': response,
            'question': question[:100]  # Store truncated question for logging
        }
        
        logging.info(f"Cached response for question: {question[:50]}...")
    
    def _update_session_context(self, question: str, category: str = None) -> None:
        """Update session context with user activity"""
        # Add to recent questions (keep last 10)
        self.session_context['recent_questions'].append({
            'question': question,
            'timestamp': datetime.now(),
            'category': category
        })
        
        # Keep only last 10 questions
        if len(self.session_context['recent_questions']) > 10:
            self.session_context['recent_questions'] = self.session_context['recent_questions'][-10:]
        
        # Extract and track user interests
        interests = self._extract_interests(question)
        self.session_context['user_interests'].update(interests)
        
        # Keep interest set reasonable size
        if len(self.session_context['user_interests']) > 20:
            # Convert to list, keep last 20, convert back to set
            interests_list = list(self.session_context['user_interests'])
            self.session_context['user_interests'] = set(interests_list[-20:])
    
    def _extract_interests(self, question: str) -> set:
        """Extract user interests from question text"""
        interests = set()
        
        # Define keyword mappings
        interest_keywords = {
            'networking': ['network', 'internet', 'wifi', 'connection', 'ip', 'dns', 'tcp', 'ssh'],
            'security': ['security', 'firewall', 'antivirus', 'encryption', 'password', 'auth'],
            'linux': ['linux', 'unix', 'bash', 'shell', 'ubuntu', 'debian'],
            'windows': ['windows', 'powershell', 'cmd', 'registry', 'wmi'],
            'hardware': ['hardware', 'cpu', 'memory', 'disk', 'gpu', 'temperature'],
            'performance': ['performance', 'speed', 'monitor', 'usage', 'benchmark'],
            'files': ['file', 'folder', 'directory', 'copy', 'move', 'delete'],
            'development': ['git', 'code', 'programming', 'development', 'api', 'database']
        }
        
        question_lower = question.lower()
        
        for interest, keywords in interest_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                interests.add(interest)
        
        return interests
    
    def _get_session_context_summary(self) -> str:
        """Get a summary of current session context"""
        context_parts = []
        
        # Session duration
        duration = datetime.now() - self.session_context['start_time']
        context_parts.append(f"Session duration: {duration.total_seconds()/60:.1f} minutes")
        
        # Recent questions count
        recent_count = len(self.session_context['recent_questions'])
        if recent_count > 0:
            context_parts.append(f"Recent questions: {recent_count}")
            
            # Most recent question categories
            recent_categories = [q.get('category') for q in self.session_context['recent_questions'][-3:] if q.get('category')]
            if recent_categories:
                context_parts.append(f"Recent topics: {', '.join(set(recent_categories))}")
        
        # User interests
        if self.session_context['user_interests']:
            interests = sorted(list(self.session_context['user_interests']))
            context_parts.append(f"User interests: {', '.join(interests[:5])}")
        
        return ' | '.join(context_parts)
    
    def _parse_gemini_response(self, content: str) -> Dict[str, Any]:
        """Parse Gemini API response and extract structured information"""
        try:
            # Handle markdown formatting
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                content = content[json_start:json_end].strip()
            
            # Try to parse as JSON
            parsed = json.loads(content)
            
            # Validate structure
            if isinstance(parsed, dict) and "content" in parsed:
                return parsed
            else:
                return None
                
        except json.JSONDecodeError:
            # If it's not valid JSON, treat as plain text
            return {
                "content": content,
                "suggestions": ["what can you do?", "help", "tell me about SSH"]
            }
        except Exception as e:
            logging.error(f"Error parsing Gemini response: {e}")
            return None
    
    def _handle_capabilities_question(self) -> Dict[str, Any]:
        """Handle general capabilities questions"""
        categories = self.command_db.get_categories()
        total_operations = sum(len(self.command_db.get_operations(cat)) for cat in categories)
        
        capabilities = {
            "🖥️ System Information": "Check system specs, OS version, hardware details",
            "📁 File Operations": "Create, delete, copy, move files and folders",
            "🔧 Process Management": "List, kill, monitor running processes",
            "🌐 Network Operations": "Check connectivity, manage network settings",
            "💾 Hardware Control": "Monitor CPU, memory, disk usage",
            "👤 User Management": "Manage user accounts and permissions",
            "🔐 Security Operations": "Firewall, antivirus, system security",
            "⚙️ System Configuration": "Registry, services, startup programs",
            "📊 Performance Monitoring": "System performance, resource usage",
            "🔍 Search & Find": "Locate files, search system content"
        }
        
        response = f"""
🤖 **Terminal Assistant Capabilities**

I can help you with {total_operations} different operations across {len(categories)} categories:

**Main Categories:**
"""
        
        for emoji_title, description in capabilities.items():
            response += f"• {emoji_title}: {description}\n"
        
        response += f"""
**Available Categories in Database:**
{', '.join(categories)}

**How to Use:**
• Type natural language commands like "check cpu usage" or "create a file"
• Ask specific questions like "what network operations can you do?"
• I'll convert your requests into the appropriate {self.os_type} commands
• Risky operations will require confirmation for safety

**Examples:**
• "show me system information" → systeminfo
• "check disk space" → Get disk usage
• "list running processes" → Show active processes
• "create a backup folder" → mkdir backup

Type "help [category]" for specific category information!
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "capabilities",
            "suggestions": ["help file_operations", "what network operations can you do?", "show me hardware commands"]
        }
    
    def _handle_bios_question(self) -> Dict[str, Any]:
        """Handle BIOS-related questions"""
        bios_operations = {
            "🔍 BIOS Information": [
                "Check BIOS version and manufacturer",
                "Display firmware information",
                "Show UEFI vs Legacy BIOS status",
                "Get motherboard details"
            ],
            "⚙️ Boot Configuration": [
                "Manage boot order (via bcdedit)",
                "Check secure boot status",
                "Display boot entries",
                "Analyze boot configuration"
            ],
            "🛡️ Security Features": [
                "Check TPM (Trusted Platform Module) status",
                "Verify secure boot configuration",
                "Display hardware security features",
                "Check BitLocker readiness"
            ],
            "🖥️ Hardware Information": [
                "Display system firmware details",
                "Check memory configuration",
                "Show processor information",
                "Get hardware compatibility info"
            ],
            "🔧 System Configuration": [
                "Power management settings",
                "Hardware clock configuration",
                "System wake-up settings",
                "Performance mode information"
            ]
        }
        
        response = """
🔧 **BIOS-Related Operations I Can Help With**

"""
        
        for category, operations in bios_operations.items():
            response += f"**{category}:**\n"
            for operation in operations:
                response += f"  • {operation}\n"
            response += "\n"
        
        response += """
**Available Commands:**
• `systeminfo` - Complete system and firmware information
• `msinfo32` - Launch System Information utility
• `bcdedit` - Boot configuration management
• `powercfg` - Power management settings
• `wmic bios` - BIOS-specific information
• `dxdiag` - DirectX diagnostics with hardware info

**Example Requests:**
• "check bios version" → Get BIOS information
• "show boot configuration" → Display boot settings
• "check tpm status" → TPM information
• "display firmware details" → System firmware info

**Safety Note:** I provide information and safe configuration commands. For actual BIOS settings changes, you'll need to access your system's BIOS/UEFI setup directly during boot.
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "bios_operations",
            "suggestions": ["check bios version", "show boot configuration", "check tpm status"]
        }
    
    def _handle_hardware_question(self) -> Dict[str, Any]:
        """Handle hardware-related questions"""
        hardware_ops = self.command_db.get_operations("hardware")
        performance_ops = self.command_db.get_operations("performance")
        
        response = f"""
🖥️ **Hardware Operations Available**

I can help you with {len(hardware_ops)} hardware operations and {len(performance_ops)} performance monitoring tasks:

**Hardware Information:**
• CPU details and specifications
• Memory (RAM) information and usage
• Disk drives and storage information
• Graphics card details
• Network adapters information
• USB devices and peripherals
• Motherboard and chipset details

**Performance Monitoring:**
• CPU usage monitoring
• Memory usage statistics
• Disk I/O performance
• Network bandwidth usage
• Temperature monitoring (where available)
• Process resource consumption

**Hardware Control:**
• Device management
• Driver information
• Hardware troubleshooting
• System resource allocation
• Power management settings

**Example Commands:**
• "check cpu usage" → Real-time CPU monitoring
• "show memory information" → RAM details and usage
• "list disk drives" → Storage device information
• "display graphics card info" → GPU details
• "check network adapters" → Network hardware info

**Available Tools:**
• Task Manager data via command line
• WMI (Windows Management Instrumentation)
• PowerShell hardware cmdlets
• System diagnostic utilities
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "hardware_operations",
            "suggestions": ["check cpu usage", "show memory information", "list disk drives"]
        }
    
    def _handle_network_question(self) -> Dict[str, Any]:
        """Handle network-related questions"""
        network_ops = self.command_db.get_operations("network")
        
        response = f"""
🌐 **Network Operations Available**

I can help you with {len(network_ops)} network-related operations:

**Network Information:**
• IP address configuration
• Network adapter details
• WiFi connection status
• Network connectivity testing
• DNS configuration
• Routing table information

**Network Diagnostics:**
• Ping connectivity tests
• Trace route analysis
• Network speed testing
• Port scanning and checking
• Network troubleshooting
• Connection monitoring

**Network Management:**
• Network adapter enable/disable
• IP configuration changes
• DNS server configuration
• Network profile management
• Firewall status and rules

**Example Commands:**
• "check ip address" → Show network configuration
• "ping google.com" → Test internet connectivity
• "show network adapters" → List network interfaces
• "check wifi status" → WiFi connection information
• "test network speed" → Network performance test

**Available Tools:**
• ipconfig - IP configuration
• ping - Connectivity testing
• tracert - Route tracing
• netstat - Network connections
• nslookup - DNS queries
• netsh - Network configuration
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "network_operations",
            "suggestions": ["check ip address", "ping google.com", "show network adapters"]
        }
    
    def _handle_file_question(self) -> Dict[str, Any]:
        """Handle file operation questions"""
        file_ops = self.command_db.get_operations("file_operations")
        
        response = f"""
📁 **File Operations Available**

I can help you with {len(file_ops)} file and folder operations:

**File Management:**
• Create, delete, copy, move files
• Create and remove directories
• File and folder listing
• File property information
• File search and find operations
• File compression and extraction

**File Operations:**
• Text file creation and editing
• File content viewing
• File permission management
• File attribute modification
• Batch file operations
• File comparison

**Directory Operations:**
• Navigate directory structure
• Directory size calculation
• Folder organization
• Directory synchronization
• Folder monitoring
• Path management

**Example Commands:**
• "create a file called report.txt" → Create new file
• "make a folder named backup" → Create directory
• "list files in current directory" → Show directory contents
• "copy file to backup folder" → File copying
• "delete old files" → File deletion (with confirmation)
• "search for .txt files" → File search operations

**Safety Features:**
• Confirmation required for deletions
• Backup suggestions for risky operations
• Wildcard operation warnings
• Path validation
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "file_operations",
            "suggestions": ["create a file", "make a folder", "list files"]
        }
    
    def _handle_help_question(self) -> Dict[str, Any]:
        """Handle general help questions"""
        categories = self.command_db.get_categories()
        
        response = f"""
📚 **Terminal Assistant Help**

**How to Use:**
1. Type natural language commands like "check cpu usage"
2. Ask questions about capabilities like "what can you do?"
3. Request help for specific categories like "help network"

**Available Categories:**
{', '.join(categories)}

**Question Examples:**
• "what can you do?" - Full capabilities overview
• "what network operations can you do?" - Network-specific help
• "what bios operations can you do?" - BIOS-related help
• "help file_operations" - File operation details

**Command Examples:**
• "check system information" → systeminfo
• "show running processes" → tasklist
• "create a backup folder" → mkdir backup
• "ping google.com" → ping google.com

**Safety Features:**
• Risky commands require confirmation
• Explanations provided for all operations
• Alternative suggestions for safer approaches
• Command history logging

**Getting Started:**
• Try asking "what can you do?" to see all capabilities
• Use natural language - I'll convert to proper commands
• Ask specific questions about any category
• Type help [category] for detailed information

Type any natural language command or question to get started!
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "help",
            "suggestions": ["what can you do?", "show system information", "help network"]
        }
    
    def _handle_categories_question(self) -> Dict[str, Any]:
        """Handle questions about available categories"""
        categories = self.command_db.get_categories()
        category_descriptions = {
            "file_operations": "📁 Create, delete, copy, move files and folders",
            "network": "🌐 Network connectivity, IP configuration, diagnostics",
            "performance": "📊 System performance, resource monitoring",
            "hardware": "🖥️ Hardware information, device management",
            "security": "🔐 Security settings, firewall, antivirus",
            "user_management": "👤 User accounts, permissions, groups",
            "system": "⚙️ System configuration, services, registry",
            "process": "🔧 Process management, task monitoring",
            "search": "🔍 File search, system content search"
        }
        
        response = f"""
📂 **Available Command Categories**

I support {len(categories)} main categories of operations:

"""
        
        for category in categories:
            description = category_descriptions.get(category, f"Operations related to {category}")
            ops_count = len(self.command_db.get_operations(category))
            response += f"**{category}** ({ops_count} operations)\n"
            response += f"  {description}\n\n"
        
        response += """
**Get Category Details:**
• Type "help [category]" for specific operations
• Example: "help file_operations" or "help network"

**Category-Specific Questions:**
• "what network operations can you do?"
• "what file operations are available?"
• "what hardware commands do you support?"

**Examples by Category:**
• file_operations: "create a file", "delete folder"
• network: "check ip", "ping website"
• performance: "check cpu usage", "memory status"
• hardware: "system info", "disk space"
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "categories",
            "suggestions": [f"help {cat}" for cat in categories[:3]]
        }
    
    def _handle_ssh_question(self) -> Dict[str, Any]:
        """Handle SSH-related questions"""
        response = """
🔐 **SSH (Secure Shell) - Remote Access Protocol**

**What is SSH?**
SSH is a cryptographic network protocol that allows secure communication between computers over an unsecured network. It's primarily used for remote login and command execution.

**Key Features:**
• 🔒 **Encryption**: All data is encrypted during transmission
• 🔑 **Authentication**: Multiple authentication methods (password, key-based)
• 🛡️ **Integrity**: Data integrity verification
• 🔄 **Port Forwarding**: Secure tunneling capabilities
• 📁 **File Transfer**: Secure file transfer (SCP, SFTP)

**Common SSH Uses:**
• Remote server administration
• Secure file transfers
• Creating secure tunnels
• Remote command execution
• Git repository access
• Database connections through tunnels

**Basic SSH Commands:**
• `ssh user@hostname` - Connect to remote server
• `ssh-keygen` - Generate SSH key pairs
• `scp file user@host:/path` - Secure file copy
• `ssh -L port:host:port user@server` - Port forwarding

**SSH vs Other Protocols:**
• **Telnet**: SSH is encrypted, Telnet is not
• **FTP**: SSH includes SFTP for secure file transfer
• **RDP**: SSH is command-line, RDP is graphical

**Security Benefits:**
• Prevents eavesdropping
• Protects against connection hijacking
• Verifies server identity
• Supports two-factor authentication

**Default Port:** 22 (TCP)
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "ssh",
            "suggestions": ["tell me about terminal", "what is linux", "explain networking"]
        }
    
    def _handle_terminal_concepts_question(self) -> Dict[str, Any]:
        """Handle terminal/CLI concept questions"""
        response = """
💻 **Terminal & Command Line Interface (CLI)**

**What is a Terminal?**
A terminal is a text-based interface that allows users to interact with the operating system using typed commands instead of graphical elements.

**Key Concepts:**
• 🖥️ **Shell**: The command interpreter (bash, zsh, PowerShell, cmd)
• 📂 **Working Directory**: Your current location in the file system
• 🔤 **Commands**: Programs you can run by typing their names
• 📝 **Arguments**: Additional information passed to commands
• 🔄 **Pipes**: Chain commands together (`|`)
• 📋 **Redirection**: Send output to files (`>`, `>>`)

**Advantages of Terminal:**
• **Speed**: Faster than GUI for many tasks
• **Automation**: Easy to script and automate
• **Precision**: Exact control over operations
• **Remote Access**: Works over SSH connections
• **Resource Efficient**: Uses less memory than GUI

**Common Terminal Operations:**
• File navigation (`cd`, `ls`, `pwd`)
• File manipulation (`cp`, `mv`, `rm`, `mkdir`)
• Text processing (`cat`, `grep`, `sed`, `awk`)
• Process management (`ps`, `kill`, `top`)
• System information (`uname`, `whoami`, `date`)

**Terminal vs GUI:**
• **Terminal**: Text-based, keyboard-driven, scriptable
• **GUI**: Graphical, mouse-driven, visual
• **Both**: Have their place in modern computing

**Learning Tips:**
• Start with basic navigation commands
• Use `man command` to get help
• Practice with simple file operations
• Learn keyboard shortcuts
• Don't be afraid to experiment (safely)

**Popular Terminals:**
• **Windows**: Command Prompt, PowerShell, Windows Terminal
• **Mac**: Terminal.app, iTerm2
• **Linux**: Bash, Zsh, Fish
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "terminal_concepts",
            "suggestions": ["tell me about linux", "what is ssh", "explain networking"]
        }
    
    def _handle_linux_concepts_question(self) -> Dict[str, Any]:
        """Handle Linux/Unix concept questions"""
        response = """
🐧 **Linux & Unix Operating Systems**

**What is Linux?**
Linux is a free, open-source operating system kernel that forms the base of many operating systems (distributions). It's based on Unix principles and designed for multi-user, multi-tasking environments.

**Key Characteristics:**
• 🆓 **Open Source**: Free to use, modify, and distribute
• 🔒 **Security**: Built-in security features and permissions
• 💪 **Stability**: Designed for long-term uptime
• 🔧 **Customizable**: Highly configurable and flexible
• 🌐 **Networking**: Excellent network capabilities

**Popular Linux Distributions:**
• **Ubuntu**: User-friendly, great for beginners
• **Debian**: Stable, reliable, extensive package repository
• **CentOS/RHEL**: Enterprise-focused, commercial support
• **Fedora**: Cutting-edge features, upstream to RHEL
• **Arch**: Minimalist, highly customizable

**File System Structure:**
• `/` - Root directory (top level)
• `/home` - User home directories
• `/etc` - System configuration files
• `/bin` - Essential system binaries
• `/usr` - User programs and data
• `/var` - Variable data (logs, caches)

**Linux vs Unix:**
• **Unix**: Original system, proprietary
• **Linux**: Unix-like, open source
• **Similarities**: Commands, file structure, philosophy
• **Differences**: Licensing, kernel implementation

**Common Linux Commands:**
• `ls` - List directory contents
• `cd` - Change directory
• `sudo` - Execute as administrator
• `apt/yum` - Package management
• `chmod` - Change file permissions
• `ps` - Show running processes

**Why Use Linux?**
• **Servers**: Powers most web servers
• **Development**: Excellent development environment
• **Security**: More secure than many alternatives
• **Performance**: Efficient resource usage
• **Cost**: Free to use and deploy

**Linux Philosophy:**
• "Everything is a file"
• "Do one thing and do it well"
• "Small, sharp tools"
• "Choose portability over efficiency"
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "linux_concepts",
            "suggestions": ["tell me about ssh", "explain networking", "what is terminal"]
        }
    
    def _handle_networking_concepts_question(self) -> Dict[str, Any]:
        """Handle networking concept questions"""
        response = """
🌐 **Computer Networking Fundamentals**

**What is Networking?**
Computer networking is the practice of connecting computers and devices to share resources, data, and communicate with each other across local or global networks.

**Key Networking Concepts:**
• 🔗 **Protocol**: Rules for communication (TCP/IP, HTTP, DNS)
• 📍 **IP Address**: Unique identifier for devices (192.168.1.1)
• 🌐 **DNS**: Domain Name System (converts names to IP addresses)
• 🔌 **Port**: Communication endpoint (HTTP:80, HTTPS:443)
• 🛣️ **Router**: Directs traffic between networks
• 🔀 **Switch**: Connects devices within a network

**Network Types:**
• **LAN**: Local Area Network (home, office)
• **WAN**: Wide Area Network (internet)
• **WiFi**: Wireless local networking
• **VPN**: Virtual Private Network (secure remote access)

**TCP/IP Model (Internet Protocol Suite):**
• **Application Layer**: HTTP, FTP, SMTP, DNS
• **Transport Layer**: TCP (reliable), UDP (fast)
• **Internet Layer**: IP (routing, addressing)
• **Link Layer**: Ethernet, WiFi (physical connection)

**Common Network Commands:**
• `ping` - Test connectivity
• `traceroute` - Show network path
• `netstat` - Show network connections
• `nslookup` - DNS lookups
• `curl` - HTTP requests
• `wget` - Download files

**Network Security:**
• **Firewalls**: Control network traffic
• **Encryption**: Protect data in transit (SSL/TLS)
• **Authentication**: Verify user identity
• **VPN**: Secure remote connections

**How the Internet Works:**
1. **DNS Resolution**: Convert domain to IP address
2. **Routing**: Find path to destination
3. **TCP Connection**: Establish reliable connection
4. **Data Transfer**: Send/receive data packets
5. **Connection Close**: Terminate connection

**Network Troubleshooting:**
• Check physical connections
• Verify IP configuration
• Test connectivity (ping)
• Check DNS resolution
• Examine firewall rules
• Monitor network traffic

**Common Network Issues:**
• **Connectivity**: Can't reach destination
• **DNS Problems**: Can't resolve domain names
• **Slow Performance**: Bandwidth or latency issues
• **Security**: Blocked by firewall or security rules
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "networking_concepts",
            "suggestions": ["tell me about ssh", "what is linux", "explain security"]
        }
    
    def _handle_security_concepts_question(self) -> Dict[str, Any]:
        """Handle security concept questions"""
        response = """
🔐 **Cybersecurity & Computer Security**

**What is Cybersecurity?**
Cybersecurity is the practice of protecting systems, networks, and data from digital attacks, unauthorized access, and damage.

**Core Security Principles (CIA Triad):**
• 🔒 **Confidentiality**: Data privacy and access control
• 🔧 **Integrity**: Data accuracy and completeness
• 🟢 **Availability**: System accessibility when needed

**Common Security Threats:**
• **Malware**: Viruses, ransomware, trojans
• **Phishing**: Deceptive emails/websites
• **Social Engineering**: Manipulating people
• **DDoS**: Distributed Denial of Service attacks
• **SQL Injection**: Database attacks
• **Zero-day**: Unknown vulnerabilities

**Security Measures:**
• 🔑 **Authentication**: Verify user identity
• 🛡️ **Authorization**: Control access permissions
• 🔐 **Encryption**: Protect data confidentiality
• 🔥 **Firewalls**: Network traffic filtering
• 🦠 **Antivirus**: Malware detection/removal
• 🔄 **Backups**: Data recovery protection

**Encryption Basics:**
• **Symmetric**: Same key for encrypt/decrypt (AES)
• **Asymmetric**: Public/private key pairs (RSA)
• **Hashing**: One-way data fingerprints (SHA-256)
• **SSL/TLS**: Secure web communication

**Password Security:**
• Use strong, unique passwords
• Enable two-factor authentication (2FA)
• Password managers for storage
• Regular password updates
• Avoid common passwords

**Network Security:**
• **VPN**: Secure remote access
• **Firewall**: Network traffic control
• **IDS/IPS**: Intrusion detection/prevention
• **Network Segmentation**: Isolate critical systems
• **WiFi Security**: WPA3 encryption

**Security Best Practices:**
• Keep systems updated
• Use least privilege principle
• Regular security audits
• Employee security training
• Incident response planning
• Data classification and handling

**Common Security Tools:**
• **Nmap**: Network scanning
• **Wireshark**: Network analysis
• **Metasploit**: Penetration testing
• **John the Ripper**: Password cracking
• **Burp Suite**: Web application security

**Security Certifications:**
• **CompTIA Security+**: Entry-level
• **CISSP**: Management-level
• **CEH**: Ethical hacking
• **CISM**: Information security management
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "security_concepts",
            "suggestions": ["tell me about ssh", "explain networking", "what is linux"]
        }
    
    def _handle_general_question(self, user_input: str) -> Dict[str, Any]:
        """Handle general questions that don't match specific patterns"""
        response = f"""
🤔 **I'm not sure about that specific question**

You asked: "{user_input}"

**I can help with:**
• System operations and commands
• File and folder management
• Network diagnostics
• Hardware information
• Performance monitoring
• Security operations
• Terminal and Linux concepts
• SSH and networking topics

**Try asking:**
• "what can you do?" - See all capabilities
• "help" - General help information
• "what [category] operations can you do?" - Category-specific help
• "tell me about SSH" - Learn about SSH
• "explain terminal" - Terminal concepts
• "what is Linux?" - Linux fundamentals
• Or just tell me what you want to accomplish!

**Examples:**
• "check system information"
• "create a backup folder"
• "show network status"
• "what network operations can you do?"
• "tell me about SSH"
• "explain networking"
"""
        
        return {
            "response_type": "information",
            "content": response,
            "category": "general",
            "suggestions": ["what can you do?", "help", "tell me about SSH"]
        }

# Global instance
question_handler = QuestionHandler()
