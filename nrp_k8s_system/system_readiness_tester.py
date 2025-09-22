#!/usr/bin/env python3
"""
System Readiness Tester for NRP K8s System

Tests all major components to ensure the system is ready for operation:
- Kubernetes cluster connectivity
- LLM client functionality 
- NRP documentation cache status
- Enhanced router components
- Configuration validation
"""

import os
import sys
import time
import traceback
from pathlib import Path
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    component: str
    status: str  # "PASS", "FAIL", "WARN", "SKIP"
    message: str
    details: str = ""
    execution_time: float = 0.0

class SystemReadinessTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.base_path = Path(__file__).parent
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all readiness tests and return comprehensive report"""
        print("=" * 70)
        print("NRP K8s System Readiness Test")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Base path: {self.base_path}")
        print()
        
        # Test categories in order of dependency
        test_suites = [
            ("Environment & Dependencies", self._test_environment),
            ("LLM Client", self._test_llm_client),
            ("Kubernetes Connectivity", self._test_k8s_connectivity),
            ("Documentation Cache", self._test_documentation_cache),
            ("Enhanced Router", self._test_enhanced_router),
            ("Core System Integration", self._test_system_integration)
        ]
        
        total_start = time.time()
        
        for suite_name, test_func in test_suites:
            print(f"Testing {suite_name}...")
            print("-" * 50)
            
            try:
                test_func()
            except Exception as e:
                self.results.append(TestResult(
                    component=suite_name,
                    status="FAIL",
                    message=f"Test suite crashed: {str(e)}",
                    details=traceback.format_exc()
                ))
            
            print()
        
        total_time = time.time() - total_start
        
        # Generate final report
        return self._generate_report(total_time)
    
    def _test_environment(self):
        """Test environment variables and basic dependencies"""
        start_time = time.time()
        
        # Check Python version
        if sys.version_info >= (3, 8):
            self._add_result("Python Version", "PASS", f"Python {sys.version.split()[0]}")
        else:
            self._add_result("Python Version", "FAIL", f"Python {sys.version.split()[0]} < 3.8")
        
        # Check environment variables
        env_vars = ["NRP_API_KEY", "NRP_BASE_URL", "NRP_MODEL"]
        missing_vars = []
        
        for var in env_vars:
            value = os.environ.get(var)
            if value:
                masked_value = f"{value[:8]}..." if len(value) > 8 else "set"
                self._add_result(f"Env: {var}", "PASS", f"✓ {masked_value}")
            else:
                missing_vars.append(var)
                self._add_result(f"Env: {var}", "WARN", "Not set (may use defaults)")
        
        # Check .env file
        env_file = self.base_path / ".env"
        if env_file.exists():
            self._add_result(".env file", "PASS", f"Found at {env_file}")
        else:
            self._add_result(".env file", "WARN", "Not found (using system env)")
        
        # Test core imports
        try:
            import langchain_openai
            version = getattr(langchain_openai, '__version__', 'unknown')
            self._add_result("langchain-openai", "PASS", f"v{version}")
        except ImportError as e:
            self._add_result("langchain-openai", "FAIL", f"Import failed: {e}")
        
        try:
            import kubernetes
            version = getattr(kubernetes, '__version__', 'unknown')
            self._add_result("kubernetes", "PASS", f"v{version}")
        except ImportError as e:
            self._add_result("kubernetes", "FAIL", f"Import failed: {e}")
        
        execution_time = time.time() - start_time
        for result in self.results[-len(env_vars)-4:]:
            result.execution_time = execution_time / (len(env_vars) + 4)
    
    def _test_llm_client(self):
        """Test LLM client initialization and basic functionality"""
        start_time = time.time()
        
        try:
            # Test nrp_init import - try relative first, then absolute
            try:
                from core.nrp_init import init_chat_model
            except ImportError:
                from nrp_k8s_system.core.nrp_init import init_chat_model
            self._add_result("NRP Init Import", "PASS", "Module imported successfully")
            
            # Test client initialization
            try:
                client = init_chat_model()
                self._add_result("LLM Client Init", "PASS", "Client initialized")
                
                # Test basic invoke
                try:
                    response = client.invoke("Hello, respond with just 'OK'")
                    if hasattr(response, 'content'):
                        content = response.content.strip()
                    else:
                        content = str(response).strip()
                    
                    if content:
                        self._add_result("LLM Basic Test", "PASS", f"Response: {content[:50]}...")
                    else:
                        self._add_result("LLM Basic Test", "WARN", "Empty response")
                        
                except Exception as e:
                    self._add_result("LLM Basic Test", "FAIL", f"Invoke failed: {str(e)}")
                    
            except Exception as e:
                self._add_result("LLM Client Init", "FAIL", f"Init failed: {str(e)}")
                
        except ImportError as e:
            self._add_result("NRP Init Import", "FAIL", f"Import failed: {str(e)}")
        
        execution_time = time.time() - start_time
        for result in self.results[-3:]:
            result.execution_time = execution_time / 3
    
    def _test_k8s_connectivity(self):
        """Test Kubernetes cluster connectivity"""
        start_time = time.time()
        
        try:
            from kubernetes import client, config
            self._add_result("K8s Client Import", "PASS", "Module imported")
            
            # Try to load config
            try:
                config.load_incluster_config()
                config_type = "in-cluster"
            except:
                try:
                    config.load_kube_config()
                    config_type = "kubeconfig"
                except Exception as e:
                    self._add_result("K8s Config", "FAIL", f"Config load failed: {str(e)}")
                    return
            
            self._add_result("K8s Config", "PASS", f"Loaded {config_type} config")
            
            # Test API connectivity
            try:
                v1 = client.CoreV1Api()
                # Test connection with a simple call
                namespaces = v1.list_namespace(limit=1)
                self._add_result("K8s API Connection", "PASS", f"Connected, {len(namespaces.items)} namespace(s) accessible")
                
                # Test gsoc namespace access
                try:
                    pods = v1.list_namespaced_pod(namespace="gsoc", limit=1)
                    self._add_result("K8s gsoc Namespace", "PASS", f"Accessible, {len(pods.items)} pod(s)")
                except Exception as e:
                    if "not found" in str(e).lower():
                        self._add_result("K8s gsoc Namespace", "WARN", "Namespace 'gsoc' not found")
                    else:
                        self._add_result("K8s gsoc Namespace", "FAIL", f"Access error: {str(e)}")
                        
            except Exception as e:
                self._add_result("K8s API Connection", "FAIL", f"API call failed: {str(e)}")
                
        except ImportError as e:
            self._add_result("K8s Client Import", "FAIL", f"Import failed: {str(e)}")
        
        execution_time = time.time() - start_time
        for result in self.results[-4:]:
            result.execution_time = execution_time / 4
    
    def _test_documentation_cache(self):
        """Test NRP documentation cache and scraper"""
        start_time = time.time()
        
        cache_dir = self.base_path / "cache" / "nautilus_docs"
        
        # Check cache directory
        if cache_dir.exists():
            files = list(cache_dir.glob("*.json"))
            self._add_result("Cache Directory", "PASS", f"Found {len(files)} cached files")
            
            # Check file freshness (should be < 1 day old for active use)
            recent_files = 0
            for file in files:
                age_hours = (time.time() - file.stat().st_mtime) / 3600
                if age_hours < 24:
                    recent_files += 1
            
            if recent_files > 0:
                self._add_result("Cache Freshness", "PASS", f"{recent_files}/{len(files)} files < 24h old")
            else:
                self._add_result("Cache Freshness", "WARN", "No recent cache files found")
        else:
            self._add_result("Cache Directory", "WARN", "Cache directory not found")
        
        # Test scraper import
        try:
            try:
                from systems.nautilus_docs_scraper import NautilusDocsScraper
            except ImportError:
                from nrp_k8s_system.systems.nautilus_docs_scraper import NautilusDocsScraper
            self._add_result("Docs Scraper Import", "PASS", "Module imported")
            
            # Test scraper initialization
            try:
                scraper = NautilusDocsScraper()
                self._add_result("Scraper Init", "PASS", "Scraper initialized")
                
                # Test basic scraper functionality (without full scrape)
                if hasattr(scraper, 'cache_dir'):
                    self._add_result("Scraper Config", "PASS", f"Cache dir: {scraper.cache_dir}")
                else:
                    self._add_result("Scraper Config", "WARN", "Cache dir not configured")
                    
            except Exception as e:
                self._add_result("Scraper Init", "FAIL", f"Init failed: {str(e)}")
                
        except ImportError as e:
            self._add_result("Docs Scraper Import", "FAIL", f"Import failed: {str(e)}")
        
        execution_time = time.time() - start_time
        for result in self.results[-5:]:
            result.execution_time = execution_time / 5
    
    def _test_enhanced_router(self):
        """Test enhanced router components"""
        start_time = time.time()
        
        # Test enhanced router import
        try:
            try:
                from enhanced_intelligent_router import EnhancedIntelligentRouter
            except ImportError:
                from nrp_k8s_system.enhanced_intelligent_router import EnhancedIntelligentRouter
            self._add_result("Enhanced Router Import", "PASS", "Module imported")
            
            # Test router initialization
            try:
                router = EnhancedIntelligentRouter()
                self._add_result("Router Init", "PASS", "Router initialized")
                
                # Test router has required methods
                required_methods = ["process_query", "_handle_question", "_handle_generation"]
                missing_methods = []
                for method in required_methods:
                    if hasattr(router, method):
                        self._add_result(f"Router Method: {method}", "PASS", "Available")
                    else:
                        missing_methods.append(method)
                        self._add_result(f"Router Method: {method}", "FAIL", "Missing")
                
            except Exception as e:
                self._add_result("Router Init", "FAIL", f"Init failed: {str(e)}")
                
        except ImportError as e:
            self._add_result("Enhanced Router Import", "FAIL", f"Import failed: {str(e)}")
        
        # Test k8s operations
        try:
            try:
                from systems.k8s_operations import Agent
            except ImportError:
                from nrp_k8s_system.systems.k8s_operations import Agent
            self._add_result("K8s Operations Import", "PASS", "Module imported (Agent class)")
        except ImportError as e:
            self._add_result("K8s Operations Import", "FAIL", f"Import failed: {str(e)}")
        
        execution_time = time.time() - start_time
        for result in self.results[-6:]:
            result.execution_time = execution_time / 6
    
    def _test_system_integration(self):
        """Test overall system integration"""
        start_time = time.time()
        
        # Test main module import
        try:
            try:
                import intelligent_router
            except ImportError:
                from nrp_k8s_system import intelligent_router
            self._add_result("Main Module Import", "PASS", "intelligent_router imported")
        except ImportError as e:
            self._add_result("Main Module Import", "FAIL", f"Import failed: {str(e)}")
        
        # Test CLI entry point
        cli_file = self.base_path / "cli.py"
        if cli_file.exists():
            self._add_result("CLI Entry Point", "PASS", f"Found at {cli_file}")
        else:
            self._add_result("CLI Entry Point", "WARN", "cli.py not found")
        
        # Test package structure
        init_file = self.base_path / "__init__.py"
        if init_file.exists():
            self._add_result("Package Structure", "PASS", "__init__.py found")
        else:
            self._add_result("Package Structure", "WARN", "__init__.py missing")
        
        execution_time = time.time() - start_time
        for result in self.results[-3:]:
            result.execution_time = execution_time / 3
    
    def _add_result(self, component: str, status: str, message: str, details: str = ""):
        """Add a test result and print it immediately"""
        result = TestResult(component, status, message, details)
        self.results.append(result)
        
        # Print with status indicators
        status_symbols = {
            "PASS": "[OK]",
            "FAIL": "[FAIL]", 
            "WARN": "[WARN]",
            "SKIP": "[SKIP]"
        }
        
        symbol = status_symbols.get(status, "[?]")
        print(f"  {symbol} {component:25} {status:4} | {message}")
    
    def _generate_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("=" * 70)
        print("SYSTEM READINESS REPORT")
        print("=" * 70)
        
        # Count results by status
        status_counts = {"PASS": 0, "FAIL": 0, "WARN": 0, "SKIP": 0}
        for result in self.results:
            status_counts[result.status] += 1
        
        total_tests = len(self.results)
        pass_rate = (status_counts["PASS"] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Test Summary:")
        print(f"  Total Tests: {total_tests}")
        print(f"  [OK] Passed: {status_counts['PASS']} ({status_counts['PASS']/total_tests*100:.1f}%)")
        print(f"  [FAIL] Failed: {status_counts['FAIL']} ({status_counts['FAIL']/total_tests*100:.1f}%)")
        print(f"  [WARN] Warnings: {status_counts['WARN']} ({status_counts['WARN']/total_tests*100:.1f}%)")
        print(f"  [SKIP] Skipped: {status_counts['SKIP']} ({status_counts['SKIP']/total_tests*100:.1f}%)")
        print(f"  Pass Rate: {pass_rate:.1f}%")
        print(f"  Total Time: {total_time:.2f}s")
        print()
        
        # Overall system status
        if status_counts["FAIL"] == 0:
            if status_counts["WARN"] == 0:
                overall_status = "READY"
                status_msg = "System is fully ready for operation!"
            else:
                overall_status = "READY_WITH_WARNINGS"
                status_msg = "System is ready but has warnings to review."
        else:
            overall_status = "NOT_READY"
            status_msg = "System has critical issues that need attention."
        
        print(f"Overall Status: {overall_status}")
        print(f"   {status_msg}")
        print()
        
        # Show critical failures
        failures = [r for r in self.results if r.status == "FAIL"]
        if failures:
            print("Critical Issues:")
            for failure in failures:
                print(f"  [FAIL] {failure.component}: {failure.message}")
                if failure.details:
                    print(f"     Details: {failure.details[:100]}...")
            print()
        
        # Show warnings
        warnings = [r for r in self.results if r.status == "WARN"]
        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  [WARN] {warning.component}: {warning.message}")
            print()
        
        print("=" * 70)
        print(f"Readiness test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return {
            "overall_status": overall_status,
            "pass_rate": pass_rate,
            "total_tests": total_tests,
            "status_counts": status_counts,
            "total_time": total_time,
            "failures": [{"component": f.component, "message": f.message} for f in failures],
            "warnings": [{"component": w.component, "message": w.message} for w in warnings],
            "results": self.results
        }

def main():
    """Main entry point for system readiness testing"""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("NRP K8s System Readiness Tester")
        print("Usage: python system_readiness_tester.py")
        print("Tests all major system components for operational readiness.")
        return
    
    tester = SystemReadinessTester()
    report = tester.run_all_tests()
    
    # Exit with appropriate code
    if report["overall_status"] == "READY":
        sys.exit(0)
    elif report["overall_status"] == "READY_WITH_WARNINGS":
        sys.exit(1)  # Warnings
    else:
        sys.exit(2)  # Critical failures

if __name__ == "__main__":
    main()