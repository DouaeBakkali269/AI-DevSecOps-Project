# 🚀 Quick Start Guide
## Get Your Project Running in 15 Minutes

---

## Prerequisites Check

Before starting, make sure you have:

- [ ] **Python 3.9+** installed (`python3 --version`)
- [ ] **Node.js 18+** installed (`node --version`)
- [ ] **Git** installed (`git --version`)
- [ ] **Docker** installed (optional, but recommended) (`docker --version`)
- [ ] At least **one LLM API key** (OpenAI, Anthropic, or Together AI)

---

## Step 1: Clone & Setup (5 minutes)

```bash
# Navigate to your project directory
cd ~/projects

# If you don't have the project yet, create it
mkdir ai-devsecops-project
cd ai-devsecops-project

# Copy all the files I created into this directory
# (You should have: pipeline/, scanners/, parsers/, llm-policy-generator/, etc.)
```

---

## Step 2: Install Dependencies (5 minutes)

### Python Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# If you get permission errors, use:
pip install --user -r requirements.txt
```

### Node.js Setup

```bash
# Clone OWASP Juice Shop
git clone https://github.com/juice-shop/juice-shop.git app/juice-shop

# Install Juice Shop dependencies
cd app/juice-shop
npm install
cd ../..
```

### Security Tools

```bash
# Install Semgrep
pip install semgrep

# Install NodeJsScan
pip install nodejsscan

# Install NLTK data for evaluation
python3 -c "import nltk; nltk.download('punkt')"
```

---

## Step 3: Configure API Keys (2 minutes)

```bash
# Copy the environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Get API Keys:**

1. **OpenAI (GPT-4)**: https://platform.openai.com/api-keys
   - Sign up → Billing → Add payment → Create key
   - Cost: ~$2-5 for this project

2. **Anthropic (Claude)**: https://console.anthropic.com/
   - Sign up → Get API key
   - Cost: ~$1-3 for this project

3. **Together AI (DeepSeek)**: https://api.together.xyz/
   - Sign up → API keys
   - Cost: ~$0.50 for this project

**Minimum Setup:** You need at least ONE API key to run the project.

---

## Step 4: Run the Pipeline (3 minutes)

```bash
# Make the script executable (if not already)
chmod +x run_pipeline.sh

# Run the complete pipeline
./run_pipeline.sh
```

**What happens:**
1. ✅ Starts OWASP Juice Shop
2. ✅ Runs security scans (SAST, SCA, DAST)
3. ✅ Parses vulnerability reports
4. ✅ Generates policies with LLMs
5. ✅ Evaluates policies
6. ✅ Creates final report

**Expected time:** 10-20 minutes (depending on scan depth)

---

## Step 5: View Results (1 minute)

```bash
# Open the summary report
open results/summary_report.html
# Or on Linux: xdg-open results/summary_report.html
# Or on Windows: start results/summary_report.html
```

**What to check:**
- `results/scan_reports/` - Raw security scan outputs
- `results/parsed_data/vulnerabilities.json` - Structured vulnerability data
- `results/generated_policies/` - AI-generated policies
- `results/evaluations/metrics.json` - BLEU/ROUGE scores

---

## Troubleshooting

### Issue: "Module not found"

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: "API key not found"

```bash
# Verify .env file
cat .env | grep API_KEY

# Make sure no extra spaces around the = sign
# Correct: OPENAI_API_KEY=sk-abc123
# Wrong:   OPENAI_API_KEY = sk-abc123
```

### Issue: "Port 3000 already in use"

```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9

# Or change the port in docker-compose.yml
```

### Issue: "OWASP ZAP fails to start"

```bash
# ZAP is optional - skip it if issues persist
# The pipeline will still work with SAST and SCA

# Or use Docker version:
docker run -v $(pwd)/results:/zap/wrk \
  softwaresecurityproject/zap-stable \
  zap-baseline.py -t http://host.docker.internal:3000
```

### Issue: "Out of API credits"

**Free Alternatives:**
1. Use **Together AI** (DeepSeek) - cheapest option
2. Use **Hugging Face** inference API (free tier)
3. Run **local LLaMA** with Ollama:
   ```bash
   # Install Ollama
   curl https://ollama.ai/install.sh | sh
   
   # Run LLaMA locally
   ollama run llama3.3
   ```

---

## Next Steps

1. ✅ **Review Generated Policies**
   - Open each policy file in `results/generated_policies/`
   - Compare outputs from different models

2. ✅ **Analyze Metrics**
   - Check BLEU and ROUGE-L scores
   - Identify best-performing model

3. ✅ **Start Your Report**
   - Use template in `docs/report_template.md`
   - Fill in your results

4. ✅ **Prepare Presentation**
   - Create slides with key findings
   - Include architecture diagram
   - Show example policies

---

## Time-Saving Tips

### If you have **1 week**:
- Use only 1 LLM model
- Skip Snyk (use just npm audit)
- Use pre-written report sections
- Focus on core implementation

### If you have **2 weeks**:
- Use 2 LLM models for comparison
- Add basic visualizations
- Write thorough report sections
- Create good presentation

### If you have **3 weeks**:
- Use all 3 LLM models
- Add bonus features (refinement model)
- Conduct thorough analysis
- Create polished deliverables

---

## Common Commands

```bash
# Run only scanning
./scanners/run_sast.sh
./scanners/run_sca.sh

# Run only parsing
python3 parsers/parse_reports.py \
  --input results/scan_reports \
  --output results/parsed_data/vulnerabilities.json

# Run only policy generation
python3 llm-policy-generator/policy_generator.py \
  --model gpt-4 \
  --input results/parsed_data/vulnerabilities.json \
  --output results/generated_policies/gpt4_policies.json

# Run only evaluation
python3 evaluation/evaluate_policies.py \
  --generated results/generated_policies \
  --reference reference-policies \
  --output results/evaluations/metrics.json
```

---

## Docker Alternative (Easiest)

If you want everything in containers:

```bash
# Start everything with Docker Compose
cd pipeline
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

---

## Getting Help

1. **Check documentation**: Read `README.md` and `docs/report_template.md`
2. **Review examples**: Look at `results/examples/` (if available)
3. **Check logs**: Look in `results/*.log` for errors
4. **Debug mode**: Set `VERBOSE=true` in `.env`

---

## Success Checklist

- [ ] Pipeline runs without errors
- [ ] Vulnerabilities detected and parsed
- [ ] At least 1 LLM generates policies
- [ ] Evaluation metrics calculated
- [ ] Summary report generated
- [ ] Can explain the architecture
- [ ] Understanding of results

---

**🎉 You're ready to go! Run `./run_pipeline.sh` and watch the magic happen!**

If you get stuck, review the error messages carefully - they usually tell you exactly what's wrong.

Good luck! 🚀
