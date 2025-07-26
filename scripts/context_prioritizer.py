"""
Context Prioritizer for Smart Context Selection
Implements intelligent scoring and selection algorithms to prioritize the most relevant context in prompts.
"""

import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import math

class ContextPrioritizer:
    """Intelligent context scoring and selection for optimal prompt building."""
    
    def __init__(self):
        # Weight configuration for different relevance factors
        self.relevance_weights = {
            'recency': 0.3,      # How recent the interaction was
            'satisfaction': 0.4,  # User satisfaction with the interaction
            'similarity': 0.2,    # Content similarity to current request
            'importance': 0.1     # General importance of the interaction type
        }
        
        # Importance scores for different message types
        self.message_type_importance = {
            'post_approval': 1.0,      # High importance - successful outcomes
            'post_regeneration': 0.7,  # Medium importance - learning from feedback
            'file_upload': 0.8,        # High importance - source material
            'tone_selection': 0.6,     # Medium importance - user preferences
            'feedback': 0.9,           # High importance - direct user input
            'text': 0.5,               # Medium importance - general interaction
            'button_click': 0.4,       # Lower importance - UI interaction
            'unknown': 0.3             # Default for unknown types
        }
        
        # Content similarity keywords for different request types
        self.request_type_keywords = {
            'post_generation': ['generate', 'create', 'post', 'content', 'write'],
            'tone_change': ['tone', 'style', 'voice', 'approach', 'mood'],
            'regeneration': ['regenerate', 'redo', 'change', 'different', 'again'],
            'followup': ['follow', 'continue', 'series', 'next', 'additional'],
            'editing': ['edit', 'modify', 'adjust', 'tweak', 'improve']
        }
    
    def score_context_relevance(self, context_item: Dict, current_request: Dict) -> float:
        """
        Score the relevance of a context item for the current request.
        
        Args:
            context_item: Chat history entry to score
            current_request: Current request being processed
            
        Returns:
            Relevance score between 0.0 and 1.0
        """
        score = 0.0
        
        # Recency scoring
        recency_score = self._calculate_recency_score(context_item['timestamp'])
        score += recency_score * self.relevance_weights['recency']
        
        # Satisfaction scoring
        satisfaction_score = context_item.get('satisfaction_score', 0.5)
        if satisfaction_score is None:
            satisfaction_score = 0.5
        score += satisfaction_score * self.relevance_weights['satisfaction']
        
        # Similarity scoring
        similarity_score = self._calculate_similarity_score(context_item, current_request)
        score += similarity_score * self.relevance_weights['similarity']
        
        # Importance scoring
        importance_score = self._calculate_importance_score(context_item)
        score += importance_score * self.relevance_weights['importance']
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_recency_score(self, timestamp: str) -> float:
        """Calculate recency score based on timestamp."""
        try:
            item_time = datetime.fromisoformat(timestamp)
            time_diff = datetime.now() - item_time
            
            # Exponential decay: more recent items get higher scores
            # 1 hour = 0.95, 1 day = 0.6, 1 week = 0.1
            hours_diff = time_diff.total_seconds() / 3600
            recency_score = math.exp(-hours_diff / 24)  # 24-hour half-life
            
            return max(recency_score, 0.1)  # Minimum score of 0.1
            
        except (ValueError, TypeError):
            return 0.5  # Default score for invalid timestamps
    
    def _calculate_similarity_score(self, context_item: Dict, current_request: Dict) -> float:
        """Calculate content similarity score."""
        try:
            # Extract text content for comparison
            context_text = self._extract_text_content(context_item)
            request_text = self._extract_text_content(current_request)
            
            if not context_text or not request_text:
                return 0.5
            
            # Calculate keyword overlap
            context_words = set(re.findall(r'\b\w+\b', context_text.lower()))
            request_words = set(re.findall(r'\b\w+\b', request_text.lower()))
            
            if not context_words or not request_words:
                return 0.5
            
            # Jaccard similarity
            intersection = len(context_words.intersection(request_words))
            union = len(context_words.union(request_words))
            
            if union == 0:
                return 0.5
            
            similarity = intersection / union
            
            # Boost similarity for matching request types
            request_type = current_request.get('type', '')
            if request_type in self.request_type_keywords:
                keywords = self.request_type_keywords[request_type]
                keyword_matches = sum(1 for keyword in keywords if keyword in context_text.lower())
                if keyword_matches > 0:
                    similarity += 0.2  # Boost for keyword matches
            
            return min(similarity, 1.0)
            
        except Exception:
            return 0.5
    
    def _calculate_importance_score(self, context_item: Dict) -> float:
        """Calculate importance score based on message type and content."""
        message_type = context_item.get('message_type', 'unknown')
        base_importance = self.message_type_importance.get(message_type, 0.3)
        
        # Boost importance for interactions with high satisfaction
        satisfaction = context_item.get('satisfaction_score', 0.5)
        if satisfaction is None:
            satisfaction = 0.5
        if satisfaction > 0.8:
            base_importance += 0.2
        elif satisfaction < 0.3:
            base_importance -= 0.1
        
        # Boost importance for interactions with rich context
        context = context_item.get('context', {})
        if context and len(str(context)) > 50:
            base_importance += 0.1
        
        return min(max(base_importance, 0.1), 1.0)
    
    def _extract_text_content(self, item: Dict) -> str:
        """Extract text content from context item or request."""
        text_parts = []
        
        # Extract from various text fields
        for field in ['user_message', 'bot_response', 'content', 'feedback', 'reason']:
            if field in item and item[field]:
                text_parts.append(str(item[field]))
        
        # Extract from context dictionary
        context = item.get('context', {})
        if isinstance(context, dict):
            for key, value in context.items():
                if isinstance(value, str):
                    text_parts.append(value)
        
        return ' '.join(text_parts)
    
    def select_optimal_context(self, session: Dict, current_request: Dict, max_tokens: int = 2000) -> str:
        """
        Select the most relevant context for the current request.
        
        Args:
            session: User session with chat history
            current_request: Current request being processed
            max_tokens: Maximum tokens allowed for context
            
        Returns:
            Formatted context string for AI prompts
        """
        context_items = session.get('chat_history', [])
        
        if not context_items:
            return ""
        
        # Score all context items
        scored_items = [
            (item, self.score_context_relevance(item, current_request))
            for item in context_items
        ]
        
        # Sort by relevance score (highest first)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Select context within token limits
        selected_context = []
        current_tokens = 0
        
        for item, score in scored_items:
            item_tokens = self._estimate_tokens(str(item))
            if current_tokens + item_tokens <= max_tokens:
                selected_context.append(item)
                current_tokens += item_tokens
            else:
                break
        
        return self._format_context_for_prompt(selected_context, current_request)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _format_context_for_prompt(self, context_items: List[Dict], current_request: Dict) -> str:
        """Format selected context items for AI prompt inclusion."""
        if not context_items:
            return ""
        
        context_parts = ["## Previous Interactions Context"]
        
        for i, item in enumerate(context_items, 1):
            # Format each context item
            item_text = self._format_context_item(item, i)
            context_parts.append(item_text)
        
        # Add summary of user preferences if available
        user_prefs_summary = self._format_user_preferences_summary(context_items)
        if user_prefs_summary:
            context_parts.append(user_prefs_summary)
        
        return "\n\n".join(context_parts)
    
    def _format_context_item(self, item: Dict, index: int) -> str:
        """Format a single context item for prompt inclusion."""
        parts = [f"**Interaction {index}:**"]
        
        # Add timestamp
        timestamp = item.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M")
                parts.append(f"Time: {time_str}")
            except:
                pass
        
        # Add message type
        message_type = item.get('message_type', 'unknown')
        parts.append(f"Type: {message_type}")
        
        # Add user message if present
        user_message = item.get('user_message', '')
        if user_message:
            parts.append(f"User: {user_message[:100]}{'...' if len(user_message) > 100 else ''}")
        
        # Add satisfaction score if present
        satisfaction = item.get('satisfaction_score')
        if satisfaction is not None:
            satisfaction_emoji = "✅" if satisfaction > 0.7 else "⚠️" if satisfaction > 0.4 else "❌"
            parts.append(f"Satisfaction: {satisfaction_emoji} ({satisfaction:.1f})")
        
        # Add relevant context
        context = item.get('context', {})
        if context:
            context_str = self._format_context_dict(context)
            if context_str:
                parts.append(f"Context: {context_str}")
        
        return "\n".join(parts)
    
    def _format_context_dict(self, context: Dict) -> str:
        """Format context dictionary for display."""
        relevant_keys = ['tone_used', 'reason', 'filename', 'audience_type', 'relationship_type']
        parts = []
        
        for key in relevant_keys:
            if key in context and context[key]:
                parts.append(f"{key}: {context[key]}")
        
        return "; ".join(parts) if parts else ""
    
    def _format_user_preferences_summary(self, context_items: List[Dict]) -> str:
        """Format a summary of user preferences from context items."""
        preferences = {
            'tones': set(),
            'audience_types': set(),
            'high_satisfaction_patterns': [],
            'low_satisfaction_patterns': []
        }
        
        for item in context_items:
            # Extract tone preferences
            context = item.get('context', {})
            if 'tone_used' in context:
                preferences['tones'].add(context['tone_used'])
            
            # Extract audience preferences
            if 'audience_type' in context:
                preferences['audience_types'].add(context['audience_type'])
            
            # Track satisfaction patterns
            satisfaction = item.get('satisfaction_score')
            if satisfaction is not None:
                if satisfaction > 0.7:
                    preferences['high_satisfaction_patterns'].append({
                        'type': item.get('message_type'),
                        'context': context
                    })
                elif satisfaction < 0.4:
                    preferences['low_satisfaction_patterns'].append({
                        'type': item.get('message_type'),
                        'context': context
                    })
        
        # Format preferences summary
        summary_parts = ["**User Preferences Summary:**"]
        
        if preferences['tones']:
            summary_parts.append(f"Preferred tones: {', '.join(preferences['tones'])}")
        
        if preferences['audience_types']:
            summary_parts.append(f"Audience types: {', '.join(preferences['audience_types'])}")
        
        if preferences['high_satisfaction_patterns']:
            summary_parts.append(f"High satisfaction patterns: {len(preferences['high_satisfaction_patterns'])} interactions")
        
        if preferences['low_satisfaction_patterns']:
            summary_parts.append(f"Low satisfaction patterns: {len(preferences['low_satisfaction_patterns'])} interactions")
        
        return "\n".join(summary_parts) if len(summary_parts) > 1 else ""
    
    def get_context_statistics(self, session: Dict) -> Dict:
        """Get statistics about the context for analysis."""
        context_items = session.get('chat_history', [])
        
        if not context_items:
            return {"total_interactions": 0}
        
        stats = {
            "total_interactions": len(context_items),
            "message_types": {},
            "average_satisfaction": 0.0,
            "satisfaction_distribution": {"high": 0, "medium": 0, "low": 0},
            "recent_activity": 0
        }
        
        total_satisfaction = 0
        satisfaction_count = 0
        
        for item in context_items:
            # Count message types
            msg_type = item.get('message_type', 'unknown')
            stats['message_types'][msg_type] = stats['message_types'].get(msg_type, 0) + 1
            
            # Calculate satisfaction statistics
            satisfaction = item.get('satisfaction_score')
            if satisfaction is not None:
                total_satisfaction += satisfaction
                satisfaction_count += 1
                
                if satisfaction > 0.7:
                    stats['satisfaction_distribution']['high'] += 1
                elif satisfaction > 0.4:
                    stats['satisfaction_distribution']['medium'] += 1
                else:
                    stats['satisfaction_distribution']['low'] += 1
            
            # Count recent activity (last 24 hours)
            try:
                timestamp = datetime.fromisoformat(item.get('timestamp', ''))
                if datetime.now() - timestamp < timedelta(hours=24):
                    stats['recent_activity'] += 1
            except:
                pass
        
        if satisfaction_count > 0:
            stats['average_satisfaction'] = total_satisfaction / satisfaction_count
        
        return stats 