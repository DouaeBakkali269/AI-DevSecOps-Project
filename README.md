# 🛡️ AI-Driven DevSecOps Security Policy Generator

**Final Project 2025/2026 - 3GL**

Automated security policy generation from vulnerability reports using LLMs (GPT-4, Claude, DeepSeek).

## 📋 Project Overview

This project transforms technical vulnerability reports (SAST, SCA, DAST) into human-readable security policies compliant with NIST CSF and ISO/IEC 27001 using Large Language Models.

**Target Application:** OWASP Juice Shop (Node.js e-commerce application with intentional vulnerabilities)

---

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Git
- API Keys: OpenAI, Anthropic (Claude), or DeepSeek

### Setup Steps

```bash
# 1. Clone this project
cd ai-devsecops-project

# 2. Clone OWASP Juice Shop
git clone https://github.com/juice-shop/juice-shop.git app/juice-shop

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 5. Run the complete pipeline
./run_pipeline.sh
```

---

## 📁 Project Structure

```
ai-devsecops-project/
├── app/                          # OWASP Juice Shop application
├── pipeline/                     # CI/CD configurations
│   ├── github-actions.yml       # GitHub Actions workflow
│   └── docker-compose.yml       # Local testing environment
├── scanners/                     # Security scanning scripts
│   ├── run_sast.sh             # SAST (Semgrep, Bandit, NodeJsScan)
│   ├── run_sca.sh              # SCA (npm audit, Snyk)
│   └── run_dast.sh             # DAST (OWASP ZAP)
├── parsers/                      # Report parsing
│   ├── parse_reports.py        # Universal report parser
│   └── vulnerability_mapper.py  # Maps vulns to standards
├── llm-policy-generator/         # AI policy generation
│   ├── policy_generator.py     # Main generator (3 LLMs)
│   ├── prompts.py              # Prompt templates
│   └── models/                 # Model configurations
├── evaluation/                   # Evaluation framework
│   ├── evaluate_policies.py    # BLEU/ROUGE-L metrics
│   └── reference_comparison.py # Compare with templates
├── reference-policies/           # NIST/ISO templates
│   ├── nist_csf_templates.json
│   └── iso27001_templates.json
├── results/                      # Generated outputs
│   ├── scan_reports/           # Raw scan results
│   ├── parsed_data/            # Structured vulnerability data
│   ├── generated_policies/     # AI-generated policies
│   └── evaluations/            # Metric results
└── docs/                         # Documentation
    ├── report_template.md      # Project report
    └── presentation.pptx       # Presentation slides
```

---

## 🔧 Components

### 1. Security Scanning Tools

**SAST (Static Application Security Testing):**
- **Semgrep**: Multi-language static analysis
- **NodeJsScan**: Node.js specific vulnerabilities
- **npm audit**: Dependency vulnerabilities

**SCA (Software Composition Analysis):**
- **npm audit**: Known vulnerabilities in dependencies
- **Snyk**: Comprehensive dependency scanning

**DAST (Dynamic Application Security Testing):**
- **OWASP ZAP**: Web application vulnerability scanner

### 2. LLM Models (Comparative Study)

1. **GPT-4** (OpenAI)
2. **Claude Sonnet 4.5** (Anthropic)
3. **DeepSeek R1** or **LLaMA 3.3** (Open Source)

### 3. Evaluation Metrics

- **BLEU Score**: Translation quality
- **ROUGE-L**: Longest common subsequence
- **Compliance Score**: Alignment with NIST/ISO standards

---

## 🎯 Pipeline Workflow

```
1. Deploy Juice Shop (Docker)
   ↓
2. Run Security Scans (SAST + SCA + DAST)
   ↓
3. Parse Reports (JSON/XML → Structured Data)
   ↓
4. Generate Policies with LLMs (3 models)
   ↓
5. Evaluate Policies (BLEU/ROUGE-L)
   ↓
6. Generate Report & Visualizations
```

---

## 📊 Expected Results

### Sample Vulnerability → Policy Transformation

**Input (Vulnerability Report):**
```json
{
  "vulnerability": "SQL Injection",
  "severity": "HIGH",
  "location": "login.js:45",
  "cwe": "CWE-89"
}
```

**Output (Generated Policy - NIST CSF):**
```
Control ID: PR.DS-5
Control: Protections against data leaks are implemented

Policy Statement:
All user inputs must be validated and sanitized before database queries.
Implement parameterized queries or prepared statements to prevent SQL injection.

Implementation:
- Use ORM frameworks (e.g., Sequelize) with parameter binding
- Implement input validation on both client and server side
- Deploy Web Application Firewall (WAF) rules for SQL injection patterns

Compliance Mapping:
- NIST CSF: PR.DS-5 (Data-at-rest protection)
- ISO 27001: A.14.2.5 (Secure system engineering principles)
- OWASP Top 10: A03:2021 - Injection
```

---

## 📝 Deliverables Checklist

- [ ] **Functional Pipeline**: GitHub Actions or local Docker setup
- [ ] **3 Security Scans**: SAST, SCA, DAST reports
- [ ] **Report Parser**: JSON/XML parsing scripts
- [ ] **LLM Integration**: 3 models generating policies
- [ ] **Evaluation**: BLEU/ROUGE-L comparison
- [ ] **Reference Policies**: NIST CSF & ISO 27001 templates
- [ ] **Project Report**: 15-20 pages (LaTeX/Word)
- [ ] **Presentation**: 10-15 min slides
- [ ] **Demo Video**: 5-min walkthrough

---

## 🔬 Research Questions

1. How accurately do LLMs interpret technical vulnerability data?
2. Which model performs best for security policy generation?
3. Can AI-generated policies achieve >80% similarity with human-written policies?
4. What are the ethical implications of automated governance?

---

## 📚 References

### DevSecOps & Security
- OWASP Top 10
- NIST Cybersecurity Framework
- ISO/IEC 27001:2022

### LLMs & AI
- Attention Is All You Need (Transformers)
- LLaMA: Open and Efficient Foundation Language Models
- Constitutional AI: Harmlessness from AI Feedback

---

## 🛠️ Troubleshooting

### Common Issues

**Issue**: OWASP ZAP fails to start
**Solution**: Increase Docker memory to 4GB minimum

**Issue**: LLM API rate limits
**Solution**: Add retry logic with exponential backoff (already included)

**Issue**: Parsing errors
**Solution**: Check report format (JSON vs XML vs SARIF)

---

## 📧 Support

For questions or issues:
- Check `/docs/troubleshooting.md`
- Review example outputs in `/results/examples/`

---

## 📄 License

This project is for educational purposes (Final Project 2025/2026).

---

**⚡ Ready to run?** Execute `./run_pipeline.sh` and watch the magic happen!
