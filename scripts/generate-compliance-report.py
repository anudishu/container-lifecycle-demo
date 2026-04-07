#!/usr/bin/env python3
"""
Container Lifecycle Compliance Report Generator

Generates comprehensive compliance reports for container lifecycle management,
tracking security posture, policy adherence, and governance metrics.
"""

import argparse
import json
import datetime
import subprocess
import sys
import logging
from typing import Dict, List, Any, Optional
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComplianceReportGenerator:
    """Generate comprehensive compliance reports for container lifecycle"""
    
    def __init__(self, project_id: str, registry: str = "gcr.io"):
        self.project_id = project_id
        self.registry = registry
        self.report_data = {
            'metadata': {
                'generated_at': datetime.datetime.utcnow().isoformat(),
                'project_id': project_id,
                'registry': registry,
                'report_version': '1.0.0'
            },
            'summary': {},
            'images': {},
            'policies': {},
            'security_findings': {},
            'lifecycle_metrics': {},
            'recommendations': []
        }
    
    def run_command(self, command: List[str]) -> tuple[int, str, str]:
        """Execute command and return results"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except Exception as e:
            return 1, "", str(e)
    
    def collect_image_inventory(self) -> Dict:
        """Collect inventory of container images"""
        logger.info("Collecting container image inventory...")
        
        # Get list of images from GCR
        code, stdout, stderr = self.run_command([
            'gcloud', 'container', 'images', 'list',
            '--repository', f'{self.registry}/{self.project_id}',
            '--format', 'json'
        ])
        
        if code != 0:
            logger.error(f"Failed to list images: {stderr}")
            return {}
        
        try:
            images = json.loads(stdout)
            inventory = {}
            
            for image in images:
                image_name = image['name'].split('/')[-1]
                
                # Get image tags and metadata
                tag_code, tag_stdout, tag_stderr = self.run_command([
                    'gcloud', 'container', 'images', 'list-tags',
                    image['name'],
                    '--format', 'json',
                    '--limit', '50'
                ])
                
                if tag_code == 0:
                    tags = json.loads(tag_stdout)
                    inventory[image_name] = {
                        'name': image['name'],
                        'tags': tags,
                        'total_tags': len(tags),
                        'latest_tag': self._get_latest_tag(tags),
                        'oldest_tag': self._get_oldest_tag(tags),
                        'size_analysis': self._analyze_image_sizes(tags)
                    }
                
            return inventory
            
        except json.JSONDecodeError:
            logger.error("Failed to parse image list JSON")
            return {}
    
    def _get_latest_tag(self, tags: List[Dict]) -> Optional[Dict]:
        """Get the most recently created tag"""
        if not tags:
            return None
        return max(tags, key=lambda x: x.get('timestamp', {}).get('datetime', ''))
    
    def _get_oldest_tag(self, tags: List[Dict]) -> Optional[Dict]:
        """Get the oldest tag"""
        if not tags:
            return None
        return min(tags, key=lambda x: x.get('timestamp', {}).get('datetime', ''))
    
    def _analyze_image_sizes(self, tags: List[Dict]) -> Dict:
        """Analyze image size trends"""
        sizes = []
        for tag in tags:
            if 'imageSizeBytes' in tag:
                sizes.append(int(tag['imageSizeBytes']))
        
        if not sizes:
            return {'count': 0}
        
        return {
            'count': len(sizes),
            'average_size_mb': sum(sizes) / len(sizes) / (1024 * 1024),
            'max_size_mb': max(sizes) / (1024 * 1024),
            'min_size_mb': min(sizes) / (1024 * 1024),
            'size_trend': 'increasing' if len(sizes) > 1 and sizes[-1] > sizes[0] else 'stable'
        }
    
    def analyze_security_posture(self, inventory: Dict) -> Dict:
        """Analyze security posture of container images"""
        logger.info("Analyzing security posture...")
        
        security_findings = {
            'scanned_images': 0,
            'unscanned_images': 0,
            'critical_vulnerabilities': 0,
            'high_vulnerabilities': 0,
            'medium_vulnerabilities': 0,
            'low_vulnerabilities': 0,
            'images_with_critical': [],
            'outdated_images': [],
            'unsigned_images': []
        }
        
        for image_name, image_data in inventory.items():
            for tag_info in image_data['tags']:
                image_ref = f"{image_data['name']}@{tag_info['digest']}"
                
                # Check if image has security scan results
                if self._has_security_scan(tag_info):
                    security_findings['scanned_images'] += 1
                    vulns = self._extract_vulnerabilities(tag_info)
                    security_findings['critical_vulnerabilities'] += vulns.get('critical', 0)
                    security_findings['high_vulnerabilities'] += vulns.get('high', 0)
                    security_findings['medium_vulnerabilities'] += vulns.get('medium', 0)
                    security_findings['low_vulnerabilities'] += vulns.get('low', 0)
                    
                    if vulns.get('critical', 0) > 0:
                        security_findings['images_with_critical'].append({
                            'image': image_ref,
                            'critical_count': vulns['critical']
                        })
                else:
                    security_findings['unscanned_images'] += 1
                
                # Check if image is signed
                if not self._is_image_signed(tag_info):
                    security_findings['unsigned_images'].append(image_ref)
                
                # Check if image is outdated (older than 30 days)
                if self._is_image_outdated(tag_info, days=30):
                    security_findings['outdated_images'].append({
                        'image': image_ref,
                        'age_days': self._get_image_age_days(tag_info)
                    })
        
        return security_findings
    
    def _has_security_scan(self, tag_info: Dict) -> bool:
        """Check if image has security scan results"""
        # Look for security scan metadata in labels or annotations
        return any([
            'security.scanned' in tag_info.get('labels', {}),
            'vulnerability.scan.time' in tag_info.get('labels', {}),
            'scan.time' in tag_info.get('timestamp', {})
        ])
    
    def _extract_vulnerabilities(self, tag_info: Dict) -> Dict:
        """Extract vulnerability counts from image metadata"""
        # This would normally parse actual vulnerability scan results
        # For demo purposes, we'll simulate based on labels
        labels = tag_info.get('labels', {})
        return {
            'critical': int(labels.get('vulnerabilities.critical', '0')),
            'high': int(labels.get('vulnerabilities.high', '0')),
            'medium': int(labels.get('vulnerabilities.medium', '0')),
            'low': int(labels.get('vulnerabilities.low', '0'))
        }
    
    def _is_image_signed(self, tag_info: Dict) -> bool:
        """Check if image is signed"""
        labels = tag_info.get('labels', {})
        return any([
            'cosign.sigstore.dev/signature' in labels,
            'signature.verified' in labels,
            labels.get('signed', 'false').lower() == 'true'
        ])
    
    def _is_image_outdated(self, tag_info: Dict, days: int = 30) -> bool:
        """Check if image is older than specified days"""
        timestamp = tag_info.get('timestamp', {}).get('datetime', '')
        if not timestamp:
            return False
        
        try:
            image_date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age = datetime.datetime.now(datetime.timezone.utc) - image_date
            return age.days > days
        except (ValueError, TypeError):
            return False
    
    def _get_image_age_days(self, tag_info: Dict) -> int:
        """Get image age in days"""
        timestamp = tag_info.get('timestamp', {}).get('datetime', '')
        if not timestamp:
            return 0
        
        try:
            image_date = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age = datetime.datetime.now(datetime.timezone.utc) - image_date
            return age.days
        except (ValueError, TypeError):
            return 0
    
    def analyze_policy_compliance(self, inventory: Dict) -> Dict:
        """Analyze policy compliance across images"""
        logger.info("Analyzing policy compliance...")
        
        policy_results = {
            'total_images_checked': 0,
            'compliant_images': 0,
            'non_compliant_images': 0,
            'policy_violations': {},
            'compliance_score': 0.0
        }
        
        policies = {
            'required_labels': ['lifecycle.stage', 'security.scanned', 'version'],
            'prohibited_root_user': True,
            'max_image_size_mb': 500,
            'max_age_days': 90,
            'required_health_check': True
        }
        
        violations = {
            'missing_labels': [],
            'root_user': [],
            'oversized_images': [],
            'outdated_images': [],
            'missing_health_check': []
        }
        
        for image_name, image_data in inventory.items():
            policy_results['total_images_checked'] += len(image_data['tags'])
            
            for tag_info in image_data['tags']:
                image_ref = f"{image_data['name']}:{','.join(tag_info.get('tags', ['latest']))}"
                violations_found = 0
                
                # Check required labels
                labels = tag_info.get('labels', {})
                missing_labels = [label for label in policies['required_labels'] if label not in labels]
                if missing_labels:
                    violations['missing_labels'].append({
                        'image': image_ref,
                        'missing': missing_labels
                    })
                    violations_found += 1
                
                # Check image size
                size_mb = int(tag_info.get('imageSizeBytes', 0)) / (1024 * 1024)
                if size_mb > policies['max_image_size_mb']:
                    violations['oversized_images'].append({
                        'image': image_ref,
                        'size_mb': size_mb,
                        'limit_mb': policies['max_image_size_mb']
                    })
                    violations_found += 1
                
                # Check age
                if self._is_image_outdated(tag_info, policies['max_age_days']):
                    violations['outdated_images'].append({
                        'image': image_ref,
                        'age_days': self._get_image_age_days(tag_info),
                        'limit_days': policies['max_age_days']
                    })
                    violations_found += 1
                
                if violations_found == 0:
                    policy_results['compliant_images'] += 1
                else:
                    policy_results['non_compliant_images'] += 1
        
        policy_results['policy_violations'] = violations
        
        # Calculate compliance score
        total = policy_results['total_images_checked']
        if total > 0:
            policy_results['compliance_score'] = (policy_results['compliant_images'] / total) * 100
        
        return policy_results
    
    def generate_lifecycle_metrics(self, inventory: Dict) -> Dict:
        """Generate lifecycle management metrics"""
        logger.info("Generating lifecycle metrics...")
        
        metrics = {
            'total_repositories': len(inventory),
            'total_images': sum(len(img['tags']) for img in inventory.values()),
            'storage_usage': {
                'total_size_gb': 0,
                'average_size_mb': 0,
                'size_distribution': {}
            },
            'age_distribution': {
                '0-7_days': 0,
                '8-30_days': 0,
                '31-90_days': 0,
                '91+_days': 0
            },
            'cleanup_candidates': [],
            'deployment_frequency': {},
            'tag_patterns': {}
        }
        
        all_sizes = []
        
        for image_name, image_data in inventory.items():
            for tag_info in image_data['tags']:
                # Calculate storage metrics
                size_bytes = int(tag_info.get('imageSizeBytes', 0))
                size_mb = size_bytes / (1024 * 1024)
                all_sizes.append(size_mb)
                metrics['storage_usage']['total_size_gb'] += size_bytes / (1024 * 1024 * 1024)
                
                # Age distribution
                age_days = self._get_image_age_days(tag_info)
                if age_days <= 7:
                    metrics['age_distribution']['0-7_days'] += 1
                elif age_days <= 30:
                    metrics['age_distribution']['8-30_days'] += 1
                elif age_days <= 90:
                    metrics['age_distribution']['31-90_days'] += 1
                else:
                    metrics['age_distribution']['91+_days'] += 1
                
                # Cleanup candidates (old, unused images)
                if age_days > 90 and not self._is_image_deployed(tag_info):
                    metrics['cleanup_candidates'].append({
                        'image': f"{image_data['name']}@{tag_info['digest']}",
                        'age_days': age_days,
                        'size_mb': size_mb
                    })
                
                # Tag pattern analysis
                for tag in tag_info.get('tags', []):
                    pattern = self._classify_tag_pattern(tag)
                    metrics['tag_patterns'][pattern] = metrics['tag_patterns'].get(pattern, 0) + 1
        
        if all_sizes:
            metrics['storage_usage']['average_size_mb'] = sum(all_sizes) / len(all_sizes)
        
        return metrics
    
    def _is_image_deployed(self, tag_info: Dict) -> bool:
        """Check if image is currently deployed"""
        # This would check Kubernetes deployments for image usage
        # For demo purposes, assume recent images are deployed
        return self._get_image_age_days(tag_info) <= 30
    
    def _classify_tag_pattern(self, tag: str) -> str:
        """Classify tag naming patterns"""
        import re
        
        if tag == 'latest':
            return 'latest'
        elif re.match(r'^v?\d+\.\d+\.\d+$', tag):
            return 'semver'
        elif re.match(r'^v?\d+\.\d+$', tag):
            return 'major_minor'
        elif re.match(r'^\d{8}', tag):
            return 'date_based'
        elif re.match(r'^[a-f0-9]{7,40}$', tag):
            return 'commit_hash'
        elif 'dev' in tag.lower() or 'develop' in tag.lower():
            return 'development'
        elif 'prod' in tag.lower() or 'release' in tag.lower():
            return 'production'
        else:
            return 'other'
    
    def generate_recommendations(self, security_findings: Dict, policy_results: Dict, lifecycle_metrics: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Security recommendations
        if security_findings['unscanned_images'] > 0:
            recommendations.append(
                f"Implement vulnerability scanning for {security_findings['unscanned_images']} unscanned images"
            )
        
        if security_findings['critical_vulnerabilities'] > 0:
            recommendations.append(
                f"Address {security_findings['critical_vulnerabilities']} critical vulnerabilities immediately"
            )
        
        if len(security_findings['unsigned_images']) > 0:
            recommendations.append(
                f"Implement image signing for {len(security_findings['unsigned_images'])} unsigned images"
            )
        
        # Policy recommendations
        if policy_results['compliance_score'] < 80:
            recommendations.append(
                f"Improve policy compliance score from {policy_results['compliance_score']:.1f}% to at least 80%"
            )
        
        # Lifecycle recommendations
        cleanup_size_gb = sum(img['size_mb'] for img in lifecycle_metrics['cleanup_candidates']) / 1024
        if cleanup_size_gb > 1:
            recommendations.append(
                f"Clean up {len(lifecycle_metrics['cleanup_candidates'])} old images to save {cleanup_size_gb:.2f} GB storage"
            )
        
        if lifecycle_metrics['storage_usage']['total_size_gb'] > 50:
            recommendations.append(
                "Consider implementing automated image cleanup policies for storage optimization"
            )
        
        # Tag pattern recommendations
        latest_count = lifecycle_metrics['tag_patterns'].get('latest', 0)
        if latest_count > lifecycle_metrics['total_repositories']:
            recommendations.append(
                "Reduce reliance on 'latest' tags and implement proper versioning strategy"
            )
        
        return recommendations
    
    def generate_report(self) -> Dict:
        """Generate comprehensive compliance report"""
        logger.info("Starting compliance report generation...")
        
        # Collect data
        inventory = self.collect_image_inventory()
        security_findings = self.analyze_security_posture(inventory)
        policy_results = self.analyze_policy_compliance(inventory)
        lifecycle_metrics = self.generate_lifecycle_metrics(inventory)
        recommendations = self.generate_recommendations(security_findings, policy_results, lifecycle_metrics)
        
        # Build report
        self.report_data.update({
            'summary': {
                'total_repositories': len(inventory),
                'total_images': sum(len(img['tags']) for img in inventory.values()),
                'security_score': max(0, 100 - security_findings['critical_vulnerabilities'] * 10),
                'compliance_score': policy_results['compliance_score'],
                'storage_usage_gb': lifecycle_metrics['storage_usage']['total_size_gb'],
                'cleanup_savings_gb': sum(img['size_mb'] for img in lifecycle_metrics['cleanup_candidates']) / 1024
            },
            'images': inventory,
            'security_findings': security_findings,
            'policies': policy_results,
            'lifecycle_metrics': lifecycle_metrics,
            'recommendations': recommendations
        })
        
        logger.info("Compliance report generation completed")
        return self.report_data

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Generate Container Lifecycle Compliance Report'
    )
    parser.add_argument(
        '--project-id',
        required=True,
        help='Google Cloud Project ID'
    )
    parser.add_argument(
        '--registry',
        default='gcr.io',
        help='Container registry (default: gcr.io)'
    )
    parser.add_argument(
        '--output',
        default='compliance-report.json',
        help='Output file for compliance report'
    )
    parser.add_argument(
        '--format',
        choices=['json', 'html'],
        default='json',
        help='Report format'
    )
    
    args = parser.parse_args()
    
    # Generate report
    generator = ComplianceReportGenerator(args.project_id, args.registry)
    report = generator.generate_report()
    
    # Save report
    if args.format == 'json':
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
    elif args.format == 'html':
        # Generate HTML report (simplified)
        html_content = generate_html_report(report)
        html_filename = args.output.replace('.json', '.html')
        with open(html_filename, 'w') as f:
            f.write(html_content)
    
    # Print summary
    summary = report['summary']
    print("\nContainer Lifecycle Compliance Report")
    print("=" * 50)
    print(f"Project: {args.project_id}")
    print(f"Total Repositories: {summary['total_repositories']}")
    print(f"Total Images: {summary['total_images']}")
    print(f"Security Score: {summary['security_score']}/100")
    print(f"Compliance Score: {summary['compliance_score']:.1f}%")
    print(f"Storage Usage: {summary['storage_usage_gb']:.2f} GB")
    print(f"Potential Cleanup Savings: {summary['cleanup_savings_gb']:.2f} GB")
    print()
    
    if report['recommendations']:
        print("Top Recommendations:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"{i}. {rec}")
    
    print(f"\nFull report saved to: {args.output}")

def generate_html_report(report: Dict) -> str:
    """Generate HTML report (simplified version)"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Container Lifecycle Compliance Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; }}
            .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 5px; }}
            .recommendations {{ background: #fff3cd; padding: 15px; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Container Lifecycle Compliance Report</h1>
            <p>Generated: {report['metadata']['generated_at']}</p>
            <p>Project: {report['metadata']['project_id']}</p>
        </div>
        
        <div class="section">
            <h2>Summary Metrics</h2>
            <div class="metric">
                <h3>{report['summary']['total_repositories']}</h3>
                <p>Repositories</p>
            </div>
            <div class="metric">
                <h3>{report['summary']['total_images']}</h3>
                <p>Images</p>
            </div>
            <div class="metric">
                <h3>{report['summary']['security_score']}/100</h3>
                <p>Security Score</p>
            </div>
            <div class="metric">
                <h3>{report['summary']['compliance_score']:.1f}%</h3>
                <p>Compliance</p>
            </div>
        </div>
        
        <div class="section recommendations">
            <h2>Key Recommendations</h2>
            <ul>
                {''.join(f'<li>{rec}</li>' for rec in report['recommendations'][:10])}
            </ul>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    main()
