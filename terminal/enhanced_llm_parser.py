#!/usr/bin/env python3
"""
Enhanced LLM Parser with Advanced Command Understanding
Integrates with the comprehensive command database
"""

import google.generativeai as genai
import json
import os
import sys
import re
from typing import Optional, Dict, Any
import platform
from advanced_commands import command_db

class EnhancedLLMParser:
    def __init__(self, provider: str = "gemini", api_key: str = None, model: str = "gemini-1.5-flash"):
        """
        Initialize the Enhanced LLM Command Parser
        
        Args:
            provider: LLM provider (openai or gemini)
            api_key: API key for the chosen provider
            model: Model to use
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.os_type = platform.system()
        self.command_db = command_db
        
        # If no API key provided, try to load from config
        if not self.api_key:
            try:
                sys.path.append('config')
                from config.settings import GEMINI_API_KEY
                self.api_key = GEMINI_API_KEY
            except:
                self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key and self.api_key != "your-google-gemini-key":
            if provider == "gemini":
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model)
            else:
                self.client = None
        else:
            self.client = None
        
        # Enhanced system prompt with command database awareness
        self.system_prompt = self._create_enhanced_system_prompt()
        
    def _create_enhanced_system_prompt(self) -> str:
        """Create enhanced system prompt with command database info"""
        categories = self.command_db.get_categories()
        categories_str = ", ".join(categories)
        
        return f"""You are an advanced OS assistant that converts natural language requests into terminal commands for {self.os_type}.

Your capabilities include {len(categories)} command categories: {categories_str}

ADVANCED FEATURES:
- Parameter extraction from natural language
- File path and name recognition
- Process and service name identification
- Network target and port extraction
- User and permission handling
- Complex multi-step operations

PARAMETER EXTRACTION RULES:
- Extract filenames, paths, process names, service names, usernames, etc.
- Handle quoted strings and special characters
- Recognize wildcards and patterns
- Support relative and absolute paths
- Parse network targets (IPs, hostnames, URLs)

RISK ASSESSMENT:
- File deletion operations (especially with wildcards)
- System modification commands
- Network security changes
- User account modifications
- Service management operations
- Registry modifications

Response format (JSON):
{{
    "command": "the actual terminal command with parameters",
    "explanation": "detailed explanation of what this command does",
    "risky": true/false,
    "category": "specific category from: {categories_str}",
    "operation": "specific operation name",
    "parameters": {{"param1": "value1", "param2": "value2"}},
    "warnings": ["warning1", "warning2"] (if risky),
    "alternatives": ["safer alternative commands"] (if applicable)
}}

EXAMPLES:
User: "delete all .txt files in the Documents folder"
Response: {{
    "command": "del C:\\\\Users\\\\%USERNAME%\\\\Documents\\\\*.txt",
    "explanation": "Deletes all files with .txt extension in the Documents folder",
    "risky": true,
    "category": "file_operations",
    "operation": "delete multiple files",
    "parameters": {{"pattern": "*.txt", "path": "Documents"}},
    "warnings": ["This will permanently delete all .txt files", "Cannot be undone"],
    "alternatives": ["Move files to recycle bin first", "Create backup before deletion"]
}}

User: "show me the CPU usage"
Response: {{
    "command": "wmic process get name,processid,percentprocessortime",
    "explanation": "Displays CPU usage information for all running processes",
    "risky": false,
    "category": "performance",
    "operation": "cpu usage",
    "parameters": {{}},
    "warnings": [],
    "alternatives": []
}}

If you cannot understand the request, respond with:
{{
    "command": null,
    "explanation": "I don't understand that request or it may be inappropriate",
    "risky": false,
    "category": "unknown",
    "operation": "unknown",
    "parameters": {{}},
    "warnings": [],
    "alternatives": []
}}
"""

    def parse_command(self, user_input: str) -> Dict[str, Any]:
        """
        Parse user input using enhanced LLM understanding
        
        Args:
            user_input: Natural language input from user
            
        Returns:
            Dictionary with enhanced command information
        """
        # First check for app/browser commands - these are high priority
        app_command = self._parse_app_commands(user_input)
        if app_command:
            return app_command
        
        if not self.client:
            return self._fallback_parse(user_input)
        
        try:
            # First, try to find direct matches in command database
            search_results = self.command_db.search_commands(user_input)
            
            # Use LLM for complex parsing
            prompt = f"{self.system_prompt}\\n\\nUser: {user_input}"
            response = self.client.generate_content(prompt)
            content = response.text.strip()
            
            # Extract JSON from response
            result = self._extract_json_response(content)
            
            if result and result.get('command'):
                # Enhance with command database info if available
                result = self._enhance_with_database(result, search_results)
                return result
            else:
                return self._fallback_parse(user_input)
                
        except Exception as e:
            print(f"Enhanced LLM API error: {e}")
            return self._fallback_parse(user_input)
    
    def _extract_json_response(self, content: str) -> Dict[str, Any]:
        """Extract and validate JSON response from LLM"""
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
            
            result = json.loads(content)
            
            # Validate response structure
            if not isinstance(result, dict):
                return None
            
            # Ensure required fields exist
            required_fields = ["command", "explanation", "risky", "category", "operation"]
            for field in required_fields:
                if field not in result:
                    if field == "command":
                        result[field] = None
                    else:
                        result[field] = "unknown"
            
            # Ensure optional fields exist
            optional_fields = ["parameters", "warnings", "alternatives"]
            for field in optional_fields:
                if field not in result:
                    result[field] = {} if field == "parameters" else []
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON response: {content}")
            print(f"JSON Error: {e}")
            return None
    
    def _enhance_with_database(self, result: Dict[str, Any], search_results: list) -> Dict[str, Any]:
        """Enhance LLM result with command database information"""
        # Add command database suggestions if available
        if search_results:
            result['database_matches'] = search_results[:3]  # Top 3 matches
        
        # Validate category exists in database
        if result['category'] not in self.command_db.get_categories():
            result['category'] = 'custom'
        
        return result
    
    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """
        Enhanced fallback parsing with command database integration
        """
        # Check for browser/app commands first
        app_command = self._parse_app_commands(user_input)
        if app_command:
            return app_command
        
        # Try command database search
        search_results = self.command_db.search_commands(user_input)
        
        if search_results:
            # Use best match from database
            best_match = search_results[0]
            command_template = best_match['command']
            
            # Try to extract parameters from user input
            parameters = self._extract_parameters(user_input, command_template)
            
            # Fill template with parameters
            try:
                command = command_template.format(**parameters)
            except KeyError:
                command = command_template
            
            return {
                "command": command,
                "explanation": f"Executing: {best_match['operation']}",
                "risky": self._assess_risk(command),
                "category": best_match['category'],
                "operation": best_match['operation'],
                "parameters": parameters,
                "warnings": self._get_warnings(command) if self._assess_risk(command) else [],
                "alternatives": []
            }
        
        # Fall back to original intent mapper
        from intent_mapper import get_command
        command = get_command(user_input, self.os_type)
        
        if command:
            return {
                "command": command,
                "explanation": f"Executing: {command}",
                "risky": self._is_risky_fallback(command),
                "category": "basic",
                "operation": "basic_command",
                "parameters": {},
                "warnings": self._get_warnings(command) if self._is_risky_fallback(command) else [],
                "alternatives": []
            }
        else:
            return {
                "command": None,
                "explanation": "I don't understand that command",
                "risky": False,
                "category": "unknown",
                "operation": "unknown",
                "parameters": {},
                "warnings": [],
                "alternatives": []
            }
    
    def _extract_parameters(self, user_input: str, command_template: str) -> Dict[str, str]:
        """Extract parameters from user input for command template"""
        parameters = {}
        
        # Common parameter patterns
        patterns = {
            'filename': r'(?:file\s+(?:named\s+)?["\']?([^"\'\\s]+)["\']?)',
            'dirname': r'(?:(?:folder|directory)\s+(?:named\s+)?["\']?([^"\'\\s]+)["\']?)',
            'process_name': r'(?:process\s+["\']?([^"\'\\s]+)["\']?)',
            'service_name': r'(?:service\s+["\']?([^"\'\\s]+)["\']?)',
            'hostname': r'(?:(?:host|server)\s+["\']?([^"\'\\s]+)["\']?)',
            'target': r'(?:(?:ping|connect\s+to)\s+["\']?([^"\'\\s]+)["\']?)',
            'app_name': r'(?:(?:open|launch|start|run)\s+(?:the\s+)?(?:app\s+)?["\']?([^"\'\\s]+)["\']?)',
            'browser_name': r'(?:(?:browser|chrome|firefox|edge)\s+["\']?([^"\'\\s]*)["\']?)',
            'url': r'(?:(?:open|go\s+to|visit)\s+["\']?(https?://[^\s"\']+|[^\s"\']*\.[^\s"\']+)["\']?)',
            'search_query': r'(?:(?:search|google)\s+(?:for\s+)?["\']([^"\']*)["\'\s])',
        }
        
        user_lower = user_input.lower()
        
        for param, pattern in patterns.items():
            match = re.search(pattern, user_lower)
            if match:
                parameters[param] = match.group(1)
        
        # Set default values for common parameters
        if 'filename' not in parameters and '{filename}' in command_template:
            parameters['filename'] = 'file.txt'
        if 'dirname' not in parameters and '{dirname}' in command_template:
            parameters['dirname'] = 'new_folder'
        
        return parameters
    
    def _assess_risk(self, command: str) -> bool:
        """Enhanced risk assessment"""
        if not command:
            return False
            
        risky_patterns = [
            r'del\s+.*\*',  # Delete with wildcards
            r'rm\s+-rf',    # Recursive force delete
            r'format\s+',   # Format drive
            r'diskpart',    # Disk partitioning
            r'reg\s+delete', # Registry deletion
            r'net\s+user.*delete', # User deletion
            r'shutdown\s+', # System shutdown
            r'taskkill.*\/f', # Force kill processes
        ]
        
        command_lower = command.lower()
        for pattern in risky_patterns:
            if re.search(pattern, command_lower):
                return True
        
        return False
    
    def _is_risky_fallback(self, command: str) -> bool:
        """Fallback risk assessment"""
        from permissions import is_risky
        return is_risky(command) or self._assess_risk(command)
    
    def _get_warnings(self, command: str) -> list:
        """Generate specific warnings for risky commands"""
        warnings = []
        command_lower = command.lower()
        
        if 'del' in command_lower and '*' in command:
            warnings.append("This will delete multiple files permanently")
        if 'format' in command_lower:
            warnings.append("This will erase all data on the drive")
        if 'reg delete' in command_lower:
            warnings.append("Modifying registry can cause system instability")
        if 'net user' in command_lower and 'delete' in command_lower:
            warnings.append("This will permanently remove the user account")
        if 'shutdown' in command_lower:
            warnings.append("This will shut down the computer")
        
        return warnings
    
    def _parse_app_commands(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Parse natural language commands for opening apps and browsers"""
        user_lower = user_input.lower()
        
        # Browser-specific commands
        if any(word in user_lower for word in ['youtube', 'www.youtube.com']):
            return {
                "command": "open_youtube",
                "explanation": "Opening YouTube in your default browser",
                "risky": False,
                "category": "web_browser",
                "operation": "open_youtube",
                "parameters": {},
                "warnings": [],
                "alternatives": []
            }
        
        if any(word in user_lower for word in ['google.com', 'google search']):
            return {
                "command": "open_google",
                "explanation": "Opening Google in your default browser",
                "risky": False,
                "category": "web_browser",
                "operation": "open_google",
                "parameters": {},
                "warnings": [],
                "alternatives": []
            }
        
        # Check for URL patterns
        url_pattern = r'(?:https?://[^\s]+|[^\s]+\.[^\s]+)'
        url_match = re.search(url_pattern, user_input)
        if url_match:
            url = url_match.group(0)
            return {
                "command": f"open_url:{url}",
                "explanation": f"Opening {url} in your default browser",
                "risky": False,
                "category": "web_browser",
                "operation": "open_url",
                "parameters": {"url": url},
                "warnings": [],
                "alternatives": []
            }
        
        # Check for search queries
        search_patterns = [
            r'search\s+(?:for\s+)?["\']?([^"\']*)["\'\s]',
            r'google\s+(?:for\s+)?["\']?([^"\']*)["\'\s]',
            r'look\s+up\s+["\']?([^"\']*)["\'\s]'
        ]
        
        for pattern in search_patterns:
            match = re.search(pattern, user_lower)
            if match:
                query = match.group(1).strip()
                if query:
                    return {
                        "command": f"search_google:{query}",
                        "explanation": f"Searching Google for '{query}'",
                        "risky": False,
                        "category": "web_browser",
                        "operation": "search_google",
                        "parameters": {"query": query},
                        "warnings": [],
                        "alternatives": []
                    }
        
        # Check for browser launching
        browser_patterns = {
            'chrome': ['chrome', 'google chrome'],
            'firefox': ['firefox', 'mozilla firefox'],
            'edge': ['edge', 'microsoft edge']
        }
        
        for browser, keywords in browser_patterns.items():
            if any(keyword in user_lower for keyword in keywords):
                # Check if it's a launch command
                if any(word in user_lower for word in ['open', 'launch', 'start', 'run']):
                    return {
                        "command": f"launch_browser:{browser}",
                        "explanation": f"Launching {browser} browser",
                        "risky": False,
                        "category": "web_browser",
                        "operation": "launch_browser",
                        "parameters": {"browser": browser},
                        "warnings": [],
                        "alternatives": []
                    }
        
        # Check for app launching commands
        app_launch_patterns = [
            r'(?:open|launch|start|run)\s+(?:the\s+)?(?:app\s+)?["\']?([^"\']*)["\'\s]',
            r'(?:open|launch|start|run)\s+([^\s]+)',
            r'(?:can\s+you\s+)?(?:open|launch|start|run)\s+([^\s]+)'
        ]
        
        for pattern in app_launch_patterns:
            match = re.search(pattern, user_lower)
            if match:
                app_name = match.group(1).strip()
                if app_name and app_name not in ['the', 'an', 'a', 'my', 'this', 'that']:
                    # Remove common words that might be captured
                    app_name = re.sub(r'^(?:the\s+|an\s+|a\s+|my\s+)', '', app_name)
                    
                    return {
                        "command": f"launch_app:{app_name}",
                        "explanation": f"Launching {app_name} application",
                        "risky": False,
                        "category": "desktop_app",
                        "operation": "launch_app",
                        "parameters": {"app_name": app_name},
                        "warnings": [],
                        "alternatives": []
                    }
        
        # Check for app closing commands
        app_close_patterns = [
            r'(?:close|quit|exit|stop)\s+(?:the\s+)?(?:app\s+)?["\']?([^"\']*)["\'\s]',
            r'(?:close|quit|exit|stop)\s+([^\s]+)'
        ]
        
        for pattern in app_close_patterns:
            match = re.search(pattern, user_lower)
            if match:
                app_name = match.group(1).strip()
                if app_name and app_name not in ['the', 'an', 'a', 'my', 'this', 'that']:
                    app_name = re.sub(r'^(?:the\s+|an\s+|a\s+|my\s+)', '', app_name)
                    
                    return {
                        "command": f"close_app:{app_name}",
                        "explanation": f"Closing {app_name} application",
                        "risky": False,
                        "category": "desktop_app",
                        "operation": "close_app",
                        "parameters": {"app_name": app_name},
                        "warnings": [],
                        "alternatives": []
                    }
        
        # Check for list apps command
        if any(phrase in user_lower for phrase in ['list apps', 'show apps', 'what apps', 'installed apps']):
            return {
                "command": "list_apps",
                "explanation": "Listing all installed applications",
                "risky": False,
                "category": "desktop_app",
                "operation": "list_apps",
                "parameters": {},
                "warnings": [],
                "alternatives": []
            }
        
        return None
    
    def get_command_suggestions(self, partial_input: str) -> list:
        """Get command suggestions based on partial input"""
        return self.command_db.search_commands(partial_input)
    
    def get_help(self, category: str = None) -> Dict[str, Any]:
        """Get help information for commands"""
        if category:
            operations = self.command_db.get_operations(category)
            return {
                'category': category,
                'operations': operations,
                'total': len(operations)
            }
        else:
            categories = self.command_db.get_categories()
            return {
                'categories': categories,
                'total_categories': len(categories),
                'total_commands': sum(len(self.command_db.get_operations(cat)) for cat in categories)
            }
    
    def test_connection(self) -> bool:
        """Test if the LLM connection is working"""
        if not self.client:
            return False
        try:
            if self.provider == "gemini":
                response = self.client.generate_content("Hello")
                return True
        except:
            return False

# Create global instance
enhanced_parser = EnhancedLLMParser()
