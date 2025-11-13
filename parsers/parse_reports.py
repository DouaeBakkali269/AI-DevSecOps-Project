#!/usr/bin/env python3
"""
Universal Vulnerability Report Parser
Converts SAST, SCA, and DAST reports into unified JSON format
"""

import json
import xml.etree.ElementTree as ET
import xmltodict
import argparse
from pathlib import Path
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class VulnerabilityParser:
    """Parse security scan reports from multiple tools"""
    
    CWE_MAPPING = {
        "SQL Injection": "CWE-89",
        "XSS": "CWE-79",
        "Path Traversal": "CWE-22",
        "Command Injection": "CWE-78",
        "Insecure Deserialization": "CWE-502",
        "Broken Authentication": "CWE-287",
        "Sensitive Data Exposure": "CWE-200",
        "XXE": "CWE-611",
        "Broken Access Control": "CWE-284",
        "Security Misconfiguration": "CWE-16"
    }
    
    SEVERITY_MAPPING = {
        "CRITICAL": 5,
        "HIGH": 4,
        "MEDIUM": 3,
        "LOW": 2,
        "INFO": 1
    }
    
    def __init__(self, input_dir: Path, output_file: Path):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.vulnerabilities = []
        
    def parse_all(self):
        """Parse all reports in input directory"""
        logger.info(f"Parsing reports from {self.input_dir}")
        
        for report_file in self.input_dir.glob("*"):
            try:
                if "codeql" in report_file.name and report_file.suffix == ".sarif":
                    self._parse_codeql_sarif(report_file)
                elif "semgrep" in report_file.name:
                    self._parse_semgrep(report_file)
                elif "nodejsscan" in report_file.name:
                    self._parse_nodejsscan(report_file)
                elif "bandit" in report_file.name:
                    self._parse_bandit(report_file)
                elif "npm_audit" in report_file.name:
                    self._parse_npm_audit(report_file)
                elif "snyk" in report_file.name:
                    self._parse_snyk(report_file)
                elif "zap" in report_file.name:
                    if report_file.suffix == ".json":
                        self._parse_zap_json(report_file)
                    elif report_file.suffix == ".xml":
                        self._parse_zap_xml(report_file)
                        
            except Exception as e:
                logger.error(f"Error parsing {report_file.name}: {e}")
                
        logger.info(f"Total vulnerabilities found: {len(self.vulnerabilities)}")
        
    def _parse_codeql_sarif(self, file_path: Path):
        """Parse CodeQL SARIF report"""
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)
            
            for run in data.get("runs", []):
                tool_name = run.get("tool", {}).get("driver", {}).get("name", "CodeQL")
                
                for result in run.get("results", []):
                    # Extract location information
                    locations = result.get("locations", [])
                    if not locations:
                        continue
                    
                    location = locations[0].get("physicalLocation", {})
                    artifact_location = location.get("artifactLocation", {})
                    region = location.get("region", {})
                    
                    # Extract rule information
                    rule_id = result.get("ruleId", "Unknown")
                    message = result.get("message", {}).get("text", "")
                    level = result.get("level", "warning")
                    
                    vuln = {
                        "tool": "CodeQL",
                        "type": "SAST",
                        "title": rule_id,
                        "severity": self._map_codeql_level(level),
                        "description": message,
                        "file": artifact_location.get("uri", ""),
                        "line": region.get("startLine", 0),
                        "code_snippet": region.get("snippet", {}).get("text", ""),
                        "cwe": self._extract_cwe_from_codeql(result),
                        "owasp": self._map_to_owasp(rule_id),
                        "recommendation": self._get_codeql_recommendation(result)
                    }
                    self.vulnerabilities.append(vuln)
                    
            logger.info(f"Parsed {len([v for v in self.vulnerabilities if v['tool'] == 'CodeQL'])} CodeQL findings")
            
        except Exception as e:
            logger.error(f"Error parsing CodeQL SARIF: {e}")
            import traceback
            traceback.print_exc()

    def _map_codeql_level(self, level: str) -> str:
        """Map CodeQL severity levels to standard levels"""
        mapping = {
            "error": "HIGH",
            "warning": "MEDIUM",
            "note": "LOW",
            "none": "INFO"
        }
        return mapping.get(level.lower(), "MEDIUM")

    def _extract_cwe_from_codeql(self, result: dict) -> str:
        """Extract CWE from CodeQL result"""
        # Check properties for CWE tags
        properties = result.get("properties", {})
        tags = properties.get("tags", [])
        
        for tag in tags:
            if "cwe" in tag.lower():
                # Extract CWE number using regex
                import re
                match = re.search(r'cwe-?(\d+)', tag, re.IGNORECASE)
                if match:
                    return f"CWE-{match.group(1)}"
        
        # Check in rule metadata
        rule = result.get("rule", {})
        if rule:
            rule_properties = rule.get("properties", {})
            rule_tags = rule_properties.get("tags", [])
            for tag in rule_tags:
                if "cwe" in tag.lower():
                    import re
                    match = re.search(r'cwe-?(\d+)', tag, re.IGNORECASE)
                    if match:
                        return f"CWE-{match.group(1)}"
        
        return "CWE-Unknown"

    def _get_codeql_recommendation(self, result: dict) -> str:
        """Get recommendation from CodeQL result"""
        # Try to get help text
        message = result.get("message", {})
        help_text = message.get("markdown", message.get("text", ""))
        
        if help_text:
            return f"Review and remediate: {help_text[:200]}"
        
        return "Review CodeQL findings and apply secure coding practices"
        
    def _parse_semgrep(self, file_path: Path):
        """Parse Semgrep SAST report"""
        with open(file_path) as f:
            data = json.load(f)
            
        for result in data.get("results", []):
            vuln = {
                "tool": "Semgrep",
                "type": "SAST",
                "title": result.get("check_id", "Unknown"),
                "severity": result.get("extra", {}).get("severity", "MEDIUM").upper(),
                "description": result.get("extra", {}).get("message", ""),
                "file": result.get("path", ""),
                "line": result.get("start", {}).get("line", 0),
                "code_snippet": result.get("extra", {}).get("lines", ""),
                "cwe": self._extract_cwe(result.get("check_id", "")),
                "owasp": self._map_to_owasp(result.get("check_id", "")),
                "recommendation": result.get("extra", {}).get("fix", "Review and remediate")
            }
            self.vulnerabilities.append(vuln)
            
    def _parse_nodejsscan(self, file_path: Path):
        """Parse NodeJsScan SAST report"""
        with open(file_path) as f:
            data = json.load(f)
            
        for category, findings in data.get("sec_issues", {}).items():
            for finding in findings:
                vuln = {
                    "tool": "NodeJsScan",
                    "type": "SAST",
                    "title": finding.get("title", category),
                    "severity": finding.get("severity", "MEDIUM").upper(),
                    "description": finding.get("description", ""),
                    "file": finding.get("path", ""),
                    "line": finding.get("line", 0),
                    "code_snippet": finding.get("code", ""),
                    "cwe": self.CWE_MAPPING.get(category, "CWE-Unknown"),
                    "owasp": self._map_to_owasp(category),
                    "recommendation": finding.get("solution", "")
                }
                self.vulnerabilities.append(vuln)
                
    def _parse_bandit(self, file_path: Path):
        """Parse Bandit SAST report"""
        with open(file_path) as f:
            data = json.load(f)
            
        for result in data.get("results", []):
            vuln = {
                "tool": "Bandit",
                "type": "SAST",
                "title": result.get("test_name", "Unknown"),
                "severity": result.get("issue_severity", "MEDIUM").upper(),
                "description": result.get("issue_text", ""),
                "file": result.get("filename", ""),
                "line": result.get("line_number", 0),
                "code_snippet": result.get("code", ""),
                "cwe": result.get("issue_cwe", {}).get("id", ""),
                "owasp": self._map_to_owasp(result.get("test_name", "")),
                "recommendation": "Review security best practices"
            }
            self.vulnerabilities.append(vuln)
            
    def _parse_npm_audit(self, file_path: Path):
        """Parse npm audit SCA report"""
        with open(file_path) as f:
            data = json.load(f)
            
        for vuln_id, vuln_data in data.get("vulnerabilities", {}).items():
            vuln = {
                "tool": "npm audit",
                "type": "SCA",
                "title": vuln_data.get("name", vuln_id),
                "severity": vuln_data.get("severity", "medium").upper(),
                "description": vuln_data.get("via", [{}])[0].get("title", "") if isinstance(vuln_data.get("via"), list) else "",
                "package": vuln_data.get("name", ""),
                "version": vuln_data.get("range", ""),
                "fixed_in": vuln_data.get("fixAvailable", {}).get("version", ""),
                "cwe": "",
                "owasp": "A06:2021 - Vulnerable Components",
                "recommendation": f"Update to version {vuln_data.get('fixAvailable', {}).get('version', 'latest')}"
            }
            self.vulnerabilities.append(vuln)
            
    def _parse_snyk(self, file_path: Path):
        """Parse Snyk SCA report"""
        with open(file_path) as f:
            data = json.load(f)
        
        # Handle both single project (dict) and multi-project (list) formats
        projects = data if isinstance(data, list) else [data]
        
        for project in projects:
            project_name = project.get("projectName", "unknown")
            vulnerabilities = project.get("vulnerabilities", [])
            
            for vuln in vulnerabilities:
                vulnerability = {
                    "tool": "Snyk",
                    "type": "SCA",
                    "title": vuln.get("title", vuln.get("id", "")),
                    "severity": vuln.get("severity", "medium").upper(),
                    "description": vuln.get("description", "")[:200] if vuln.get("description") else "",
                    "package": vuln.get("packageName", vuln.get("moduleName", "")),
                    "version": vuln.get("version", ""),
                    "fixed_in": vuln.get("fixedIn", []),
                    "cwe": vuln.get("identifiers", {}).get("CWE", [""])[0] if vuln.get("identifiers") else "",
                    "cvss_score": vuln.get("cvssScore", 0),
                    "owasp": "A06:2021 - Vulnerable Components",
                    "recommendation": f"Upgrade to {', '.join(vuln.get('fixedIn', ['latest']))}" if vuln.get('fixedIn') else "Review Snyk recommendations",
                    "project": project_name
                }
                self.vulnerabilities.append(vulnerability)
            
    def _parse_zap_json(self, file_path: Path):
        """Parse OWASP ZAP JSON report"""
        with open(file_path) as f:
            data = json.load(f)
            
        for site in data.get("site", []):
            for alert in site.get("alerts", []):
                vuln = {
                    "tool": "OWASP ZAP",
                    "type": "DAST",
                    "title": alert.get("name", "Unknown"),
                    "severity": self._map_zap_risk(alert.get("riskcode", "0")),
                    "description": alert.get("desc", ""),
                    "url": alert.get("instances", [{}])[0].get("uri", ""),
                    "method": alert.get("instances", [{}])[0].get("method", ""),
                    "param": alert.get("instances", [{}])[0].get("param", ""),
                    "cwe": f"CWE-{alert.get('cweid', 'Unknown')}",
                    "owasp": self._map_to_owasp(alert.get("name", "")),
                    "recommendation": alert.get("solution", "")
                }
                self.vulnerabilities.append(vuln)
                
    def _parse_zap_xml(self, file_path: Path):
        """Parse OWASP ZAP XML report"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        for site in root.findall(".//site"):
            for alert in site.findall(".//alertitem"):
                vuln = {
                    "tool": "OWASP ZAP",
                    "type": "DAST",
                    "title": alert.find("name").text if alert.find("name") is not None else "Unknown",
                    "severity": self._map_zap_risk(alert.find("riskcode").text if alert.find("riskcode") is not None else "0"),
                    "description": alert.find("desc").text if alert.find("desc") is not None else "",
                    "url": alert.find("uri").text if alert.find("uri") is not None else "",
                    "cwe": f"CWE-{alert.find('cweid').text}" if alert.find("cweid") is not None else "CWE-Unknown",
                    "owasp": self._map_to_owasp(alert.find("name").text if alert.find("name") is not None else ""),
                    "recommendation": alert.find("solution").text if alert.find("solution") is not None else ""
                }
                self.vulnerabilities.append(vuln)
                
    def _map_zap_risk(self, risk_code: str) -> str:
        """Map ZAP risk codes to severity levels"""
        mapping = {
            "3": "HIGH",
            "2": "MEDIUM",
            "1": "LOW",
            "0": "INFO"
        }
        return mapping.get(str(risk_code), "MEDIUM")
        
    def _extract_cwe(self, check_id: str) -> str:
        """Extract CWE from check ID or map common patterns"""
        import re
        match = re.search(r'CWE-(\d+)', check_id, re.IGNORECASE)
        if match:
            return f"CWE-{match.group(1)}"
        return "CWE-Unknown"
        
    def _map_to_owasp(self, vulnerability_type: str) -> str:
        """Map vulnerability to OWASP Top 10 2021"""
        owasp_mapping = {
            "sql": "A03:2021 - Injection",
            "injection": "A03:2021 - Injection",
            "xss": "A03:2021 - Injection",
            "authentication": "A07:2021 - Identification and Authentication Failures",
            "session": "A07:2021 - Identification and Authentication Failures",
            "access": "A01:2021 - Broken Access Control",
            "authorization": "A01:2021 - Broken Access Control",
            "crypto": "A02:2021 - Cryptographic Failures",
            "sensitive": "A02:2021 - Cryptographic Failures",
            "xxe": "A05:2021 - Security Misconfiguration",
            "deserialization": "A08:2021 - Software and Data Integrity Failures",
            "component": "A06:2021 - Vulnerable and Outdated Components",
            "logging": "A09:2021 - Security Logging and Monitoring Failures",
            "ssrf": "A10:2021 - Server-Side Request Forgery"
        }
        
        vulnerability_lower = vulnerability_type.lower()
        for key, value in owasp_mapping.items():
            if key in vulnerability_lower:
                return value
                
        return "A04:2021 - Insecure Design"
        
    def save_results(self):
        """Save parsed vulnerabilities to JSON"""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "metadata": {
                "total_vulnerabilities": len(self.vulnerabilities),
                "by_severity": self._count_by_severity(),
                "by_type": self._count_by_type(),
                "by_tool": self._count_by_tool()
            },
            "vulnerabilities": self.vulnerabilities
        }
        
        with open(self.output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Results saved to {self.output_file}")
        
    def _count_by_severity(self) -> Dict[str, int]:
        """Count vulnerabilities by severity"""
        counts = {}
        for vuln in self.vulnerabilities:
            severity = vuln.get("severity", "UNKNOWN")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
        
    def _count_by_type(self) -> Dict[str, int]:
        """Count vulnerabilities by type (SAST/SCA/DAST)"""
        counts = {}
        for vuln in self.vulnerabilities:
            vuln_type = vuln.get("type", "UNKNOWN")
            counts[vuln_type] = counts.get(vuln_type, 0) + 1
        return counts
        
    def _count_by_tool(self) -> Dict[str, int]:
        """Count vulnerabilities by scanning tool"""
        counts = {}
        for vuln in self.vulnerabilities:
            tool = vuln.get("tool", "UNKNOWN")
            counts[tool] = counts.get(tool, 0) + 1
        return counts


def main():
    parser = argparse.ArgumentParser(description="Parse vulnerability reports")
    parser.add_argument("--input", required=True, help="Input directory with scan reports")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    vulnerability_parser = VulnerabilityParser(args.input, args.output)
    vulnerability_parser.parse_all()
    vulnerability_parser.save_results()
    
    logger.info("✅ Parsing complete!")


if __name__ == "__main__":
    main()
