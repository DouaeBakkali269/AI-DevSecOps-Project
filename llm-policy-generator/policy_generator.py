#!/usr/bin/env python3
"""
ISO 27001 Security Policy Generator
Generates security policies based on vulnerability scans and ISO 27001 Annex A controls.
"""

import json
import os
import argparse
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv


def load_vulnerabilities(path="../results/parsed_data/vulnerabilities.json"):
    """Load vulnerabilities from JSON file."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    # Resolve path relative to script location
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r') as f:
        return json.load(f)


def load_iso27001_annex(path="../reference-policies/iso27001_templates.json"):
    """Load ISO 27001 Annex A controls."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    # Resolve path relative to script location
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r') as f:
        return f.read()


def load_iso27001_annex_controls(path="../docs/ISO27001-AnnexA.txt"):
    """Load ISO 27001 Annex A controls list from text file."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    # Resolve path relative to script location
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def build_system_prompt(vulnerabilities, iso_annex, iso_annex_controls_list):
    """Build the system prompt for the LLM."""

    prompt = f"""You are a security policy expert specializing in ISO 27001 compliance. Your task is to analyze vulnerability scan results and generate comprehensive security policies.

**CONTEXT - ISO 27001 Annex A Controls List:**
This is the complete list of ISO 27001:2022 Annex A controls available for reference:
{iso_annex_controls_list}

**CONTEXT - Vulnerability Scan Results:**
{json.dumps(vulnerabilities, indent=2)}

**YOUR TASK:**
1. Analyze all vulnerabilities and group them by related security domains
2. Map each vulnerability group to relevant ISO 27001 Annex A controls (refer to the controls list above for available control numbers)
3. Rank the controls by severity based on the number and criticality of violations
4. Generate comprehensive security policies for the top priority areas

**OUTPUT FORMAT:**
For each policy, provide:
- **Policy Title:** Clear, descriptive name
- **ISO 27001 Reference:** Specific Annex A control numbers (use the format A.X.Y from the controls list above)
- **Severity:** CRITICAL/HIGH/MEDIUM/LOW (based on worst vulnerability in group)
- **Summary of Vulnerabilities:** List specific vulnerabilities addressed with tool, file, and line numbers where applicable
- **Policy Content:** Detailed policy requirements and standards
- **Corrective Actions:** Specific, prioritized steps to remediate

**EXAMPLE OUTPUT:**
{iso_annex}

Generate 3-10 policies covering the most critical security gaps identified in the vulnerability data. Focus on actionable, evidence-based policies that directly address the discovered vulnerabilities."""

    return prompt


def generate_policies(api_key, model, vulnerabilities, iso_annex, iso_annex_controls_list):
    """Generate policies using OpenRouter API."""
    
    # Initialize OpenAI client for OpenRouter
    try:
        import httpx
    except ImportError:
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    else:
        http_client = httpx.Client(
            timeout=httpx.Timeout(600.0, connect=10.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            http_client=http_client,
        )
    
    system_prompt = build_system_prompt(vulnerabilities, iso_annex, iso_annex_controls_list)
    
    print(f"  DEBUG: Prompt length: {len(system_prompt)} characters")
    print(f"  DEBUG: Model: {model}")
    
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://github.com/DouaeBakkali269/AI-DevSecOps-Project",
                "X-Title": "ISO 27001 Policy Generator",
            },
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": system_prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )
        
        # Debug: Print the full response object
        print(f"  DEBUG: Response object: {completion}")
        print(f"  DEBUG: Response model dump: {completion.model_dump_json(indent=2)}")
        
        # Check if response was filtered
        if hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            
            # Check for finish_reason
            if hasattr(choice, 'finish_reason'):
                print(f"  DEBUG: Finish reason: {choice.finish_reason}")
                if choice.finish_reason == 'content_filter':
                    raise ValueError("Response was blocked by content filter")
            
            # Check for message content
            if hasattr(choice, 'message') and choice.message:
                content = choice.message.content
                
                print(f"  DEBUG: Response type: {type(content)}")
                print(f"  DEBUG: Content is None: {content is None}")
                
                if content is not None:
                    print(f"  DEBUG: Content length: {len(content)}")
                    print(f"  DEBUG: Content (first 500 chars): {content[:500] if len(content) > 0 else '(empty string)'}")
                    print(f"  DEBUG: Content repr: {repr(content[:100])}")
                
                # Validate that we got content
                if content is None:
                    raise ValueError("LLM returned None content. The response may have been filtered or empty.")
                if not content.strip():
                    raise ValueError(f"LLM returned empty content. Content type: {type(content)}, length: {len(content) if content else 0}")
                
                return content
            else:
                raise ValueError("Response has no message content")
        else:
            raise ValueError("Response has no choices")
            
    except Exception as e:
        print(f"  ERROR in generate_policies: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Clean up HTTP client if we created one
        if 'http_client' in locals():
            http_client.close()


def save_policy(policy_content, output_dir="../results/generated_policies"):
    """Save generated policy to file with unique timestamp."""
    # Validate content
    if policy_content is None:
        raise ValueError("Cannot save None content to file")
    if not isinstance(policy_content, str):
        raise ValueError(f"Expected string content, got {type(policy_content)}")
    if not policy_content.strip():
        raise ValueError("Cannot save empty content to file")
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    # Resolve path relative to script location
    full_output_dir = (script_dir / output_dir).resolve()
    
    # Create output directory if it doesn't exist
    full_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"security_policy_{timestamp}.md"
    filepath = full_output_dir / filename
    
    # Save policy with UTF-8 encoding
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(policy_content)
    
    # Verify file was written
    if not filepath.exists() or filepath.stat().st_size == 0:
        raise IOError(f"Failed to save policy to {filepath}")
    
    return str(filepath)


def main():
    # Load environment variables from .env file if it exists
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    current_dir = Path.cwd()
    
    # Try multiple locations for .env file
    env_files = [
        project_root / ".env",
        script_dir / ".env",
        current_dir / ".env",
    ]
    
    env_loaded = False
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)
            env_loaded = True
            break
    
    if not env_loaded:
        load_dotenv(override=False)
    
    parser = argparse.ArgumentParser(
        description="Generate ISO 27001 security policies from vulnerability scans"
    )
    parser.add_argument(
        "--model",
        default="openai/gpt-4o-mini",  # Changed to a more reliable model
        help="OpenRouter model to use (default: openai/gpt-4o-mini)"
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENROUTER_API_KEY"),
        help="OpenRouter API key (default: from .env file or OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--vulnerabilities",
        default="../results/parsed_data/vulnerabilities.json",
        help="Path to vulnerabilities JSON file"
    )
    parser.add_argument(
        "--iso-annex",
        default="../reference-policies/iso27001_templates.json",
        help="Path to ISO 27001 Annex A reference file"
    )
    parser.add_argument(
        "--iso-annex-controls",
        default="../docs/ISO27001-AnnexA.txt",
        help="Path to ISO 27001 Annex A controls list text file"
    )
    parser.add_argument(
        "--output-dir",
        default="../results/generated_policies",
        help="Output directory for generated policies"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        print("ERROR: OpenRouter API key required.")
        print("  Options:")
        print("  1. Create a .env file in the project root with: OPENROUTER_API_KEY=your_key_here")
        print("  2. Set OPENROUTER_API_KEY environment variable")
        print("  3. Use --api-key command line argument")
        return 1
    
    print(f"Loading vulnerabilities from {args.vulnerabilities}...")
    try:
        vulnerabilities = load_vulnerabilities(args.vulnerabilities)
        print(f"✓ Loaded {vulnerabilities['metadata']['total_vulnerabilities']} vulnerabilities")
    except FileNotFoundError:
        print(f"ERROR: Vulnerabilities file not found at {args.vulnerabilities}")
        return 1
    
    print(f"Loading ISO 27001 Annex A from {args.iso_annex}...")
    try:
        iso_annex = load_iso27001_annex(args.iso_annex)
        print(f"✓ Loaded ISO 27001 Annex A ({len(iso_annex)} characters)")
    except FileNotFoundError:
        print(f"ERROR: ISO 27001 Annex A file not found at {args.iso_annex}")
        return 1
    
    print(f"Loading ISO 27001 Annex A controls list from {args.iso_annex_controls}...")
    try:
        iso_annex_controls_list = load_iso27001_annex_controls(args.iso_annex_controls)
        print(f"✓ Loaded ISO 27001 Annex A controls list ({len(iso_annex_controls_list)} characters)")
    except FileNotFoundError:
        print(f"ERROR: ISO 27001 Annex A controls list file not found at {args.iso_annex_controls}")
        return 1
    
    print(f"\nGenerating policies using model: {args.model}...")
    try:
        policy_content = generate_policies(
            args.api_key,
            args.model,
            vulnerabilities,
            iso_annex,
            iso_annex_controls_list
        )
        print("✓ Policies generated successfully")
        print(f"  Response length: {len(policy_content)} characters")
        print(f"  Preview (first 200 chars): {policy_content[:200]}...")
    except ValueError as e:
        print(f"ERROR: Validation error - {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"ERROR: Failed to generate policies: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\nSaving policies to {args.output_dir}...")
    try:
        filepath = save_policy(policy_content, args.output_dir)
        print(f"✓ Policies saved to: {filepath}")
        file_size = Path(filepath).stat().st_size
        print(f"  File size: {file_size} bytes")
    except (ValueError, IOError) as e:
        print(f"ERROR: Failed to save policies: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error while saving: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "="*60)
    print("POLICY GENERATION COMPLETE")
    print("="*60)
    print(f"Model used: {args.model}")
    print(f"Output file: {filepath}")
    
    return 0


if __name__ == "__main__":
    exit(main())