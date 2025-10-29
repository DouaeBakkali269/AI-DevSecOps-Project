#!/usr/bin/env python3
"""
Policy Evaluation Framework
Evaluates generated policies using BLEU and ROUGE-L metrics
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import logging

import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class PolicyEvaluator:
    """Evaluate generated policies against reference policies"""
    
    def __init__(self, generated_dir: Path, reference_dir: Path):
        self.generated_dir = Path(generated_dir)
        self.reference_dir = Path(reference_dir)
        self.results = {
            "models": {},
            "summary": {}
        }
        
    def evaluate_all(self):
        """Evaluate all generated policies"""
        logger.info("Starting policy evaluation...")
        
        # Load reference policies
        reference_policies = self._load_reference_policies()
        
        # Evaluate each model's policies
        for policy_file in self.generated_dir.glob("*_policies.json"):
            model_name = policy_file.stem.replace("_policies", "")
            logger.info(f"Evaluating {model_name}...")
            
            with open(policy_file) as f:
                data = json.load(f)
                generated_policies = data.get("policies", [])
            
            model_results = self._evaluate_model(generated_policies, reference_policies)
            self.results["models"][model_name] = model_results
            
        # Calculate summary statistics
        self._calculate_summary()
        
    def _load_reference_policies(self) -> Dict[str, str]:
        """Load reference NIST/ISO policy templates"""
        references = {}
        
        # Load NIST CSF templates
        nist_file = self.reference_dir / "nist_csf_templates.json"
        if nist_file.exists():
            with open(nist_file) as f:
                nist_data = json.load(f)
                for template in nist_data.get("templates", []):
                    references[template["control_id"]] = template["policy_text"]
        
        # Load ISO 27001 templates
        iso_file = self.reference_dir / "iso27001_templates.json"
        if iso_file.exists():
            with open(iso_file) as f:
                iso_data = json.load(f)
                for template in iso_data.get("templates", []):
                    references[template["control_id"]] = template["policy_text"]
        
        logger.info(f"Loaded {len(references)} reference policies")
        return references
        
    def _evaluate_model(self, generated_policies: List[Dict], reference_policies: Dict[str, str]) -> Dict:
        """Evaluate policies from a single model"""
        bleu_scores = []
        rouge_scores = []
        
        for policy in generated_policies:
            policy_text = policy.get("policy", "")
            
            # Find best matching reference policy
            best_bleu = 0
            best_rouge = 0
            
            for ref_id, ref_text in reference_policies.items():
                # Calculate BLEU score
                bleu = self._calculate_bleu(policy_text, ref_text)
                bleu_scores.append(bleu)
                best_bleu = max(best_bleu, bleu)
                
                # Calculate ROUGE-L score
                rouge = self._calculate_rouge_l(policy_text, ref_text)
                rouge_scores.append(rouge)
                best_rouge = max(best_rouge, rouge)
        
        results = {
            "bleu": {
                "mean": np.mean(bleu_scores) if bleu_scores else 0,
                "median": np.median(bleu_scores) if bleu_scores else 0,
                "std": np.std(bleu_scores) if bleu_scores else 0,
                "min": np.min(bleu_scores) if bleu_scores else 0,
                "max": np.max(bleu_scores) if bleu_scores else 0
            },
            "rouge_l": {
                "mean": np.mean(rouge_scores) if rouge_scores else 0,
                "median": np.median(rouge_scores) if rouge_scores else 0,
                "std": np.std(rouge_scores) if rouge_scores else 0,
                "min": np.min(rouge_scores) if rouge_scores else 0,
                "max": np.max(rouge_scores) if rouge_scores else 0
            },
            "policy_count": len(generated_policies),
            "evaluation_details": self._analyze_policies(generated_policies)
        }
        
        return results
        
    def _calculate_bleu(self, candidate: str, reference: str) -> float:
        """Calculate BLEU score between candidate and reference"""
        # Tokenize
        candidate_tokens = nltk.word_tokenize(candidate.lower())
        reference_tokens = nltk.word_tokenize(reference.lower())
        
        # Calculate BLEU with smoothing
        smoothing = SmoothingFunction()
        score = sentence_bleu(
            [reference_tokens], 
            candidate_tokens,
            smoothing_function=smoothing.method1
        )
        
        return score
        
    def _calculate_rouge_l(self, candidate: str, reference: str) -> float:
        """Calculate ROUGE-L score between candidate and reference"""
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        scores = scorer.score(reference, candidate)
        return scores['rougeL'].fmeasure
        
    def _analyze_policies(self, policies: List[Dict]) -> Dict:
        """Analyze policy quality metrics"""
        analysis = {
            "avg_length": 0,
            "compliance_coverage": {
                "nist": 0,
                "iso27001": 0,
                "owasp": 0
            },
            "severity_distribution": {}
        }
        
        total_length = 0
        nist_count = 0
        iso_count = 0
        owasp_count = 0
        
        for policy in policies:
            policy_text = policy.get("policy", "")
            total_length += len(policy_text.split())
            
            # Check compliance mentions
            policy_lower = policy_text.lower()
            if "nist" in policy_lower or "csf" in policy_lower:
                nist_count += 1
            if "iso" in policy_lower or "27001" in policy_lower:
                iso_count += 1
            if "owasp" in policy_lower:
                owasp_count += 1
            
            # Count by severity
            severity = policy.get("severity", "UNKNOWN")
            analysis["severity_distribution"][severity] = \
                analysis["severity_distribution"].get(severity, 0) + 1
        
        if policies:
            analysis["avg_length"] = total_length / len(policies)
            analysis["compliance_coverage"]["nist"] = (nist_count / len(policies)) * 100
            analysis["compliance_coverage"]["iso27001"] = (iso_count / len(policies)) * 100
            analysis["compliance_coverage"]["owasp"] = (owasp_count / len(policies)) * 100
        
        return analysis
        
    def _calculate_summary(self):
        """Calculate summary statistics across all models"""
        if not self.results["models"]:
            return
        
        models = self.results["models"]
        
        # Best model by BLEU
        best_bleu_model = max(models.items(), 
                             key=lambda x: x[1]["bleu"]["mean"])
        
        # Best model by ROUGE-L
        best_rouge_model = max(models.items(), 
                              key=lambda x: x[1]["rouge_l"]["mean"])
        
        self.results["summary"] = {
            "best_bleu": {
                "model": best_bleu_model[0],
                "score": best_bleu_model[1]["bleu"]["mean"]
            },
            "best_rouge_l": {
                "model": best_rouge_model[0],
                "score": best_rouge_model[1]["rouge_l"]["mean"]
            },
            "model_comparison": {
                model: {
                    "bleu": data["bleu"]["mean"],
                    "rouge_l": data["rouge_l"]["mean"]
                }
                for model, data in models.items()
            }
        }
        
    def save_results(self, output_file: Path):
        """Save evaluation results to file"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
            
        logger.info(f"Evaluation results saved to {output_file}")
        
        # Print summary
        self._print_summary()
        
    def _print_summary(self):
        """Print evaluation summary"""
        print("\n" + "="*60)
        print("POLICY EVALUATION SUMMARY")
        print("="*60)
        
        for model, results in self.results["models"].items():
            print(f"\n{model.upper()}")
            print("-" * 40)
            print(f"BLEU Score:    {results['bleu']['mean']:.4f} (±{results['bleu']['std']:.4f})")
            print(f"ROUGE-L Score: {results['rouge_l']['mean']:.4f} (±{results['rouge_l']['std']:.4f})")
            print(f"Policies:      {results['policy_count']}")
            print(f"Avg Length:    {results['evaluation_details']['avg_length']:.0f} words")
            
            coverage = results['evaluation_details']['compliance_coverage']
            print(f"\nCompliance Coverage:")
            print(f"  NIST CSF:    {coverage['nist']:.1f}%")
            print(f"  ISO 27001:   {coverage['iso27001']:.1f}%")
            print(f"  OWASP:       {coverage['owasp']:.1f}%")
        
        if self.results["summary"]:
            print("\n" + "="*60)
            print("BEST PERFORMING MODEL")
            print("="*60)
            print(f"Best BLEU:    {self.results['summary']['best_bleu']['model']} "
                  f"({self.results['summary']['best_bleu']['score']:.4f})")
            print(f"Best ROUGE-L: {self.results['summary']['best_rouge_l']['model']} "
                  f"({self.results['summary']['best_rouge_l']['score']:.4f})")
        print()


def main():
    parser = argparse.ArgumentParser(description="Evaluate generated security policies")
    parser.add_argument("--generated", required=True, help="Directory with generated policies")
    parser.add_argument("--reference", required=True, help="Directory with reference policies")
    parser.add_argument("--output", required=True, help="Output JSON file")
    
    args = parser.parse_args()
    
    evaluator = PolicyEvaluator(args.generated, args.reference)
    evaluator.evaluate_all()
    evaluator.save_results(Path(args.output))
    
    logger.info("✅ Evaluation complete!")


if __name__ == "__main__":
    main()
