#!/usr/bin/env python3
"""
Generate Visualizations for Project Results
Creates charts and graphs for the final report
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
import numpy as np

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

def load_vulnerabilities(file_path):
    """Load vulnerability data"""
    with open(file_path) as f:
        data = json.load(f)
    return data

def load_metrics(file_path):
    """Load evaluation metrics"""
    with open(file_path) as f:
        data = json.load(f)
    return data

def plot_vulnerability_distribution(vuln_data, output_dir):
    """Plot vulnerability distribution by severity and type"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # By Severity
    severity_data = vuln_data['metadata']['by_severity']
    severities = list(severity_data.keys())
    counts = list(severity_data.values())
    
    colors = {'CRITICAL': '#d32f2f', 'HIGH': '#f57c00', 
              'MEDIUM': '#fbc02d', 'LOW': '#388e3c', 'INFO': '#1976d2'}
    bar_colors = [colors.get(s, '#9e9e9e') for s in severities]
    
    axes[0].bar(severities, counts, color=bar_colors)
    axes[0].set_title('Vulnerabilities by Severity', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Severity Level')
    axes[0].set_ylabel('Count')
    axes[0].grid(axis='y', alpha=0.3)
    
    # By Type (SAST/SCA/DAST)
    type_data = vuln_data['metadata']['by_type']
    types = list(type_data.keys())
    type_counts = list(type_data.values())
    
    axes[1].bar(types, type_counts, color=['#3498db', '#2ecc71', '#e74c3c'])
    axes[1].set_title('Vulnerabilities by Scan Type', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Scan Type')
    axes[1].set_ylabel('Count')
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'vulnerability_distribution.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'vulnerability_distribution.png'}")
    plt.close()

def plot_tool_comparison(vuln_data, output_dir):
    """Plot comparison of different scanning tools"""
    tool_data = vuln_data['metadata']['by_tool']
    
    tools = list(tool_data.keys())
    counts = list(tool_data.values())
    
    plt.figure(figsize=(12, 6))
    bars = plt.barh(tools, counts, color=sns.color_palette("husl", len(tools)))
    
    # Add value labels
    for i, bar in enumerate(bars):
        width = bar.get_width()
        plt.text(width, bar.get_y() + bar.get_height()/2, 
                f' {int(width)}', ha='left', va='center', fontweight='bold')
    
    plt.title('Vulnerability Detection by Tool', fontsize=14, fontweight='bold')
    plt.xlabel('Number of Vulnerabilities Detected')
    plt.ylabel('Security Tool')
    plt.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'tool_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'tool_comparison.png'}")
    plt.close()

def plot_model_comparison(metrics_data, output_dir):
    """Plot LLM model comparison"""
    models = list(metrics_data['models'].keys())
    
    bleu_scores = [metrics_data['models'][m]['bleu']['mean'] for m in models]
    rouge_scores = [metrics_data['models'][m]['rouge_l']['mean'] for m in models]
    
    x = np.arange(len(models))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar(x - width/2, bleu_scores, width, label='BLEU', color='#3498db')
    bars2 = ax.bar(x + width/2, rouge_scores, width, label='ROUGE-L', color='#2ecc71')
    
    ax.set_xlabel('LLM Model', fontweight='bold')
    ax.set_ylabel('Score', fontweight='bold')
    ax.set_title('LLM Model Performance Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([m.upper() for m in models])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'model_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'model_comparison.png'}")
    plt.close()

def plot_compliance_coverage(metrics_data, output_dir):
    """Plot compliance framework coverage"""
    models = list(metrics_data['models'].keys())
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    frameworks = ['nist', 'iso27001', 'owasp']
    titles = ['NIST CSF Coverage', 'ISO 27001 Coverage', 'OWASP Coverage']
    
    for idx, framework in enumerate(frameworks):
        coverage = [metrics_data['models'][m]['evaluation_details']['compliance_coverage'][framework] 
                   for m in models]
        
        bars = axes[idx].bar([m.upper() for m in models], coverage, 
                            color=sns.color_palette("Set2", len(models)))
        axes[idx].set_title(titles[idx], fontweight='bold')
        axes[idx].set_ylabel('Coverage (%)')
        axes[idx].set_ylim(0, 100)
        axes[idx].grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            axes[idx].text(bar.get_x() + bar.get_width()/2., height,
                          f'{height:.1f}%', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'compliance_coverage.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'compliance_coverage.png'}")
    plt.close()

def plot_severity_heatmap(vuln_data, output_dir):
    """Create a heatmap of vulnerabilities by tool and severity"""
    # Create data structure
    tools = list(vuln_data['metadata']['by_tool'].keys())
    severities = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO']
    
    # Count vulnerabilities by tool and severity
    matrix = []
    for tool in tools:
        row = []
        tool_vulns = [v for v in vuln_data['vulnerabilities'] if v.get('tool') == tool]
        for severity in severities:
            count = len([v for v in tool_vulns if v.get('severity') == severity])
            row.append(count)
        matrix.append(row)
    
    # Create heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt='d', cmap='YlOrRd', 
                xticklabels=severities, yticklabels=tools,
                cbar_kws={'label': 'Number of Vulnerabilities'})
    plt.title('Vulnerability Distribution: Tool vs Severity', fontsize=14, fontweight='bold')
    plt.xlabel('Severity Level', fontweight='bold')
    plt.ylabel('Security Tool', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'severity_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_dir / 'severity_heatmap.png'}")
    plt.close()

def generate_summary_stats(vuln_data, metrics_data, output_file):
    """Generate summary statistics document"""
    summary = []
    summary.append("=" * 60)
    summary.append("PROJECT RESULTS SUMMARY")
    summary.append("=" * 60)
    summary.append("")
    
    # Vulnerability Stats
    summary.append("VULNERABILITY DETECTION")
    summary.append("-" * 40)
    summary.append(f"Total Vulnerabilities: {vuln_data['metadata']['total_vulnerabilities']}")
    summary.append("")
    summary.append("By Severity:")
    for sev, count in vuln_data['metadata']['by_severity'].items():
        summary.append(f"  {sev:10s}: {count:3d}")
    summary.append("")
    summary.append("By Type:")
    for vtype, count in vuln_data['metadata']['by_type'].items():
        summary.append(f"  {vtype:10s}: {count:3d}")
    summary.append("")
    
    # Model Performance
    summary.append("LLM MODEL PERFORMANCE")
    summary.append("-" * 40)
    for model, data in metrics_data['models'].items():
        summary.append(f"\n{model.upper()}")
        summary.append(f"  BLEU Score:    {data['bleu']['mean']:.4f} (±{data['bleu']['std']:.4f})")
        summary.append(f"  ROUGE-L Score: {data['rouge_l']['mean']:.4f} (±{data['rouge_l']['std']:.4f})")
        summary.append(f"  Policies Generated: {data['policy_count']}")
    
    summary.append("")
    summary.append("BEST PERFORMING MODEL")
    summary.append("-" * 40)
    if 'summary' in metrics_data and metrics_data['summary']:
        summary.append(f"Best BLEU:    {metrics_data['summary']['best_bleu']['model']} "
                      f"({metrics_data['summary']['best_bleu']['score']:.4f})")
        summary.append(f"Best ROUGE-L: {metrics_data['summary']['best_rouge_l']['model']} "
                      f"({metrics_data['summary']['best_rouge_l']['score']:.4f})")
    
    summary.append("")
    summary.append("=" * 60)
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(summary))
    
    print(f"✓ Saved: {output_file}")
    
    # Also print to console
    print('\n' + '\n'.join(summary))

def main():
    # Paths
    project_dir = Path(__file__).parent.parent
    vuln_file = project_dir / "results" / "parsed_data" / "vulnerabilities.json"
    metrics_file = project_dir / "results" / "evaluations" / "metrics.json"
    output_dir = project_dir / "results" / "visualizations"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("GENERATING VISUALIZATIONS")
    print("=" * 60)
    print()
    
    # Check if files exist
    if not vuln_file.exists():
        print(f"❌ Vulnerability file not found: {vuln_file}")
        print("   Run the pipeline first: ./run_pipeline.sh")
        return
    
    if not metrics_file.exists():
        print(f"❌ Metrics file not found: {metrics_file}")
        print("   Run the evaluation first")
        return
    
    # Load data
    vuln_data = load_vulnerabilities(vuln_file)
    metrics_data = load_metrics(metrics_file)
    
    # Generate visualizations
    print("Generating charts...")
    plot_vulnerability_distribution(vuln_data, output_dir)
    plot_tool_comparison(vuln_data, output_dir)
    plot_severity_heatmap(vuln_data, output_dir)
    
    if metrics_data.get('models'):
        plot_model_comparison(metrics_data, output_dir)
        plot_compliance_coverage(metrics_data, output_dir)
    
    # Generate summary
    summary_file = output_dir / "summary_statistics.txt"
    generate_summary_stats(vuln_data, metrics_data, summary_file)
    
    print()
    print("=" * 60)
    print("✅ ALL VISUALIZATIONS GENERATED!")
    print("=" * 60)
    print()
    print(f"📁 Output Location: {output_dir}")
    print()
    print("Generated files:")
    for file in output_dir.glob("*.png"):
        print(f"  → {file.name}")
    print(f"  → summary_statistics.txt")
    print()

if __name__ == "__main__":
    main()
