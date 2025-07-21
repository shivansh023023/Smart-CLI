#!/usr/bin/env python3
"""
Modern AI Assistant with Sleek Black and Gold UI
Similar to Claude interface but with custom styling
"""

import customtkinter as ctk
from intent_mapper import get_command
from enhanced_command_executor import execute_enhanced_command, get_background_processes, kill_background_process
from command_session import get_current_session, update_session_context, get_command_suggestions, get_session_summary
from interactive_session_handler import (
    create_interactive_session, start_interactive_session, send_to_interactive_session,
    get_interactive_session_output, list_interactive_sessions, close_interactive_session
)
from permissions import is_risky
from enhanced_llm_parser import EnhancedLLMParser
from question_handler import question_handler
from system_info import SystemInfo
from conversation_manager import remember_interaction, get_context_for_query, get_personalized_greeting
from ai_suggestion_engine import AISuggestionEngine
from suggestion_ui import SuggestionManager
import platform
import os
import datetime
import sys
import time
import tkinter as tk
from tkinter import font as tkfont
sys.path.append('config')
from config.settings import *

# Set the appearance mode to dark
ctk.set_appearance_mode("dark")

class ModernOSAssistantApp:
    def __init__(self):
        # Initialize the main window
        self.app = ctk.CTk()
        self.app.title("✨ AI Terminal Assistant")
        self.app.geometry("1400x900")
        self.app.minsize(1200, 800)
        
        # Configure enhanced color scheme with gradients and depth
        self.colors = {
            "bg_primary": "#0a0a0a",        # Deep black
            "bg_secondary": "#1a1a1a",      # Card background
            "bg_tertiary": "#2d2d2d",       # Elevated surfaces
            "bg_quaternary": "#404040",     # Highest elevation
            "accent_gold": "#FFD700",       # Primary gold
            "accent_gold_dark": "#B8860B",  # Darker gold
            "accent_gold_light": "#FFEC8B", # Light gold
            "accent_blue": "#00D4FF",       # Cyan accent
            "accent_purple": "#B794F6",     # Purple accent
            "text_primary": "#FFFFFF",      # Pure white
            "text_secondary": "#E2E8F0",    # Light gray
            "text_muted": "#94A3B8",        # Medium gray
            "text_dim": "#64748B",          # Dim text
            "success": "#10B981",           # Modern green
            "warning": "#F59E0B",           # Modern orange
            "error": "#EF4444",             # Modern red
            "info": "#3B82F6",              # Modern blue
            "hover": "#374151",             # Hover state
            "shadow": "#000000",            # Shadow color
            "gradient_start": "#1a1a1a",    # Gradient start
            "gradient_end": "#0a0a0a"       # Gradient end
        }
        
        # Configure the main window
        self.app.configure(fg_color=self.colors["bg_primary"])
        
        # Initialize Enhanced LLM parser
        self.llm_parser = EnhancedLLMParser(
            provider=LLM_PROVIDER, 
            api_key=GEMINI_API_KEY if LLM_PROVIDER == "gemini" else OPENAI_API_KEY, 
            model=LLM_MODEL
        )
        
        # Test LLM connection
        self.llm_connected = self.llm_parser.test_connection()
        
        # Session management
        self.current_session = get_current_session()
        self.active_interactive_sessions = {}
        self.current_interactive_session = None
        
        # State management
        self.waiting_for_confirmation = False
        self.pending_command = None
        self.pending_explanation = None
        
        # Initialize AI suggestion system
        self.suggestion_engine = AISuggestionEngine(self.llm_parser)
        self.suggestion_manager = None  # Will be initialized after UI creation
        
        # Create the modern interface
        self.create_modern_interface()
        
        # Initialize suggestion manager after UI is created
        self.init_suggestion_system()
        
        # Show welcome message
        self.show_welcome_message()
        
        # Start periodic updates
        self.update_status()
        
    def create_modern_interface(self):
        """Create the modern, sleek interface"""
        # Main container
        self.main_container = ctk.CTkFrame(
            self.app, 
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header
        self.create_header()
        
        # Main content area
        self.create_main_content()
        
        # Footer with input
        self.create_footer()
        
    def create_header(self):
        """Create the enhanced header with modern design"""
        header_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0,
            height=100
        )
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Left section - Title and subtitle
        left_section = ctk.CTkFrame(
            header_frame,
            fg_color="transparent"
        )
        left_section.pack(side="left", fill="y", padx=30, pady=15)
        
        # Main title with enhanced styling
        title_label = ctk.CTkLabel(
            left_section,
            text="✨ AI Terminal Assistant",
            font=ctk.CTkFont(family="JetBrains Mono", size=28, weight="bold"),
            text_color=self.colors["accent_gold"]
        )
        title_label.pack(anchor="w")
        
        # Subtitle
        subtitle_label = ctk.CTkLabel(
            left_section,
            text="Next-generation intelligent command interface",
            font=ctk.CTkFont(family="JetBrains Mono", size=11),
            text_color=self.colors["text_muted"]
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))
        
        # Right section - Status indicators
        right_section = ctk.CTkFrame(
            header_frame,
            fg_color="transparent"
        )
        right_section.pack(side="right", fill="y", padx=30, pady=15)
        
        # Status indicators container
        status_container = ctk.CTkFrame(
            right_section,
            fg_color=self.colors["bg_tertiary"],
            corner_radius=15
        )
        status_container.pack(fill="both", expand=True)
        
        # AI Status with enhanced indicator
        ai_status_frame = ctk.CTkFrame(
            status_container,
            fg_color="transparent"
        )
        ai_status_frame.pack(side="left", padx=20, pady=15)
        
        # AI Status indicator
        ai_status_color = self.colors["success"] if self.llm_connected else self.colors["error"]
        ai_status_text = "🧠 AI" if self.llm_connected else "⚠️ AI"
        ai_status_desc = "Online" if self.llm_connected else "Offline"
        
        ai_status_label = ctk.CTkLabel(
            ai_status_frame,
            text=ai_status_text,
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color=ai_status_color
        )
        ai_status_label.pack()
        
        ai_desc_label = ctk.CTkLabel(
            ai_status_frame,
            text=ai_status_desc,
            font=ctk.CTkFont(family="JetBrains Mono", size=9),
            text_color=ai_status_color
        )
        ai_desc_label.pack()
        
        # System info with enhanced display
        system_frame = ctk.CTkFrame(
            status_container,
            fg_color="transparent"
        )
        system_frame.pack(side="right", padx=20, pady=15)
        
        # System icon and info
        system_icon = ctk.CTkLabel(
            system_frame,
            text="🖥️",
            font=ctk.CTkFont(family="JetBrains Mono", size=16)
        )
        system_icon.pack()
        
        system_label = ctk.CTkLabel(
            system_frame,
            text=f"{platform.system()}",
            font=ctk.CTkFont(family="JetBrains Mono", size=9, weight="bold"),
            text_color=self.colors["text_secondary"]
        )
        system_label.pack()
        
        # Add a subtle animated indicator for AI status
        if self.llm_connected:
            self.animate_status_indicator(ai_status_label)
    
    def animate_status_indicator(self, label):
        """Add a subtle animation to the AI status indicator"""
        def pulse():
            try:
                current_color = label.cget("text_color")
                new_color = self.colors["accent_gold"] if current_color == self.colors["success"] else self.colors["success"]
                label.configure(text_color=new_color)
                # Schedule next animation
                self.app.after(2000, pulse)
            except:
                pass  # Widget might be destroyed
        
        # Start the animation
        self.app.after(2000, pulse)
        
    def create_main_content(self):
        """Create the main content area with chat and sidebar"""
        content_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors["bg_primary"],
            corner_radius=0
        )
        content_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Chat area (main)
        self.create_chat_area(content_frame)
        
        # Sidebar (right)
        self.create_sidebar(content_frame)
        
    def create_chat_area(self, parent):
        """Create the main chat area"""
        chat_frame = ctk.CTkFrame(
            parent,
            fg_color=self.colors["bg_primary"],
            corner_radius=15
        )
        chat_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        # Chat history with custom scrollbar
        self.chat_history = ctk.CTkTextbox(
            chat_frame,
            wrap="word",
            font=ctk.CTkFont(family="JetBrains Mono", size=12),
            fg_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_primary"],
            corner_radius=10,
            scrollbar_button_color=self.colors["accent_gold"],
            scrollbar_button_hover_color=self.colors["accent_gold_dark"]
        )
        self.chat_history.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Add custom tags for different message types
        self.setup_chat_tags()
        
    def create_sidebar(self, parent):
        """Create the sidebar with quick actions and info"""
        sidebar_frame = ctk.CTkFrame(
            parent,
            fg_color=self.colors["bg_secondary"],
            corner_radius=15,
            width=300
        )
        sidebar_frame.pack(side="right", fill="y", padx=(0, 20), pady=20)
        sidebar_frame.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = ctk.CTkLabel(
            sidebar_frame,
            text="⚡ Quick Actions",
            font=ctk.CTkFont(family="JetBrains Mono", size=16, weight="bold"),
            text_color=self.colors["accent_gold"]
        )
        sidebar_title.pack(pady=20)
        
        # Quick action buttons
        self.create_quick_actions(sidebar_frame)
        
        # Session info
        self.create_session_info(sidebar_frame)
        
    def create_quick_actions(self, parent):
        """Create quick action buttons"""
        actions_frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )
        actions_frame.pack(fill="x", padx=15, pady=10)
        
        # Define quick actions
        quick_actions = [
            ("🔄 Background Processes", self.show_background_processes),
            ("📊 System Info", self.show_system_info),
            ("🎯 Interactive Mode", self.start_interactive_mode),
            ("📁 List Apps", self.list_applications),
            ("🔍 Session Details", self.show_session_details),
            ("💾 Export Session", self.export_session)
        ]
        
        for action_text, action_func in quick_actions:
            btn = ctk.CTkButton(
                actions_frame,
                text=action_text,
                font=ctk.CTkFont(family="JetBrains Mono", size=11),
                fg_color=self.colors["bg_tertiary"],
                text_color=self.colors["text_primary"],
                border_color=self.colors["accent_gold"],
                border_width=1,
                corner_radius=8,
                height=32,
                command=action_func
            )
            btn.pack(fill="x", pady=5)
            
            # Add hover effect for both background and text color changes
            def on_enter(event, button=btn):
                button.configure(
                    fg_color=self.colors["accent_gold"],
                    text_color=self.colors["bg_primary"]
                )
            
            def on_leave(event, button=btn):
                button.configure(
                    fg_color=self.colors["bg_tertiary"],
                    text_color=self.colors["text_primary"]
                )
            
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
    def create_session_info(self, parent):
        """Create session information display"""
        info_frame = ctk.CTkFrame(
            parent,
            fg_color=self.colors["bg_tertiary"],
            corner_radius=10
        )
        info_frame.pack(fill="x", padx=15, pady=20)
        
        # Session title
        session_title = ctk.CTkLabel(
            info_frame,
            text="📈 Session Stats",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            text_color=self.colors["accent_gold"]
        )
        session_title.pack(pady=(15, 10))
        
        # Session stats
        self.session_stats = ctk.CTkLabel(
            info_frame,
            text="Loading...",
            font=ctk.CTkFont(family="JetBrains Mono", size=10),
            text_color=self.colors["text_secondary"],
            justify="left"
        )
        self.session_stats.pack(pady=(0, 15), padx=15)
        
        # Update session stats
        self.update_session_stats()
        
    def create_footer(self):
        """Create the input footer"""
        footer_frame = ctk.CTkFrame(
            self.main_container,
            fg_color=self.colors["bg_secondary"],
            corner_radius=0,
            height=100
        )
        footer_frame.pack(fill="x", padx=0, pady=0)
        footer_frame.pack_propagate(False)
        
        # Input container
        input_container = ctk.CTkFrame(
            footer_frame,
            fg_color="transparent"
        )
        input_container.pack(fill="x", padx=20, pady=20)
        
        # Input field
        self.input_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="✨ Ask me anything or give me a command...",
            font=ctk.CTkFont(family="JetBrains Mono", size=14),
            fg_color=self.colors["bg_tertiary"],
            text_color=self.colors["text_primary"],
            placeholder_text_color=self.colors["text_muted"],
            border_color=self.colors["accent_gold"],
            border_width=2,
            corner_radius=25,
            height=40
        )
        self.input_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.input_entry.bind("<Return>", lambda e: self.process_input())
        self.input_entry.bind("<KeyRelease>", self.on_input_change)
        
        # Send button
        self.send_button = ctk.CTkButton(
            input_container,
            text="🚀 Send",
            font=ctk.CTkFont(family="JetBrains Mono", size=14, weight="bold"),
            fg_color=self.colors["accent_gold"],
            hover_color=self.colors["accent_gold_dark"],
            text_color=self.colors["bg_primary"],
            corner_radius=25,
            width=100,
            height=40,
            command=self.process_input
        )
        self.send_button.pack(side="right")
        
    def setup_chat_tags(self):
        """Setup custom tags for different message types"""
        # User messages
        self.chat_history.tag_config("user", 
                                    foreground=self.colors["accent_gold"])
        
        # Assistant messages
        self.chat_history.tag_config("assistant", 
                                    foreground=self.colors["text_primary"])
        
        # System messages
        self.chat_history.tag_config("system", 
                                    foreground=self.colors["text_muted"])
        
        # Success messages
        self.chat_history.tag_config("success", 
                                    foreground=self.colors["success"])
        
        # Error messages
        self.chat_history.tag_config("error", 
                                    foreground=self.colors["error"])
        
        # Warning messages
        self.chat_history.tag_config("warning", 
                                    foreground=self.colors["warning"])
        
    def display_message(self, message, tag="assistant", compact=False):
        """Display a message in the chat with optional compact formatting"""

        if compact:
            # Remove emojis from the message
            message = ''.join(char for char in message if char.isalnum() or char.isspace() or char in ",.!?<>/[]")

        if tag == "user":
            formatted_msg = f"You: {message}\n"
        else:
            formatted_msg = f"Assistant: {message}\n"

        self.chat_history.insert("end", formatted_msg)
        self.chat_history.see("end")
        
    def show_welcome_message(self):
        """Show a beautiful welcome message"""
        welcome_msg = f"""
🌟 Welcome to your AI Terminal Assistant! 🌟

🧠 AI Status: {"✅ Connected" if self.llm_connected else "❌ Offline"}
🖥️ System: {platform.system()} {platform.release()}

Ready to assist you! 🚀
"""
        self.display_message(welcome_msg, "system")
        
    def on_input_change(self, event):
        """Handle input changes for suggestions"""
        current_text = self.input_entry.get()
        if len(current_text) > 2:
            # Could implement real-time suggestions here
            pass
            
    def process_input(self):
        """Process user input with modern styling"""
        user_msg = self.input_entry.get().strip()
        if not user_msg:
            return
            
        # Display user message
        self.display_message(user_msg, "user")
        self.input_entry.delete(0, "end")
        
        # Handle confirmation flow
        if self.waiting_for_confirmation:
            if user_msg.strip().upper() == "I AGREE":
                self.display_message("⚡ Executing command...", "system")
                success, output = execute_enhanced_command(self.pending_command)
                
                if success:
                    self.display_message(f"✅ {output}", "success")
                else:
                    self.display_message(f"❌ {output}", "error")
                    
                self.waiting_for_confirmation = False
                self.pending_command = None
                self.pending_explanation = None
            else:
                self.display_message("Please type 'I AGREE' to proceed with the risky command.", "warning")
            return
            
        # Handle questions
        if question_handler.is_question(user_msg):
            response = question_handler.handle_question(user_msg)
            self.display_message(response['content'])
            # Remember the question and answer interaction
            remember_interaction(user_msg, response['content'], 'question')
            return
            
        # Get conversation context to enhance LLM processing
        context = get_context_for_query(user_msg)
        
        # Process with LLM
        self.display_message("🤔 Thinking...", "system")
        result = self.llm_parser.parse_command(user_msg)
        
        if not result['command']:
            # Display error message compactly
            error_response = f"{result['explanation']}"
            self.display_message(error_response, "error", compact=True)
            # Remember the failed interaction
            remember_interaction(user_msg, error_response, 'error')
            return

        command = result['command']
        explanation = result['explanation']
        start_time = time.time()

        if result['risky']:
            # For risky commands, use normal flow and messaging
            risk_msg = f"RISKY COMMAND DETECTED: {command}, {result['explanation']}"
            self.display_message(risk_msg, "warning")
            self.pending_command = command
            self.pending_explanation = explanation
            self.waiting_for_confirmation = True
            # Remember the risky command interaction
            remember_interaction(user_msg, risk_msg, 'risky_command')
        else:
            self.display_message(f"Executing command...")

            # Execute command
            success, output = execute_enhanced_command(command)
            execution_time = time.time() - start_time
            
            # Display result
            if success:
                success_response = f"✅ {output}"
                self.display_message(success_response, "success")
                # Remember successful command execution
                remember_interaction(user_msg, success_response, 'command_success')
            else:
                error_response = f"❌ {output}"
                self.display_message(error_response, "error")
                # Remember failed command execution
                remember_interaction(user_msg, error_response, 'command_error')
                
                # Try AI fallback if available
                if self.llm_connected:
                    self.display_message("🤖 Trying AI fallback...", "system")
                    # Fallback logic here
                    
            # Update session context
            update_session_context(command, success, output, execution_time)
            
        # Update session stats
        self.update_session_stats()
        
    # Quick action methods
    def show_background_processes(self):
        """Show system processes"""
        try:
            self.display_message("🔍 Getting system processes...", "system")
            
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
                    self.display_message("🖥️ Windows System Processes:", "system")
                    self.display_message("─" * 60, "system")
                    
                    lines = result.stdout.split('\n')
                    for line in lines[:30]:  # Show first 30 lines
                        if line.strip():
                            self.display_message(line)
                    
                    if len(lines) > 30:
                        self.display_message(f"... and {len(lines) - 30} more processes")
                else:
                    self.display_message(f"❌ PowerShell error: {result.stderr}", "error")
                    
            else:
                # Use ps aux for Linux/Unix
                result = subprocess.run(
                    ["ps", "aux"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    self.display_message("🐧 Linux System Processes:", "system")
                    self.display_message("─" * 60, "system")
                    
                    lines = result.stdout.split('\n')
                    for line in lines[:30]:  # Show first 30 lines
                        if line.strip():
                            self.display_message(line)
                    
                    if len(lines) > 30:
                        self.display_message(f"... and {len(lines) - 30} more processes")
                else:
                    self.display_message(f"❌ ps command error: {result.stderr}", "error")
                    
        except subprocess.TimeoutExpired:
            self.display_message("❌ Process listing timed out", "error")
        except Exception as e:
            self.display_message(f"❌ Error getting processes: {str(e)}", "error")
            import traceback
            self.display_message(f"Traceback: {traceback.format_exc()}", "error")
            
    def show_system_info(self):
        """Show comprehensive system information"""
        try:
            self.display_message("🔍 Gathering comprehensive system information...", "system")
            
            # Initialize SystemInfo
            sys_info = SystemInfo()
            
            # Get comprehensive system information
            comprehensive_info = sys_info.get_comprehensive_system_info()
            
            # Display basic system information
            basic_info = f"""
💻 System Overview

🖥️ Platform: {platform.system()} {platform.release()}
🏗️ Architecture: {platform.architecture()[0]}
📡 Hostname: {platform.node()}
"""
            self.display_message(basic_info)
            
            # Display power management information
            power_info = comprehensive_info.get('power_management', {})
            if power_info and not power_info.get('error'):
                battery = power_info.get('battery', {})
                power_consumption = power_info.get('power_consumption', {})
                
                power_msg = "🔋 Power Management\n"
                if battery:
                    power_msg += f"• Battery: {battery.get('name', 'Unknown')} ({battery.get('status', 'Unknown')})\n"
                    if battery.get('estimated_charge_remaining'):
                        power_msg += f"• Charge: {battery.get('estimated_charge_remaining')}%\n"
                
                if power_consumption:
                    power_msg += f"• CPU Usage: {power_consumption.get('cpu_usage', 'N/A')}%\n"
                    power_msg += f"• Memory Usage: {power_consumption.get('memory_usage', 'N/A')}%\n"
                    power_msg += f"• Disk Usage: {power_consumption.get('disk_usage', 'N/A')}%\n"
                
                self.display_message(power_msg)
            
            # Display peripheral devices
            peripherals = comprehensive_info.get('peripheral_devices', {})
            if peripherals and not peripherals.get('error'):
                peripheral_msg = "🔌 Connected Devices\n"
                
                usb_devices = peripherals.get('usb_devices', [])
                if usb_devices:
                    peripheral_msg += f"• USB Devices: {len(usb_devices)} connected\n"
                    for device in usb_devices[:3]:  # Show first 3
                        peripheral_msg += f"  - {device.get('description', 'Unknown')}\n"
                    if len(usb_devices) > 3:
                        peripheral_msg += f"  ... and {len(usb_devices) - 3} more\n"
                
                audio_devices = peripherals.get('audio_devices', [])
                if audio_devices:
                    peripheral_msg += f"• Audio Devices: {len(audio_devices)} detected\n"
                    for device in audio_devices[:2]:  # Show first 2
                        peripheral_msg += f"  - {device.get('name', 'Unknown')}\n"
                
                input_devices = peripherals.get('input_devices', [])
                if input_devices:
                    peripheral_msg += f"• Input Devices: {len(input_devices)} detected\n"
                
                self.display_message(peripheral_msg)
            
            # Display driver information
            drivers = comprehensive_info.get('active_drivers', {})
            if drivers and not drivers.get('error'):
                driver_summary = drivers.get('summary', {})
                driver_msg = f"""
🔧 System Drivers

• Total System Drivers: {driver_summary.get('total_system_drivers', 'N/A')}
• Running Drivers: {driver_summary.get('running_drivers', 'N/A')}
• Stopped Drivers: {driver_summary.get('stopped_drivers', 'N/A')}
• PnP Drivers: {driver_summary.get('total_pnp_drivers', 'N/A')}
"""
                self.display_message(driver_msg)
            
            # Display network information
            network = comprehensive_info.get('network_connectivity', {})
            if network and not network.get('error'):
                network_stats = network.get('network_statistics', {})
                interfaces = network.get('network_interfaces', [])
                active_connections = network.get('active_connections', [])
                
                network_msg = f"""
🌐 Network Information

• Network Interfaces: {len(interfaces)} detected
• Active Connections: {len(active_connections)}
• Bytes Sent: {network_stats.get('bytes_sent', 'N/A'):,}
• Bytes Received: {network_stats.get('bytes_recv', 'N/A'):,}
• Packets Sent: {network_stats.get('packets_sent', 'N/A'):,}
• Packets Received: {network_stats.get('packets_recv', 'N/A'):,}
"""
                self.display_message(network_msg)
            
            # Display firewall status
            firewall = comprehensive_info.get('firewall_status', {})
            if firewall and not firewall.get('error'):
                firewall_msg = f"""
🛡️ Security Status

• Firewall Status: {firewall.get('overall_status', 'Unknown')}
"""
                profiles = firewall.get('profiles', {})
                if profiles:
                    firewall_msg += "• Firewall Profiles:\n"
                    for profile_name, profile_data in profiles.items():
                        state = profile_data.get('state', 'Unknown')
                        firewall_msg += f"  - {profile_name}: {state}\n"
                
                defender = firewall.get('windows_defender', {})
                if defender and defender.get('antivirus_enabled') is not None:
                    av_status = "Enabled" if defender.get('antivirus_enabled') else "Disabled"
                    firewall_msg += f"• Windows Defender: {av_status}\n"
                
                self.display_message(firewall_msg)
            
            # Display temperature information
            temperatures = comprehensive_info.get('temperatures', {})
            if temperatures and not temperatures.get('error'):
                alerts = temperatures.get('alerts', [])
                cpu_temps = temperatures.get('cpu', [])
                system_temps = temperatures.get('system', [])
                
                temp_msg = "🌡️ System Temperatures\n\n"
                
                # Display CPU temperatures
                if cpu_temps:
                    temp_msg += "💻 CPU Sensors:\n"
                    for cpu_temp in cpu_temps:
                        label = cpu_temp.get('label', 'Unknown')
                        current = cpu_temp.get('current', 'N/A')
                        if current != 'N/A':
                            temp_msg += f"• {label}: {current}°C\n"
                        else:
                            temp_msg += f"• {label}: {current}\n"
                    temp_msg += "\n"
                
                # Display system temperatures
                if system_temps:
                    temp_msg += "🖥️ System Sensors:\n"
                    for sys_temp in system_temps:
                        label = sys_temp.get('label', 'Unknown')
                        current = sys_temp.get('current', 'N/A')
                        if current != 'N/A':
                            temp_msg += f"• {label}: {current}°C\n"
                        else:
                            temp_msg += f"• {label}: {current}\n"
                    temp_msg += "\n"
                
                # Display alerts if any
                if alerts:
                    temp_msg += f"⚠️ Temperature Alerts ({len(alerts)}):\n"
                    for alert in alerts[:3]:  # Show first 3 alerts
                        temp_msg += f"• {alert.get('sensor', 'Unknown')}: {alert.get('current', 'N/A')}°C ({alert.get('level', 'Unknown')})\n"
                
                # If no temperature data available
                if not cpu_temps and not system_temps:
                    temp_msg += "• No temperature sensors available\n"
                    if temperatures.get('info', {}).get('message'):
                        temp_msg += f"• {temperatures['info']['message']}\n"
                
                self.display_message(temp_msg)
            
            self.display_message("✅ System information gathered successfully!", "success")
            
        except Exception as e:
            self.display_message(f"❌ Error gathering system information: {str(e)}", "error")
            
            # Fallback to basic system info
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                fallback_msg = f"""
💻 Basic System Information (Fallback)

🖥️ Platform: {platform.system()} {platform.release()}
🏗️ Architecture: {platform.architecture()[0]}
💾 Memory: {memory.percent}% used ({memory.used // (1024**3):.1f}GB / {memory.total // (1024**3):.1f}GB)
🔥 CPU Usage: {cpu_percent}%
📡 Hostname: {platform.node()}
"""
                self.display_message(fallback_msg)
            except ImportError:
                self.display_message("❌ Install 'psutil' for basic system information")
            
    def start_interactive_mode(self):
        """Start interactive mode"""
        self.display_message("🎯 Interactive mode activated! Type commands for real-time execution.")
        
    def list_applications(self):
        """List installed applications"""
        from desktop_app_controller import list_installed_apps
        apps = list_installed_apps()
        
        if apps:
            msg = "📱 Installed Applications (showing first 15):\n"
            for app in apps[:15]:
                msg += f"• {app['name']} ({app['source']})\n"
            if len(apps) > 15:
                msg += f"... and {len(apps) - 15} more apps\n"
            self.display_message(msg)
        else:
            self.display_message("❌ No applications found")
            
    def show_session_details(self):
        """Show detailed session information"""
        try:
            summary = get_session_summary()
            details = f"""
📊 Session Details

🆔 Session ID: {summary['session_id']}
⏱️ Duration: {summary['duration']}
📁 Working Directory: {summary['working_directory']}
🔧 Commands Executed: {summary['commands_executed']}
🎯 Unique Commands: {summary['unique_commands']}

📈 Most Frequent Commands:
"""
            for cmd, count in list(summary['most_frequent_commands'].items())[:5]:
                details += f"• {cmd} ({count} times)\n"
                
            self.display_message(details)
        except Exception as e:
            self.display_message(f"❌ Error getting session details: {str(e)}", "error")
            
    def export_session(self):
        """Export session data"""
        try:
            summary = get_session_summary()
            filename = f"session_export_{summary['session_id']}.json"
            
            import json
            with open(filename, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
                
            self.display_message(f"📁 Session exported to: {filename}", "success")
        except Exception as e:
            self.display_message(f"❌ Export failed: {str(e)}", "error")
            
    def update_session_stats(self):
        """Update session statistics"""
        try:
            summary = get_session_summary()
            stats_text = f"""
⏱️ Duration: {summary['duration']}
🔧 Commands: {summary['commands_executed']}
🎯 Unique: {summary['unique_commands']}
📁 Directory: {os.path.basename(summary['working_directory'])}
"""
            self.session_stats.configure(text=stats_text)
        except Exception as e:
            self.session_stats.configure(text="❌ Error loading stats")
            
    def update_status(self):
        """Update status periodically"""
        self.update_session_stats()
        # Schedule next update
        self.app.after(10000, self.update_status)  # Update every 10 seconds
        
    def init_suggestion_system(self):
        """Initialize the AI suggestion system after UI creation"""
        try:
            # Initialize suggestion manager with the input widget
            self.suggestion_manager = SuggestionManager(
                parent=self.input_entry.master,
                entry_widget=self.input_entry,
                suggestion_engine=self.suggestion_engine,
                colors=self.colors  # Pass our color scheme
            )
            
            # Get conversation context for initial suggestions
            context = get_context_for_query("")
            
            # Update suggestion engine with current context
            if context:
                self.suggestion_engine.update_context(context)
                
        except Exception as e:
            print(f"Warning: Could not initialize suggestion system: {e}")
            # Continue without suggestions if initialization fails
            self.suggestion_manager = None
            
    def cleanup(self):
        """Cleanup resources when app closes"""
        try:
            if self.suggestion_manager:
                self.suggestion_manager.cleanup()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
        
    def run(self):
        """Run the application"""
        try:
            self.app.mainloop()
        finally:
            self.cleanup()

if __name__ == "__main__":
    app = ModernOSAssistantApp()
    app.run()
