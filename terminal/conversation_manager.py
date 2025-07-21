#!/usr/bin/env python3
"""
Conversation Manager - Advanced Memory & Context System
Makes the assistant remember everything and build intelligent context
"""

import json
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import threading
import time
from collections import defaultdict, Counter
import re

class ConversationManager:
    """Advanced conversation memory and context management system"""
    
    def __init__(self, db_path: str = "data/conversation_memory.db"):
        self.db_path = db_path
        self.session_id = self._generate_session_id()
        self.conversation_history = []
        self.user_profile = {}
        self.context_cache = {}
        self.patterns = {}
        self.preferences = {}
        self.relationships = {}
        
        # Initialize database
        self._init_database()
        
        # Load user profile
        self._load_user_profile()
        
        # Start background analysis
        self._start_background_analysis()
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hash_part = hashlib.md5(f"{timestamp}_{os.getpid()}".encode()).hexdigest()[:8]
        return f"session_{timestamp}_{hash_part}"
    
    def _init_database(self):
        """Initialize SQLite database for persistent memory"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    user_input TEXT NOT NULL,
                    assistant_response TEXT,
                    command_executed TEXT,
                    success BOOLEAN,
                    context_data TEXT,
                    sentiment TEXT,
                    intent TEXT,
                    entities TEXT,
                    follow_up_suggestions TEXT,
                    execution_time REAL,
                    error_message TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT,
                    confidence REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success_rate REAL DEFAULT 0.5
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity1 TEXT NOT NULL,
                    entity2 TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.5,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def _load_user_profile(self):
        """Load user profile from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT key, value, category, confidence FROM user_profile')
                for row in cursor.fetchall():
                    key, value, category, confidence = row
                    if category not in self.user_profile:
                        self.user_profile[category] = {}
                    
                    try:
                        # Try to parse JSON values
                        parsed_value = json.loads(value)
                        self.user_profile[category][key] = {
                            'value': parsed_value,
                            'confidence': confidence
                        }
                    except:
                        self.user_profile[category][key] = {
                            'value': value,
                            'confidence': confidence
                        }
        except Exception as e:
            print(f"Error loading user profile: {e}")
    
    def remember_interaction(self, user_input: str, assistant_response: str, 
                           command_executed: str = None, success: bool = True,
                           execution_time: float = 0.0, error_message: str = None):
        """Remember a complete interaction with full context"""
        
        # Analyze the interaction
        analysis = self._analyze_interaction(user_input, assistant_response, 
                                           command_executed, success)
        
        # Store in memory
        interaction = {
            'timestamp': datetime.now(),
            'user_input': user_input,
            'assistant_response': assistant_response,
            'command_executed': command_executed,
            'success': success,
            'execution_time': execution_time,
            'error_message': error_message,
            'analysis': analysis
        }
        
        self.conversation_history.append(interaction)
        
        # Store in database
        self._store_interaction_db(interaction)
        
        # Update user profile
        self._update_user_profile(analysis)
        
        # Learn patterns
        self._learn_patterns(interaction)
        
        # Update relationships
        self._update_relationships(analysis)
    
    def _analyze_interaction(self, user_input: str, assistant_response: str,
                           command_executed: str, success: bool) -> Dict[str, Any]:
        """Analyze interaction to extract insights"""
        
        analysis = {
            'intent': self._extract_intent(user_input),
            'entities': self._extract_entities(user_input),
            'sentiment': self._analyze_sentiment(user_input),
            'complexity': self._assess_complexity(user_input),
            'context_references': self._find_context_references(user_input),
            'follow_up_suggestions': self._generate_follow_up_suggestions(user_input, command_executed, success),
            'learning_opportunities': self._identify_learning_opportunities(user_input, success)
        }
        
        return analysis
    
    def _extract_intent(self, user_input: str) -> str:
        """Extract user intent from input"""
        user_lower = user_input.lower()
        
        # Intent patterns
        intent_patterns = {
            'file_management': ['file', 'folder', 'directory', 'create', 'delete', 'move', 'copy'],
            'system_info': ['system', 'info', 'cpu', 'memory', 'disk', 'performance'],
            'network': ['network', 'wifi', 'internet', 'connection', 'ping', 'ip'],
            'application': ['app', 'application', 'software', 'program', 'install', 'launch'],
            'question': ['what', 'how', 'why', 'when', 'where', 'explain', 'tell me'],
            'troubleshooting': ['error', 'problem', 'issue', 'fix', 'broken', 'not working'],
            'automation': ['automate', 'script', 'batch', 'schedule', 'recurring'],
            'learning': ['learn', 'tutorial', 'guide', 'help', 'teach', 'show me']
        }
        
        # Count matches for each intent
        intent_scores = {}
        for intent, keywords in intent_patterns.items():
            score = sum(1 for keyword in keywords if keyword in user_lower)
            if score > 0:
                intent_scores[intent] = score
        
        # Return highest scoring intent
        if intent_scores:
            return max(intent_scores, key=intent_scores.get)
        else:
            return 'general'
    
    def _extract_entities(self, user_input: str) -> List[Dict[str, str]]:
        """Extract entities from user input"""
        entities = []
        
        # File patterns
        file_patterns = [
            r'(\w+\.\w+)',  # filename.extension
            r'([A-Z]:\\[^\s]+)',  # Windows paths
            r'(/[^\s]+)',  # Unix paths
        ]
        
        # Number patterns
        number_patterns = [
            r'(\d+)\s*(gb|mb|kb|tb)',  # Storage sizes
            r'(\d+)\s*(hour|minute|second)s?',  # Time durations
            r'(\d+)\s*(%)',  # Percentages
        ]
        
        # Application patterns
        app_patterns = [
            r'(chrome|firefox|edge|safari)',
            r'(notepad|word|excel|powerpoint)',
            r'(python|node|java|git)',
        ]
        
        # Extract file entities
        for pattern in file_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'file', 'value': match})
        
        # Extract number entities
        for pattern in number_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'quantity', 'value': ' '.join(match)})
        
        # Extract app entities
        for pattern in app_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                entities.append({'type': 'application', 'value': match})
        
        return entities
    
    def _analyze_sentiment(self, user_input: str) -> str:
        """Analyze sentiment of user input"""
        user_lower = user_input.lower()
        
        positive_words = ['good', 'great', 'excellent', 'perfect', 'amazing', 'love', 'like', 'thanks', 'thank you']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'error', 'problem', 'issue', 'broken', 'failed']
        frustrated_words = ['frustrated', 'annoyed', 'confused', 'stuck', 'help', 'urgent', 'quickly']
        
        positive_score = sum(1 for word in positive_words if word in user_lower)
        negative_score = sum(1 for word in negative_words if word in user_lower)
        frustrated_score = sum(1 for word in frustrated_words if word in user_lower)
        
        if frustrated_score > 0:
            return 'frustrated'
        elif positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'
    
    def _assess_complexity(self, user_input: str) -> str:
        """Assess complexity level of user request"""
        # Count complexity indicators
        complexity_score = 0
        
        # Multiple steps
        if any(word in user_input.lower() for word in ['and', 'then', 'after', 'followed by']):
            complexity_score += 2
        
        # Conditional logic
        if any(word in user_input.lower() for word in ['if', 'when', 'unless', 'provided that']):
            complexity_score += 2
        
        # Technical terms
        technical_terms = ['api', 'database', 'server', 'configuration', 'environment', 'deployment']
        complexity_score += sum(1 for term in technical_terms if term in user_input.lower())
        
        # File paths or complex parameters
        if re.search(r'[/\\]|--?\w+|\w+\.\w+', user_input):
            complexity_score += 1
        
        if complexity_score >= 4:
            return 'high'
        elif complexity_score >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _find_context_references(self, user_input: str) -> List[str]:
        """Find references to previous context"""
        references = []
        
        # Pronoun references
        pronouns = ['it', 'that', 'this', 'them', 'those', 'these']
        for pronoun in pronouns:
            if pronoun in user_input.lower():
                references.append(f"pronoun:{pronoun}")
        
        # Temporal references
        temporal = ['previous', 'last', 'earlier', 'before', 'again', 'same']
        for temp in temporal:
            if temp in user_input.lower():
                references.append(f"temporal:{temp}")
        
        # Direct references to recent commands
        if len(self.conversation_history) > 0:
            recent_commands = [item.get('command_executed', '') for item in self.conversation_history[-5:]]
            for cmd in recent_commands:
                if cmd and any(word in user_input.lower() for word in cmd.split()[:2]):
                    references.append(f"command_reference:{cmd}")
        
        return references
    
    def _generate_follow_up_suggestions(self, user_input: str, command_executed: str, success: bool) -> List[str]:
        """Generate intelligent follow-up suggestions"""
        suggestions = []
        
        if not success:
            suggestions.append("Would you like me to try a different approach?")
            suggestions.append("Need help troubleshooting this issue?")
            return suggestions
        
        # Based on intent and command
        intent = self._extract_intent(user_input)
        
        if intent == 'file_management':
            suggestions.extend([
                "Would you like to set up automatic backups for these files?",
                "Should I show you the file properties?",
                "Want me to organize similar files?"
            ])
        
        elif intent == 'system_info':
            suggestions.extend([
                "Would you like me to monitor this continuously?",
                "Should I set up alerts for unusual activity?",
                "Want to see historical performance data?"
            ])
        
        elif intent == 'application':
            suggestions.extend([
                "Would you like me to create a shortcut for this?",
                "Should I check for updates?",
                "Want to customize the application settings?"
            ])
        
        elif intent == 'network':
            suggestions.extend([
                "Should I run a network diagnostic?",
                "Would you like me to monitor connection stability?",
                "Want to see detailed network statistics?"
            ])
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _identify_learning_opportunities(self, user_input: str, success: bool) -> List[str]:
        """Identify opportunities for the user to learn"""
        opportunities = []
        
        if not success:
            opportunities.append("Let me explain what went wrong and how to avoid it")
        
        # Check for advanced alternatives
        if 'simple' in user_input.lower() or 'basic' in user_input.lower():
            opportunities.append("I can show you more advanced techniques for this")
        
        # Check for automation opportunities
        if any(word in user_input.lower() for word in ['repeatedly', 'often', 'always', 'daily']):
            opportunities.append("This seems like something we could automate")
        
        # Check for efficiency improvements
        if any(word in user_input.lower() for word in ['slow', 'long', 'time-consuming']):
            opportunities.append("I can show you faster ways to do this")
        
        return opportunities
    
    def _update_user_profile(self, analysis: Dict[str, Any]):
        """Update user profile based on interaction analysis"""
        
        # Update preferences
        intent = analysis['intent']
        if intent not in self.preferences:
            self.preferences[intent] = 0
        self.preferences[intent] += 1
        
        # Update skill level indicators
        complexity = analysis['complexity']
        if 'skill_level' not in self.user_profile:
            self.user_profile['skill_level'] = {}
        
        if intent not in self.user_profile['skill_level']:
            self.user_profile['skill_level'][intent] = {'level': 'beginner', 'confidence': 0.5}
        
        # Adjust skill level based on complexity and success
        current_level = self.user_profile['skill_level'][intent]['level']
        if complexity == 'high' and current_level == 'beginner':
            self.user_profile['skill_level'][intent]['level'] = 'intermediate'
        elif complexity == 'high' and current_level == 'intermediate':
            self.user_profile['skill_level'][intent]['level'] = 'advanced'
        
        # Store in database
        self._store_profile_update('preferences', intent, self.preferences[intent])
        self._store_profile_update('skill_level', f"{intent}_level", 
                                 self.user_profile['skill_level'][intent]['level'])
    
    def _store_profile_update(self, category: str, key: str, value: Any):
        """Store profile update in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO user_profile (key, value, category, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (key, json.dumps(value), category, datetime.now()))
        except Exception as e:
            print(f"Error storing profile update: {e}")
    
    def _learn_patterns(self, interaction: Dict[str, Any]):
        """Learn patterns from interactions"""
        user_input = interaction['user_input']
        success = interaction['success']
        command = interaction.get('command_executed', '')
        
        # Learn command patterns
        if command:
            pattern_key = f"command_pattern:{command[:50]}"
            if pattern_key not in self.patterns:
                self.patterns[pattern_key] = {
                    'frequency': 0,
                    'success_rate': 0.0,
                    'contexts': []
                }
            
            self.patterns[pattern_key]['frequency'] += 1
            # Update success rate
            total_attempts = self.patterns[pattern_key]['frequency']
            current_successes = self.patterns[pattern_key]['success_rate'] * (total_attempts - 1)
            new_successes = current_successes + (1 if success else 0)
            self.patterns[pattern_key]['success_rate'] = new_successes / total_attempts
    
    def _update_relationships(self, analysis: Dict[str, Any]):
        """Update entity relationships"""
        entities = analysis['entities']
        intent = analysis['intent']
        
        # Build relationships between entities and intents
        for entity in entities:
            entity_value = entity['value']
            relationship_key = f"{intent}:{entity_value}"
            
            if relationship_key not in self.relationships:
                self.relationships[relationship_key] = {
                    'strength': 0.1,
                    'frequency': 0
                }
            
            self.relationships[relationship_key]['frequency'] += 1
            self.relationships[relationship_key]['strength'] = min(1.0, 
                self.relationships[relationship_key]['strength'] + 0.1)
    
    def _store_interaction_db(self, interaction: Dict[str, Any]):
        """Store interaction in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO conversations (
                        session_id, timestamp, user_input, assistant_response,
                        command_executed, success, context_data, sentiment,
                        intent, entities, follow_up_suggestions, execution_time, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.session_id,
                    interaction['timestamp'],
                    interaction['user_input'],
                    interaction['assistant_response'],
                    interaction.get('command_executed'),
                    interaction['success'],
                    json.dumps(interaction['analysis']),
                    interaction['analysis']['sentiment'],
                    interaction['analysis']['intent'],
                    json.dumps(interaction['analysis']['entities']),
                    json.dumps(interaction['analysis']['follow_up_suggestions']),
                    interaction['execution_time'],
                    interaction.get('error_message')
                ))
        except Exception as e:
            print(f"Error storing interaction: {e}")
    
    def get_context_for_query(self, query: str) -> Dict[str, Any]:
        """Get relevant context for a new query"""
        context = {
            'relevant_history': [],
            'user_preferences': {},
            'suggested_approach': None,
            'personalized_response': None,
            'follow_up_suggestions': [],
            'user_skill_level': 'beginner'
        }
        
        # Analyze current query
        current_analysis = self._analyze_interaction(query, "", "", True)
        current_intent = current_analysis['intent']
        
        # Get relevant history
        context['relevant_history'] = self._get_relevant_history(current_intent, query)
        
        # Get user preferences for this intent
        if current_intent in self.preferences:
            context['user_preferences'] = {
                'frequency': self.preferences[current_intent],
                'skill_level': self.user_profile.get('skill_level', {}).get(current_intent, {}).get('level', 'beginner')
            }
        
        # Get suggested approach based on patterns
        context['suggested_approach'] = self._get_suggested_approach(current_intent, query)
        
        # Personalize response
        context['personalized_response'] = self._get_personalized_response(current_analysis)
        
        # Generate contextual follow-up suggestions
        context['follow_up_suggestions'] = self._generate_contextual_suggestions(current_analysis)
        
        return context
    
    def _get_relevant_history(self, intent: str, query: str) -> List[Dict[str, Any]]:
        """Get relevant historical interactions"""
        relevant = []
        
        # Get recent interactions with same intent
        for interaction in reversed(self.conversation_history[-10:]):
            if interaction['analysis']['intent'] == intent:
                relevant.append({
                    'timestamp': interaction['timestamp'],
                    'user_input': interaction['user_input'],
                    'success': interaction['success'],
                    'command': interaction.get('command_executed', ''),
                    'similarity': self._calculate_similarity(query, interaction['user_input'])
                })
        
        # Sort by similarity and recency
        relevant.sort(key=lambda x: (x['similarity'], x['timestamp']), reverse=True)
        
        return relevant[:3]  # Return top 3 most relevant
    
    def _calculate_similarity(self, query1: str, query2: str) -> float:
        """Calculate similarity between two queries"""
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _get_suggested_approach(self, intent: str, query: str) -> Optional[str]:
        """Get suggested approach based on learned patterns"""
        
        # Find similar successful patterns
        successful_patterns = []
        for pattern_key, pattern_data in self.patterns.items():
            if pattern_data['success_rate'] > 0.7 and pattern_data['frequency'] >= 2:
                successful_patterns.append((pattern_key, pattern_data))
        
        if successful_patterns:
            # Sort by success rate and frequency
            successful_patterns.sort(key=lambda x: (x[1]['success_rate'], x[1]['frequency']), reverse=True)
            best_pattern = successful_patterns[0]
            return f"Based on your history, this approach has a {best_pattern[1]['success_rate']:.1%} success rate"
        
        return None
    
    def _get_personalized_response(self, analysis: Dict[str, Any]) -> str:
        """Generate personalized response based on user profile"""
        intent = analysis['intent']
        sentiment = analysis['sentiment']
        complexity = analysis['complexity']
        
        # Get user skill level
        skill_level = self.user_profile.get('skill_level', {}).get(intent, {}).get('level', 'beginner')
        
        # Personalize based on skill level
        if skill_level == 'beginner':
            if complexity == 'high':
                return "This looks like an advanced task. I'll break it down into simple steps for you."
            else:
                return "I'll guide you through this step by step."
        
        elif skill_level == 'intermediate':
            if complexity == 'low':
                return "This is straightforward for you. I'll provide a quick solution."
            else:
                return "I'll provide the solution with some advanced options you might find useful."
        
        elif skill_level == 'advanced':
            return "I'll provide the direct solution along with advanced alternatives and optimizations."
        
        # Handle sentiment
        if sentiment == 'frustrated':
            return "I can see this is frustrating. Let me help you resolve this quickly."
        elif sentiment == 'positive':
            return "Great! I'm happy to help you with this."
        
        return "I'm here to help you with this task."
    
    def _generate_contextual_suggestions(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate contextual suggestions based on analysis"""
        suggestions = []
        intent = analysis['intent']
        
        # Get user's common follow-up patterns
        if intent in self.preferences and self.preferences[intent] > 3:
            suggestions.append(f"You often work with {intent} tasks. Would you like me to set up a workflow?")
        
        # Suggest learning opportunities
        if intent in self.user_profile.get('skill_level', {}):
            skill_level = self.user_profile['skill_level'][intent]['level']
            if skill_level == 'beginner':
                suggestions.append(f"Want to learn more advanced {intent} techniques?")
        
        # Suggest automation
        if intent in self.preferences and self.preferences[intent] > 5:
            suggestions.append(f"You do {intent} tasks frequently. Should I help you automate this?")
        
        return suggestions
    
    def _start_background_analysis(self):
        """Start background analysis thread"""
        def analyze_periodically():
            while True:
                time.sleep(60)  # Analyze every minute
                self._analyze_usage_patterns()
        
        analysis_thread = threading.Thread(target=analyze_periodically, daemon=True)
        analysis_thread.start()
    
    def _analyze_usage_patterns(self):
        """Analyze usage patterns periodically"""
        if len(self.conversation_history) < 5:
            return
        
        # Analyze recent patterns
        recent_intents = [item['analysis']['intent'] for item in self.conversation_history[-10:]]
        intent_counts = Counter(recent_intents)
        
        # Update preferences
        for intent, count in intent_counts.items():
            if intent not in self.preferences:
                self.preferences[intent] = 0
            self.preferences[intent] += count
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get comprehensive conversation summary"""
        if not self.conversation_history:
            return {'message': 'No conversations yet'}
        
        total_interactions = len(self.conversation_history)
        successful_interactions = sum(1 for item in self.conversation_history if item['success'])
        
        # Most common intents
        intents = [item['analysis']['intent'] for item in self.conversation_history]
        intent_counts = Counter(intents)
        
        # Average execution time
        execution_times = [item['execution_time'] for item in self.conversation_history if item['execution_time'] > 0]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        
        return {
            'session_id': self.session_id,
            'total_interactions': total_interactions,
            'success_rate': successful_interactions / total_interactions if total_interactions > 0 else 0,
            'most_common_intents': dict(intent_counts.most_common(5)),
            'average_execution_time': avg_execution_time,
            'user_preferences': self.preferences,
            'skill_levels': self.user_profile.get('skill_level', {}),
            'conversation_start': self.conversation_history[0]['timestamp'] if self.conversation_history else None,
            'last_interaction': self.conversation_history[-1]['timestamp'] if self.conversation_history else None
        }
    
    def get_personalized_greeting(self) -> str:
        """Get personalized greeting based on user profile"""
        if not self.conversation_history:
            return "👋 Hello! I'm your AI assistant. I'm here to learn about you and help you more effectively over time."
        
        # Analyze user's most common activity
        recent_intents = [item['analysis']['intent'] for item in self.conversation_history[-5:]]
        if recent_intents:
            most_common = Counter(recent_intents).most_common(1)[0][0]
            return f"👋 Welcome back! I see you often work with {most_common} tasks. How can I help you today?"
        
        return "👋 Welcome back! How can I assist you today?"
    
    def get_recent_commands(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commands for AI suggestion engine"""
        recent_commands = []
        
        # Get recent interactions that had successful commands
        for interaction in reversed(self.conversation_history[-limit:]):
            if interaction.get('command_executed') and interaction.get('success'):
                recent_commands.append({
                    'command': interaction['command_executed'],
                    'user_input': interaction['user_input'],
                    'timestamp': interaction['timestamp'],
                    'intent': interaction['analysis']['intent'],
                    'success': interaction['success'],
                    'execution_time': interaction['execution_time']
                })
        
        # Also try to get from database for persistence across sessions
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT command_executed, user_input, timestamp, intent, success, execution_time
                    FROM conversations 
                    WHERE command_executed IS NOT NULL AND success = 1
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
                
                db_commands = []
                for row in cursor.fetchall():
                    cmd, user_input, timestamp, intent, success, exec_time = row
                    db_commands.append({
                        'command': cmd,
                        'user_input': user_input,
                        'timestamp': timestamp,
                        'intent': intent,
                        'success': bool(success),
                        'execution_time': exec_time or 0.0
                    })
                
                # Merge with recent commands, avoiding duplicates
                command_texts = {cmd['command'] for cmd in recent_commands}
                for db_cmd in db_commands:
                    if db_cmd['command'] not in command_texts:
                        recent_commands.append(db_cmd)
                        if len(recent_commands) >= limit:
                            break
        
        except Exception as e:
            print(f"Error retrieving recent commands from database: {e}")
        
        return recent_commands[:limit]
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old conversation data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('DELETE FROM conversations WHERE timestamp < ?', (cutoff_date,))
                print(f"Cleaned up conversations older than {days_to_keep} days")
        except Exception as e:
            print(f"Error cleaning up old data: {e}")

# Global instance
conversation_manager = ConversationManager()

# Convenience functions
def remember_interaction(user_input: str, assistant_response: str, 
                        command_executed: str = None, success: bool = True,
                        execution_time: float = 0.0, error_message: str = None):
    """Remember an interaction"""
    return conversation_manager.remember_interaction(
        user_input, assistant_response, command_executed, 
        success, execution_time, error_message
    )

def get_context_for_query(query: str) -> Dict[str, Any]:
    """Get context for a query"""
    return conversation_manager.get_context_for_query(query)

def get_conversation_summary() -> Dict[str, Any]:
    """Get conversation summary"""
    return conversation_manager.get_conversation_summary()

def get_personalized_greeting() -> str:
    """Get personalized greeting"""
    return conversation_manager.get_personalized_greeting()

def get_recent_commands(limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent commands for AI suggestion engine"""
    return conversation_manager.get_recent_commands(limit)

# Example usage
if __name__ == "__main__":
    print("🧠 Conversation Manager Test")
    print("=" * 50)
    
    # Test interaction memory
    remember_interaction(
        "show me system information",
        "Here's your system information...",
        "systeminfo",
        True,
        2.5
    )
    
    # Test context retrieval
    context = get_context_for_query("check cpu usage")
    print(f"Context for 'check cpu usage': {context}")
    
    # Test personalized greeting
    greeting = get_personalized_greeting()
    print(f"Personalized greeting: {greeting}")
    
    # Test conversation summary
    summary = get_conversation_summary()
    print(f"Conversation summary: {summary}")
