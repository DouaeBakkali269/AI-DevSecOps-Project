#!/usr/bin/env python3
"""
Master Script: Run All Evaluations
Runs all evaluation scripts in sequence: BLEU, ROUGE-L, and AI-as-a-Judge
"""

import sys
import subprocess
from pathlib import Path


def run_script(script_name):
    """Run a Python script and return success status."""
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_name}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            check=False
        )
        
        if result.returncode == 0:
            print(f"\n✓ {script_name} completed successfully")
            return True
        else:
            print(f"\n✗ {script_name} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"\n✗ Error running {script_name}: {e}")
        return False


def main():
    """Run all evaluation scripts in sequence."""
    print(f"\n{'='*60}")
    print("RUNNING ALL EVALUATIONS")
    print(f"{'='*60}")
    print("\nThis script will run:")
    print("  1. BLEU Score Evaluation")
    print("  2. ROUGE-L Score Evaluation")
    print("  3. AI-as-a-Judge Evaluation")
    print("\nNote: Make sure you have generated policies first using run-all-generations.py")
    
    scripts = [
        "evaluate-bleu.py",
        "evaluate-rouge.py",
        "evaluate-ai-judge.py"
    ]
    
    results = {}
    
    for script in scripts:
        success = run_script(script)
        results[script] = success
        
        if not success:
            print(f"\nWARNING: {script} failed. Continuing with remaining evaluations...")
    
    # Print summary
    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    
    for script, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"  {script}: {status}")
    
    successful = sum(1 for s in results.values() if s)
    total = len(results)
    
    print(f"\nTotal: {successful}/{total} evaluations completed successfully")
    
    if successful == total:
        print("\n✓ All evaluations completed successfully!")
        return 0
    else:
        print(f"\n✗ {total - successful} evaluation(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())

