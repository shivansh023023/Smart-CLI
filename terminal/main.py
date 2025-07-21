import customtkinter as ctk
from enhanced_command_executor import execute_enhanced_command, get_background_processes, create_test_background_process
from command_session import get_current_session, update_session_context, get_session_summary, get_command_suggestions
from interactive_session_handler import (
    create_interactive_session, start_interactive_session, 
    list_interactive_sessions, close_interactive_session
)
from enhanced_llm_parser import EnhancedLLMParser
from question_handler import question_handler
import platform
import os
import datetime
import sys
import time
sys.path.append('config')
from config.settings import *

class OSAssistantApp:
    def __init__(self):
        ctk.set_appearance_mode(THEME)
        self.app = ctk.CTk()
        self.app.title(APP_TITLE)
        self.app.geometry("900x700")  # Larger window for new features

        # State management for confirmation flow
        self.waiting_for_confirmation = False
        self.pending_command = None
        self.pending_explanation = None

        # Initialize Enhanced LLM parser
        self.llm_parser = EnhancedLLMParser(
            provider=LLM_PROVIDER, 
            api_key=GEMINI_API_KEY if LLM_PROVIDER == "gemini" else OPENAI_API_KEY, 
            model=LLM_MODEL
        )
        
        # Test LLM connection and show status
        self.llm_connected = self.llm_parser.test_connection()
        
        # Session management
        self.current_session = get_current_session()
        self.active_interactive_sessions = {}
        self.current_interactive_session = None
        
        # Create main layout
        self.create_main_layout()
        
        # Show welcome message
        self.show_welcome_message()
        
        # Start periodic updates
        self.update_status()
        
    def create_main_layout(self):
        """Create the main application layout with tabs"""
        # Create tabview
        self.tabview = ctk.CTkTabview(self.app)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Main command tab
        self.command_tab = self.tabview.add("Commands")
        self.create_command_interface(self.command_tab)
        
        # Session management tab
        self.session_tab = self.tabview.add("Sessions")
        self.create_session_interface(self.session_tab)
        
        # Interactive sessions tab
        self.interactive_tab = self.tabview.add("Interactive")
        self.create_interactive_interface(self.interactive_tab)
        
        # System info tab
        self.info_tab = self.tabview.add("System Info")
        self.create_info_interface(self.info_tab)
        
    def create_command_interface(self, parent):
        """Create the main command interface"""
        # Chat history
        self.chat_history = ctk.CTkTextbox(parent, wrap="word")
        self.chat_history.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Input frame
        self.input_frame = ctk.CTkFrame(parent)
        self.input_frame.pack(padx=10, pady=10, fill="x")
        
        # Command suggestions frame
        self.suggestions_frame = ctk.CTkFrame(self.input_frame)
        
        # Input entry with suggestions
        self.input_entry = ctk.CTkEntry(self.input_frame)
        self.input_entry.insert(0, "Type a command...")
        self.input_entry.bind("<FocusIn>", lambda e: self.input_entry.delete(0, "end"))
        self.input_entry.bind("<Return>", lambda e: self.process_input())
        self.input_entry.bind("<KeyRelease>", self.on_input_change)
        self.input_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self.input_frame)
        self.buttons_frame.pack(side="right", padx=5, pady=5)
        
        # Send button
        self.send_button = ctk.CTkButton(self.buttons_frame, text="Send", command=self.process_input, width=80)
        self.send_button.pack(side="left", padx=2)
        
        # Interactive button
        self.interactive_button = ctk.CTkButton(self.buttons_frame, text="Interactive", 
                                               command=self.start_interactive_mode, width=80)
        self.interactive_button.pack(side="left", padx=2)
        
        # System processes button
        self.bg_processes_button = ctk.CTkButton(self.buttons_frame, text="Processes", 
                                               command=self.show_background_processes, width=80)
        self.bg_processes_button.pack(side="left", padx=2)
        
        # Test background process button
        self.test_bg_button = ctk.CTkButton(self.buttons_frame, text="Test BG", 
                                          command=self.create_test_background_process, width=80)
        self.test_bg_button.pack(side="left", padx=2)
        
    def create_session_interface(self, parent):
        """Create session management interface"""
        # Session info frame
        self.session_info_frame = ctk.CTkFrame(parent)
        self.session_info_frame.pack(fill="x", padx=10, pady=10)
        
        # Session summary
        self.session_summary = ctk.CTkTextbox(parent, height=300)
        self.session_summary.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Control buttons
        self.session_controls = ctk.CTkFrame(parent)
        self.session_controls.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.session_controls, text="Refresh Session Info", 
                     command=self.update_session_info).pack(side="left", padx=5)
        
        ctk.CTkButton(self.session_controls, text="Export Session", 
                     command=self.export_session).pack(side="left", padx=5)
        
    def create_interactive_interface(self, parent):
        """Create interactive sessions interface"""
        # Sessions list
        self.interactive_sessions_frame = ctk.CTkFrame(parent)
        self.interactive_sessions_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Session list
        self.sessions_listbox = ctk.CTkTextbox(self.interactive_sessions_frame, height=200)
        self.sessions_listbox.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Controls for interactive sessions
        self.interactive_controls = ctk.CTkFrame(parent)
        self.interactive_controls.pack(fill="x", padx=10, pady=10)
        
        # New session entry
        self.new_session_entry = ctk.CTkEntry(self.interactive_controls, placeholder_text="Enter command for new session")
        self.new_session_entry.pack(side="left", padx=5, pady=5, fill="x", expand=True)
        
        ctk.CTkButton(self.interactive_controls, text="Start Session", 
                     command=self.start_new_interactive_session).pack(side="right", padx=5)
        
        # Session controls
        self.session_action_frame = ctk.CTkFrame(parent)
        self.session_action_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.session_action_frame, text="Refresh List", 
                     command=self.update_interactive_sessions).pack(side="left", padx=5)
        
        ctk.CTkButton(self.session_action_frame, text="Close Selected", 
                     command=self.close_selected_session).pack(side="left", padx=5)
        
    def create_info_interface(self, parent):
        """Create system info interface"""
        self.system_info = ctk.CTkTextbox(parent, wrap="word")
        self.system_info.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Info controls
        self.info_controls = ctk.CTkFrame(parent)
        self.info_controls.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(self.info_controls, text="Refresh System Info", 
                     command=self.update_system_info).pack(side="left", padx=5)
        
        ctk.CTkButton(self.info_controls, text="Show Performance", 
                     command=self.show_performance_info).pack(side="left", padx=5)
        
        # Initialize system info
        self.update_system_info()
    
    def on_input_change(self, event):
        """Handle input changes for command suggestions"""
        current_text = self.input_entry.get()
        if len(current_text) > 2:  # Only suggest after 2 characters
            suggestions = get_command_suggestions(current_text, limit=3)
            if suggestions:
                self.show_suggestions(suggestions)
            else:
                self.hide_suggestions()
        else:
            self.hide_suggestions()
    
    def show_suggestions(self, suggestions):
        """Show command suggestions"""
        # For now, just display in chat (can be enhanced with dropdown)
        suggestion_text = "💡 Suggestions: " + ", ".join([s['command'] for s in suggestions[:3]])
        # Could implement a dropdown here
    
    def hide_suggestions(self):
        """Hide command suggestions"""
        pass  # Placeholder for hiding suggestions dropdown
    
    def start_interactive_mode(self):
        """Start interactive mode for current command"""
        command = self.input_entry.get().strip()
        if command:
            session_id = create_interactive_session(command)
            if start_interactive_session(session_id):
                self.current_interactive_session = session_id
                self.active_interactive_sessions[session_id] = command
                self.display_message(f"🔄 Started interactive session: {session_id}")
                self.input_entry.delete(0, "end")
                self.tabview.set("Interactive")
                self.update_interactive_sessions()
            else:
                self.display_message("❌ Failed to start interactive session")
    
    def show_background_processes(self):
        """Show system processes"""
        try:
            self.display_message("🔍 Getting system processes...")
            
            import platform
            import subprocess
            
            if platform.system() == "Windows":
                # Use PowerShell Get-Process for Windows
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Process | Select-Object Name, Id, CPU, WorkingSet | Format-Table -AutoSize"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.display_message("🖥️ Windows System Processes:")
                    self.display_message("─" * 60)
                    
                    lines = result.stdout.split('\n')
                    for line in lines[:30]:  # Show first 30 lines
                        if line.strip():
                            self.display_message(line)
                    
                    if len(lines) > 30:
                        self.display_message(f"... and {len(lines) - 30} more processes")
                else:
                    self.display_message(f"❌ PowerShell error: {result.stderr}")
                    
            else:
                # Use ps aux for Linux/Unix
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.display_message("🐧 Linux System Processes:")
                    self.display_message("─" * 60)
                    
                    lines = result.stdout.split('\n')
                    for line in lines[:30]:  # Show first 30 lines
                        if line.strip():
                            self.display_message(line)
                    
                    if len(lines) > 30:
                        self.display_message(f"... and {len(lines) - 30} more processes")
                else:
                    self.display_message(f"❌ ps command error: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            self.display_message("❌ Process listing timed out")
        except Exception as e:
            self.display_message(f"❌ Error getting processes: {str(e)}")
            import traceback
            self.display_message(f"Traceback: {traceback.format_exc()}")
    
    def create_test_background_process(self):
        """Create a test background process"""
        try:
            from enhanced_command_executor import create_test_background_process
            process_id = create_test_background_process()
            self.display_message(f"✅ Created test background process: {process_id}")
            self.display_message("💡 Now click 'BG Processes' to see it running!")
        except Exception as e:
            self.display_message(f"❌ Error creating test process: {str(e)}")
            import traceback
            self.display_message(f"Traceback: {traceback.format_exc()}")
    
    def update_session_info(self):
        """Update session information display"""
        try:
            summary = get_session_summary()
            info_text = f"📊 Session Summary\n"
            info_text += f"Session ID: {summary['session_id']}\n"
            info_text += f"Duration: {summary['duration']}\n"
            info_text += f"Working Directory: {summary['working_directory']}\n"
            info_text += f"Commands Executed: {summary['commands_executed']}\n"
            info_text += f"Unique Commands: {summary['unique_commands']}\n\n"
            
            info_text += "🔄 Most Frequent Commands:\n"
            for cmd, count in summary['most_frequent_commands'].items():
                info_text += f"  • {cmd} ({count} times)\n"
            
            info_text += "\n📁 Recent Files:\n"
            for file_path in summary['recent_files'][:10]:
                info_text += f"  • {file_path}\n"
            
            if summary['git_status'] and summary['git_status'].get('is_git_repo'):
                info_text += "\n🌿 Git Status:\n"
                git_status = summary['git_status']
                if git_status.get('modified_files'):
                    info_text += f"  Modified: {', '.join(git_status['modified_files'])}\n"
                if git_status.get('untracked_files'):
                    info_text += f"  Untracked: {', '.join(git_status['untracked_files'])}\n"
            
            self.session_summary.delete("1.0", "end")
            self.session_summary.insert("1.0", info_text)
            
        except Exception as e:
            self.session_summary.delete("1.0", "end")
            self.session_summary.insert("1.0", f"Error updating session info: {str(e)}")
    
    def export_session(self):
        """Export session data"""
        try:
            summary = get_session_summary()
            filename = f"session_export_{summary['session_id']}.json"
            
            import json
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            self.display_message(f"📁 Session exported to: {filename}")
            
        except Exception as e:
            self.display_message(f"❌ Export failed: {str(e)}")
    
    def start_new_interactive_session(self):
        """Start a new interactive session"""
        command = self.new_session_entry.get().strip()
        if command:
            session_id = create_interactive_session(command)
            if start_interactive_session(session_id):
                self.active_interactive_sessions[session_id] = command
                self.display_message(f"🔄 Started interactive session: {session_id}")
                self.new_session_entry.delete(0, "end")
                self.update_interactive_sessions()
            else:
                self.display_message("❌ Failed to start interactive session")
    
    def update_interactive_sessions(self):
        """Update interactive sessions display"""
        try:
            sessions = list_interactive_sessions()
            sessions_text = "🔄 Interactive Sessions:\n\n"
            
            if sessions:
                for session in sessions:
                    sessions_text += f"Session ID: {session['session_id']}\n"
                    sessions_text += f"Type: {session['session_type']}\n"
                    sessions_text += f"State: {session['state']}\n"
                    sessions_text += f"Command: {session['command']}\n"
                    sessions_text += f"Uptime: {session['uptime']}\n"
                    sessions_text += f"Last Activity: {session['last_activity']}\n"
                    sessions_text += "-" * 50 + "\n"
            else:
                sessions_text += "No active interactive sessions\n"
            
            self.sessions_listbox.delete("1.0", "end")
            self.sessions_listbox.insert("1.0", sessions_text)
            
        except Exception as e:
            self.sessions_listbox.delete("1.0", "end")
            self.sessions_listbox.insert("1.0", f"Error updating sessions: {str(e)}")
    
    def close_selected_session(self):
        """Close selected interactive session"""
        # Simple implementation - close the first session
        # In a real implementation, you'd have session selection
        sessions = list_interactive_sessions()
        if sessions:
            session_id = sessions[0]['session_id']
            if close_interactive_session(session_id):
                self.display_message(f"✅ Closed session: {session_id}")
                if session_id in self.active_interactive_sessions:
                    del self.active_interactive_sessions[session_id]
                self.update_interactive_sessions()
            else:
                self.display_message(f"❌ Failed to close session: {session_id}")
        else:
            self.display_message("ℹ️ No sessions to close")
    
    def update_system_info(self):
        """Update system information display"""
        try:
            import psutil
            import platform
            
            info_text = "💻 System Information\n\n"
            info_text += f"Platform: {platform.system()} {platform.release()}\n"
            info_text += f"Architecture: {platform.architecture()[0]}\n"
            info_text += f"Processor: {platform.processor()}\n"
            info_text += f"Hostname: {platform.node()}\n\n"
            
            # Memory info
            memory = psutil.virtual_memory()
            info_text += f"Memory: {memory.percent}% used ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)\n"
            
            # CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            info_text += f"CPU Usage: {cpu_percent}%\n"
            
            # Disk info
            disk = psutil.disk_usage('/')
            info_text += f"Disk Usage: {disk.percent}% used ({disk.used // (1024**3):.1f}GB / {disk.total // (1024**3):.1f}GB)\n\n"
            
            # Network info
            info_text += "🌐 Network Interfaces:\n"
            for interface, addrs in psutil.net_if_addrs().items():
                info_text += f"  {interface}:\n"
                for addr in addrs:
                    if addr.family == 2:  # IPv4
                        info_text += f"    IPv4: {addr.address}\n"
            
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", info_text)
            
        except ImportError:
            # Fallback if psutil is not available
            info_text = "💻 Basic System Information\n\n"
            info_text += f"Platform: {platform.system()} {platform.release()}\n"
            info_text += f"Architecture: {platform.architecture()[0]}\n"
            info_text += f"Processor: {platform.processor()}\n"
            info_text += f"Hostname: {platform.node()}\n\n"
            info_text += "Install 'psutil' for detailed system information\n"
            
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", info_text)
            
        except Exception as e:
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", f"Error getting system info: {str(e)}")
    
    def show_performance_info(self):
        """Show performance information"""
        try:
            import psutil
            
            perf_text = "📊 Performance Information\n\n"
            
            # CPU per core
            cpu_per_core = psutil.cpu_percent(percpu=True, interval=1)
            perf_text += "🔥 CPU Usage per Core:\n"
            for i, percent in enumerate(cpu_per_core):
                perf_text += f"  Core {i}: {percent}%\n"
            
            # Top processes by CPU
            perf_text += "\n🔄 Top Processes by CPU:\n"
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            for proc in processes[:10]:
                perf_text += f"  {proc['name']} (PID: {proc['pid']}): {proc['cpu_percent']}%\n"
            
            # Memory usage
            perf_text += "\n💾 Memory Usage:\n"
            memory = psutil.virtual_memory()
            perf_text += f"  Available: {memory.available // (1024**3):.1f}GB\n"
            perf_text += f"  Used: {memory.used // (1024**3):.1f}GB\n"
            perf_text += f"  Cached: {memory.cached // (1024**3):.1f}GB\n"
            
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", perf_text)
            
        except ImportError:
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", "Install 'psutil' for performance information")
        except Exception as e:
            self.system_info.delete("1.0", "end")
            self.system_info.insert("1.0", f"Error getting performance info: {str(e)}")
    
    def update_status(self):
        """Update status periodically"""
        # Update session info if on sessions tab
        if hasattr(self, 'tabview') and self.tabview.get() == "Sessions":
            self.update_session_info()
        
        # Update interactive sessions if on interactive tab
        if hasattr(self, 'tabview') and self.tabview.get() == "Interactive":
            self.update_interactive_sessions()
        
        # Schedule next update
        self.app.after(5000, self.update_status)  # Update every 5 seconds

    def show_welcome_message(self):
        """Show welcome message and LLM status"""
        welcome_msg = f"🤖 Welcome to {APP_TITLE}!\n"
        if self.llm_connected:
            provider_name = "Gemini" if LLM_PROVIDER == "gemini" else "GPT"
            welcome_msg += f"🧠 AI Enhanced - {provider_name}-powered natural language processing enabled\n"
        else:
            welcome_msg += "⚠️ AI Mode: Fallback to basic command mapping (API key not working)\n"
        welcome_msg += "\nTry commands like:\n"
        welcome_msg += "• Create a file named 'test.txt' on the desktop\n"
        welcome_msg += "• Show me the current directory\n"
        welcome_msg += "• What's my IP address?\n"
        welcome_msg += "• List all files in this folder\n\n"
        welcome_msg += "Ask questions like:\n"
        welcome_msg += "• What can you do?\n"
        welcome_msg += "• What BIOS operations can you do?\n"
        welcome_msg += "• What network operations are available?\n"
        welcome_msg += "• Help me with file operations\n"
        self.display_message(welcome_msg)

    def display_message(self, msg):
        self.chat_history.insert("end", msg + "\n")
        self.chat_history.see("end")

    def process_input(self):
        user_msg = self.input_entry.get().strip()
        if not user_msg or user_msg == "Type a command...": return

        self.display_message(f"You: {user_msg}")
        self.input_entry.delete(0, "end")

        if self.waiting_for_confirmation:
            if user_msg.strip().upper() == "I AGREE":
                self.display_message("Executing risky command...")
                success, output = execute_enhanced_command(self.pending_command)
                self.display_message(f"[{'✔' if success else '✖'}] {output}")
                if self.pending_explanation:
                    self.display_message(f"ℹ️ {self.pending_explanation}")
                self.log_command(self.pending_command, output)
                self.waiting_for_confirmation = False
                self.pending_command = None
                self.pending_explanation = None
            else:
                self.display_message("Please type 'I AGREE' to proceed.")
            return

        # Use question handler to determine if it's a question
        if question_handler.is_question(user_msg):
            response = question_handler.handle_question(user_msg)
            self.display_message(response['content'])
            return
        
        # Use LLM parser to understand the command
        self.display_message("🤔 Thinking...")
        result = self.llm_parser.parse_command(user_msg)
        
        if not result['command']:
            self.display_message(f"❌ {result['explanation']}")
            return

        command = result['command']
        explanation = result['explanation']
        is_risky_cmd = result['risky']
        category = result['category']
        operation = result.get('operation', 'unknown')
        parameters = result.get('parameters', {})
        warnings = result.get('warnings', [])
        alternatives = result.get('alternatives', [])

        if is_risky_cmd:
            risk_msg = f"⚠️ Risky command detected:\n`{command}`\n\n"
            risk_msg += f"💡 Explanation: {explanation}\n"
            risk_msg += f"📁 Category: {category}\n"
            risk_msg += f"🔧 Operation: {operation}\n"
            
            if parameters:
                risk_msg += f"⚙️ Parameters: {', '.join([f'{k}={v}' for k, v in parameters.items()])}\n"
            
            if warnings:
                risk_msg += f"⚠️ Warnings:\n"
                for warning in warnings:
                    risk_msg += f"   • {warning}\n"
            
            if alternatives:
                risk_msg += f"💡 Safer alternatives:\n"
                for alt in alternatives:
                    risk_msg += f"   • {alt}\n"
            
            risk_msg += "\nType 'I AGREE' to continue."
            self.display_message(risk_msg)
            self.pending_command = command
            self.pending_explanation = explanation
            self.waiting_for_confirmation = True
        else:
            self.display_message(f"💡 {explanation}")
            self.display_message(f"📁 Category: {category} | 🔧 Operation: {operation}")
            
            if parameters:
                param_str = ', '.join([f'{k}={v}' for k, v in parameters.items()])
                self.display_message(f"⚙️ Parameters: {param_str}")
            
            self.display_message(f"🔧 Executing: `{command}`")
            
            # Use enhanced command execution for better support
            start_time = time.time()
            success, output = execute_enhanced_command(command)
            execution_time = time.time() - start_time
            
            # If command failed, try AI fallback system
            if not success and self.llm_connected:
                self.display_message(f"[⚠️] Command failed: {output}")
                self.display_message("🤖 Trying AI fallback system...")
                
                try:
                    from ai_fallback_system import handle_command_failure
                    
                    fallback_result = handle_command_failure(
                        original_command=command,
                        user_intent=user_msg,
                        error_message=output,
                        context={
                            "category": category,
                            "operation": operation,
                            "parameters": parameters
                        }
                    )
                    
                    if fallback_result["success"]:
                        success = True
                        solution = fallback_result["successful_solution"]
                        output = f"AI Fallback Success: {solution['output']}"
                        self.display_message(f"[✅] AI found solution: {solution['command']}")
                        self.display_message(f"[✔️] {solution['output']}")
                    else:
                        self.display_message(f"[❌] AI fallback also failed")
                        if "ai_suggestions" in fallback_result:
                            suggestions = fallback_result["ai_suggestions"]
                            if "analysis" in suggestions:
                                self.display_message(f"💡 AI Analysis: {suggestions['analysis']}")
                            if "additional_help" in suggestions:
                                self.display_message(f"🔧 Additional Help: {suggestions['additional_help']}")
                        
                except Exception as e:
                    self.display_message(f"[⚠️] AI fallback system error: {str(e)}")
            else:
                self.display_message(f"[{'✔' if success else '✖'}] {output}")
            
            # Update session context
            update_session_context(command, success, output, execution_time)
            
            self.log_command(command, output)

    def log_command(self, cmd, output):
        os.makedirs("logs", exist_ok=True)
        with open("logs/command_history.log", "a", encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now()}] {cmd} -> {output}\n")

    def run(self):
        self.app.mainloop()

if __name__ == "__main__":
    OSAssistantApp().run()
