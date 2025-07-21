#!/usr/bin/env python3
"""
Real-time Suggestion UI Component
Provides a modern, interactive suggestion dropdown for the terminal
"""

import customtkinter as ctk
from typing import List, Dict, Callable, Optional
import threading
import time

class SuggestionUI:
    def __init__(self, parent_frame, entry_widget, suggestion_callback: Optional[Callable] = None):
        self.parent_frame = parent_frame
        self.entry_widget = entry_widget
        self.suggestion_callback = suggestion_callback
        
        # UI State
        self.is_visible = False
        self.selected_index = -1
        self.current_suggestions = []
        self.suggestion_widgets = []
        
        # Create suggestion container
        self.suggestion_frame = None
        self.suggestion_scrollable = None
        
        # Styling
        self.colors = {
            'bg': "#2B2B2B",
            'hover': "#3A3A3A",
            'selected': "#404040",
            'text': "#FFFFFF",
            'secondary_text': "#CCCCCC",
            'border': "#555555",
            'command': "#66D9EF",
            'recent': "#A6E22E",
            'ai': "#F92672",
            'natural': "#FD971F",
            'context': "#AE81FF"
        }
        
        # Animation
        self.animation_frame = None
        self.fade_alpha = 0.0
        self.target_alpha = 0.0
        
        # Setup key bindings
        self.setup_key_bindings()
        
    def setup_key_bindings(self):
        """Setup keyboard navigation for suggestions"""
        self.entry_widget.bind('<KeyPress>', self.on_key_press)
        self.entry_widget.bind('<KeyRelease>', self.on_key_release)
        self.entry_widget.bind('<FocusOut>', self.on_focus_out)
        
    def on_key_press(self, event):
        """Handle key press events for navigation"""
        if not self.is_visible:
            return
            
        key = event.keysym
        
        if key == 'Down':
            self.select_next()
            return 'break'
        elif key == 'Up':
            self.select_previous()
            return 'break'
        elif key == 'Return' or key == 'Tab':
            if self.selected_index >= 0:
                self.apply_suggestion()
                return 'break'
        elif key == 'Escape':
            self.hide_suggestions()
            return 'break'
            
    def on_key_release(self, event):
        """Handle key release events"""
        # Don't trigger on navigation keys
        if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Escape']:
            return
            
        # Reset selection when typing
        if event.keysym not in ['Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R']:
            self.selected_index = -1
            
    def on_focus_out(self, event):
        """Handle focus loss"""
        # Delay hiding to allow for suggestion clicks
        self.parent_frame.after(100, self.hide_suggestions)
        
    def show_suggestions(self, suggestions: List[Dict]):
        """Show suggestion dropdown with given suggestions"""
        if not suggestions:
            self.hide_suggestions()
            return
            
        self.current_suggestions = suggestions
        self.selected_index = -1
        
        # Create suggestion frame if needed
        if not self.suggestion_frame:
            self.create_suggestion_frame()
            
        # Clear existing widgets
        self.clear_suggestion_widgets()
        
        # Create suggestion widgets
        self.create_suggestion_widgets()
        
        # Position and show
        self.position_suggestions()
        self.is_visible = True
        self.animate_in()
        
    def hide_suggestions(self):
        """Hide suggestion dropdown"""
        if not self.is_visible:
            return
            
        self.is_visible = False
        self.animate_out()
        
    def create_suggestion_frame(self):
        """Create the main suggestion container"""
        # Create frame positioned relative to entry
        self.suggestion_frame = ctk.CTkFrame(
            self.parent_frame,
            fg_color=self.colors['bg'],
            border_width=1,
            border_color=self.colors['border'],
            corner_radius=8
        )
        
        # Create scrollable frame for suggestions
        self.suggestion_scrollable = ctk.CTkScrollableFrame(
            self.suggestion_frame,
            width=400,
            height=250,
            fg_color="transparent",
            scrollbar_fg_color=self.colors['bg'],
            scrollbar_button_color=self.colors['border'],
            scrollbar_button_hover_color=self.colors['hover']
        )
        self.suggestion_scrollable.pack(fill="both", expand=True, padx=2, pady=2)
        
    def create_suggestion_widgets(self):
        """Create individual suggestion widgets"""
        self.suggestion_widgets = []
        
        for i, suggestion in enumerate(self.current_suggestions):
            # Create suggestion item frame
            item_frame = ctk.CTkFrame(
                self.suggestion_scrollable,
                fg_color="transparent",
                hover_color=self.colors['hover'],
                corner_radius=6,
                height=50
            )
            item_frame.pack(fill="x", padx=2, pady=1)
            
            # Create content frame
            content_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=8, pady=4)
            
            # Type indicator
            type_color = self.get_type_color(suggestion['type'])
            type_label = ctk.CTkLabel(
                content_frame,
                text=self.get_type_icon(suggestion['type']),
                text_color=type_color,
                font=("Consolas", 14, "bold"),
                width=20
            )
            type_label.pack(side="left", padx=(0, 8))
            
            # Command text
            command_label = ctk.CTkLabel(
                content_frame,
                text=suggestion['command'],
                text_color=self.colors['command'],
                font=("Consolas", 12, "bold"),
                anchor="w"
            )
            command_label.pack(side="left", fill="x", expand=True)
            
            # Confidence indicator
            confidence = suggestion.get('confidence', 0.5)
            confidence_text = f"{int(confidence * 100)}%"
            confidence_label = ctk.CTkLabel(
                content_frame,
                text=confidence_text,
                text_color=self.colors['secondary_text'],
                font=("Consolas", 10),
                width=40
            )
            confidence_label.pack(side="right", padx=(8, 0))
            
            # Description
            description_label = ctk.CTkLabel(
                content_frame,
                text=suggestion['description'],
                text_color=self.colors['secondary_text'],
                font=("Consolas", 10),
                anchor="w"
            )
            description_label.pack(side="bottom", fill="x", pady=(2, 0))
            
            # Bind click event
            self.bind_click_events(item_frame, i)
            
            # Store reference
            self.suggestion_widgets.append({
                'frame': item_frame,
                'content': content_frame,
                'suggestion': suggestion,
                'index': i
            })
            
    def bind_click_events(self, widget, index):
        """Bind click events to suggestion widgets"""
        def on_click(event):
            self.selected_index = index
            self.apply_suggestion()
            
        def on_enter(event):
            if self.selected_index != index:
                self.update_selection(index)
                
        widget.bind("<Button-1>", on_click)
        widget.bind("<Enter>", on_enter)
        
        # Bind to all child widgets too
        for child in widget.winfo_children():
            child.bind("<Button-1>", on_click)
            child.bind("<Enter>", on_enter)
            
    def get_type_color(self, suggestion_type: str) -> str:
        """Get color for suggestion type"""
        type_colors = {
            'command': self.colors['command'],
            'command_fuzzy': self.colors['command'],
            'recent': self.colors['recent'],
            'ai_powered': self.colors['ai'],
            'natural_language': self.colors['natural'],
            'context_git': self.colors['context']
        }
        return type_colors.get(suggestion_type, self.colors['text'])
        
    def get_type_icon(self, suggestion_type: str) -> str:
        """Get icon for suggestion type"""
        type_icons = {
            'command': '⚡',
            'command_fuzzy': '🔍',
            'recent': '🕐',
            'ai_powered': '🤖',
            'natural_language': '💬',
            'context_git': '🔗'
        }
        return type_icons.get(suggestion_type, '•')
        
    def position_suggestions(self):
        """Position suggestion dropdown relative to entry widget"""
        if not self.suggestion_frame:
            return
            
        # Get entry widget position
        entry_x = self.entry_widget.winfo_x()
        entry_y = self.entry_widget.winfo_y()
        entry_height = self.entry_widget.winfo_height()
        entry_width = self.entry_widget.winfo_width()
        
        # Calculate position
        x = entry_x
        y = entry_y + entry_height + 2
        
        # Ensure it fits on screen
        parent_width = self.parent_frame.winfo_width()
        parent_height = self.parent_frame.winfo_height()
        
        # Adjust if too close to right edge
        if x + 400 > parent_width:
            x = parent_width - 400
            
        # Adjust if too close to bottom edge
        if y + 250 > parent_height:
            y = entry_y - 250 - 2
            
        # Position the frame
        self.suggestion_frame.place(x=x, y=y, width=400, height=250)
        
    def clear_suggestion_widgets(self):
        """Clear existing suggestion widgets"""
        for widget_data in self.suggestion_widgets:
            widget_data['frame'].destroy()
        self.suggestion_widgets.clear()
        
    def select_next(self):
        """Select next suggestion"""
        if not self.current_suggestions:
            return
            
        self.selected_index = (self.selected_index + 1) % len(self.current_suggestions)
        self.update_selection(self.selected_index)
        
    def select_previous(self):
        """Select previous suggestion"""
        if not self.current_suggestions:
            return
            
        self.selected_index = (self.selected_index - 1) % len(self.current_suggestions)
        self.update_selection(self.selected_index)
        
    def update_selection(self, index: int):
        """Update visual selection"""
        self.selected_index = index
        
        # Update widget appearances
        for i, widget_data in enumerate(self.suggestion_widgets):
            if i == index:
                widget_data['frame'].configure(fg_color=self.colors['selected'])
            else:
                widget_data['frame'].configure(fg_color="transparent")
                
        # Scroll to selected item
        if index >= 0 and index < len(self.suggestion_widgets):
            selected_widget = self.suggestion_widgets[index]['frame']
            self.suggestion_scrollable._parent_canvas.yview_moveto(
                index / len(self.suggestion_widgets)
            )
            
    def apply_suggestion(self):
        """Apply the selected suggestion"""
        if self.selected_index < 0 or self.selected_index >= len(self.current_suggestions):
            return
            
        suggestion = self.current_suggestions[self.selected_index]
        command = suggestion['command']
        
        # Set command in entry widget
        self.entry_widget.delete(0, "end")
        self.entry_widget.insert(0, command)
        
        # Hide suggestions
        self.hide_suggestions()
        
        # Call callback if provided
        if self.suggestion_callback:
            self.suggestion_callback(suggestion)
            
    def animate_in(self):
        """Animate suggestion dropdown in"""
        if not self.suggestion_frame:
            return
            
        self.target_alpha = 1.0
        self.fade_alpha = 0.0
        self.suggestion_frame.lift()
        self.animate_fade()
        
    def animate_out(self):
        """Animate suggestion dropdown out"""
        if not self.suggestion_frame:
            return
            
        self.target_alpha = 0.0
        self.animate_fade()
        
    def animate_fade(self):
        """Animate fade effect"""
        if not self.suggestion_frame:
            return
            
        # Simple fade animation
        alpha_step = 0.1
        if self.fade_alpha < self.target_alpha:
            self.fade_alpha = min(self.fade_alpha + alpha_step, self.target_alpha)
        elif self.fade_alpha > self.target_alpha:
            self.fade_alpha = max(self.fade_alpha - alpha_step, self.target_alpha)
            
        # Apply alpha (simulate with positioning)
        if self.fade_alpha > 0:
            self.suggestion_frame.tkraise()
        else:
            self.suggestion_frame.place_forget()
            
        # Continue animation if needed
        if self.fade_alpha != self.target_alpha:
            self.animation_frame = self.parent_frame.after(50, self.animate_fade)
            
    def update_suggestions(self, suggestions: List[Dict]):
        """Update suggestions without hiding/showing"""
        if self.is_visible:
            self.show_suggestions(suggestions)
        else:
            self.current_suggestions = suggestions
            
    def is_suggestion_visible(self) -> bool:
        """Check if suggestions are currently visible"""
        return self.is_visible
        
    def get_selected_suggestion(self) -> Optional[Dict]:
        """Get currently selected suggestion"""
        if 0 <= self.selected_index < len(self.current_suggestions):
            return self.current_suggestions[self.selected_index]
        return None
        
    def destroy(self):
        """Clean up resources"""
        if self.animation_frame:
            self.parent_frame.after_cancel(self.animation_frame)
            
        if self.suggestion_frame:
            self.suggestion_frame.destroy()
            
        self.suggestion_widgets.clear()
        self.current_suggestions.clear()


class SuggestionManager:
    """Manages the integration between suggestion engine and UI"""
    
    def __init__(self, parent_frame, entry_widget, suggestion_engine):
        self.parent_frame = parent_frame
        self.entry_widget = entry_widget
        self.suggestion_engine = suggestion_engine
        
        # Create UI
        self.ui = SuggestionUI(parent_frame, entry_widget, self.on_suggestion_selected)
        
        # Setup suggestion engine callback
        self.suggestion_engine.set_suggestion_callback(self.on_suggestions_received)
        
        # Bind entry events
        self.entry_widget.bind('<KeyRelease>', self.on_input_change)
        
        # State
        self.last_input = ""
        self.input_timer = None
        
    def on_input_change(self, event):
        """Handle input changes"""
        current_input = self.entry_widget.get()
        
        # Ignore navigation keys
        if event.keysym in ['Up', 'Down', 'Return', 'Tab', 'Escape']:
            return
            
        # Check if input actually changed
        if current_input == self.last_input:
            return
            
        self.last_input = current_input
        
        # Cancel previous timer
        if self.input_timer:
            self.parent_frame.after_cancel(self.input_timer)
            
        # Start new timer
        if current_input and len(current_input) >= 2:
            self.input_timer = self.parent_frame.after(
                300, lambda: self.request_suggestions(current_input)
            )
        else:
            self.ui.hide_suggestions()
            
    def request_suggestions(self, user_input: str):
        """Request suggestions from the engine"""
        # Get context (you might want to pass actual context here)
        context = {
            'current_directory': '.',  # Replace with actual current directory
            'timestamp': time.time()
        }
        
        # Get suggestions asynchronously
        self.suggestion_engine.get_suggestions_async(user_input, context)
        
    def on_suggestions_received(self, suggestions: List[Dict]):
        """Handle suggestions received from engine"""
        # Update UI on main thread
        self.parent_frame.after(0, lambda: self.ui.show_suggestions(suggestions))
        
    def on_suggestion_selected(self, suggestion: Dict):
        """Handle suggestion selection"""
        # You can add logging or other actions here
        print(f"Selected suggestion: {suggestion['command']} ({suggestion['type']})")
        
    def hide_suggestions(self):
        """Hide suggestions"""
        self.ui.hide_suggestions()
        
    def show_suggestions_for_input(self, user_input: str):
        """Show suggestions for specific input"""
        context = {
            'current_directory': '.',
            'timestamp': time.time()
        }
        
        suggestions = self.suggestion_engine.get_suggestions(user_input, context)
        self.ui.show_suggestions(suggestions)
        
    def destroy(self):
        """Clean up resources"""
        if self.input_timer:
            self.parent_frame.after_cancel(self.input_timer)
            
        self.ui.destroy()
