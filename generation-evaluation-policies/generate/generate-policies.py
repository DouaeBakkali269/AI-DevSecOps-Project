#!/usr/bin/env python3
"""
Policy Generation Script
Generates security policies for a given LLM model using the same system prompt as policy_generator.py
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_vulnerabilities(path="results/parsed_data/vulnerabilities.json"):
    """Load vulnerabilities from JSON file."""
    script_dir = Path(__file__).parent.parent
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_iso27001_annex(path="reference-policies/iso27001_templates.json"):
    """Load ISO 27001 Annex A controls."""
    script_dir = Path(__file__).parent.parent
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def load_iso27001_annex_controls(path="docs/ISO27001-AnnexA.txt"):
    """Load ISO 27001 Annex A controls list from text file."""
    script_dir = Path(__file__).parent.parent
    full_path = (script_dir / path).resolve()
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()


def build_system_prompt(vulnerabilities, iso_annex, iso_annex_controls_list):
    """Build the system prompt for the LLM - same as policy_generator.py"""
    
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
For each policy, provide the following fields (as described in the ISO 27001 reference policies):

- **control_id**: The ISO 27001 Annex A control identifier (e.g., "A.8.8").
- **domain**: The relevant ISO 27001 control domain for the policy.
- **title**: A clear and descriptive policy title.
- **severity**: The severity rating of the policy (e.g., HIGH, MEDIUM, LOW, or CRITICAL), based on the most critical associated vulnerability.
- **policy_text**: Detailed policy requirements and standards addressing the identified vulnerabilities, written as concise actionable statements.
- **vulnerabilities**: A list of specific vulnerabilities discovered that are not compliant with this policy. Each entry should reference tools, files, line numbers, or other relevant identifiers where possible.
- **implementation_requirements**: A list of key steps, technologies, or organizational requirements necessary to implement this policy in practice.
- **verification_methods**: A list of methods or evidence types used to verify policy compliance (e.g., reviews, audits, testing, reporting).

Return each policy in this fielded structure, as shown in the ISO 27001 template example.

**IMPORTANT: You MUST return valid JSON only. The output should be a JSON object with a "policies" array containing policy objects with the fields described above.**

**EXAMPLE OUTPUT:**
{iso_annex}

Generate 3-10 policies covering the most critical security gaps identified in the vulnerability data. Focus on actionable, evidence-based policies that directly address the discovered vulnerabilities. Return your response as a JSON object with the same structure as the example above."""

    return prompt


def generate_policies(api_key, model, vulnerabilities, iso_annex, iso_annex_controls_list):
    """Generate policies using OpenRouter API with proper timeout handling and reasoning support."""
    
    # Initialize OpenAI client for OpenRouter with very large timeout to wait indefinitely
    # Use a very large timeout value (24 hours) to effectively wait indefinitely
    try:
        import httpx
        # Set timeout to a very large value (24 hours in seconds = 86400)
        # This effectively waits indefinitely for model responses
        http_client = httpx.Client(
            timeout=httpx.Timeout(86400.0, connect=30.0),  # 24 hours total, 30s connect
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            http_client=http_client,
            timeout=86400.0,  # 24 hours timeout
        )
    except ImportError:
        # Fallback if httpx not available - create client without custom HTTP client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=86400.0,  # 24 hours timeout
        )
        http_client = None
    
    system_prompt = build_system_prompt(vulnerabilities, iso_annex, iso_annex_controls_list)
    
    print(f"  DEBUG: Prompt length: {len(system_prompt)} characters")
    print(f"  DEBUG: Model: {model}")
    print(f"  DEBUG: Timeout set to 24 hours - waiting indefinitely for model response...")
    print(f"  DEBUG: This may take several minutes for large responses...")
    
    # Check if this is Kimi-K2-Thinking model (needs reasoning enabled)
    # Note: Kimi-K2 is no longer the reference model, but we keep reasoning support
    # in case it's used for evaluation
    is_kimi = model.lower() in ["moonshotai/kimi-k2-thinking", "kimi-k2-thinking"]
    
    # Prepare extra_body for reasoning if needed
    extra_body = {}
    if is_kimi:
        extra_body = {"reasoning": {"enabled": True}}
        print(f"  DEBUG: Reasoning enabled for {model} (this may take longer)")
    
    try:
        # Create completion with proper OpenRouter syntax
        completion_params = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": system_prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 16000,  # Increased to handle longer responses
            "extra_headers": {
                "HTTP-Referer": "https://github.com/DouaeBakkali269/AI-DevSecOps-Project",
                "X-Title": "ISO 27001 Policy Generator",
            }
        }
        
        # Add extra_body if reasoning is enabled
        if extra_body:
            completion_params["extra_body"] = extra_body
            print(f"  DEBUG: Sending request with reasoning enabled...")
        else:
            print(f"  DEBUG: Sending request...")
        
        print(f"  DEBUG: Waiting for API response (timeout: 24 hours)...")
        completion = client.chat.completions.create(**completion_params)
        print(f"  DEBUG: Received API response")
        
        # Wait for the response to complete
        if hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            
            # Check for finish_reason
            if hasattr(choice, 'finish_reason'):
                finish_reason = choice.finish_reason
                print(f"  DEBUG: Finish reason: {finish_reason}")
                
                if finish_reason == 'content_filter':
                    raise ValueError("Response was blocked by content filter")
                elif finish_reason == 'length':
                    print(f"  WARNING: Response was truncated due to token limit")
                elif finish_reason != 'stop':
                    print(f"  WARNING: Unexpected finish_reason: {finish_reason}")
            
            # Check for message content
            if hasattr(choice, 'message') and choice.message:
                content = choice.message.content
                
                print(f"  DEBUG: Response type: {type(content)}")
                print(f"  DEBUG: Content is None: {content is None}")
                
                if content is not None:
                    content_length = len(content) if isinstance(content, str) else 0
                    print(f"  DEBUG: Content length: {content_length} characters")
                    if content_length > 0:
                        print(f"  DEBUG: Content preview (first 200 chars): {content[:200]}...")
                
                # Validate that we got content
                if content is None:
                    raise ValueError("LLM returned None content. The response may still be processing or was filtered.")
                
                if not isinstance(content, str):
                    raise ValueError(f"LLM returned non-string content: {type(content)}")
                
                if not content.strip():
                    raise ValueError(f"LLM returned empty content. Content type: {type(content)}, length: {len(content)}")
                
                print(f"  DEBUG: Successfully received {len(content)} characters of content")
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
        if http_client:
            try:
                http_client.close()
            except:
                pass


def parse_policy_response(response_text, model_name):
    """Parse LLM response and extract JSON policies with improved truncation handling."""
    # Try to extract JSON from the response
    response_text = response_text.strip()
    
    # Remove markdown code blocks if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        if lines[0].startswith("```json") or lines[0].startswith("```"):
            response_text = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
    
    # Try to parse as JSON
    try:
        policy_data = json.loads(response_text)
        
        # Validate structure
        if "policies" not in policy_data:
            # If the response is directly a list of policies, wrap it
            if isinstance(policy_data, list):
                policy_data = {"policies": policy_data}
            else:
                raise ValueError("Response does not contain 'policies' field")
        
        # Add metadata
        policy_data["metadata"] = {
            "model": model_name,
            "total_policies": len(policy_data["policies"]),
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return policy_data
    except json.JSONDecodeError as e:
        print(f"  WARNING: Failed to parse JSON response: {e}")
        print(f"  Attempting to extract partial JSON from truncated response...")
        
        # Try to extract partial JSON from truncated response
        partial_data = None
        try:
            # Try to find the policies array and extract what we can
            import re
            
            # Look for policies array start
            policies_match = re.search(r'"policies"\s*:\s*\[', response_text)
            if policies_match:
                start_idx = policies_match.end() - 1  # Include the '['
                # Try to extract complete policy objects
                bracket_depth = 0
                in_string = False
                escape_next = False
                policies_text = []
                current_policy = []
                
                i = start_idx
                while i < len(response_text):
                    char = response_text[i]
                    
                    if escape_next:
                        current_policy.append(char)
                        escape_next = False
                        i += 1
                        continue
                    
                    if char == '\\':
                        current_policy.append(char)
                        escape_next = True
                        i += 1
                        continue
                    
                    if char == '"':
                        in_string = not in_string
                        current_policy.append(char)
                    elif not in_string:
                        if char == '{':
                            bracket_depth += 1
                            current_policy.append(char)
                        elif char == '}':
                            bracket_depth -= 1
                            current_policy.append(char)
                            if bracket_depth == 0:
                                # Complete policy object
                                policy_str = ''.join(current_policy)
                                try:
                                    policy_obj = json.loads(policy_str)
                                    policies_text.append(policy_obj)
                                    current_policy = []
                                except:
                                    pass
                                # Look for comma or end
                                i += 1
                                while i < len(response_text) and response_text[i] in ' \n\r\t,':
                                    i += 1
                                continue
                        else:
                            current_policy.append(char)
                    else:
                        current_policy.append(char)
                    
                    i += 1
                
                if policies_text:
                    partial_data = {
                        "standard": "ISO/IEC 27001:2022",
                        "policies": policies_text
                    }
                    print(f"  INFO: Extracted {len(policies_text)} complete policy(ies) from truncated response")
        except Exception as extract_error:
            print(f"  WARNING: Failed to extract partial JSON: {extract_error}")
        
        # Return structure with raw response
        policies_extracted = partial_data["policies"] if partial_data else []
        result = {
            "metadata": {
                "model": model_name,
                "total_policies": len(policies_extracted),
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "parse_error": str(e),
                "is_truncated": True
            },
            "policies": policies_extracted,
            "raw_response": response_text
        }
        
        # If we extracted some policies, report success
        if partial_data and len(policies_extracted) > 0:
            print(f"  INFO: Saved {len(policies_extracted)} policies from truncated response")
        
        return result


def save_policies(policy_data, output_dir, model_name):
    """Save generated policies to JSON file."""
    script_dir = Path(__file__).parent
    full_output_dir = (script_dir / output_dir).resolve()
    
    full_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create safe filename from model name
    safe_model_name = model_name.replace("/", "_").replace("\\", "_")
    filename = f"{safe_model_name}_policies.json"
    filepath = full_output_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(policy_data, f, indent=2, ensure_ascii=False)
    
    return str(filepath)


def main():
    """Main function for standalone execution."""
    import argparse
    
    # Load environment variables
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    env_files = [
        project_root / ".env",
        script_dir / ".env",
    ]
    
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)
            break
    else:
        load_dotenv(override=False)
    
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment")
        return 1
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate security policies for LLM models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate for a single model:
  python generate-policies.py --model openai/gpt-5
  
  # Generate for multiple models:
  python generate-policies.py --models openai/gpt-5 openai/gpt-5-mini
  
  # Generate for all models in the list:
  python generate-policies.py --all
        """
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Single model to generate policies for (e.g., openai/gpt-5)"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        help="Multiple models to generate policies for (e.g., --models openai/gpt-5 openai/gpt-5-mini)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate policies for all evaluation models"
    )
    parser.add_argument(
        "--output-dir",
        default="generated_policies",
        help="Output directory for generated policies (default: generated_policies)"
    )
    
    args = parser.parse_args()
    
    # Determine which models to process
    models_to_process = []
    
    if args.model:
        models_to_process = [args.model]
    elif args.models:
        models_to_process = args.models
    elif args.all:
        # Import evaluation models list
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "run_all_generations", 
                Path(__file__).parent / "run-all-generations.py"
            )
            run_all_generations = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(run_all_generations)
            models_to_process = run_all_generations.EVALUATION_MODELS
        except Exception as e:
            print(f"ERROR: Could not import EVALUATION_MODELS: {e}")
            print("Use --model or --models instead.")
            return 1
    else:
        # Default: single model from command line (backward compatibility)
        if len(sys.argv) > 1:
            models_to_process = [sys.argv[1]]
        else:
            parser.print_help()
            return 1
    
    # Load data once
    print("\nLoading input data...")
    try:
        vulnerabilities = load_vulnerabilities()
        print(f"✓ Loaded {vulnerabilities['metadata']['total_vulnerabilities']} vulnerabilities")
        
        iso_annex = load_iso27001_annex()
        print(f"✓ Loaded ISO 27001 Annex A templates")
        
        iso_annex_controls_list = load_iso27001_annex_controls()
        print(f"✓ Loaded ISO 27001 Annex A controls list")
    except Exception as e:
        print(f"ERROR: Failed to load input data: {e}")
        return 1
    
    # Generate policies for each model
    print(f"\n{'='*60}")
    print(f"GENERATING POLICIES FOR {len(models_to_process)} MODEL(S)")
    print(f"{'='*60}\n")
    
    results = []
    
    for i, model_name in enumerate(models_to_process, 1):
        print(f"[{i}/{len(models_to_process)}] Generating policies for: {model_name}")
        print(f"{'='*60}")
        
        try:
            response_text = generate_policies(
                api_key,
                model_name,
                vulnerabilities,
                iso_annex,
                iso_annex_controls_list
            )
            
            policy_data = parse_policy_response(response_text, model_name)
            
            filepath = save_policies(policy_data, args.output_dir, model_name)
            print(f"[OK] Policies saved to: {filepath}")
            print(f"  Total policies: {policy_data['metadata'].get('total_policies', 0)}")
            
            results.append({
                "model": model_name,
                "status": "success",
                "filepath": filepath,
                "policies_count": policy_data['metadata'].get('total_policies', 0)
            })
            
        except Exception as e:
            print(f"[X] ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "model": model_name,
                "status": "failed",
                "error": str(e)
            })
        
        print()  # Blank line between models
    
    # Summary
    print(f"{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    
    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    
    print(f"Successfully generated: {len(successful)}/{len(models_to_process)}")
    for r in successful:
        print(f"  [OK] {r['model']}: {r['policies_count']} policies")
    
    if failed:
        print(f"\nFailed: {len(failed)}/{len(models_to_process)}")
        for r in failed:
            print(f"  [X] {r['model']}: {r.get('error', 'unknown error')}")
    
    return 0 if len(failed) == 0 else 1


if __name__ == "__main__":
    exit(main())
