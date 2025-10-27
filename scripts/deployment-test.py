#!/usr/bin/env python3
"""
Deployment Test Suite

Validates deployed container application endpoints, security,
and performance characteristics as part of lifecycle management.
"""

import argparse
import json
import requests
import time
import sys
import logging
from typing import Dict, List, Tuple, Optional
from urllib.parse import urlparse
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentTester:
    """Container deployment validation framework"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.timeout = timeout
        self.results = {
            'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'base_url': base_url,
            'tests': {},
            'overall_status': 'UNKNOWN',
            'performance_metrics': {}
        }
    
    def make_request(self, endpoint: str, method: str = 'GET', **kwargs) -> Tuple[bool, Dict]:
        """Make HTTP request and return success status and details"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            start_time = time.time()
            response = self.session.request(method, url, **kwargs)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            return True, {
                'status_code': response.status_code,
                'response_time_ms': response_time,
                'headers': dict(response.headers),
                'content': response.text[:1000] if response.text else '',  # Truncate for logging
                'success': response.status_code < 400
            }
            
        except Exception as e:
            return False, {
                'error': str(e),
                'success': False
            }
    
    def test_health_endpoint(self) -> bool:
        """Test application health endpoint"""
        logger.info("Testing health endpoint...")
        
        success, details = self.make_request('/health')
        
        if not success:
            self.results['tests']['health'] = {
                'status': 'FAIL',
                'message': 'Health endpoint unreachable',
                'details': details
            }
            return False
        
        if not details['success']:
            self.results['tests']['health'] = {
                'status': 'FAIL',
                'message': f'Health endpoint returned status {details["status_code"]}',
                'details': details
            }
            return False
        
        try:
            response_data = json.loads(details['content'])
            if response_data.get('status') == 'healthy':
                self.results['tests']['health'] = {
                    'status': 'PASS',
                    'message': 'Health endpoint responding correctly',
                    'response_time_ms': details['response_time_ms'],
                    'details': response_data
                }
                return True
            else:
                self.results['tests']['health'] = {
                    'status': 'FAIL',
                    'message': 'Health endpoint reports unhealthy status',
                    'details': details
                }
                return False
        except json.JSONDecodeError:
            self.results['tests']['health'] = {
                'status': 'FAIL',
                'message': 'Health endpoint returned invalid JSON',
                'details': details
            }
            return False
    
    def test_readiness_endpoint(self) -> bool:
        """Test application readiness endpoint"""
        logger.info("Testing readiness endpoint...")
        
        success, details = self.make_request('/readiness')
        
        if not success or not details['success']:
            self.results['tests']['readiness'] = {
                'status': 'FAIL',
                'message': 'Readiness endpoint failed',
                'details': details
            }
            return False
        
        try:
            response_data = json.loads(details['content'])
            if response_data.get('status') == 'ready':
                self.results['tests']['readiness'] = {
                    'status': 'PASS',
                    'message': 'Readiness endpoint responding correctly',
                    'response_time_ms': details['response_time_ms'],
                    'details': response_data
                }
                return True
            else:
                self.results['tests']['readiness'] = {
                    'status': 'FAIL',
                    'message': 'Application not ready',
                    'details': details
                }
                return False
        except json.JSONDecodeError:
            self.results['tests']['readiness'] = {
                'status': 'FAIL',
                'message': 'Readiness endpoint returned invalid JSON',
                'details': details
            }
            return False
    
    def test_main_endpoint(self) -> bool:
        """Test main application endpoint"""
        logger.info("Testing main endpoint...")
        
        success, details = self.make_request('/')
        
        if not success or not details['success']:
            self.results['tests']['main_endpoint'] = {
                'status': 'FAIL',
                'message': 'Main endpoint failed',
                'details': details
            }
            return False
        
        try:
            response_data = json.loads(details['content'])
            if 'message' in response_data and 'version' in response_data:
                self.results['tests']['main_endpoint'] = {
                    'status': 'PASS',
                    'message': 'Main endpoint responding correctly',
                    'response_time_ms': details['response_time_ms'],
                    'details': response_data
                }
                return True
            else:
                self.results['tests']['main_endpoint'] = {
                    'status': 'FAIL',
                    'message': 'Main endpoint missing required fields',
                    'details': details
                }
                return False
        except json.JSONDecodeError:
            self.results['tests']['main_endpoint'] = {
                'status': 'FAIL',
                'message': 'Main endpoint returned invalid JSON',
                'details': details
            }
            return False
    
    def test_lifecycle_endpoint(self) -> bool:
        """Test container lifecycle endpoint"""
        logger.info("Testing lifecycle endpoint...")
        
        success, details = self.make_request('/lifecycle')
        
        if not success or not details['success']:
            self.results['tests']['lifecycle'] = {
                'status': 'FAIL',
                'message': 'Lifecycle endpoint failed',
                'details': details
            }
            return False
        
        try:
            response_data = json.loads(details['content'])
            required_fields = ['stage', 'image', 'deployment', 'security']
            
            if all(field in response_data for field in required_fields):
                self.results['tests']['lifecycle'] = {
                    'status': 'PASS',
                    'message': 'Lifecycle endpoint providing complete information',
                    'response_time_ms': details['response_time_ms'],
                    'details': response_data
                }
                return True
            else:
                missing_fields = [f for f in required_fields if f not in response_data]
                self.results['tests']['lifecycle'] = {
                    'status': 'FAIL',
                    'message': f'Lifecycle endpoint missing fields: {missing_fields}',
                    'details': details
                }
                return False
        except json.JSONDecodeError:
            self.results['tests']['lifecycle'] = {
                'status': 'FAIL',
                'message': 'Lifecycle endpoint returned invalid JSON',
                'details': details
            }
            return False
    
    def test_security_headers(self) -> bool:
        """Test security headers"""
        logger.info("Testing security headers...")
        
        success, details = self.make_request('/')
        
        if not success:
            self.results['tests']['security_headers'] = {
                'status': 'FAIL',
                'message': 'Cannot test security headers - endpoint unreachable',
                'details': details
            }
            return False
        
        headers = details['headers']
        required_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        missing_headers = [h for h in required_headers if h not in headers]
        
        if missing_headers:
            self.results['tests']['security_headers'] = {
                'status': 'WARN',
                'message': f'Missing security headers: {missing_headers}',
                'present_headers': [h for h in required_headers if h in headers],
                'missing_headers': missing_headers
            }
            return True  # Warn but don't fail
        else:
            self.results['tests']['security_headers'] = {
                'status': 'PASS',
                'message': 'All required security headers present',
                'security_headers': {h: headers[h] for h in required_headers}
            }
            return True
    
    def test_performance(self) -> bool:
        """Test application performance"""
        logger.info("Testing performance metrics...")
        
        # Test multiple requests to get average response time
        response_times = []
        failed_requests = 0
        
        for i in range(5):
            success, details = self.make_request('/health')
            if success and details['success']:
                response_times.append(details['response_time_ms'])
            else:
                failed_requests += 1
        
        if not response_times:
            self.results['tests']['performance'] = {
                'status': 'FAIL',
                'message': 'All performance test requests failed'
            }
            return False
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        self.results['performance_metrics'] = {
            'average_response_time_ms': avg_response_time,
            'max_response_time_ms': max_response_time,
            'min_response_time_ms': min_response_time,
            'successful_requests': len(response_times),
            'failed_requests': failed_requests,
            'success_rate': len(response_times) / (len(response_times) + failed_requests)
        }
        
        # Performance thresholds
        if avg_response_time > 1000:  # 1 second threshold
            self.results['tests']['performance'] = {
                'status': 'WARN',
                'message': f'Average response time ({avg_response_time:.2f}ms) exceeds threshold',
                'metrics': self.results['performance_metrics']
            }
        elif avg_response_time > 2000:  # 2 second fail threshold
            self.results['tests']['performance'] = {
                'status': 'FAIL',
                'message': f'Average response time ({avg_response_time:.2f}ms) unacceptable',
                'metrics': self.results['performance_metrics']
            }
            return False
        else:
            self.results['tests']['performance'] = {
                'status': 'PASS',
                'message': f'Performance acceptable (avg: {avg_response_time:.2f}ms)',
                'metrics': self.results['performance_metrics']
            }
        
        return True
    
    def test_kubernetes_deployment(self) -> bool:
        """Test Kubernetes deployment status"""
        logger.info("Testing Kubernetes deployment...")
        
        try:
            # Check deployment status
            result = subprocess.run([
                'kubectl', 'get', 'deployment', 'container-lifecycle-demo',
                '-n', 'container-lifecycle-demo', '-o', 'json'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                self.results['tests']['kubernetes'] = {
                    'status': 'FAIL',
                    'message': 'Failed to get Kubernetes deployment status',
                    'error': result.stderr
                }
                return False
            
            deployment_info = json.loads(result.stdout)
            status = deployment_info.get('status', {})
            
            ready_replicas = status.get('readyReplicas', 0)
            desired_replicas = status.get('replicas', 0)
            
            if ready_replicas == desired_replicas and ready_replicas > 0:
                self.results['tests']['kubernetes'] = {
                    'status': 'PASS',
                    'message': f'Deployment healthy: {ready_replicas}/{desired_replicas} replicas ready',
                    'ready_replicas': ready_replicas,
                    'desired_replicas': desired_replicas
                }
                return True
            else:
                self.results['tests']['kubernetes'] = {
                    'status': 'FAIL',
                    'message': f'Deployment unhealthy: {ready_replicas}/{desired_replicas} replicas ready',
                    'ready_replicas': ready_replicas,
                    'desired_replicas': desired_replicas
                }
                return False
                
        except subprocess.TimeoutExpired:
            self.results['tests']['kubernetes'] = {
                'status': 'FAIL',
                'message': 'Kubectl command timed out'
            }
            return False
        except Exception as e:
            self.results['tests']['kubernetes'] = {
                'status': 'WARN',
                'message': f'Could not check Kubernetes status: {e}'
            }
            return True  # Don't fail if kubectl is not available
    
    def run_all_tests(self) -> Dict:
        """Run all deployment tests"""
        logger.info(f"Starting deployment tests for: {self.base_url}")
        
        tests = [
            self.test_health_endpoint,
            self.test_readiness_endpoint,
            self.test_main_endpoint,
            self.test_lifecycle_endpoint,
            self.test_security_headers,
            self.test_performance,
            self.test_kubernetes_deployment
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test failed with exception: {e}")
        
        # Determine overall status
        failed_tests = [name for name, result in self.results['tests'].items()
                       if result['status'] == 'FAIL']
        
        if not failed_tests:
            warned_tests = [name for name, result in self.results['tests'].items()
                          if result['status'] == 'WARN']
            if warned_tests:
                self.results['overall_status'] = 'PASS_WITH_WARNINGS'
            else:
                self.results['overall_status'] = 'PASS'
        else:
            self.results['overall_status'] = 'FAIL'
        
        logger.info(f"Deployment tests completed. Status: {self.results['overall_status']}")
        logger.info(f"Tests passed: {passed_tests}/{total_tests}")
        
        return self.results

def get_service_url() -> Optional[str]:
    """Get service URL from Kubernetes"""
    try:
        # Try to get LoadBalancer service external IP
        result = subprocess.run([
            'kubectl', 'get', 'service', 'container-lifecycle-demo-lb',
            '-n', 'container-lifecycle-demo',
            '-o', 'jsonpath={.status.loadBalancer.ingress[0].ip}'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and result.stdout.strip():
            return f"http://{result.stdout.strip()}"
        
        # Fallback to ClusterIP with port-forward
        logger.warning("LoadBalancer IP not available, attempting port-forward...")
        return "http://localhost:8080"  # Assume port-forward is set up
        
    except Exception as e:
        logger.warning(f"Could not get service URL: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Deployment Test Suite for Container Lifecycle Management'
    )
    parser.add_argument(
        '--url',
        help='Base URL of the deployed application'
    )
    parser.add_argument(
        '--output',
        default='deployment-test-results.json',
        help='Output file for test results'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Request timeout in seconds'
    )
    
    args = parser.parse_args()
    
    # Determine URL
    if args.url:
        base_url = args.url
    else:
        base_url = get_service_url()
        if not base_url:
            logger.error("Could not determine service URL. Please provide --url argument.")
            sys.exit(1)
    
    # Run tests
    tester = DeploymentTester(base_url, args.timeout)
    results = tester.run_all_tests()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\\nDeployment Test Results for {base_url}")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print()
    
    for test_name, result in results['tests'].items():
        status_emoji = "✅" if result['status'] == 'PASS' else "⚠️" if result['status'] == 'WARN' else "❌"
        print(f"{status_emoji} {test_name.replace('_', ' ').title()}: {result['status']}")
        print(f"   {result['message']}")
    
    if 'performance_metrics' in results and results['performance_metrics']:
        print("\\nPerformance Metrics:")
        metrics = results['performance_metrics']
        print(f"   Average Response Time: {metrics['average_response_time_ms']:.2f}ms")
        print(f"   Success Rate: {metrics['success_rate']*100:.1f}%")
    
    # Exit with appropriate code
    if results['overall_status'] == 'FAIL':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
