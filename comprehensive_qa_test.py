#!/usr/bin/env python3
"""
Comprehensive QA Testing System

This system:
1. Reads all questions from QA.txt
2. Processes each question through the enhanced NRP system
3. Records detailed answers, logs, timing, and performance metrics
4. Saves results for later analysis
"""

import sys
import os
import time
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add the nrp_k8s_system to path
sys.path.insert(0, str(Path(__file__).parent / "nrp_k8s_system"))

from nrp_k8s_system.agents.orchestrator import AgentOrchestrator


class QATestResult:
    """Class to store test results for a single question."""

    def __init__(self, question_id: int, question_text: str):
        self.question_id = question_id
        self.question_text = question_text
        self.start_time = time.time()
        self.end_time = None
        self.duration = None

        # System response data
        self.success = False
        self.response_content = ""
        self.agent_type = ""
        self.confidence = ""
        self.intent_classification = ""

        # Performance metrics
        self.response_length = 0
        self.source_citations = []
        self.nrp_specific = False
        self.contains_yaml = False
        self.contains_urls = False

        # Error handling
        self.error_occurred = False
        self.error_message = ""
        self.error_traceback = ""

        # Logs
        self.system_logs = []

    def complete(self, response_content: str, success: bool, **kwargs):
        """Mark the test as complete and record results."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

        self.success = success
        self.response_content = response_content
        self.response_length = len(response_content)

        # Extract metadata
        self.agent_type = kwargs.get('agent_type', 'Unknown')
        self.confidence = kwargs.get('confidence', 'Unknown')
        self.intent_classification = kwargs.get('intent', 'Unknown')

        # Analyze response content
        self._analyze_response_content()

    def add_error(self, error_message: str, error_traceback: str = ""):
        """Record error information."""
        self.error_occurred = True
        self.error_message = error_message
        self.error_traceback = error_traceback
        self.complete("", False)

    def add_log(self, log_message: str):
        """Add a log entry."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.system_logs.append(f"[{timestamp}] {log_message}")

    def _analyze_response_content(self):
        """Analyze the response content for key indicators."""
        if not self.response_content:
            return

        content_lower = self.response_content.lower()

        # Check for NRP-specific content
        nrp_indicators = [
            'nrp', 'nautilus', 'national research platform',
            'nrp.ai', 'nvidia.com/gpu', 'nvidia.com/a100',
            'rook-ceph', 'haproxy', 'ceph', 'alveo'
        ]
        self.nrp_specific = any(indicator in content_lower for indicator in nrp_indicators)

        # Check for YAML content
        self.contains_yaml = 'yaml' in content_lower or '```yaml' in self.response_content

        # Extract URL citations
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]*'
        urls = re.findall(url_pattern, self.response_content)
        self.contains_urls = len(urls) > 0
        self.source_citations = urls

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'question_id': self.question_id,
            'question_text': self.question_text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'success': self.success,
            'response_content': self.response_content,
            'response_length': self.response_length,
            'agent_type': self.agent_type,
            'confidence': self.confidence,
            'intent_classification': self.intent_classification,
            'nrp_specific': self.nrp_specific,
            'contains_yaml': self.contains_yaml,
            'contains_urls': self.contains_urls,
            'source_citations': self.source_citations,
            'error_occurred': self.error_occurred,
            'error_message': self.error_message,
            'error_traceback': self.error_traceback,
            'system_logs': self.system_logs
        }


class ComprehensiveQATester:
    """Main testing system for processing QA questions."""

    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.results: List[QATestResult] = []
        self.start_time = time.time()

    def load_questions(self, qa_file_path: str) -> List[Tuple[int, str]]:
        """Load questions from QA.txt file."""
        questions = []

        try:
            with open(qa_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Remove any trailing annotations like "NRP" or "media.nrp.ai"
                    question_text = line.split(' NRP')[0].split(' docs.')[0].split(' media.')[0].split(' sdsc.')[0]
                    question_text = question_text.strip()

                    if question_text:
                        questions.append((line_num, question_text))

        except Exception as e:
            print(f"Error loading questions from {qa_file_path}: {e}")
            return []

        return questions

    def process_single_question(self, question_id: int, question_text: str) -> QATestResult:
        """Process a single question and return detailed results."""
        print(f"\n{'='*80}")
        print(f"PROCESSING QUESTION {question_id}")
        print(f"{'='*80}")
        print(f"Q: {question_text}")
        print(f"{'='*80}")

        result = QATestResult(question_id, question_text)
        result.add_log(f"Starting question {question_id}")

        try:
            # Process the question through the system
            result.add_log("Calling orchestrator.process_request")
            response_content, success = self.orchestrator.process_request(question_text)
            result.add_log(f"Orchestrator completed - Success: {success}")

            # Record the result
            result.complete(
                response_content=response_content,
                success=success,
                agent_type="Orchestrator",  # Could be enhanced to detect actual agent
                confidence="Unknown",  # Could be enhanced to extract confidence
                intent="Unknown"  # Could be enhanced to extract intent
            )

            print(f"\nSUCCESS: {success}")
            print(f"RESPONSE LENGTH: {len(response_content)} characters")
            print(f"DURATION: {result.duration:.2f} seconds")
            print(f"NRP SPECIFIC: {result.nrp_specific}")
            print(f"SOURCE CITATIONS: {len(result.source_citations)}")

            # Print response preview
            preview = response_content[:300] + "..." if len(response_content) > 300 else response_content
            print(f"\nRESPONSE PREVIEW:")
            print("-" * 50)
            print(preview)
            print("-" * 50)

        except Exception as e:
            error_trace = traceback.format_exc()
            result.add_error(str(e), error_trace)
            result.add_log(f"Error occurred: {e}")

            print(f"\nERROR: {e}")
            print(f"DURATION: {result.duration:.2f} seconds")

        return result

    def run_comprehensive_test(self, qa_file_path: str) -> Dict[str, Any]:
        """Run the comprehensive test on all questions."""
        print("COMPREHENSIVE NRP QA SYSTEM TEST")
        print("=" * 80)
        print(f"Loading questions from: {qa_file_path}")

        # Load questions
        questions = self.load_questions(qa_file_path)
        if not questions:
            print("No questions loaded!")
            return {"error": "No questions loaded"}

        print(f"Loaded {len(questions)} questions")
        print(f"Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Process each question
        for question_id, question_text in questions:
            try:
                result = self.process_single_question(question_id, question_text)
                self.results.append(result)

                # Brief pause between questions to avoid overwhelming the system
                time.sleep(1)

            except KeyboardInterrupt:
                print(f"\n\nTest interrupted by user at question {question_id}")
                break
            except Exception as e:
                print(f"\n\nUnexpected error processing question {question_id}: {e}")
                # Create error result
                error_result = QATestResult(question_id, question_text)
                error_result.add_error(f"Unexpected error: {e}", traceback.format_exc())
                self.results.append(error_result)

        # Generate summary
        return self._generate_summary()

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive summary of test results."""
        total_time = time.time() - self.start_time
        total_questions = len(self.results)

        if total_questions == 0:
            return {"error": "No results to summarize"}

        # Calculate metrics
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if r.error_occurred)
        avg_duration = sum(r.duration or 0 for r in self.results) / total_questions
        nrp_specific = sum(1 for r in self.results if r.nrp_specific)
        with_citations = sum(1 for r in self.results if r.source_citations)
        with_yaml = sum(1 for r in self.results if r.contains_yaml)

        summary = {
            "test_summary": {
                "total_questions": total_questions,
                "successful_responses": successful,
                "failed_responses": failed,
                "success_rate": successful / total_questions * 100,
                "total_test_time": total_time,
                "average_response_time": avg_duration,
                "nrp_specific_responses": nrp_specific,
                "responses_with_citations": with_citations,
                "responses_with_yaml": with_yaml
            },
            "detailed_results": [result.to_dict() for result in self.results]
        }

        return summary

    def save_results(self, output_file: str, summary: Dict[str, Any]):
        """Save results to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file_timestamped = output_file.replace('.json', f'_{timestamp}.json')

            with open(output_file_timestamped, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)

            print(f"\nResults saved to: {output_file_timestamped}")
            return output_file_timestamped

        except Exception as e:
            print(f"Error saving results: {e}")
            return None


def main():
    """Main execution function."""
    qa_file_path = r"D:\Gsoc Gitlab\ocean\breakwater\mcp\tests\QA.txt"
    output_file = r"D:\Gsoc Gitlab\ocean\breakwater\qa_test_results.json"

    # Verify QA file exists
    if not os.path.exists(qa_file_path):
        print(f"QA file not found: {qa_file_path}")
        sys.exit(1)

    # Run comprehensive test
    tester = ComprehensiveQATester()
    summary = tester.run_comprehensive_test(qa_file_path)

    # Print summary
    if "test_summary" in summary:
        ts = summary["test_summary"]
        print(f"\n{'='*80}")
        print("COMPREHENSIVE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Questions: {ts['total_questions']}")
        print(f"Successful Responses: {ts['successful_responses']}")
        print(f"Failed Responses: {ts['failed_responses']}")
        print(f"Success Rate: {ts['success_rate']:.1f}%")
        print(f"Total Test Time: {ts['total_test_time']:.2f} seconds")
        print(f"Average Response Time: {ts['average_response_time']:.2f} seconds")
        print(f"NRP-Specific Responses: {ts['nrp_specific_responses']}")
        print(f"Responses with Citations: {ts['responses_with_citations']}")
        print(f"Responses with YAML: {ts['responses_with_yaml']}")

    # Save results
    saved_file = tester.save_results(output_file, summary)

    if saved_file:
        print(f"\n✓ All results saved to: {saved_file}")
        print(f"✓ Ready for detailed analysis!")

    return summary.get("test_summary", {}).get("success_rate", 0) > 80


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)