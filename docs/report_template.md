# Final Project Report
## Integrating Generative AI into DevSecOps for Automated Security Policy Generation

**Student Name:** [Your Name]  
**Program:** 3GL  
**Academic Year:** 2025/2026  
**Date:** [Submission Date]

---

## Executive Summary

[Brief overview of the project, key findings, and main contributions - 200-300 words]

This project explores the integration of Large Language Models (LLMs) into DevSecOps pipelines to automate the generation of security policies from technical vulnerability reports. We implemented a complete pipeline that scans the OWASP Juice Shop application using SAST, SCA, and DAST tools, then uses three different LLMs (GPT-4, Claude Sonnet 4.5, and DeepSeek R1) to generate security policies compliant with NIST CSF and ISO/IEC 27001 standards. 

Key findings include:
- [Model X] achieved the highest BLEU score of [X.XX]
- [Model Y] demonstrated superior compliance coverage at [XX]%
- The automated approach reduced policy generation time by [XX]%

---

## Table of Contents

1. Introduction & Context
2. Literature Review
3. Methodology
4. Architecture & Implementation
5. Results & Evaluation
6. Discussion
7. Ethical Considerations
8. Conclusion & Future Work
9. References
10. Appendices

---

## 1. Introduction & Context

### 1.1 Problem Statement

Modern software development increasingly relies on DevSecOps pipelines to ensure continuous integration of security throughout the development lifecycle. However, a persistent challenge remains: translating technical vulnerability reports into actionable, human-readable security policies aligned with international standards such as NIST CSF and ISO/IEC 27001.

Traditional approaches to security policy generation are:
- **Time-consuming**: Manual policy writing requires significant expertise and time
- **Inconsistent**: Different analysts may interpret the same vulnerability differently
- **Lagging**: Policies often lag behind newly discovered vulnerabilities
- **Error-prone**: Manual processes are susceptible to human error

### 1.2 Research Questions

This project addresses the following research questions:

1. **RQ1**: How accurately can LLMs interpret technical vulnerability data from multiple security scanning tools?
2. **RQ2**: Which LLM architecture (GPT-4, Claude, or DeepSeek) performs best for security policy generation?
3. **RQ3**: Can AI-generated policies achieve comparable quality (>80% similarity) to human-written policies?
4. **RQ4**: What are the ethical and practical implications of using AI for automated security governance?

### 1.3 Project Objectives

- Set up a comprehensive DevSecOps pipeline integrating SAST, SCA, and DAST tools
- Develop parsing mechanisms to preprocess security reports from multiple formats
- Implement LLM-based policy generation using three different models
- Evaluate generated policies using quantitative metrics (BLEU, ROUGE-L)
- Analyze compliance with security frameworks (NIST CSF, ISO 27001)
- Critically assess ethical, privacy, and reliability concerns

### 1.4 Scope & Limitations

**In Scope:**
- OWASP Juice Shop as target application
- Three security scanning types (SAST, SCA, DAST)
- Three LLM models for comparative analysis
- NIST CSF and ISO/IEC 27001 compliance mapping

**Out of Scope:**
- Real-time threat intelligence integration
- Automated policy deployment and enforcement
- Multi-language application support
- Production-level scalability optimization

---

## 2. Literature Review

### 2.1 DevSecOps and Security Automation

[Review existing literature on DevSecOps practices, security automation, and policy generation]

**Key References:**
- Kim, G., et al. (2021). *The DevOps Handbook*
- OWASP DevSecOps Guidelines
- NIST Special Publication 800-218: Secure Software Development Framework

### 2.2 Large Language Models in Cybersecurity

[Discuss recent applications of LLMs in security, including vulnerability detection, threat analysis, and documentation generation]

**Recent Developments:**
- GPT-4 Technical Report (OpenAI, 2023)
- Claude 2 Constitutional AI (Anthropic, 2023)
- DeepSeek R1: Reinforcement Learning for Reasoning
- LLaMA 3: Open Foundation Models

### 2.3 Security Policy Frameworks

[Overview of NIST CSF and ISO 27001, their structure, and compliance requirements]

**Standards Reviewed:**
- NIST Cybersecurity Framework 2.0
- ISO/IEC 27001:2022
- OWASP Top 10 2021

### 2.4 Research Gap

Despite advancements in both DevSecOps automation and LLM capabilities, limited research exists on using LLMs specifically for security policy generation. This project fills this gap by:
- Providing empirical comparison of multiple LLM models
- Establishing evaluation metrics for policy quality
- Addressing compliance alignment systematically

---

## 3. Methodology

### 3.1 Research Design

This project follows a **Design Science Research** approach with the following phases:

1. **Problem Identification**: Gap in automated policy generation
2. **Design**: DevSecOps pipeline with LLM integration
3. **Development**: Implementation of scanning, parsing, and generation components
4. **Evaluation**: Quantitative and qualitative assessment
5. **Communication**: Documentation and presentation

### 3.2 Target Application

**OWASP Juice Shop**
- Technology: Node.js, Express, Angular, SQLite
- Purpose: Intentionally vulnerable web application
- Vulnerabilities: 100+ known security flaws
- Why selected: Well-documented, diverse vulnerability types, active community

### 3.3 Security Scanning Tools

#### SAST (Static Application Security Testing)
- **Semgrep**: Multi-language static analysis
- **NodeJsScan**: Node.js specific security scanning
- **Bandit**: Python security linter (for comparison)

#### SCA (Software Composition Analysis)
- **npm audit**: Node.js dependency vulnerability scanning
- **Snyk**: Comprehensive dependency and license scanning

#### DAST (Dynamic Application Security Testing)
- **OWASP ZAP**: Web application penetration testing

### 3.4 LLM Models Selection

| Model | Version | Parameters | API Provider | Cost |
|-------|---------|------------|--------------|------|
| GPT-4 | gpt-4 | 1.76T (estimated) | OpenAI | $0.03/1K tokens |
| Claude | Sonnet 4.5 | Unknown | Anthropic | $0.015/1K tokens |
| DeepSeek | R1 | 671B | Together AI | $0.0008/1K tokens |

**Selection Criteria:**
- State-of-the-art performance
- API availability
- Different architectures (transformer, constitutional AI, reasoning)
- Cost-effectiveness for research

### 3.5 Evaluation Metrics

#### Quantitative Metrics

**BLEU (Bilingual Evaluation Understudy)**
- Measures n-gram overlap between generated and reference policies
- Range: 0.0 to 1.0 (higher is better)
- Formula: BLEU = BP × exp(∑(wₙ log pₙ))

**ROUGE-L (Recall-Oriented Understudy for Gisting Evaluation - Longest Common Subsequence)**
- Measures longest common subsequence between texts
- Range: 0.0 to 1.0 (higher is better)
- Formula: ROUGE-L = (1+β²)×(R×P) / (R+β²×P)

#### Qualitative Metrics

- **Compliance Coverage**: Percentage of policies mentioning NIST/ISO controls
- **Policy Completeness**: Presence of required sections (scope, requirements, implementation)
- **Actionability**: Specificity and implementability of recommendations

### 3.6 Experimental Setup

**Hardware:**
- [Your system specifications]

**Software:**
- Python 3.11
- Node.js 18.x
- Docker 24.x
- GitHub Actions for CI/CD

**API Keys Required:**
- OpenAI API key
- Anthropic API key
- Together AI API key

---

## 4. Architecture & Implementation

### 4.1 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DevSecOps Pipeline                       │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              OWASP Juice Shop Application                   │
│                  (Target System)                            │
└─────────────────────────────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐     ┌────────┐    ┌────────┐
         │  SAST  │     │  SCA   │    │  DAST  │
         └────────┘     └────────┘    └────────┘
         Semgrep        npm audit      OWASP ZAP
         NodeJsScan     Snyk
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌─────────────────┐
                    │ Report Parser   │
                    │ (Multi-format)  │
                    └─────────────────┘
                             │
                             ▼
                ┌────────────────────────────┐
                │  Structured Vulnerability  │
                │  Data (JSON)               │
                └────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐     ┌────────┐    ┌────────┐
         │  GPT-4 │     │ Claude │    │DeepSeek│
         └────────┘     └────────┘    └────────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                ┌────────────────────────────┐
                │   Generated Policies       │
                │   (NIST CSF & ISO 27001)   │
                └────────────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   Evaluation    │
                    │   (BLEU/ROUGE)  │
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Final Report    │
                    │ & Dashboard     │
                    └─────────────────┘
```

### 4.2 Component Details

#### 4.2.1 Security Scanning Layer

[Detailed description of how each scanner is configured and integrated]

**Implementation:**
```python
# Example SAST configuration
semgrep_config = {
    "rules": "auto",
    "output_format": "json",
    "metrics": True
}
```

#### 4.2.2 Report Parser

[Explain the parsing logic for different report formats]

**Key Features:**
- Universal JSON/XML/HTML parser
- CWE and OWASP mapping
- Severity normalization
- Deduplication logic

#### 4.2.3 LLM Policy Generator

[Detail the prompt engineering and API integration]

**Prompt Structure:**
```
System: You are a security policy expert...
User: Generate policy for [vulnerability type]...
Context: [Vulnerability details, standards, requirements]
```

#### 4.2.4 Evaluation Framework

[Describe the evaluation pipeline and metrics calculation]

### 4.3 Implementation Challenges

1. **Report Format Inconsistency**: Different tools use different output formats
2. **API Rate Limiting**: Managing LLM API quotas
3. **Vulnerability Deduplication**: Same issue reported by multiple tools
4. **Context Length Limits**: LLMs have token limits

**Solutions Implemented:**
[Describe how you addressed each challenge]

---

## 5. Results & Evaluation

### 5.1 Vulnerability Detection Results

**Total Vulnerabilities Found:** [X]

| Severity | SAST | SCA | DAST | Total |
|----------|------|-----|------|-------|
| Critical | X    | X   | X    | X     |
| High     | X    | X   | X    | X     |
| Medium   | X    | X   | X    | X     |
| Low      | X    | X   | X    | X     |

**Top 5 Vulnerability Types:**
1. [Type] - [Count] instances
2. [Type] - [Count] instances
3. [Type] - [Count] instances
4. [Type] - [Count] instances
5. [Type] - [Count] instances

### 5.2 Policy Generation Results

**Total Policies Generated:**
- GPT-4: [X] policies
- Claude: [X] policies
- DeepSeek: [X] policies

### 5.3 Quantitative Evaluation

#### BLEU Scores

| Model | Mean | Median | Std Dev | Min | Max |
|-------|------|--------|---------|-----|-----|
| GPT-4 | X.XX | X.XX   | X.XX    | X.XX| X.XX|
| Claude| X.XX | X.XX   | X.XX    | X.XX| X.XX|
| DeepSeek| X.XX | X.XX | X.XX    | X.XX| X.XX|

#### ROUGE-L Scores

| Model | Mean | Median | Std Dev | Min | Max |
|-------|------|--------|---------|-----|-----|
| GPT-4 | X.XX | X.XX   | X.XX    | X.XX| X.XX|
| Claude| X.XX | X.XX   | X.XX    | X.XX| X.XX|
| DeepSeek| X.XX | X.XX | X.XX    | X.XX| X.XX|

### 5.4 Qualitative Evaluation

#### Compliance Coverage

| Model | NIST CSF | ISO 27001 | OWASP |
|-------|----------|-----------|-------|
| GPT-4 | XX%      | XX%       | XX%   |
| Claude| XX%      | XX%       | XX%   |
| DeepSeek| XX%    | XX%       | XX%   |

#### Policy Quality Analysis

**Average Policy Length:**
- GPT-4: [X] words
- Claude: [X] words
- DeepSeek: [X] words

**Completeness Score** (presence of required sections):
[Analysis of how many policies include all required sections]

### 5.5 Comparative Analysis

**Best Performing Model:**
[Based on your results, which model performed best overall and why]

**Model Strengths & Weaknesses:**

**GPT-4:**
- Strengths: [List]
- Weaknesses: [List]

**Claude:**
- Strengths: [List]
- Weaknesses: [List]

**DeepSeek:**
- Strengths: [List]
- Weaknesses: [List]

---

## 6. Discussion

### 6.1 Interpretation of Results

[Discuss what the results mean in context of research questions]

**RQ1: Accuracy of Vulnerability Interpretation**
[Your findings]

**RQ2: Best Performing Model**
[Your findings]

**RQ3: Similarity to Human-Written Policies**
[Your findings]

**RQ4: Practical Implications**
[Your findings]

### 6.2 Practical Applications

**Benefits:**
- Reduced policy generation time from days to minutes
- Consistent policy format and structure
- Automatic compliance mapping
- Scalable to large vulnerability datasets

**Limitations:**
- Requires human review and validation
- May miss contextual organizational requirements
- Dependent on API availability and cost
- Risk of AI hallucination

### 6.3 Comparison with Existing Approaches

[Compare your approach with manual policy generation and rule-based automation]

---

## 7. Ethical Considerations

### 7.1 AI Reliability and Trust

- **Hallucination Risk**: LLMs may generate plausible but incorrect policies
- **Accountability**: Who is responsible for AI-generated security guidance?
- **Validation**: Human oversight remains essential

### 7.2 Privacy Concerns

- **Data Exposure**: Vulnerability reports may contain sensitive system information
- **API Privacy**: Sending security data to third-party LLM providers
- **Recommendation**: Use private LLM deployments for sensitive environments

### 7.3 Bias and Fairness

- **Training Data Bias**: LLMs trained on public security content may favor certain frameworks
- **Language Limitations**: Most LLMs perform best in English
- **Mitigation**: Diverse reference policies and multi-model comparison

### 7.4 Responsible AI Use

**Best Practices:**
1. Always validate AI-generated policies with security experts
2. Maintain human-in-the-loop for critical decisions
3. Use AI as augmentation, not replacement
4. Regularly audit policy quality
5. Implement version control and change tracking

---

## 8. Conclusion & Future Work

### 8.1 Summary of Findings

[Concise summary of main results and contributions]

This project successfully demonstrated that:
1. [Key finding 1]
2. [Key finding 2]
3. [Key finding 3]

### 8.2 Contributions

**Technical Contributions:**
- Complete DevSecOps pipeline with LLM integration
- Multi-format vulnerability report parser
- Comparative evaluation framework

**Research Contributions:**
- Empirical comparison of LLMs for policy generation
- Quantitative metrics for policy quality assessment
- Analysis of AI reliability in security governance

### 8.3 Limitations

1. **Limited Scope**: Single application (Juice Shop)
2. **Snapshot Evaluation**: Point-in-time assessment, not longitudinal
3. **Evaluation Metrics**: BLEU/ROUGE may not fully capture policy quality
4. **Resource Constraints**: Limited API budget for extensive testing

### 8.4 Future Work

**Short-term Improvements:**
1. Test on diverse applications (Python, Java, PHP)
2. Implement second-stage refinement model
3. Add real-time feedback loop
4. Develop policy validation framework

**Long-term Research Directions:**
1. Fine-tune open-source LLMs on security policy corpus
2. Integrate threat intelligence feeds
3. Automated policy deployment and enforcement
4. Multi-stakeholder policy generation (developers, auditors, executives)

### 8.5 Final Remarks

[Personal reflection on the project and lessons learned]

---

## 9. References

[Use IEEE, ACM, or your institution's preferred citation format]

### Academic Papers
1. Author, A. (Year). Title. *Journal*, volume(issue), pages.

### Standards & Frameworks
1. NIST (2024). *Cybersecurity Framework 2.0*
2. ISO/IEC (2022). *Information Security Management - ISO/IEC 27001:2022*
3. OWASP (2021). *OWASP Top 10 2021*

### Technical Documentation
1. OpenAI (2023). *GPT-4 Technical Report*
2. Anthropic (2023). *Claude 2: Constitutional AI*
3. DeepSeek (2024). *DeepSeek R1: Reinforcement Learning Reasoning*

### Tools & Software
1. OWASP Juice Shop: https://github.com/juice-shop/juice-shop
2. Semgrep: https://semgrep.dev/
3. OWASP ZAP: https://www.zaproxy.org/

---

## 10. Appendices

### Appendix A: Installation Guide

[Step-by-step setup instructions]

### Appendix B: Sample Policies

[Include 2-3 complete generated policies as examples]

### Appendix C: Evaluation Data

[Include full evaluation metrics tables]

### Appendix D: Code Repository

GitHub Repository: [Your repository URL]

---

## Document Information

**Document Version:** 1.0  
**Last Updated:** [Date]  
**Word Count:** [Approximate count]  
**Contact:** [Your email]

---

**End of Report**
