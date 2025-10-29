#!/bin/bash

# Main Pipeline Execution Script
# Orchestrates the complete DevSecOps security policy generation workflow

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JUICE_SHOP_DIR="${PROJECT_DIR}/app/juice-shop"
RESULTS_DIR="${PROJECT_DIR}/results"
SCAN_REPORTS_DIR="${RESULTS_DIR}/scan_reports"
PARSED_DATA_DIR="${RESULTS_DIR}/parsed_data"
POLICIES_DIR="${RESULTS_DIR}/generated_policies"
EVAL_DIR="${RESULTS_DIR}/evaluations"

# Load environment variables
if [ -f "${PROJECT_DIR}/.env" ]; then
    export $(cat "${PROJECT_DIR}/.env" | grep -v '^#' | xargs)
fi

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  AI-Driven DevSecOps Security Policy Generator                ║${NC}"
echo -e "${GREEN}║  Automated Security Analysis & Policy Generation              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create output directories
mkdir -p "${SCAN_REPORTS_DIR}" "${PARSED_DATA_DIR}" "${POLICIES_DIR}" "${EVAL_DIR}"

# ============================================================================
# Phase 1: Setup OWASP Juice Shop
# ============================================================================
echo -e "${YELLOW}[Phase 1/6] Setting up OWASP Juice Shop...${NC}"

if [ ! -d "${JUICE_SHOP_DIR}" ]; then
    echo "Cloning OWASP Juice Shop..."
    git clone https://github.com/juice-shop/juice-shop.git "${JUICE_SHOP_DIR}"
    cd "${JUICE_SHOP_DIR}"
    npm install
else
    echo "✓ Juice Shop already exists"
fi

# Start Juice Shop
echo "Starting Juice Shop application..."
cd "${JUICE_SHOP_DIR}"
npm start > /dev/null 2>&1 &
JUICE_SHOP_PID=$!
echo "✓ Juice Shop started (PID: ${JUICE_SHOP_PID})"

# Wait for application to be ready
echo "Waiting for application to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null; then
        echo "✓ Application is ready"
        break
    fi
    sleep 2
done

# ============================================================================
# Phase 2: Security Scanning (SAST + SCA + DAST)
# ============================================================================
echo -e "\n${YELLOW}[Phase 2/6] Running security scans...${NC}"

cd "${PROJECT_DIR}"

# SAST - Semgrep
echo "→ Running Semgrep (SAST)..."
if command -v semgrep &> /dev/null; then
    semgrep --config=auto "${JUICE_SHOP_DIR}" \
        --json --output "${SCAN_REPORTS_DIR}/semgrep_report.json" \
        2>/dev/null || true
    echo "  ✓ Semgrep scan complete"
else
    echo "  ⚠ Semgrep not installed, skipping..."
fi

# SAST - NodeJsScan
echo "→ Running NodeJsScan (SAST)..."
if command -v nodejsscan &> /dev/null; then
    nodejsscan -d "${JUICE_SHOP_DIR}" \
        -o "${SCAN_REPORTS_DIR}/nodejsscan_report.json" \
        2>/dev/null || true
    echo "  ✓ NodeJsScan complete"
else
    echo "  ⚠ NodeJsScan not installed, skipping..."
fi

# SCA - npm audit
echo "→ Running npm audit (SCA)..."
cd "${JUICE_SHOP_DIR}"
npm audit --json > "${SCAN_REPORTS_DIR}/npm_audit_report.json" 2>/dev/null || true
echo "  ✓ npm audit complete"
cd "${PROJECT_DIR}"

# SCA - Snyk (if token available)
if [ ! -z "${SNYK_TOKEN}" ]; then
    echo "→ Running Snyk (SCA)..."
    cd "${JUICE_SHOP_DIR}"
    snyk auth "${SNYK_TOKEN}" 2>/dev/null || true
    snyk test --json > "${SCAN_REPORTS_DIR}/snyk_report.json" 2>/dev/null || true
    echo "  ✓ Snyk scan complete"
    cd "${PROJECT_DIR}"
fi

# DAST - OWASP ZAP
echo "→ Running OWASP ZAP (DAST)..."
if command -v zap-cli &> /dev/null || command -v docker &> /dev/null; then
    # Use ZAP Docker image
    docker run --rm -v "${SCAN_REPORTS_DIR}:/zap/wrk:rw" \
        -t softwaresecurityproject/zap-stable zap-baseline.py \
        -t http://host.docker.internal:3000 \
        -J zap_report.json -r zap_report.html \
        2>/dev/null || true
    echo "  ✓ ZAP scan complete"
else
    echo "  ⚠ ZAP not available, skipping..."
fi

echo "✓ Security scanning complete!"

# ============================================================================
# Phase 3: Parse Reports
# ============================================================================
echo -e "\n${YELLOW}[Phase 3/6] Parsing vulnerability reports...${NC}"

python3 parsers/parse_reports.py \
    --input "${SCAN_REPORTS_DIR}" \
    --output "${PARSED_DATA_DIR}/vulnerabilities.json"

echo "✓ Report parsing complete"

# ============================================================================
# Phase 4: Generate Policies with LLMs
# ============================================================================
echo -e "\n${YELLOW}[Phase 4/6] Generating security policies with LLMs...${NC}"

# GPT-4
if [ ! -z "${OPENAI_API_KEY}" ]; then
    echo "→ Generating policies with GPT-4..."
    python3 llm-policy-generator/policy_generator.py \
        --model gpt-4 \
        --input "${PARSED_DATA_DIR}/vulnerabilities.json" \
        --output "${POLICIES_DIR}/gpt4_policies.json"
    echo "  ✓ GPT-4 policies generated"
else
    echo "  ⚠ OpenAI API key not set, skipping GPT-4..."
fi

# Claude
if [ ! -z "${ANTHROPIC_API_KEY}" ]; then
    echo "→ Generating policies with Claude Sonnet 4.5..."
    python3 llm-policy-generator/policy_generator.py \
        --model claude-sonnet-4.5 \
        --input "${PARSED_DATA_DIR}/vulnerabilities.json" \
        --output "${POLICIES_DIR}/claude_policies.json"
    echo "  ✓ Claude policies generated"
else
    echo "  ⚠ Anthropic API key not set, skipping Claude..."
fi

# DeepSeek
if [ ! -z "${TOGETHER_API_KEY}" ]; then
    echo "→ Generating policies with DeepSeek R1..."
    python3 llm-policy-generator/policy_generator.py \
        --model deepseek-r1 \
        --input "${PARSED_DATA_DIR}/vulnerabilities.json" \
        --output "${POLICIES_DIR}/deepseek_policies.json"
    echo "  ✓ DeepSeek policies generated"
else
    echo "  ⚠ Together API key not set, skipping DeepSeek..."
fi

echo "✓ Policy generation complete"

# ============================================================================
# Phase 5: Evaluate Policies
# ============================================================================
echo -e "\n${YELLOW}[Phase 5/6] Evaluating generated policies...${NC}"

python3 evaluation/evaluate_policies.py \
    --generated "${POLICIES_DIR}" \
    --reference reference-policies \
    --output "${EVAL_DIR}/metrics.json"

echo "✓ Evaluation complete"

# ============================================================================
# Phase 6: Generate Report
# ============================================================================
echo -e "\n${YELLOW}[Phase 6/6] Generating final report...${NC}"

# Create summary HTML report
cat > "${RESULTS_DIR}/summary_report.html" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Security Policy Generation Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        .metric { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 4px; }
        .success { color: #27ae60; }
        .warning { color: #f39c12; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #3498db; color: white; }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🛡️ AI-Driven Security Policy Generation Report</h1>
        <p><strong>Generated:</strong> $(date)</p>
        
        <h2>📊 Vulnerability Summary</h2>
        <div class="metric">
            Results available in: <code>results/parsed_data/vulnerabilities.json</code>
        </div>
        
        <h2>🤖 Generated Policies</h2>
        <div class="metric">
            <ul>
                <li>GPT-4 policies: <code>results/generated_policies/gpt4_policies.json</code></li>
                <li>Claude policies: <code>results/generated_policies/claude_policies.json</code></li>
                <li>DeepSeek policies: <code>results/generated_policies/deepseek_policies.json</code></li>
            </ul>
        </div>
        
        <h2>📈 Evaluation Metrics</h2>
        <div class="metric">
            Detailed metrics: <code>results/evaluations/metrics.json</code>
        </div>
        
        <h2>✅ Next Steps</h2>
        <ol>
            <li>Review generated policies in <code>results/generated_policies/</code></li>
            <li>Compare evaluation metrics in <code>results/evaluations/metrics.json</code></li>
            <li>Analyze which LLM performed best</li>
            <li>Prepare final project report</li>
        </ol>
    </div>
</body>
</html>
EOF

echo "✓ Report generated: ${RESULTS_DIR}/summary_report.html"

# ============================================================================
# Cleanup
# ============================================================================
echo -e "\n${YELLOW}Cleaning up...${NC}"
kill ${JUICE_SHOP_PID} 2>/dev/null || true
echo "✓ Juice Shop stopped"

# ============================================================================
# Summary
# ============================================================================
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Pipeline Execution Complete! ✅                               ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "📁 Results Location:"
echo "   → Scan Reports:     ${SCAN_REPORTS_DIR}/"
echo "   → Parsed Data:      ${PARSED_DATA_DIR}/"
echo "   → Generated Policies: ${POLICIES_DIR}/"
echo "   → Evaluations:      ${EVAL_DIR}/"
echo "   → Summary Report:   ${RESULTS_DIR}/summary_report.html"
echo ""
echo "🎯 Next Steps:"
echo "   1. Open summary_report.html in browser"
echo "   2. Review generated policies"
echo "   3. Analyze evaluation metrics"
echo "   4. Prepare final project report"
echo ""
