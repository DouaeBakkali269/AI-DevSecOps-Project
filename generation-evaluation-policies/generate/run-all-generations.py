#!/usr/bin/env python3
"""
Run Policy Generation for Reference Model and All Evaluation Models
Generates policies using openai/gpt-5 as reference, then all other models.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import the generation function
# Use importlib to handle the hyphenated filename
import importlib.util
spec = importlib.util.spec_from_file_location("generate_policies", Path(__file__).parent / "generate-policies.py")
generate_policies_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_policies_module)

from generate_policies_module import (
    load_vulnerabilities,
    load_iso27001_annex,
    load_iso27001_annex_controls,
    generate_policies,
    parse_policy_response,
    save_policies
)

# Models to evaluate (updated list)
# Note: Removed anthropic/claude-haiku-4.5 and moonshotai/kimi-k2-thinking
# Added: openai/gpt-5-nano, openai/gpt-oss-120b
EVALUATION_MODELS = [
    "openai/gpt-5-mini",
    "openai/gpt-5-nano",
    "openai/gpt-oss-120b",
    "x-ai/grok-4-fast",
    "minimax/minimax-m2",
    "meta-llama/llama-3.3-70b-instruct",
    "z-ai/glm-4.6",
    "google/gemini-2.5-flash",
]

# Reference model: openai/gpt-5
REFERENCE_MODEL = "openai/gpt-5"

PROGRESS_FILE = "generation_progress.json"
OUTPUT_DIR = "c:/Users/Asus/Desktop/AI-DevSecOps-Project/generation-evaluation-policies/generated_policies"


def load_progress():
    """Load progress from checkpoint file."""
    progress_file = Path(__file__).parent / PROGRESS_FILE
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "reference_generated": False,
        "reference_file": None,
        "completed_models": [],
        "failed_models": []
    }


def save_progress(progress):
    """Save progress to checkpoint file."""
    progress_file = Path(__file__).parent / PROGRESS_FILE
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def generate_single_policy(api_key, model_name, vulnerabilities, iso_annex, iso_annex_controls_list, output_dir):
    """Generate policies for a single model with error handling."""
    print(f"\n{'='*60}")
    print(f"Generating policies for: {model_name}")
    print(f"{'='*60}")
    
    try:
        # Generate policies
        response_text = generate_policies(
            api_key,
            model_name,
            vulnerabilities,
            iso_annex,
            iso_annex_controls_list
        )
        
        # Parse response
        policy_data = parse_policy_response(response_text, model_name)
        
        # Check for parse errors
        if "parse_error" in policy_data.get("metadata", {}):
            parse_error = policy_data["metadata"]["parse_error"]
            is_truncated = policy_data.get("metadata", {}).get("is_truncated", False)
            if is_truncated:
                print(f"  WARNING: Response was truncated. Error: {parse_error[:100]}...")
                print(f"  INFO: Extracted {len(policy_data.get('policies', []))} policies from truncated response")
            else:
                print(f"  WARNING: Parse error occurred: {parse_error[:100]}...")
        
        # Save policies
        filepath = save_policies(policy_data, output_dir, model_name)
        print(f"✓ Policies saved to: {filepath}")
        print(f"  Total policies: {policy_data['metadata'].get('total_policies', 0)}")
        
        return {
            "model": model_name,
            "filepath": filepath,
            "status": "success",
            "policies_count": policy_data['metadata'].get('total_policies', 0)
        }
        
    except Exception as e:
        print(f"  ERROR: Failed to generate policies for {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return {
            "model": model_name,
            "status": "failed",
            "error": str(e)
        }


def main():
    """Main function to run all policy generations."""
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
        print("  Please set OPENROUTER_API_KEY in .env file or environment")
        return 1
    
    # Load progress
    progress = load_progress()
    print(f"\n{'='*60}")
    print("POLICY GENERATION RUNNER")
    print(f"{'='*60}")
    print(f"Progress loaded: {len(progress.get('completed_models', []))} models completed")
    
    # Load input data
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
    
    # Generate reference policies first
    if not progress.get("reference_generated", False):
        print(f"\n{'='*60}")
        print("GENERATING REFERENCE POLICIES")
        print(f"{'='*60}")
        print(f"Reference model: {REFERENCE_MODEL}")
        
        result = generate_single_policy(
            api_key,
            REFERENCE_MODEL,
            vulnerabilities,
            iso_annex,
            iso_annex_controls_list,
            OUTPUT_DIR
        )
        
        if result["status"] == "success":
            progress["reference_generated"] = True
            progress["reference_file"] = result["filepath"]
            progress["reference_model"] = REFERENCE_MODEL
            save_progress(progress)
            print(f"\n✓ Reference policies generated successfully")
        else:
            print(f"\n✗ Failed to generate reference policies")
            progress["failed_models"].append(result)
            save_progress(progress)
            return 1
    else:
        print(f"\n✓ Reference policies already generated: {progress.get('reference_file')}")
    
    # Generate policies for all evaluation models
    print(f"\n{'='*60}")
    print("GENERATING POLICIES FOR EVALUATION MODELS")
    print(f"{'='*60}")
    
    completed_models = set(progress.get("completed_models", []))
    failed_models = {m["model"] for m in progress.get("failed_models", [])}
    
    models_to_run = [
        model for model in EVALUATION_MODELS
        if model not in completed_models and model not in failed_models
    ]
    
    if not models_to_run:
        print("\n✓ All models have already been processed")
        print(f"  Completed: {len(completed_models)} models")
        print(f"  Failed: {len(failed_models)} models")
        return 0
    
    print(f"\nModels to process: {len(models_to_run)}")
    print(f"Models already completed: {len(completed_models)}")
    
    results = []
    for i, model_name in enumerate(models_to_run, 1):
        print(f"\n[{i}/{len(models_to_run)}] Processing: {model_name}")
        
        result = generate_single_policy(
            api_key,
            model_name,
            vulnerabilities,
            iso_annex,
            iso_annex_controls_list,
            OUTPUT_DIR
        )
        
        results.append(result)
        
        # Save progress after each model
        if result["status"] == "success":
            progress["completed_models"].append(model_name)
        else:
            progress["failed_models"].append(result)
        
        save_progress(progress)
    
    # Print summary
    print(f"\n{'='*60}")
    print("GENERATION SUMMARY")
    print(f"{'='*60}")
    print(f"Reference model: {REFERENCE_MODEL}")
    print(f"  Status: {'✓ Generated' if progress['reference_generated'] else '✗ Failed'}")
    print(f"\nEvaluation models:")
    print(f"  Successfully generated: {len([r for r in results if r['status'] == 'success'])}")
    print(f"  Failed: {len([r for r in results if r['status'] == 'failed'])}")
    
    # Save final results summary
    summary = {
        "reference_model": REFERENCE_MODEL,
        "reference_file": progress.get("reference_file"),
        "evaluation_models": results,
        "total_models": len(EVALUATION_MODELS),
        "successful": len([r for r in results if r['status'] == 'success']),
        "failed": len([r for r in results if r['status'] == 'failed'])
    }
    
    summary_file = Path(__file__).parent / "generation_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Summary saved to: {summary_file}")
    print(f"✓ Progress saved to: {Path(__file__).parent / PROGRESS_FILE}")
    
    return 0


if __name__ == "__main__":
    exit(main())

