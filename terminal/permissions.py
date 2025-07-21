risky_keywords = [
    "format", "rm", "rm -rf", "diskpart", "mkfs", "shutdown", "reg delete", "del", "kill"
]

def is_risky(command):
    return any(risk in command.lower() for risk in risky_keywords)
