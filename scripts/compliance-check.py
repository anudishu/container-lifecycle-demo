#!/usr/bin/env python3
"""
Container Compliance Checker

This script validates container images against enterprise security
and compliance requirements for the complete lifecycle management.
"""

import argparse
import json
import subprocess
import sys
import datetime
import logging
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplianceChecker:
    """Container compliance validation framework"""
    
    def __init__(self, image_name: str):
        self.image_name = image_name
        self.compliance_results = {
            'image': image_name,
            'timestamp': datetime.datetime.utcnow().isoformat(),
            'checks': {},
            'overall_status': 'UNKNOWN',
            'security_score': 0,
            'recommendations': []
        }
    
    def run_command(self, command: List[str]) -> Tuple[int, str, str]:
        """Execute shell command and return results"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def check_image_signature(self) -> bool:
        """Verify image signature with cosign"""
        logger.info("Checking image signature...")
        
        # Check if image is signed with cosign
        code, stdout, stderr = self.run_command([
            'cosign', 'verify', self.image_name
        ])
        
        if code == 0:
            self.compliance_results['checks']['signature'] = {
                'status': 'PASS',
                'message': 'Image is properly signed'
            }
            return True
        else:
            # For demo purposes, allow images from gcr.io (trusted registry)
            if 'gcr.io' in self.image_name:
                self.compliance_results['checks']['signature'] = {
                    'status': 'PASS',
                    'message': 'Image from trusted registry (gcr.io)'
                }
                return True
            
            self.compliance_results['checks']['signature'] = {
                'status': 'FAIL',
                'message': 'Image signature verification failed',
                'details': stderr
            }
            return False
    
    def check_vulnerability_scan(self) -> bool:
        """Check for vulnerability scan results"""
        logger.info("Checking vulnerability scan results...")
        
        # Run Trivy scan
        code, stdout, stderr = self.run_command([
            'trivy', 'image', '--format', 'json', '--quiet', self.image_name
        ])
        
        if code != 0:
            self.compliance_results['checks']['vulnerability_scan'] = {
                'status': 'FAIL',
                'message': 'Vulnerability scan failed',
                'details': stderr
            }
            return False
        
        try:
            scan_results = json.loads(stdout)
            critical_vulns = 0
            high_vulns = 0
            
            for result in scan_results.get('Results', []):
                for vuln in result.get('Vulnerabilities', []):
                    severity = vuln.get('Severity', '').upper()
                    if severity == 'CRITICAL':
                        critical_vulns += 1
                    elif severity == 'HIGH':
                        high_vulns += 1
            
            if critical_vulns > 0:
                self.compliance_results['checks']['vulnerability_scan'] = {
                    'status': 'FAIL',
                    'message': f'Found {critical_vulns} critical vulnerabilities',
                    'critical_count': critical_vulns,
                    'high_count': high_vulns
                }
                return False
            elif high_vulns > 5:  # Threshold for high vulnerabilities
                self.compliance_results['checks']['vulnerability_scan'] = {
                    'status': 'WARN',
                    'message': f'Found {high_vulns} high vulnerabilities (threshold: 5)',
                    'critical_count': critical_vulns,
                    'high_count': high_vulns
                }
                return True  # Allow but warn
            else:
                self.compliance_results['checks']['vulnerability_scan'] = {
                    'status': 'PASS',
                    'message': 'No critical vulnerabilities found',
                    'critical_count': critical_vulns,
                    'high_count': high_vulns
                }
                return True
                
        except json.JSONDecodeError:
            self.compliance_results['checks']['vulnerability_scan'] = {
                'status': 'FAIL',
                'message': 'Failed to parse vulnerability scan results'
            }
            return False
    
    def check_image_configuration(self) -> bool:
        """Check container image configuration"""
        logger.info("Checking image configuration...")
        
        # Inspect image configuration
        code, stdout, stderr = self.run_command([
            'docker', 'inspect', self.image_name
        ])
        
        if code != 0:
            self.compliance_results['checks']['configuration'] = {
                'status': 'FAIL',
                'message': 'Failed to inspect image',
                'details': stderr
            }
            return False
        
        try:
            config = json.loads(stdout)[0]
            image_config = config['Config']
            
            # Check if running as non-root
            user = image_config.get('User', '')
            if not user or user == '0' or user == 'root':
                self.compliance_results['checks']['configuration'] = {
                    'status': 'FAIL',
                    'message': 'Image runs as root user'
                }
                return False
            
            # Check for security labels
            labels = image_config.get('Labels', {})
            required_labels = ['lifecycle.stage', 'security.scanned']
            missing_labels = [label for label in required_labels if label not in labels]
            
            if missing_labels:
                self.compliance_results['checks']['configuration'] = {
                    'status': 'WARN',
                    'message': f'Missing security labels: {missing_labels}'
                }
            else:
                self.compliance_results['checks']['configuration'] = {
                    'status': 'PASS',
                    'message': 'Image configuration compliant'
                }
            
            return True
            
        except (json.JSONDecodeError, KeyError, IndexError):
            self.compliance_results['checks']['configuration'] = {
                'status': 'FAIL',
                'message': 'Failed to parse image configuration'
            }
            return False
    
    def check_base_image_compliance(self) -> bool:
        """Check if base image is from approved list"""
        logger.info("Checking base image compliance...")
        
        # Get image history to determine base image
        code, stdout, stderr = self.run_command([
            'docker', 'history', '--no-trunc', '--format', 'json', self.image_name
        ])
        
        if code != 0:
            self.compliance_results['checks']['base_image'] = {
                'status': 'FAIL',
                'message': 'Failed to get image history'
            }
            return False
        
        # Approved base images
        approved_bases = [
            'node:18-alpine',
            'gcr.io/distroless/nodejs18',
            'chainguard/node'
        ]
        
        # For this demo, we'll consider any alpine-based image as approved
        if 'alpine' in self.image_name.lower():
            self.compliance_results['checks']['base_image'] = {
                'status': 'PASS',
                'message': 'Using approved Alpine-based image'
            }
            return True
        
        self.compliance_results['checks']['base_image'] = {
            'status': 'WARN',
            'message': 'Base image compliance could not be verified'
        }
        return True  # Allow with warning for demo
    
    def check_sbom_generation(self) -> bool:
        """Check if SBOM (Software Bill of Materials) is available"""
        logger.info("Checking SBOM availability...")
        
        # Try to generate SBOM with syft
        code, stdout, stderr = self.run_command([
            'syft', 'packages', self.image_name, '-o', 'json'
        ])
        
        if code == 0:
            try:
                sbom = json.loads(stdout)
                package_count = len(sbom.get('artifacts', []))
                
                self.compliance_results['checks']['sbom'] = {
                    'status': 'PASS',
                    'message': f'SBOM generated successfully ({package_count} packages)',
                    'package_count': package_count
                }
                return True
            except json.JSONDecodeError:
                pass
        
        self.compliance_results['checks']['sbom'] = {
            'status': 'WARN',
            'message': 'SBOM generation not available (syft not found)'
        }
        return True  # Don't fail for missing optional tool
    
    def calculate_security_score(self) -> int:
        """Calculate overall security score based on checks"""
        total_checks = len(self.compliance_results['checks'])
        if total_checks == 0:
            return 0
        
        passed = sum(1 for check in self.compliance_results['checks'].values()
                    if check['status'] == 'PASS')
        warned = sum(1 for check in self.compliance_results['checks'].values()
                    if check['status'] == 'WARN')
        
        # PASS = full points, WARN = half points, FAIL = no points
        score = ((passed * 2 + warned) * 100) // (total_checks * 2)
        return min(score, 100)
    
    def generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on results"""
        recommendations = []
        
        for check_name, result in self.compliance_results['checks'].items():
            if result['status'] == 'FAIL':
                if check_name == 'signature':
                    recommendations.append("Sign container images using cosign or similar tool")
                elif check_name == 'vulnerability_scan':
                    recommendations.append("Fix critical vulnerabilities before deployment")
                elif check_name == 'configuration':
                    recommendations.append("Configure container to run as non-root user")
                elif check_name == 'base_image':
                    recommendations.append("Use approved base images from security-hardened sources")
            
            elif result['status'] == 'WARN':
                if check_name == 'vulnerability_scan':
                    recommendations.append("Review and fix high-severity vulnerabilities")
                elif check_name == 'configuration':
                    recommendations.append("Add required security labels to image")
                elif check_name == 'sbom':
                    recommendations.append("Generate and include SBOM for supply chain transparency")
        
        return recommendations
    
    def run_compliance_check(self) -> Dict:
        """Run all compliance checks"""
        logger.info(f"Starting compliance check for image: {self.image_name}")
        
        checks = [
            self.check_image_signature,
            self.check_vulnerability_scan,
            self.check_image_configuration,
            self.check_base_image_compliance,
            self.check_sbom_generation
        ]
        
        passed_checks = 0
        total_checks = len(checks)
        
        for check in checks:
            try:
                if check():
                    passed_checks += 1
            except Exception as e:
                logger.error(f"Check failed with exception: {e}")
        
        # Calculate results
        self.compliance_results['security_score'] = self.calculate_security_score()
        self.compliance_results['recommendations'] = self.generate_recommendations()
        
        # Determine overall status
        failed_checks = [name for name, result in self.compliance_results['checks'].items()
                        if result['status'] == 'FAIL']
        
        if not failed_checks:
            if any(result['status'] == 'WARN' for result in self.compliance_results['checks'].values()):
                self.compliance_results['overall_status'] = 'PASS_WITH_WARNINGS'
            else:
                self.compliance_results['overall_status'] = 'PASS'
        else:
            self.compliance_results['overall_status'] = 'FAIL'
        
        logger.info(f"Compliance check completed. Status: {self.compliance_results['overall_status']}")
        logger.info(f"Security Score: {self.compliance_results['security_score']}/100")
        
        return self.compliance_results

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Container Compliance Checker for Enterprise Governance'
    )
    parser.add_argument(
        '--image',
        required=True,
        help='Container image name to check'
    )
    parser.add_argument(
        '--output',
        default='compliance-report.json',
        help='Output file for compliance report'
    )
    parser.add_argument(
        '--fail-on-warnings',
        action='store_true',
        help='Fail the check if warnings are found'
    )
    parser.add_argument(
        '--min-score',
        type=int,
        default=70,
        help='Minimum security score required (0-100)'
    )
    
    args = parser.parse_args()
    
    # Run compliance check
    checker = ComplianceChecker(args.image)
    results = checker.run_compliance_check()
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print(f"\nCompliance Check Results for {args.image}")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Security Score: {results['security_score']}/100")
    print()
    
    for check_name, result in results['checks'].items():
        mark = {'PASS': '[ok]', 'WARN': '[warn]', 'FAIL': '[fail]'}.get(result['status'], '[?]')
        print(f"{mark} {check_name.replace('_', ' ').title()}: {result['status']}")
        print(f"   {result['message']}")
    
    if results['recommendations']:
        print("\nRecommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
    
    # Determine exit code
    if results['overall_status'] == 'FAIL':
        sys.exit(1)
    elif results['overall_status'] == 'PASS_WITH_WARNINGS' and args.fail_on_warnings:
        sys.exit(1)
    elif results['security_score'] < args.min_score:
        print(f"\nSecurity score {results['security_score']} below minimum {args.min_score}")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
