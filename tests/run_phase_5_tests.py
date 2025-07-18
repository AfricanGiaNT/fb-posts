#!/usr/bin/env python3
"""
Test Runner for Phase 5.1 & 5.2 Implementation
Executes all tests for Enhanced Session Architecture and AI Project Analysis Engine
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add scripts and tests directories to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
sys.path.insert(0, str(PROJECT_ROOT / 'tests'))

class Phase5TestRunner:
    """Simplified test runner using pytest"""
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self):
        """Run all Phase 5 tests using pytest"""
        print("🚀 **Phase 5.1 & 5.2 Test Execution Started**\n")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # Define test files
        test_files = [
            {
                'name': 'Phase 5.1: Session Architecture',
                'file': 'tests/test_phase_5_1_session_architecture.py',
                'description': 'Multi-file session management and batch upload workflow'
            },
            {
                'name': 'Phase 5.2: Project Analysis Engine',
                'file': 'tests/test_phase_5_2_project_analyzer.py',
                'description': 'AI-powered file categorization and project narrative extraction'
            },
            {
                'name': 'Phase 5 Integration Tests',
                'file': 'tests/test_phase_5_integration.py',
                'description': 'Complete multi-file workflow integration'
            }
        ]
        
        # Run each test file
        all_passed = True
        for test_info in test_files:
            success = self._run_test_file(test_info)
            all_passed = all_passed and success
        
        self.end_time = time.time()
        
        # Generate final report
        self._generate_final_report()
        
        return all_passed
    
    def _run_test_file(self, test_info):
        """Run a specific test file using pytest"""
        print(f"\n📋 **{test_info['name']}**")
        print(f"   {test_info['description']}")
        print("-" * 60)
        
        try:
            # Run pytest on the specific file
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                test_info['file'],
                '-v', '--tb=short', '--no-header'
            ], capture_output=True, text=True, cwd=PROJECT_ROOT)
            
            # Parse pytest output
            output_lines = result.stdout.split('\n')
            
            # Find the summary line
            passed = 0
            failed = 0
            errors = 0
            
            for line in output_lines:
                if 'passed' in line and ('failed' in line or 'error' in line):
                    # Parse line like "3 failed, 20 passed in 47.10s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            passed = int(parts[i-1])
                        elif part == 'failed':
                            failed = int(parts[i-1])
                        elif part == 'error':
                            errors = int(parts[i-1])
                elif 'passed' in line and 'failed' not in line and 'error' not in line:
                    # Parse line like "23 passed in 47.10s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'passed':
                            passed = int(parts[i-1])
            
            total = passed + failed + errors
            
            if result.returncode == 0:
                print(f"   ✅ {passed}/{total} tests passed")
                success = True
            else:
                print(f"   ❌ {passed}/{total} tests passed, {failed + errors} failed")
                success = False
                
                # Show some failure details
                if result.stderr:
                    print(f"   Error output: {result.stderr[:200]}...")
            
            # Store results
            self.test_results[test_info['name']] = {
                'total': total,
                'passed': passed,
                'failed': failed + errors,
                'success_rate': (passed / total * 100) if total > 0 else 0
            }
            
            self.total_tests += total
            self.passed_tests += passed
            self.failed_tests += failed + errors
            
            return success
            
        except Exception as e:
            print(f"   ❌ Error running tests: {e}")
            self.test_results[test_info['name']] = {
                'total': 0,
                'passed': 0,
                'failed': 1,
                'success_rate': 0
            }
            self.failed_tests += 1
            return False
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        duration = self.end_time - self.start_time
        overall_success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print("\n" + "=" * 80)
        print("🎯 **FINAL TEST REPORT**")
        print("=" * 80)
        
        # Overall statistics
        print(f"\n📊 **Overall Statistics:**")
        print(f"   • Total Tests Run: {self.total_tests}")
        print(f"   • Tests Passed: {self.passed_tests}")
        print(f"   • Tests Failed: {self.failed_tests}")
        print(f"   • Success Rate: {overall_success_rate:.1f}%")
        print(f"   • Execution Time: {duration:.2f} seconds")
        
        # Detailed results by suite
        print(f"\n📋 **Results by Test Suite:**")
        for suite_name, results in self.test_results.items():
            status = "✅" if results['failed'] == 0 else "❌"
            print(f"   {status} {suite_name}: {results['passed']}/{results['total']} ({results['success_rate']:.1f}%)")
        
        # Implementation status
        print(f"\n🚀 **Phase 5.1 & 5.2 Implementation Status:**")
        
        phase_51_success = self.test_results.get('Phase 5.1: Session Architecture', {}).get('success_rate', 0) >= 90
        phase_52_success = self.test_results.get('Phase 5.2: Project Analysis Engine', {}).get('success_rate', 0) >= 90
        integration_success = self.test_results.get('Phase 5 Integration Tests', {}).get('success_rate', 0) >= 90
        
        print(f"   {'✅' if phase_51_success else '❌'} Phase 5.1: Enhanced Session Architecture")
        print(f"   {'✅' if phase_52_success else '❌'} Phase 5.2: AI Project Analysis Engine")
        print(f"   {'✅' if integration_success else '❌'} Integration & Workflow Tests")
        
        # Features implemented
        print(f"\n🎯 **Features Successfully Implemented:**")
        
        if phase_51_success:
            print("   ✅ Multi-file session management")
            print("   ✅ Batch upload workflow (/batch command)")
            print("   ✅ Extended timeout handling (30 minutes)")
            print("   ✅ File categorization system")
            print("   ✅ Backward compatibility with single-file mode")
        
        if phase_52_success:
            print("   ✅ AI-powered file categorization")
            print("   ✅ Project narrative analysis")
            print("   ✅ Cross-file relationship mapping")
            print("   ✅ Content completeness assessment")
            print("   ✅ Technical stack extraction")
        
        if integration_success:
            print("   ✅ Complete multi-file workflow")
            print("   ✅ Content strategy generation")
            print("   ✅ Cross-file reference system")
            print("   ✅ Tone recommendations per phase")
            print("   ✅ Project overview generation")
        
        # Next steps
        print(f"\n🔄 **Next Steps:**")
        if overall_success_rate >= 90:
            print("   🚀 Phase 5.1 & 5.2 implementation is ready for production")
            print("   ⏭️  Begin Phase 5.3: Multi-File Content Generation")
            print("   📝 Update documentation with new multi-file features")
        elif overall_success_rate >= 70:
            print("   🔧 Minor fixes needed for remaining failing tests")
            print("   📋 Review implementation details for failed components")
            print("   🚀 Close to production readiness")
        else:
            print("   🔧 Address failing tests before proceeding")
            print("   📋 Review implementation details for failed components")
            print("   🧪 Add additional test coverage for edge cases")
        
        # Performance notes
        print(f"\n⚡ **Performance Notes:**")
        tests_per_second = self.total_tests / duration if duration > 0 else 0
        print(f"   • Test execution speed: {tests_per_second:.1f} tests/second")
        
        if duration < 30:
            print("   ✅ Fast test execution - good for development cycle")
        elif duration < 60:
            print("   ⚠️  Moderate test execution time")
        else:
            print("   ⚠️  Slow test execution - consider optimization")
        
        print("\n" + "=" * 80)
        
        # Final status
        if overall_success_rate >= 90:
            print("🎉 **PHASE 5.1 & 5.2 IMPLEMENTATION SUCCESSFUL!**")
        elif overall_success_rate >= 70:
            print("⚠️  **PHASE 5.1 & 5.2 IMPLEMENTATION MOSTLY SUCCESSFUL**")
        else:
            print("❌ **PHASE 5.1 & 5.2 IMPLEMENTATION NEEDS WORK**")
        
        print("=" * 80)
    
    def run_specific_test(self, test_name):
        """Run a specific test file"""
        test_mapping = {
            'phase51': 'tests/test_phase_5_1_session_architecture.py',
            'phase52': 'tests/test_phase_5_2_project_analyzer.py',
            'integration': 'tests/test_phase_5_integration.py'
        }
        
        if test_name not in test_mapping:
            print(f"❌ Unknown test: {test_name}")
            print(f"Available tests: {', '.join(test_mapping.keys())}")
            return False
        
        test_file = test_mapping[test_name]
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', 
                test_file,
                '-v'
            ], cwd=PROJECT_ROOT)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running test: {e}")
            return False


def main():
    """Main test execution function"""
    runner = Phase5TestRunner()
    
    # Check for specific test argument
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        print(f"🎯 Running specific test: {test_name}")
        success = runner.run_specific_test(test_name)
    else:
        print("🚀 Running all Phase 5.1 & 5.2 tests...")
        success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 