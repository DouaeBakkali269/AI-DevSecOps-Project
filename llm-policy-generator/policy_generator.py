#!/usr/bin/env python3
"""
LLM-Based Security Policy Generator
Generates security policies from vulnerability data using multiple LLMs
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import logging
import os
from datetime import datetime

import openai
from anthropic import Anthropic
import requests

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class PolicyGenerator:
    """Generate security policies using LLMs"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.policies = []
        
        # Initialize appropriate client
        if "gpt" in model_name.lower():
            openai.api_key = os.getenv("OPENAI_API_KEY")
            self.client_type = "openai"
        elif "claude" in model_name.lower():
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.client_type = "anthropic"
        elif "deepseek" in model_name.lower() or "llama" in model_name.lower():
            self.together_api_key = os.getenv("TOGETHER_API_KEY")
            self.client_type = "together"
        else:
            raise ValueError(f"Unknown model: {model_name}")
            
    def generate_policies(self, vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate policies for all vulnerabilities"""
        logger.info(f"Generating policies with {self.model_name}...")
        
        # Group vulnerabilities by type for batch processing
        vuln_groups = self._group_vulnerabilities(vulnerabilities)
        
        for group_name, vulns in vuln_groups.items():
            logger.info(f"Processing {len(vulns)} {group_name} vulnerabilities")
            policy = self._generate_policy_for_group(group_name, vulns)
            self.policies.append(policy)
            
        return self.policies
        
    def _group_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict[str, List[Dict]]:
        """Group vulnerabilities by title/category"""
        groups = {}
        for vuln in vulnerabilities:
            title = vuln.get("title", "Unknown")
            if title not in groups:
                groups[title] = []
            groups[title].append(vuln)
        return groups
        
    def _generate_policy_for_group(self, group_name: str, vulnerabilities: List[Dict]) -> Dict:
        """Generate policy for a group of similar vulnerabilities"""
        
        # Build context from vulnerabilities
        context = self._build_context(group_name, vulnerabilities)
        
        # Generate policy using appropriate model
        if self.client_type == "openai":
            policy_content = self._generate_with_openai(context)
        elif self.client_type == "anthropic":
            policy_content = self._generate_with_anthropic(context)
        elif self.client_type == "together":
            policy_content = self._generate_with_together(context)
        else:
            policy_content = "Error: Unknown client type"
            
        # Structure the policy
        policy = {
            "vulnerability_group": group_name,
            "affected_count": len(vulnerabilities),
            "severity": self._get_max_severity(vulnerabilities),
            "policy": policy_content,
            "generated_by": self.model_name,
            "generated_at": datetime.now().isoformat(),
            "vulnerabilities": vulnerabilities
        }
        
        return policy
        
    def _build_context(self, group_name: str, vulnerabilities: List[Dict]) -> str:
        """Build context for LLM prompt"""
        context = f"""You are a security policy expert. Generate a comprehensive security policy for the following vulnerability group.

Vulnerability Type: {group_name}
Number of Instances: {len(vulnerabilities)}
Severity: {self._get_max_severity(vulnerabilities)}

Sample Vulnerability Details:
"""
        # Add details from first few vulnerabilities
        for vuln in vulnerabilities[:3]:
            context += f"""
- Tool: {vuln.get('tool', 'Unknown')}
- Type: {vuln.get('type', 'Unknown')}
- Description: {vuln.get('description', 'No description')}
- Location: {vuln.get('file', 'Unknown')}:{vuln.get('line', 0)}
- CWE: {vuln.get('cwe', 'Unknown')}
- OWASP: {vuln.get('owasp', 'Unknown')}
"""
        
        context += """
Generate a security policy following this structure:

1. POLICY STATEMENT
   - Clear, actionable policy statement
   
2. SCOPE
   - What this policy covers
   - Which systems/components are affected
   
3. REQUIREMENTS
   - Specific technical requirements
   - Implementation guidelines
   
4. COMPLIANCE MAPPING
   - Map to NIST Cybersecurity Framework (identify relevant functions and categories)
   - Map to ISO/IEC 27001:2022 (identify relevant controls)
   - Map to OWASP Top 10 2021 (if applicable)
   
5. IMPLEMENTATION GUIDANCE
   - Step-by-step remediation steps
   - Code examples or configuration changes (if applicable)
   - Tools and technologies to use
   
6. VERIFICATION
   - How to verify compliance
   - Testing procedures
   
7. MONITORING & MAINTENANCE
   - Ongoing monitoring requirements
   - Review frequency

Make the policy:
- Clear and actionable for developers
- Compliant with security standards (NIST CSF, ISO 27001)
- Specific to the vulnerability type
- Professional and formal in tone
"""
        
        return context
        
    def _generate_with_openai(self, context: str) -> str:
        """Generate policy using OpenAI GPT-4"""
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a security policy expert specializing in DevSecOps and compliance frameworks."},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Error generating policy: {e}"
            
    def _generate_with_anthropic(self, context: str) -> str:
        """Generate policy using Claude"""
        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": context}
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return f"Error generating policy: {e}"
            
    def _generate_with_together(self, context: str) -> str:
        """Generate policy using Together AI (DeepSeek/LLaMA)"""
        try:
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.together_api_key}",
                "Content-Type": "application/json"
            }
            
            # Use DeepSeek R1 or LLaMA 3.3
            model = "deepseek-ai/deepseek-r1" if "deepseek" in self.model_name.lower() else "meta-llama/Llama-3.3-70B-Instruct"
            
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a security policy expert."},
                    {"role": "user", "content": context}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Together API error: {e}")
            return f"Error generating policy: {e}"
            
    def _get_max_severity(self, vulnerabilities: List[Dict]) -> str:
        """Get maximum severity from vulnerability list"""
        severity_order = {"CRITICAL": 5, "HIGH": 4, "MEDIUM": 3, "LOW": 2, "INFO": 1}
        max_severity = "INFO"
        max_value = 0
        
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "INFO")
            value = severity_order.get(severity, 0)
            if value > max_value:
                max_value = value
                max_severity = severity
                
        return max_severity
        
    def save_policies(self, output_file: Path):
        """Save generated policies to file"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = {
            "metadata": {
                "model": self.model_name,
                "total_policies": len(self.policies),
                "generated_at": datetime.now().isoformat()
            },
            "policies": self.policies
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
            
        logger.info(f"Policies saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate security policies using LLMs")
    parser.add_argument("--model", required=True, 
                       choices=["gpt-4", "claude-sonnet-4.5", "deepseek-r1", "llama-3.3"],
                       help="LLM model to use")
    parser.add_argument("--input", required=True, help="Input JSON file with vulnerabilities")
    parser.add_argument("--output", required=True, help="Output JSON file for policies")
    
    args = parser.parse_args()
    
    # Load vulnerabilities
    with open(args.input) as f:
        data = json.load(f)
        vulnerabilities = data.get("vulnerabilities", [])
    
    logger.info(f"Loaded {len(vulnerabilities)} vulnerabilities")
    
    # Generate policies
    generator = PolicyGenerator(args.model)
    generator.generate_policies(vulnerabilities)
    generator.save_policies(Path(args.output))
    
    logger.info("✅ Policy generation complete!")


if __name__ == "__main__":
    main()
