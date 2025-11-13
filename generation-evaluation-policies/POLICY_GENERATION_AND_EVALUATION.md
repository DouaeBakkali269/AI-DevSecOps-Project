# Policy Generation and Evaluation Framework

This document provides a comprehensive overview of the policy generation and evaluation framework implemented in this project.

## Table of Contents
1. [Policy Generation](#policy-generation)
   - [Process Overview](#process-overview)
   - [Key Components](#key-components)
   - [Usage](#usage)

2. [Evaluation Methods](#evaluation-methods)
   - [BLEU Score](#bleu-score)
   - [ROUGE-L Score](#rouge-l-score)
   - [AI-as-a-Judge](#ai-as-a-judge)

3. [AI-as-a-Judge Implementation Details](#ai-as-a-judge-implementation-details)
   - [Evaluation Criteria](#evaluation-criteria)
   - [Scoring System](#scoring-system)
   - [Implementation](#implementation)

4. [Running the Framework](#running-the-framework)
   - [Prerequisites](#prerequisites)
   - [Execution Steps](#execution-steps)

## Policy Generation

### Process Overview
The policy generation process involves creating security policies that align with ISO 27001 Annex A controls. The system uses various LLM models to generate these policies based on vulnerability data and ISO 27001 templates.

### Key Components

1. **Input Data**
   - Vulnerability data from security scans
   - ISO 27001 Annex A control templates
   - ISO 27001 control descriptions

2. **Generation Process**
   - Loads vulnerabilities and ISO 27001 controls
   - Builds a comprehensive system prompt for the LLM
   - Generates policies using specified LLM models
   - Saves generated policies in JSON format

3. **Supported Models**
   - openai/gpt-5 (reference model)
   - openai/gpt-5-mini
   - openai/gpt-5-nano
   - openai/gpt-oss-120b
   - x-ai/grok-4-fast
   - minimax/minimax-m2
   - meta-llama/llama-3.3-70b-instruct
   - z-ai/glm-4.6
   - google/gemini-2.5-flash

### Usage
```bash
# Generate policies for all models
python generate/run-all-generations.py

# Generate policies for a specific model
python generate/generate-policies.py --model openai/gpt-5
```

## Evaluation Methods

The framework includes three main evaluation methods to assess the quality of generated policies.

### BLEU Score
- **Purpose**: Measures the n-gram overlap between generated and reference policies
- **Implementation**: Uses sacreBLEU library with fallback to NLTK
- **Output**: Scores from 0 to 1, where 1 indicates perfect match with reference

### ROUGE-L Score
- **Purpose**: Evaluates the longest common subsequence between generated and reference policies
- **Implementation**: Uses ROUGE-L metric focusing on recall of longest common subsequences
- **Output**: F1 score between 0 and 1

### AI-as-a-Judge
- **Purpose**: Uses an LLM (GPT-5) to evaluate policies based on multiple criteria
- **Implementation**: Detailed evaluation across five dimensions (see below)
- **Output**: Scores from 0-100 for each criterion and an overall score

## AI-as-a-Judge Implementation Details

### Evaluation Criteria

1. **ISO 27001 Alignment (0-100)**
   - How well the policy aligns with the specified ISO 27001 control
   - Assesses if the policy addresses the intended security concerns

2. **Policy Completeness (0-100)**
   - Evaluates if the policy covers all relevant aspects of the control
   - Checks for missing elements compared to the reference policy

3. **Actionability (0-100)**
   - Assesses if the policy provides clear, implementable actions
   - Evaluates specificity and practicality of requirements

4. **Technical Accuracy (0-100)**
   - Verifies the technical correctness of the policy
   - Checks for accurate security measures and mitigations

5. **Linguistic Quality (0-100)**
   - Evaluates clarity, coherence, and professionalism of the policy text
   - Assesses if the tone is appropriate for a security policy document

### Scoring System
- Each criterion is scored from 0-100
- The overall score is the average of all criteria scores
- Scores are aggregated across all policy pairs for a final model evaluation

### Implementation

The AI judge is implemented in `evaluate/evaluate-ai-judge.py` with the following key components:

1. **Policy Matching**
   - Matches policies between reference and candidate by control_id
   - Falls back to index-based matching if control_id matching fails

2. **Evaluation Prompt**
   - Uses a detailed prompt that includes:
     - The reference policy (gold standard)
     - The candidate policy to evaluate
     - Clear evaluation criteria and scoring instructions
     - Required output format (JSON)

3. **API Integration**
   - Uses OpenRouter API to access the judge model (GPT-5)
   - Implements robust error handling and retries
   - Includes timeout and rate limiting considerations

4. **Result Aggregation**
   - Calculates average scores across all evaluated policies
   - Generates visualizations of the results
   - Saves detailed evaluation metrics

## Running the Framework

### Prerequisites
- Python 3.8+
- Required packages (install with `pip install -r requirements.txt`)
- OpenRouter API key set in environment variables

### Execution Steps

1. **Generate Policies**
   ```bash
   cd generation-evaluation-policies
   python generate/run-all-generations.py
   ```

2. **Run Evaluations**
   ```bash
   # Run all evaluations (BLEU, ROUGE-L, and AI Judge)
   python evaluate/run-all-evaluations.py
   
   # Run specific evaluation
   python evaluate/evaluate-ai-judge.py
   ```

3. **View Results**
   - Generated policies: `generated_policies/`
   - Evaluation results: `evaluation-results/`
   - Charts and visualizations: `evaluation-images/`

## Output Files

- **Generated Policies**: JSON files named `{model_name}_policies.json`
- **Evaluation Results**: 
  - `bleu_results.json`
  - `rouge_results.json`
  - `ai_judge_results.json`
- **Visualizations**:
  - `bleu_scores_chart.png`
  - `rouge_scores_chart.png`
  - `ai_judge_scores_chart.png`

## Troubleshooting

1. **Missing API Key**
   - Ensure `OPENROUTER_API_KEY` is set in your environment variables
   - Create a `.env` file in the project root if needed

2. **Model Failures**
   - Some models may fail due to rate limiting or API issues
   - Check the logs for specific error messages
   - The framework will continue with remaining models if one fails

3. **Memory Issues**
   - Large policy sets may require significant memory
   - Consider processing in smaller batches if needed
