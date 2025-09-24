#!/usr/bin/env python3
"""
Conversational Summary Buffer for Knowledge Updates
==================================================
Maintains and updates knowledge resources with conversation context
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ConversationalSummaryBuffer:
    """
    Intelligent buffer that stores, updates and summarizes knowledge resources
    with conversational context for better resource management
    """

    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        self.buffer_file = self.cache_dir / "conversation_buffer.json"
        self.knowledge_file = self.cache_dir / "knowledge_updates.json"
        self.summary_file = self.cache_dir / "knowledge_summary.json"

        self.buffer = self._load_buffer()
        self.knowledge_base = self._load_knowledge()
        self.summary = self._load_summary()

    def _load_buffer(self) -> Dict:
        """Load conversation buffer from disk"""
        if self.buffer_file.exists():
            with open(self.buffer_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "conversations": [],
            "last_updated": None,
            "total_queries": 0,
            "successful_responses": 0
        }

    def _load_knowledge(self) -> Dict:
        """Load knowledge base from disk"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "resource_updates": {},
            "query_patterns": {},
            "successful_responses": {},
            "failed_queries": {}
        }

    def _load_summary(self) -> Dict:
        """Load knowledge summary from disk"""
        if self.summary_file.exists():
            with open(self.summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "total_interactions": 0,
            "most_requested_topics": {},
            "resource_update_frequency": {},
            "success_rate": 0.0,
            "last_summary_update": None
        }

    def add_conversation(self, query: str, intent: str, response: str, success: bool, metadata: Optional[Dict] = None):
        """Add a conversation to the buffer with context"""
        timestamp = datetime.now().isoformat()

        conversation = {
            "timestamp": timestamp,
            "query": query,
            "intent": intent,
            "response": response,
            "success": success,
            "metadata": metadata or {},
            "query_length": len(query),
            "response_length": len(response)
        }

        self.buffer["conversations"].append(conversation)
        self.buffer["last_updated"] = timestamp
        self.buffer["total_queries"] += 1

        if success:
            self.buffer["successful_responses"] += 1

        # Update knowledge patterns
        self._update_knowledge_patterns(query, intent, success, response)

        # Maintain buffer size (keep last 100 conversations)
        if len(self.buffer["conversations"]) > 100:
            self.buffer["conversations"] = self.buffer["conversations"][-100:]

        self._save_buffer()
        self._update_summary()

    def _update_knowledge_patterns(self, query: str, intent: str, success: bool, response: str):
        """Update knowledge patterns based on conversation"""
        # Extract key topics from query
        topics = self._extract_topics(query)

        for topic in topics:
            if topic not in self.knowledge_base["query_patterns"]:
                self.knowledge_base["query_patterns"][topic] = {
                    "count": 0,
                    "success_rate": 0.0,
                    "common_intents": {},
                    "last_query": None
                }

            pattern = self.knowledge_base["query_patterns"][topic]
            pattern["count"] += 1
            pattern["last_query"] = datetime.now().isoformat()

            # Update intent tracking
            if intent not in pattern["common_intents"]:
                pattern["common_intents"][intent] = 0
            pattern["common_intents"][intent] += 1

            # Update success rate
            if success:
                if topic not in self.knowledge_base["successful_responses"]:
                    self.knowledge_base["successful_responses"][topic] = 0
                self.knowledge_base["successful_responses"][topic] += 1
            else:
                if topic not in self.knowledge_base["failed_queries"]:
                    self.knowledge_base["failed_queries"][topic] = 0
                self.knowledge_base["failed_queries"][topic] += 1

            # Calculate success rate
            total = self.knowledge_base["successful_responses"].get(topic, 0) + self.knowledge_base["failed_queries"].get(topic, 0)
            if total > 0:
                pattern["success_rate"] = self.knowledge_base["successful_responses"].get(topic, 0) / total

        self._save_knowledge()

    def _extract_topics(self, query: str) -> List[str]:
        """Extract topics from query for pattern tracking"""
        keywords = {
            "gpu": ["gpu", "a100", "h100", "v100", "rtx", "nvidia"],
            "storage": ["storage", "pvc", "volume", "ceph", "s3", "persistent"],
            "networking": ["network", "service", "ingress", "port", "endpoint"],
            "pods": ["pod", "container", "deployment", "replica"],
            "yaml": ["yaml", "example", "template", "configuration"],
            "security": ["rbac", "secret", "configmap", "permission"],
            "monitoring": ["logs", "metrics", "monitoring", "prometheus"]
        }

        query_lower = query.lower()
        topics = []

        for topic, words in keywords.items():
            if any(word in query_lower for word in words):
                topics.append(topic)

        return topics or ["general"]

    def get_knowledge_insights(self) -> Dict:
        """Get insights about knowledge patterns and resource updates"""
        return {
            "conversation_stats": {
                "total_queries": self.buffer["total_queries"],
                "successful_responses": self.buffer["successful_responses"],
                "success_rate": self.buffer["successful_responses"] / max(1, self.buffer["total_queries"])
            },
            "top_topics": self._get_top_topics(),
            "intent_distribution": self._get_intent_distribution(),
            "knowledge_gaps": self._identify_knowledge_gaps(),
            "resource_update_needs": self._identify_update_needs()
        }

    def _get_top_topics(self) -> List[Dict]:
        """Get most frequently requested topics"""
        topics = []
        for topic, data in self.knowledge_base["query_patterns"].items():
            topics.append({
                "topic": topic,
                "count": data["count"],
                "success_rate": data["success_rate"],
                "last_query": data["last_query"]
            })
        return sorted(topics, key=lambda x: x["count"], reverse=True)[:10]

    def _get_intent_distribution(self) -> Dict:
        """Get distribution of intents across conversations"""
        intent_counts = {}
        for conv in self.buffer["conversations"]:
            intent = conv["intent"]
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        return intent_counts

    def _identify_knowledge_gaps(self) -> List[Dict]:
        """Identify topics with low success rates (knowledge gaps)"""
        gaps = []
        for topic, data in self.knowledge_base["query_patterns"].items():
            if data["success_rate"] < 0.7 and data["count"] >= 3:
                gaps.append({
                    "topic": topic,
                    "success_rate": data["success_rate"],
                    "count": data["count"],
                    "needs_improvement": True
                })
        return sorted(gaps, key=lambda x: x["success_rate"])

    def _identify_update_needs(self) -> List[str]:
        """Identify resources that need updates based on failed queries"""
        update_needs = []

        # Check for high failure rate topics
        for topic, failure_count in self.knowledge_base["failed_queries"].items():
            success_count = self.knowledge_base["successful_responses"].get(topic, 0)
            total = failure_count + success_count

            if total >= 5 and failure_count / total > 0.4:
                update_needs.append(f"Topic '{topic}' has high failure rate: {failure_count}/{total} failures")

        return update_needs

    def _update_summary(self):
        """Update knowledge summary"""
        top_topics = self._get_top_topics()[:5]
        topics_dict = {topic["topic"]: topic["count"] for topic in top_topics}

        self.summary = {
            "total_interactions": self.buffer["total_queries"],
            "most_requested_topics": topics_dict,
            "resource_update_frequency": self._calculate_update_frequency(),
            "success_rate": self.buffer["successful_responses"] / max(1, self.buffer["total_queries"]),
            "last_summary_update": datetime.now().isoformat()
        }
        self._save_summary()

    def _calculate_update_frequency(self) -> Dict:
        """Calculate how often different resources are updated"""
        frequency = {}
        now = datetime.now()

        for topic, data in self.knowledge_base["query_patterns"].items():
            if data["last_query"]:
                last_query = datetime.fromisoformat(data["last_query"])
                days_since = (now - last_query).days

                if days_since == 0:
                    frequency[topic] = "today"
                elif days_since == 1:
                    frequency[topic] = "yesterday"
                elif days_since <= 7:
                    frequency[topic] = f"{days_since} days ago"
                else:
                    frequency[topic] = f"{days_since // 7} weeks ago"

        return frequency

    def _save_buffer(self):
        """Save conversation buffer to disk"""
        with open(self.buffer_file, 'w', encoding='utf-8') as f:
            json.dump(self.buffer, f, indent=2, ensure_ascii=False)

    def _save_knowledge(self):
        """Save knowledge base to disk"""
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)

    def _save_summary(self):
        """Save knowledge summary to disk"""
        with open(self.summary_file, 'w', encoding='utf-8') as f:
            json.dump(self.summary, f, indent=2, ensure_ascii=False)

# Global instance for easy access
knowledge_buffer = ConversationalSummaryBuffer("D:/Gsoc Gitlab/ocean/breakwater/nrp_k8s_system/cache")