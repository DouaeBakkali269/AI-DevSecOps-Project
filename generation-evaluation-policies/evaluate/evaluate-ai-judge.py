#!/usr/bin/env python3
"""
AI-as-a-Judge Evaluation Script
Evaluates generated policies using openai/gpt-5 as a judge model.
Compares policies by matching them to ISO 27001 controls and scoring across multiple criteria.
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Import constants from run-all-generations
import importlib.util
spec = importlib.util.spec_from_file_location("run_all_generations", Path(__file__).parent / "run-all-generations.py")
run_all_generations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_all_generations)

REFERENCE_MODEL = run_all_generations.REFERENCE_MODEL
EVALUATION_MODELS = run_all_generations.EVALUATION_MODELS
OUTPUT_DIR = run_all_generations.OUTPUT_DIR

PROGRESS_FILE = "ai_judge_evaluation_progress.json"
RESULTS_FILE = "ai_judge_results.json"
JUDGE_MODEL = "openai/gpt-5-mini"  # Using openai/gpt-5 as judge (same as reference model)


def load_progress():
    """Load evaluation progress."""
    progress_file = Path(__file__).parent / PROGRESS_FILE
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "completed_models": [],
        "completed_pairs": {},  # Track which policy pairs have been evaluated
        "scores": {}
    }


def save_progress(progress):
    """Save evaluation progress."""
    progress_file = Path(__file__).parent / PROGRESS_FILE
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def load_policies(filepath):
    """Load policies from JSON file."""
    policy_file = Path(__file__).parent / filepath
    if not policy_file.exists():
        raise FileNotFoundError(f"Policy file not found: {filepath}")
    
    with open(policy_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def match_policies_by_control(ref_policies, cand_policies):
    """Match policies from reference and candidate by control_id."""
    ref_by_control = defaultdict(list)
    cand_by_control = defaultdict(list)
    
    for policy in ref_policies.get("policies", []):
        control_id = policy.get("control_id", "unknown")
        ref_by_control[control_id].append(policy)
    
    for policy in cand_policies.get("policies", []):
        control_id = policy.get("control_id", "unknown")
        cand_by_control[control_id].append(policy)
    
    # Match policies by control_id
    matched_pairs = []
    
    for control_id in set(ref_by_control.keys()) | set(cand_by_control.keys()):
        ref_pols = ref_by_control.get(control_id, [])
        cand_pols = cand_by_control.get(control_id, [])
        
        # If both have policies, match them
        if ref_pols and cand_pols:
            # Match first to first, second to second, etc.
            for ref_pol, cand_pol in zip(ref_pols, cand_pols):
                matched_pairs.append((control_id, ref_pol, cand_pol))
        
        # If only reference has policy, still include it (candidate missing)
        elif ref_pols:
            for ref_pol in ref_pols:
                matched_pairs.append((control_id, ref_pol, None))
        
        # If only candidate has policy, include it (reference missing)
        elif cand_pols:
            for cand_pol in cand_pols:
                matched_pairs.append((control_id, None, cand_pol))
    
    # If no matches by control_id, fall back to index-based matching
    if not matched_pairs:
        ref_pols_list = ref_policies.get("policies", [])
        cand_pols_list = cand_policies.get("policies", [])
        
        for i, (ref_pol, cand_pol) in enumerate(zip(ref_pols_list, cand_pols_list)):
            control_id = ref_pol.get("control_id", f"index_{i}")
            matched_pairs.append((control_id, ref_pol, cand_pol))
    
    return matched_pairs


def format_policy_for_evaluation(policy):
    """Format a policy object into a readable string for evaluation."""
    if policy is None:
        return "No policy provided."
    
    parts = []
    if "control_id" in policy:
        parts.append(f"Control ID: {policy['control_id']}")
    if "domain" in policy:
        parts.append(f"Domain: {policy['domain']}")
    if "title" in policy:
        parts.append(f"Title: {policy['title']}")
    if "severity" in policy:
        parts.append(f"Severity: {policy['severity']}")
    if "policy_text" in policy:
        parts.append(f"Policy Text: {policy['policy_text']}")
    if "policy_content" in policy:
        parts.append(f"Policy Content: {policy['policy_content']}")
    if "implementation_requirements" in policy:
        reqs = policy["implementation_requirements"]
        if isinstance(reqs, list):
            parts.append(f"Implementation Requirements:\n" + "\n".join(f"  - {r}" for r in reqs))
        else:
            parts.append(f"Implementation Requirements: {reqs}")
    if "verification_methods" in policy:
        methods = policy["verification_methods"]
        if isinstance(methods, list):
            parts.append(f"Verification Methods:\n" + "\n".join(f"  - {m}" for m in methods))
        else:
            parts.append(f"Verification Methods: {methods}")
    
    return "\n\n".join(parts)


def create_judge_prompt(ref_policy, cand_policy, control_id):
    """Create prompt for AI judge to evaluate a policy pair."""
    
    ref_text = format_policy_for_evaluation(ref_policy)
    cand_text = format_policy_for_evaluation(cand_policy)
    
    prompt = f"""You are an expert cybersecurity and information security policy evaluator specializing in ISO/IEC 27001:2022 Annex A Controls.

**TASK:**
Compare a candidate policy against a reference policy for ISO 27001 Control {control_id}. The reference policy is the gold standard, and you need to evaluate how well the candidate policy measures up.

**REFERENCE POLICY (Gold Standard):**
{ref_text}

**CANDIDATE POLICY (To Evaluate):**
{cand_text}

**EVALUATION CRITERIA:**
Rate the candidate policy on a scale of 0-100 for each criterion:

1. **ISO 27001 Alignment** (0-100): How well does the candidate policy align with the correct Annex A control? Does it address the same security concerns as the reference?

2. **Policy Completeness** (0-100): Does the candidate policy cover all relevant vulnerabilities and controls? Compare the comprehensiveness with the reference.

3. **Actionability** (0-100): Are the corrective actions and implementation requirements practical, specific, and implementable? Compare with the reference.

4. **Technical Accuracy** (0-100): Is the technical content correct? Are the security measures and mitigations accurate and appropriate?

5. **Linguistic Quality** (0-100): Is the policy clear, coherent, and professionally written? Is the tone appropriate for a security policy document?

**OUTPUT FORMAT:**
Provide your evaluation as a JSON object with the following structure:
{{
  "iso_27001_alignment": <score 0-100>,
  "policy_completeness": <score 0-100>,
  "actionability": <score 0-100>,
  "technical_accuracy": <score 0-100>,
  "linguistic_quality": <score 0-100>,
  "overall_score": <average of all scores>,
  "comments": "<brief explanation of your evaluation>"
}}

Return ONLY the JSON object, no additional text."""

    return prompt


def evaluate_policy_pair(api_key, ref_policy, cand_policy, control_id):
    """Use AI judge to evaluate a single policy pair."""
    
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
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            timeout=86400.0,  # 24 hours timeout
        )
        http_client = None
    
    prompt = create_judge_prompt(ref_policy, cand_policy, control_id)
    
    # Check if this is Kimi-K2-Thinking model (needs reasoning enabled)
    # Note: Judge model is now openai/gpt-5, so no reasoning needed
    is_kimi = JUDGE_MODEL.lower() in ["moonshotai/kimi-k2-thinking", "kimi-k2-thinking"]
    
    # Prepare extra_body for reasoning if needed (only for Kimi-K2)
    extra_body = {}
    if is_kimi:
        extra_body = {"reasoning": {"enabled": True}}
    
    try:
        # Create completion with proper OpenRouter syntax
        completion_params = {
            "model": JUDGE_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,  # Lower temperature for more consistent evaluation
            "max_tokens": 2000,
            "extra_headers": {
                "HTTP-Referer": "https://github.com/DouaeBakkali269/AI-DevSecOps-Project",
                "X-Title": "ISO 27001 Policy Judge",
            }
        }
        
        # Add extra_body if reasoning is enabled
        if extra_body:
            completion_params["extra_body"] = extra_body
        
        # Wait for response with long timeout
        completion = client.chat.completions.create(**completion_params)
        
        if hasattr(completion, 'choices') and completion.choices:
            choice = completion.choices[0]
            
            if hasattr(choice, 'message') and choice.message:
                content = choice.message.content
                
                # Wait for content to be available
                if content is None:
                    raise ValueError("Judge model returned None content. The response may still be processing.")
                
                if not isinstance(content, str):
                    raise ValueError(f"Judge model returned non-string content: {type(content)}")
                
                if not content.strip():
                    raise ValueError(f"Judge model returned empty content. Content type: {type(content)}, length: {len(content)}")
                
                # Parse JSON response
                content = content.strip()
                
                # Remove markdown code blocks if present
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```json") or lines[0].startswith("```"):
                        content = "\n".join(lines[1:-1]) if lines[-1].startswith("```") else "\n".join(lines[1:])
                
                try:
                    evaluation = json.loads(content)
                    
                    # Validate structure
                    required_fields = [
                        "iso_27001_alignment", "policy_completeness", 
                        "actionability", "technical_accuracy", "linguistic_quality"
                    ]
                    
                    for field in required_fields:
                        if field not in evaluation:
                            raise ValueError(f"Missing required field: {field}")
                        score = evaluation[field]
                        if not isinstance(score, (int, float)) or score < 0 or score > 100:
                            raise ValueError(f"Invalid score for {field}: {score}")
                    
                    # Calculate overall score if not provided
                    if "overall_score" not in evaluation:
                        scores = [
                            evaluation["iso_27001_alignment"],
                            evaluation["policy_completeness"],
                            evaluation["actionability"],
                            evaluation["technical_accuracy"],
                            evaluation["linguistic_quality"]
                        ]
                        evaluation["overall_score"] = sum(scores) / len(scores)
                    
                    return evaluation
                    
                except json.JSONDecodeError as e:
                    print(f"  WARNING: Failed to parse JSON response: {e}")
                    print(f"  Response: {content[:200]}")
                    # Return default scores on parse error
                    return {
                        "iso_27001_alignment": 0,
                        "policy_completeness": 0,
                        "actionability": 0,
                        "technical_accuracy": 0,
                        "linguistic_quality": 0,
                        "overall_score": 0,
                        "error": f"JSON parse error: {str(e)}"
                    }
        else:
            raise ValueError("Judge model returned no choices")
            
    except Exception as e:
        print(f"  ERROR in evaluate_policy_pair: {e}")
        raise
    finally:
        if http_client:
            try:
                http_client.close()
            except:
                pass


def evaluate_model(api_key, reference_policies, candidate_policies, model_name):
    """Evaluate all policy pairs for a model."""
    
    print(f"  Matching policies by control_id...")
    matched_pairs = match_policies_by_control(reference_policies, candidate_policies)
    
    print(f"  Found {len(matched_pairs)} policy pairs to evaluate")
    
    all_evaluations = []
    pair_scores = {}
    
    for i, (control_id, ref_policy, cand_policy) in enumerate(matched_pairs, 1):
        pair_key = f"{model_name}_{control_id}_{i}"
        
        print(f"    [{i}/{len(matched_pairs)}] Evaluating control {control_id}...")
        
        try:
            evaluation = evaluate_policy_pair(api_key, ref_policy, cand_policy, control_id)
            evaluation["control_id"] = control_id
            evaluation["pair_index"] = i
            all_evaluations.append(evaluation)
            pair_scores[pair_key] = evaluation
            
        except Exception as e:
            print(f"      ERROR evaluating pair {i}: {e}")
            # Add default scores on error
            error_eval = {
                "control_id": control_id,
                "pair_index": i,
                "iso_27001_alignment": 0,
                "policy_completeness": 0,
                "actionability": 0,
                "technical_accuracy": 0,
                "linguistic_quality": 0,
                "overall_score": 0,
                "error": str(e)
            }
            all_evaluations.append(error_eval)
            pair_scores[pair_key] = error_eval
            continue
    
    # Calculate aggregate scores
    if all_evaluations:
        aggregate = {
            "iso_27001_alignment": sum(e.get("iso_27001_alignment", 0) for e in all_evaluations) / len(all_evaluations),
            "policy_completeness": sum(e.get("policy_completeness", 0) for e in all_evaluations) / len(all_evaluations),
            "actionability": sum(e.get("actionability", 0) for e in all_evaluations) / len(all_evaluations),
            "technical_accuracy": sum(e.get("technical_accuracy", 0) for e in all_evaluations) / len(all_evaluations),
            "linguistic_quality": sum(e.get("linguistic_quality", 0) for e in all_evaluations) / len(all_evaluations),
            "overall_score": sum(e.get("overall_score", 0) for e in all_evaluations) / len(all_evaluations),
            "total_pairs_evaluated": len(all_evaluations),
            "individual_evaluations": all_evaluations
        }
    else:
        aggregate = {
            "iso_27001_alignment": 0,
            "policy_completeness": 0,
            "actionability": 0,
            "technical_accuracy": 0,
            "linguistic_quality": 0,
            "overall_score": 0,
            "total_pairs_evaluated": 0,
            "individual_evaluations": []
        }
    
    return aggregate, pair_scores


def plot_ai_judge_scores(results, output_file="ai_judge_scores_chart.png"):
    """Plot AI judge scores as a bar chart."""
    script_dir = Path(__file__).parent
    output_path = script_dir / output_file
    
    models = []
    scores = []
    colors = []
    
    # Generate colors for each model
    import matplotlib.cm as cm
    color_map = cm.get_cmap('tab10')
    
    for i, (model, data) in enumerate(sorted(results.items())):
        models.append(model.replace("/", "\n"))  # Split model name for readability
        scores.append(data.get("overall_score", 0))
        colors.append(color_map(i % 10))
    
    plt.figure(figsize=(14, 6))
    bars = plt.bar(models, scores, color=colors, alpha=0.8, edgecolor='black')
    
    plt.xlabel("Model", fontsize=12, fontweight='bold')
    plt.ylabel("AI Judge Score (0-100)", fontsize=12, fontweight='bold')
    plt.title("AI-as-a-Judge Evaluation: Overall Score by Model", fontsize=14, fontweight='bold')
    plt.ylim(0, 100)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] AI Judge scores chart saved to: {output_path}")
    return str(output_path)


def main():
    """Main evaluation function."""
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
    
    progress = load_progress()
    
    print(f"\n{'='*60}")
    print("AI-AS-A-JUDGE EVALUATION")
    print(f"{'='*60}")
    print(f"Judge model: {JUDGE_MODEL}")
    
    # Load reference policies
    print("\nLoading reference policies...")
    try:
        ref_file = progress.get("reference_file")
        if not ref_file:
            safe_ref_name = REFERENCE_MODEL.replace("/", "_")
            ref_file = f"{OUTPUT_DIR}/{safe_ref_name}_policies.json"
        
        reference_policies = load_policies(ref_file)
        ref_policy_count = reference_policies.get('metadata', {}).get('total_policies', 0) or len(reference_policies.get('policies', []))
        print(f"[OK] Loaded reference policies from: {ref_file}")
        print(f"  Total policies: {ref_policy_count}")
        
        if ref_policy_count == 0:
            print(f"[ERROR] Reference policies file contains no policies!")
            return 1
    except FileNotFoundError:
        print(f"[ERROR] Reference policies file not found: {ref_file}")
        print(f"  Please generate reference policies first using run-all-generations.py")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to load reference policies: {e}")
        return 1
    
    # Load and evaluate each model
    results = progress.get("scores", {})
    completed_models = set(progress.get("completed_models", []))
    
    models_to_evaluate = [
        model for model in EVALUATION_MODELS
        if model not in completed_models
    ]
    
    if not models_to_evaluate and results:
        print("\n✓ All models have already been evaluated")
    else:
        print(f"\nEvaluating {len(models_to_evaluate)} models...")
        
        for i, model_name in enumerate(models_to_evaluate, 1):
            print(f"\n[{i}/{len(models_to_evaluate)}] Evaluating: {model_name}")
            
            try:
                # Load candidate policies
                safe_model_name = model_name.replace("/", "_")
                cand_file = f"{OUTPUT_DIR}/{safe_model_name}_policies.json"
                
                candidate_policies = load_policies(cand_file)
                print(f"  Loaded {candidate_policies['metadata'].get('total_policies', 0)} policies")
                
                # Evaluate model
                aggregate_scores, pair_scores = evaluate_model(
                    api_key,
                    reference_policies,
                    candidate_policies,
                    model_name
                )
                
                results[model_name] = aggregate_scores
                
                print(f"  Overall Score: {aggregate_scores['overall_score']:.2f}/100")
                print(f"  ISO 27001 Alignment: {aggregate_scores['iso_27001_alignment']:.2f}")
                print(f"  Policy Completeness: {aggregate_scores['policy_completeness']:.2f}")
                print(f"  Actionability: {aggregate_scores['actionability']:.2f}")
                print(f"  Technical Accuracy: {aggregate_scores['technical_accuracy']:.2f}")
                print(f"  Linguistic Quality: {aggregate_scores['linguistic_quality']:.2f}")
                
                # Save progress after each model
                progress["completed_models"].append(model_name)
                progress["scores"] = results
                progress["pair_scores"] = progress.get("pair_scores", {})
                progress["pair_scores"].update(pair_scores)
                save_progress(progress)
                
            except FileNotFoundError:
                print(f"  WARNING: Policy file not found, skipping: {cand_file}")
                continue
            except Exception as e:
                print(f"  ERROR: Failed to evaluate {model_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # Save final results
    final_results = {
        "judge_model": JUDGE_MODEL,
        "reference_model": REFERENCE_MODEL,
        "reference_file": ref_file,
        "evaluation_date": str(Path(__file__).parent),
        "scores": results
    }
    
    results_file = script_dir / RESULTS_FILE
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Results saved to: {results_file}")
    
    # Generate visualization
    if results:
        print("\nGenerating AI Judge scores visualization...")
        try:
            chart_path = plot_ai_judge_scores(results)
            print(f"✓ Chart saved to: {chart_path}")
        except Exception as e:
            print(f"WARNING: Failed to generate chart: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    print(f"\n{'='*60}")
    print("AI-JUDGE EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Judge model: {JUDGE_MODEL}")
    print(f"Reference model: {REFERENCE_MODEL}")
    print(f"Evaluated models: {len(results)}")
    
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1].get("overall_score", 0), reverse=True)
        print(f"\nTop performing models (by overall score):")
        for model, data in sorted_results[:5]:
            print(f"  {model}: {data.get('overall_score', 0):.2f}/100")
    
    return 0


if __name__ == "__main__":
    exit(main())

