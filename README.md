# 🤖 AI Terminal Assistant

Welcome to the AI Terminal Assistant! This innovative command-line tool is designed to make your life easier by transforming your natural language inputs into executable system commands in real-time. Whether you're managing files, exploring system information, or controlling applications, this assistant has you covered.

## 📜 Features

### 🧠 AI-Powered Command Processing
- **Natural Language to Command Conversion**: Seamlessly convert your everyday language into precise terminal commands with the power of OpenAI and Google Gemini APIs.
- **Context-Aware Suggestions**: Enjoy intelligent command suggestions that remember your history and current context.
- **Dynamic Risk Assessment**: Safeguard your operations with smart risk evaluation.

### 💻 Advanced System Operations
- **500+ Command Database**: Explore a wide range of operations across categories like file management, networking, and security.
- **Cross-Platform**: Compatible with Windows, Linux, and macOS, ensuring consistent performance wherever you work.
- **Background Process Management**: Handle your long-running tasks effortlessly.

### 🚀 User-Friendly Interface
- **Modern Design**: Experience a sleek, dark-themed UI with glassmorphism effects and a responsive layout for any device.
- **Interactive Multi-Tab Layout**: Access commands, sessions, interactive modes, and system info effortlessly.
- **Real-Time Monitoring**: Keep an eye on system performance with live updates.

## 📂 Project Structure

Here's how everything is organized:
terminal/
*     ├── main.py                           # Launch the main application
*     ├── main_modern.py                    # Alternative interface
*     ├── enhanced_llm_parser.py            # Command parsing with AI
*     ├── enhanced_command_executor.py      # Command execution logic
*     ├── conversation_manager.py           # Handles memory and user context
*     ├── command_session.py                # Session management
*     ├── ai_suggestion_engine.py           # Real-time AI suggestions
*     ├── desktop_app_controller.py         # Control installed applications
*     ├── web_browser_controller.py         # Manage web browsers
*     ├── system_info.py                    # Get detailed system info
*     ├── advanced_commands.py              # Comprehensive command library
*     ├── question_handler.py               # Answer system-related questions
*     ├── config/
*     │   ├── settings.py                   # Key settings and configurations
*     ├── data/
*     │   ├── context.db                    # Stores session context information
*     └── logs/
*     └── command_history.log           # Records command history *

## 🔧 Setup & Installation

### Prerequisites
- **Python 3.8+**: Make sure it's installed on your system.
- **API Keys**: Register for OpenAI and Google Gemini.

### Installation Steps
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ai-terminal-assistant.git
   cd ai-terminal-assistant
2. Install Dependencies:
   pip install customtkinter psutil wmi openai google-generativeai
3. Configure API Keys:
   Edit the file config/settings.py and add your API keys:
   GEMINI_API_KEY = "your-gemini-api-key"
4. Launch the Application:
   Run your preferred interface:
   python main_modern.py  # For modern UI
   python main.py         # For tabbed interface
