# Configuration settings for the Waifu OS Assistant

# OpenAI API Configuration
OPENAI_API_KEY = "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"
# Google Gemini API Configuration
GEMINI_API_KEY = "AIzaSyC7hOpnmO5nQ8Pbg8WCmUNNUKv_2hU7vRY"

# LLM Provider Configuration
LLM_PROVIDER = "gemini"  # Options: openai, gemini
LLM_MODEL = "gemini-1.5-flash"  # Options: gpt-3.5-turbo, gpt-4, gemini-1.5-flash
LLM_TEMPERATURE = 0.1  # Lower = more deterministic, Higher = more creative
LLM_MAX_TOKENS = 500

# Application Settings
APP_TITLE = "Waifu OS Assistant - AI Enhanced"
APP_GEOMETRY = "700x500"  # Slightly larger for better UX
THEME = "dark"

# Safety Settings
REQUIRE_CONFIRMATION_FOR_RISKY = True
LOG_ALL_COMMANDS = True
