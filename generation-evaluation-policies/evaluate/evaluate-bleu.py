#!/usr/bin/env python3
"""
BLEU Score Evaluation Script
Evaluates generated policies against reference policies using BLEU score.
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

# Try to import BLEU libraries
try:
    from sacrebleu import BLEU
    BLEU_AVAILABLE = True
    USE_NLTK = False  # Using sacrebleu, not NLTK
except ImportError:
    try:
        from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
        BLEU_AVAILABLE = True
        USE_NLTK = True  # Using NLTK as fallback
    except ImportError:
        BLEU_AVAILABLE = False
        USE_NLTK = False  # Neither available

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

PROGRESS_FILE = "c:/Users/Asus/Desktop/AI-DevSecOps-Project/generation-evaluation-policies/evaluation-results/bleu_evaluation_progress.json"
RESULTS_FILE = "c:/Users/Asus/Desktop/AI-DevSecOps-Project/generation-evaluation-policies/evaluation-results/bleu_results.json"


def load_progress():
    """Load evaluation progress."""
    progress_file = Path(PROGRESS_FILE)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    if progress_file.exists():
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "completed_models": [],
        "scores": {}
    }


def save_progress(progress):
    """Save evaluation progress."""
    progress_file = Path(PROGRESS_FILE)
    progress_file.parent.mkdir(parents=True, exist_ok=True)
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


def load_policies(filepath):
    """Load policies from JSON file."""
    policy_file = Path(filepath) if os.path.isabs(filepath) else (Path(__file__).parent / filepath)
    if not policy_file.exists():
        raise FileNotFoundError(f"Policy file not found: {filepath}")
    
    with open(policy_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_policy_text(policy_obj):
    """Extract text content from a policy object."""
    # Combine all text fields into a single string
    text_parts = []
    
    if "title" in policy_obj:
        text_parts.append(policy_obj["title"])
    if "policy_text" in policy_obj:
        text_parts.append(policy_obj["policy_text"])
    if "policy_content" in policy_obj:
        text_parts.append(policy_obj["policy_content"])
    if "implementation_requirements" in policy_obj:
        if isinstance(policy_obj["implementation_requirements"], list):
            text_parts.extend(policy_obj["implementation_requirements"])
        else:
            text_parts.append(str(policy_obj["implementation_requirements"]))
    if "verification_methods" in policy_obj:
        if isinstance(policy_obj["verification_methods"], list):
            text_parts.extend(policy_obj["verification_methods"])
        else:
            text_parts.append(str(policy_obj["verification_methods"]))
    
    return " ".join(text_parts)


def tokenize_text(text):
    """Tokenize text into words."""
    # Simple tokenization - split by whitespace and punctuation
    import re
    tokens = re.findall(r'\b\w+\b', text.lower())
    return tokens


def calculate_bleu_score(reference_policies, candidate_policies):
    """Calculate BLEU score between reference and candidate policies."""
    if not BLEU_AVAILABLE:
        raise ImportError("BLEU evaluation requires sacrebleu or nltk. Install with: pip install sacrebleu or pip install nltk")
    
    # Group policies by control_id for matching
    ref_by_control = defaultdict(list)
    cand_by_control = defaultdict(list)
    
    for policy in reference_policies.get("policies", []):
        control_id = policy.get("control_id", "unknown")
        ref_by_control[control_id].append(extract_policy_text(policy))
    
    for policy in candidate_policies.get("policies", []):
        control_id = policy.get("control_id", "unknown")
        cand_by_control[control_id].append(extract_policy_text(policy))
    
    # Calculate BLEU for matched policies
    all_scores = []
    
    # Match policies by control_id
    matched_controls = set(ref_by_control.keys()) & set(cand_by_control.keys())
    
    if not matched_controls:
        print("  WARNING: No policies matched by control_id. Matching all policies.")
        # Fallback: match by index
        ref_policies = reference_policies.get("policies", [])
        cand_policies = candidate_policies.get("policies", [])
        
        for ref_policy, cand_policy in zip(ref_policies, cand_policies):
            ref_text = extract_policy_text(ref_policy)
            cand_text = extract_policy_text(cand_policy)
            
            ref_tokens = tokenize_text(ref_text)
            cand_tokens = tokenize_text(cand_text)
            
            if not ref_tokens or not cand_tokens:
                continue
            
            if USE_NLTK:
                from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
                smooth = SmoothingFunction().method1
                score = sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smooth)
            else:
                # Use sacrebleu
                bleu = BLEU()
                ref_str = " ".join(ref_tokens)
                cand_str = " ".join(cand_tokens)
                result = bleu.sentence_score(cand_str, [ref_str])
                score = result.score / 100.0  # sacrebleu returns percentage
            
            all_scores.append(score)
    else:
        # Match by control_id
        for control_id in matched_controls:
            ref_texts = ref_by_control[control_id]
            cand_texts = cand_by_control[control_id]
            
            # Use the first policy for each control
            ref_text = ref_texts[0] if ref_texts else ""
            cand_text = cand_texts[0] if cand_texts else ""
            
            if not ref_text or not cand_text:
                continue
            
            ref_tokens = tokenize_text(ref_text)
            cand_tokens = tokenize_text(cand_text)
            
            if not ref_tokens or not cand_tokens:
                continue
            
            if USE_NLTK:
                from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
                smooth = SmoothingFunction().method1
                score = sentence_bleu([ref_tokens], cand_tokens, smoothing_function=smooth)
            else:
                # Use sacrebleu
                bleu = BLEU()
                ref_str = " ".join(ref_tokens)
                cand_str = " ".join(cand_tokens)
                result = bleu.sentence_score(cand_str, [ref_str])
                score = result.score / 100.0  # sacrebleu returns percentage
            
            all_scores.append(score)
    
    # Calculate average BLEU score
    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
    else:
        avg_score = 0.0
    
    return {
        "average_bleu": avg_score,
        "individual_scores": all_scores,
        "matched_policies": len(all_scores),
        "total_reference_policies": len(reference_policies.get("policies", [])),
        "total_candidate_policies": len(candidate_policies.get("policies", []))
    }


def plot_bleu_scores(results, output_file="bleu_scores_chart.png"):
    """Plot BLEU scores as a bar chart."""
    output_dir = Path("c:/Users/Asus/Desktop/AI-DevSecOps-Project/generation-evaluation-policies/evaluation-images")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_file
    
    models = []
    scores = []
    colors = []
    
    # Generate colors for each model
    import matplotlib.cm as cm
    color_map = cm.get_cmap('tab10')
    
    for i, (model, data) in enumerate(sorted(results.items())):
        models.append(model.replace("/", "\n"))  # Split model name for readability
        scores.append(data["average_bleu"])
        colors.append(color_map(i % 10))
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(models, scores, color=colors, alpha=0.8, edgecolor='black')
    
    plt.xlabel("Model", fontsize=12, fontweight='bold')
    plt.ylabel("BLEU Score", fontsize=12, fontweight='bold')
    plt.title("BLEU Score Evaluation: Generated Policies vs Reference Policies", fontsize=14, fontweight='bold')
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"[OK] BLEU scores chart saved to: {output_path}")
    return str(output_path)


def main():
    """Main evaluation function."""
    if not BLEU_AVAILABLE:
        print("ERROR: BLEU evaluation requires sacrebleu or nltk")
        print("  Install with: pip install sacrebleu")
        print("  Or: pip install nltk")
        return 1
    
    script_dir = Path(__file__).parent
    progress = load_progress()
    
    print(f"\n{'='*60}")
    print("BLEU SCORE EVALUATION")
    print(f"{'='*60}")
    
    # Load reference policies
    print("\nLoading reference policies...")
    try:
        # Get reference file from progress or search for it
        ref_file = progress.get("reference_file")
        if not ref_file:
            # Try to find reference policy file
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
    
    # Check which model files actually exist and skip missing ones
    existing_models = []
    missing_models = []
    
    for model_name in models_to_evaluate:
        safe_model_name = model_name.replace("/", "_")
        cand_file = script_dir / OUTPUT_DIR / f"{safe_model_name}_policies.json"
        if cand_file.exists():
            existing_models.append(model_name)
        else:
            missing_models.append(model_name)
    
    if missing_models:
        print(f"\nWARNING: Policy files not found for {len(missing_models)} model(s), skipping:")
        for model in missing_models:
            print(f"  - {model}")
        print()
    
    if not existing_models and results:
        print("\n[OK] All available models have already been evaluated")
    elif not existing_models:
        print("\n[ERROR] No policy files found for any evaluation models!")
        return 1
    else:
        print(f"\nEvaluating {len(existing_models)} model(s)...")
        
        for i, model_name in enumerate(existing_models, 1):
            print(f"\n[{i}/{len(existing_models)}] Evaluating: {model_name}")
            
            try:
                # Load candidate policies
                safe_model_name = model_name.replace("/", "_")
                cand_file = f"{OUTPUT_DIR}/{safe_model_name}_policies.json"
                
                candidate_policies = load_policies(cand_file)
                policy_count = candidate_policies.get('metadata', {}).get('total_policies', 0) or len(candidate_policies.get('policies', []))
                print(f"  Loaded {policy_count} policies")
                
                # Skip if no policies
                if policy_count == 0:
                    print(f"  WARNING: No policies found, skipping evaluation")
                    continue
                
                # Calculate BLEU score
                score_data = calculate_bleu_score(reference_policies, candidate_policies)
                results[model_name] = score_data
                
                print(f"  Average BLEU: {score_data['average_bleu']:.4f}")
                print(f"  Matched policies: {score_data['matched_policies']}")
                
                # Save progress after each model
                progress["completed_models"].append(model_name)
                progress["scores"] = results
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
        print("\nGenerating BLEU scores visualization...")
        try:
            chart_path = plot_bleu_scores(results)
            print(f"✓ Chart saved to: {chart_path}")
        except Exception as e:
            print(f"WARNING: Failed to generate chart: {e}")
            import traceback
            traceback.print_exc()
    
    # Print summary
    print(f"\n{'='*60}")
    print("BLEU EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Reference model: {REFERENCE_MODEL}")
    print(f"Evaluated models: {len(results)}")
    
    if results:
        sorted_results = sorted(results.items(), key=lambda x: x[1]["average_bleu"], reverse=True)
        print(f"\nTop performing models:")
        for model, data in sorted_results[:5]:
            print(f"  {model}: {data['average_bleu']:.4f}")
    
    return 0


if __name__ == "__main__":
    exit(main())

