#!/usr/bin/env python3
"""
AI Fallback System for Terminal Assistant
This system uses AI to provide solutions when standard commands fail
"""

import subprocess
import sys
import os
import time
import json
import google.generativeai as genai
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from enhanced_command_executor import execute_enhanced_command

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AIFallbackSystem:
    def __init__(self, gemini_api_key: str = None):
        """Initialize the AI Fallback System"""
        self.gemini_api_key = gemini_api_key or self._get_gemini_api_key()
        self.gemini_client = None
        
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel("gemini-1.5-flash")
                logger.info("AI Fallback System initialized with Gemini API")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
        
        # Success patterns for learning
        self.success_patterns = []
        self.failure_patterns = []
        
    def _get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from config"""
        try:
            sys.path.append('config')
            from config.settings import GEMINI_API_KEY
            return GEMINI_API_KEY
        except:
            return os.getenv("GEMINI_API_KEY")
    
    def handle_command_failure(self, 
                             original_command: str, 
                             user_intent: str, 
                             error_message: str,
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle a command failure by using AI to find alternative solutions
        
        Args:
            original_command: The command that failed
            user_intent: What the user was trying to achieve
            error_message: The error message from the failed command
            context: Additional context information
            
        Returns:
            Dictionary with AI suggestions and execution results
        """
        logger.info(f"🤖 AI Fallback triggered for: {user_intent}")
        
        result = {
            "success": False,
            "original_command": original_command,
            "user_intent": user_intent,
            "error_message": error_message,
            "ai_suggestions": [],
            "successful_solution": None,
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.gemini_client:
            result["error"] = "AI Fallback System not available (no API key)"
            return result
        
        try:
            # Get system context
            system_context = self._get_system_context()
            
            # Create prompt for AI
            prompt = self._create_fallback_prompt(
                original_command, 
                user_intent, 
                error_message, 
                system_context, 
                context
            )
            
            # Get AI suggestions
            response = self.gemini_client.generate_content(prompt)
            ai_suggestions = self._parse_ai_response(response.text)
            
            if ai_suggestions:
                result["ai_suggestions"] = ai_suggestions
                
                # Try executing the AI suggestions
                success_result = self._execute_ai_suggestions(ai_suggestions)
                
                if success_result["success"]:
                    result["success"] = True
                    result["successful_solution"] = success_result
                    self._record_success_pattern(user_intent, success_result["command"])
                else:
                    result["execution_attempts"] = success_result.get("attempts", [])
                    self._record_failure_pattern(user_intent, original_command, error_message)
            else:
                result["error"] = "No valid AI suggestions received"
                
        except Exception as e:
            logger.error(f"AI Fallback System error: {e}")
            result["error"] = f"AI Fallback System error: {str(e)}"
        
        return result
    
    def _create_fallback_prompt(self, 
                              original_command: str, 
                              user_intent: str, 
                              error_message: str,
                              system_context: str,
                              context: Dict[str, Any] = None) -> str:
        """Create a prompt for the AI to generate alternative solutions"""
        
        context_str = ""
        if context:
            context_str = f"\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""You are an expert system administrator helping a user resolve a command failure.

User Intent: {user_intent}
Failed Command: {original_command}
Error Message: {error_message}

System Context:
{system_context}
{context_str}

Please provide alternative solutions to achieve the user's intent. Consider:
1. Different command approaches
2. Alternative tools or utilities
3. Workarounds for the specific error
4. System-specific solutions
5. Prerequisites that might be missing

Respond with a JSON object containing:
{{
    "analysis": "Brief analysis of why the original command failed",
    "solutions": [
        {{
            "command": "alternative command",
            "explanation": "what this command does",
            "success_probability": 0.8,
            "risk_level": "low|medium|high",
            "prerequisites": ["requirement1", "requirement2"],
            "expected_outcome": "what should happen"
        }}
    ],
    "additional_help": "Any additional troubleshooting steps"
}}

Only provide safe, appropriate commands for the detected operating system.
"""
        
        return prompt
    
    def _get_system_context(self) -> str:
        """Get comprehensive system context"""
        context = []
        
        try:
            # Operating system info
            result = subprocess.run('ver', shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                context.append(f"OS: {result.stdout.strip()}")
            
            # PowerShell version
            result = subprocess.run('powershell -Command "$PSVersionTable.PSVersion"', 
                                  shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                context.append(f"PowerShell: {result.stdout.strip()}")
            
            # Current directory
            result = subprocess.run('cd', shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                context.append(f"Current Directory: {result.stdout.strip()}")
            
            # Available tools
            tools = ['python', 'powershell', 'cmd', 'wmic', 'sc', 'net']
            available_tools = []
            for tool in tools:
                result = subprocess.run(f'where {tool}', shell=True, capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    available_tools.append(tool)
            
            if available_tools:
                context.append(f"Available Tools: {', '.join(available_tools)}")
            
            # User privileges
            result = subprocess.run('whoami /groups', shell=True, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                if "S-1-16-12288" in result.stdout:  # High integrity level
                    context.append("Privileges: Administrator")
                else:
                    context.append("Privileges: Standard User")
            
        except Exception as e:
            context.append(f"Context gathering error: {str(e)}")
        
        return "\n".join(context)
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse AI response and validate structure"""
        try:
            # Handle markdown formatting
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            ai_response = json.loads(response_text)
            
            # Validate structure
            if "solutions" in ai_response and isinstance(ai_response["solutions"], list):
                return ai_response
            else:
                logger.error("Invalid AI response structure")
                return None
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _execute_ai_suggestions(self, ai_suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI suggestions in order of success probability"""
        result = {
            "success": False,
            "command": None,
            "output": "",
            "attempts": []
        }
        
        solutions = ai_suggestions.get("solutions", [])
        
        # Sort by success probability (highest first)
        solutions.sort(key=lambda x: x.get("success_probability", 0), reverse=True)
        
        for i, solution in enumerate(solutions):
            command = solution.get("command", "")
            explanation = solution.get("explanation", "")
            risk_level = solution.get("risk_level", "medium")
            prerequisites = solution.get("prerequisites", [])
            
            try:
                logger.info(f"🤖 Trying AI solution {i+1}: {explanation}")
                logger.info(f"   Command: {command}")
                logger.info(f"   Risk Level: {risk_level}")
                
                # Check prerequisites if any
                if prerequisites:
                    prereq_check = self._check_prerequisites(prerequisites)
                    if not prereq_check["all_met"]:
                        logger.info(f"   ⚠️ Prerequisites not met: {prereq_check['missing']}")
                        result["attempts"].append({
                            "command": command,
                            "explanation": explanation,
                            "success": False,
                            "output": f"Prerequisites not met: {prereq_check['missing']}"
                        })
                        continue
                
                # Execute the command
                success, output = execute_enhanced_command(command)
                
                attempt_info = {
                    "command": command,
                    "explanation": explanation,
                    "risk_level": risk_level,
                    "success": success,
                    "output": output
                }
                result["attempts"].append(attempt_info)
                
                if success:
                    logger.info(f"   ✅ AI solution successful!")
                    result["success"] = True
                    result["command"] = command
                    result["output"] = output
                    return result
                else:
                    logger.info(f"   ❌ AI solution failed: {output}")
                
                # Wait between attempts
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"   ⚠️ Error executing AI solution: {str(e)}")
                result["attempts"].append({
                    "command": command,
                    "explanation": explanation,
                    "success": False,
                    "output": str(e)
                })
        
        return result
    
    def _check_prerequisites(self, prerequisites: List[str]) -> Dict[str, Any]:
        """Check if prerequisites are met"""
        result = {
            "all_met": True,
            "missing": [],
            "checked": []
        }
        
        for prereq in prerequisites:
            try:
                # Check if command/tool exists
                check_result = subprocess.run(f'where {prereq}', shell=True, capture_output=True, text=True, timeout=5)
                if check_result.returncode == 0:
                    result["checked"].append(f"{prereq}: Available")
                else:
                    result["all_met"] = False
                    result["missing"].append(prereq)
                    result["checked"].append(f"{prereq}: Not found")
                    
            except Exception as e:
                result["all_met"] = False
                result["missing"].append(prereq)
                result["checked"].append(f"{prereq}: Error checking - {str(e)}")
        
        return result
    
    def _record_success_pattern(self, user_intent: str, successful_command: str):
        """Record successful patterns for learning"""
        pattern = {
            "user_intent": user_intent,
            "successful_command": successful_command,
            "timestamp": datetime.now().isoformat()
        }
        
        self.success_patterns.append(pattern)
        
        # Keep only last 100 patterns
        if len(self.success_patterns) > 100:
            self.success_patterns = self.success_patterns[-100:]
    
    def _record_failure_pattern(self, user_intent: str, failed_command: str, error_message: str):
        """Record failure patterns for learning"""
        pattern = {
            "user_intent": user_intent,
            "failed_command": failed_command,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.failure_patterns.append(pattern)
        
        # Keep only last 100 patterns
        if len(self.failure_patterns) > 100:
            self.failure_patterns = self.failure_patterns[-100:]
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learned patterns"""
        return {
            "success_patterns": len(self.success_patterns),
            "failure_patterns": len(self.failure_patterns),
            "recent_successes": self.success_patterns[-10:] if self.success_patterns else [],
            "recent_failures": self.failure_patterns[-10:] if self.failure_patterns else []
        }

# Global instance
ai_fallback_system = AIFallbackSystem()

def handle_command_failure(original_command: str, 
                         user_intent: str, 
                         error_message: str,
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle command failure with AI assistance"""
    return ai_fallback_system.handle_command_failure(
        original_command, 
        user_intent, 
        error_message, 
        context
    )

# Test function
def test_ai_fallback_system():
    """Test the AI Fallback System"""
    print("🧪 Testing AI Fallback System")
    print("=" * 50)
    
    # Test with a failing Bluetooth command
    print("\n1. Testing Bluetooth command failure...")
    result = handle_command_failure(
        original_command="btctl enable",
        user_intent="turn on bluetooth",
        error_message="command not found",
        context={"platform": "Windows", "user_privileges": "standard"}
    )
    
    print(json.dumps(result, indent=2, default=str))
    
    print("\n🎉 AI Fallback System test completed!")

if __name__ == "__main__":
    test_ai_fallback_system()
