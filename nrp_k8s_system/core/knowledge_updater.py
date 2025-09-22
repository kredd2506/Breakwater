#!/usr/bin/env python3
"""
Knowledge Base Updater
======================

Background service for continuously updating the knowledge base
without blocking user requests.

Features:
- Scheduled updates of knowledge base
- Incremental updates for specific topics
- Health monitoring of knowledge base
- Performance tracking
"""

import os
import time
import threading
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json

from .fast_knowledge_builder import FastKnowledgeBuilder

logger = logging.getLogger(__name__)

class KnowledgeUpdater:
    """
    Background updater for the knowledge base.

    Runs in a separate thread and periodically updates the knowledge base
    without interfering with user requests.
    """

    def __init__(self, update_interval_hours: int = 24):
        self.update_interval = update_interval_hours * 3600  # Convert to seconds
        self.knowledge_builder = FastKnowledgeBuilder()

        # Update control
        self.update_thread: Optional[threading.Thread] = None
        self.stop_updating = threading.Event()
        self.is_running = False

        # Update tracking
        self.last_update_check = 0
        self.update_history = []

        # Status file
        self.status_file = self.knowledge_builder.cache_dir / "updater_status.json"

    def start_background_updates(self):
        """Start background updates in a separate thread."""
        if self.is_running:
            logger.warning("Background updater already running")
            return

        self.stop_updating.clear()
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        self.is_running = True

        logger.info(f"Started background knowledge updater (interval: {self.update_interval/3600:.1f} hours)")

    def stop_background_updates(self):
        """Stop background updates."""
        if not self.is_running:
            return

        self.stop_updating.set()
        if self.update_thread:
            self.update_thread.join(timeout=5)

        self.is_running = False
        logger.info("Stopped background knowledge updater")

    def _update_loop(self):
        """Main update loop running in background thread."""
        while not self.stop_updating.is_set():
            try:
                current_time = time.time()

                # Check if update is needed
                if current_time - self.last_update_check >= self.update_interval:
                    logger.info("Starting scheduled knowledge base update")

                    update_start = time.time()
                    success = self._perform_update()
                    update_duration = time.time() - update_start

                    # Record update
                    self._record_update(success, update_duration)
                    self.last_update_check = current_time

                    if success:
                        logger.info(f"Knowledge base updated successfully in {update_duration:.1f}s")
                    else:
                        logger.warning("Knowledge base update failed")

                # Sleep for a short interval before checking again
                self.stop_updating.wait(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                self.stop_updating.wait(600)  # Wait 10 minutes on error

    def _perform_update(self) -> bool:
        """Perform the actual knowledge base update."""
        try:
            # Check if knowledge base needs updating
            if not self._should_update():
                logger.info("Knowledge base is up to date, skipping update")
                return True

            # Perform incremental update
            success = self.knowledge_builder.build_knowledge_base(force_rebuild=False)

            if success:
                self._save_status()

            return success

        except Exception as e:
            logger.error(f"Knowledge base update failed: {e}")
            return False

    def _should_update(self) -> bool:
        """Check if knowledge base should be updated."""
        try:
            stats = self.knowledge_builder.get_stats()

            # Always update if not built
            if not stats['is_built']:
                return True

            # Check for critical topics that might need updates
            critical_queries = ["A100 GPU", "V100 GPU", "NVIDIA GPU", "Kubernetes GPU"]

            for query in critical_queries:
                results = self.knowledge_builder.quick_search(query, limit=3)
                if len(results) < 2:  # Insufficient results for critical topics
                    logger.info(f"Insufficient results for critical query: {query}")
                    return True

            # Check age of knowledge base
            try:
                with open(self.knowledge_builder.build_status_file, 'r') as f:
                    status = json.load(f)
                    last_built = int(status.get('last_built', 0))
                    age_hours = (time.time() - last_built) / 3600

                    if age_hours > 72:  # Update if older than 3 days
                        logger.info(f"Knowledge base is {age_hours:.1f} hours old, updating")
                        return True
            except:
                return True  # Update if we can't determine age

            return False

        except Exception as e:
            logger.warning(f"Failed to check update requirements: {e}")
            return True  # Update on error to be safe

    def _record_update(self, success: bool, duration: float):
        """Record update in history."""
        update_record = {
            'timestamp': int(time.time()),
            'success': success,
            'duration': duration,
            'stats': self.knowledge_builder.get_stats() if success else None
        }

        self.update_history.append(update_record)

        # Keep only last 50 updates
        if len(self.update_history) > 50:
            self.update_history = self.update_history[-50:]

    def _save_status(self):
        """Save updater status to disk."""
        try:
            status = {
                'is_running': self.is_running,
                'last_update_check': self.last_update_check,
                'update_interval': self.update_interval,
                'update_history': self.update_history[-10:]  # Save last 10 updates
            }

            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save updater status: {e}")

    def force_update(self) -> bool:
        """Force an immediate update of the knowledge base."""
        logger.info("Forcing immediate knowledge base update")

        try:
            update_start = time.time()
            success = self.knowledge_builder.build_knowledge_base(force_rebuild=True)
            update_duration = time.time() - update_start

            self._record_update(success, update_duration)
            self.last_update_check = time.time()

            if success:
                self._save_status()
                logger.info(f"Forced update completed in {update_duration:.1f}s")
            else:
                logger.error("Forced update failed")

            return success

        except Exception as e:
            logger.error(f"Forced update failed: {e}")
            return False

    def get_update_status(self) -> Dict[str, Any]:
        """Get current update status."""
        stats = self.knowledge_builder.get_stats()

        next_check = self.last_update_check + self.update_interval
        time_to_next = max(0, next_check - time.time())

        recent_updates = self.update_history[-5:] if self.update_history else []

        return {
            'is_running': self.is_running,
            'knowledge_base_stats': stats,
            'last_update_check': self.last_update_check,
            'next_update_in_seconds': time_to_next,
            'update_interval_hours': self.update_interval / 3600,
            'recent_updates': recent_updates,
            'total_updates': len(self.update_history)
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform health check of the knowledge base."""
        try:
            stats = self.knowledge_builder.get_stats()

            # Test critical searches
            critical_tests = [
                "A100 GPU configuration",
                "Kubernetes pod",
                "GPU resource limits"
            ]

            search_results = {}
            for test_query in critical_tests:
                results = self.knowledge_builder.quick_search(test_query, limit=3)
                search_results[test_query] = {
                    'result_count': len(results),
                    'avg_relevance': sum(r.get('relevance', 0) for r in results) / len(results) if results else 0
                }

            # Overall health score
            health_score = 0.0

            # Knowledge base built
            if stats['is_built']:
                health_score += 0.3

            # Sufficient templates
            if stats['total_templates'] >= 10:
                health_score += 0.2

            # GPU templates available
            if stats['gpu_templates'] >= 3:
                health_score += 0.2

            # Search performance
            avg_search_performance = sum(r['avg_relevance'] for r in search_results.values()) / len(search_results)
            health_score += avg_search_performance * 0.3

            health_status = "excellent" if health_score > 0.8 else "good" if health_score > 0.6 else "poor"

            return {
                'health_score': health_score,
                'health_status': health_status,
                'knowledge_base_stats': stats,
                'search_test_results': search_results,
                'updater_running': self.is_running,
                'timestamp': int(time.time())
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'health_score': 0.0,
                'health_status': 'error',
                'error': str(e),
                'timestamp': int(time.time())
            }


# Global updater instance
_global_updater: Optional[KnowledgeUpdater] = None

def get_knowledge_updater() -> KnowledgeUpdater:
    """Get the global knowledge updater instance."""
    global _global_updater
    if _global_updater is None:
        _global_updater = KnowledgeUpdater()
    return _global_updater

def start_background_updates():
    """Start background knowledge base updates."""
    updater = get_knowledge_updater()
    updater.start_background_updates()

def stop_background_updates():
    """Stop background knowledge base updates."""
    updater = get_knowledge_updater()
    updater.stop_background_updates()

def force_knowledge_update() -> bool:
    """Force an immediate knowledge base update."""
    updater = get_knowledge_updater()
    return updater.force_update()

def get_knowledge_health() -> Dict[str, Any]:
    """Get knowledge base health status."""
    updater = get_knowledge_updater()
    return updater.health_check()