#!/usr/bin/env python3
"""
Setup Verification Script
Checks if all dependencies and configurations are correct
Windows-friendly version - pauses before closing
"""

import sys
import subprocess
import os
from pathlib import Path
import importlib

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_mark(passed):
    return f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 9
    status = check_mark(passed)
    print(f"{status} Python version: {version.major}.{version.minor}.{version.micro}")
    if not passed:
        print(f"   {Colors.YELLOW}⚠ Python 3.9+ required. You have {version.major}.{version.minor}{Colors.END}")
    return passed

def check_command(command, name):
    """Check if a command exists"""
    try:
        result = subprocess.run([command, '--version'],
                              capture_output=True, text=True, timeout=5)
        passed = result.returncode == 0
        status = check_mark(passed)
        if passed:
            version = result.stdout.split('\n')[0]
            print(f"{status} {name}: {version}")
        else:
            print(f"{status} {name}: Not found")
        return passed
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{check_mark(False)} {name}: Not found")
        return False

def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"{check_mark(True)} {package_name}: {version}")
        return True
    except ImportError:
        print(f"{check_mark(False)} {package_name}: Not installed")
        return False

def check_env_file():
    """Check if .env file exists and has required keys"""
    env_file = Path('.env')

    if not env_file.exists():
        print(f"{check_mark(False)} .env file: Not found")
        print(f"   {Colors.YELLOW}→ Copy .env.example to .env and add your API keys{Colors.END}")
        return False

    with open(env_file) as f:
        content = f.read()

    has_openai = 'OPENAI_API_KEY=' in content and 'sk-' in content
    has_anthropic = 'ANTHROPIC_API_KEY=' in content and 'sk-ant-' in content
    has_together = 'TOGETHER_API_KEY=' in content

    api_keys_found = has_openai or has_anthropic or has_together

    print(f"{check_mark(True)} .env file: Found")
    print(f"   OpenAI key:    {check_mark(has_openai)}")
    print(f"   Anthropic key: {check_mark(has_anthropic)}")
    print(f"   Together key:  {check_mark(has_together)}")

    if not api_keys_found:
        print(f"   {Colors.YELLOW}⚠ No API keys configured - add at least one{Colors.END}")

    return api_keys_found

def check_directories():
    """Check if required directories exist"""
    required_dirs = [
        'pipeline', 'scanners', 'parsers', 'llm-policy-generator',
        'evaluation', 'reference-policies', 'results', 'docs'
    ]

    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        exists = dir_path.exists()
        print(f"{check_mark(exists)} Directory: {dir_name}")
        if not exists:
            print(f"   {Colors.YELLOW}→ Missing directory: {dir_name}{Colors.END}")
        all_exist = all_exist and exists

    return all_exist

def check_juice_shop():
    """Check if Juice Shop is cloned"""
    juice_shop_dir = Path('app/juice-shop')
    exists = juice_shop_dir.exists()

    if exists:
        has_package_json = (juice_shop_dir / 'package.json').exists()
        has_node_modules = (juice_shop_dir / 'node_modules').exists()

        print(f"{check_mark(True)} Juice Shop: Cloned")
        print(f"   package.json:  {check_mark(has_package_json)}")
        print(f"   node_modules:  {check_mark(has_node_modules)}")

        if not has_node_modules:
            print(f"   {Colors.YELLOW}→ Run: cd app/juice-shop && npm install{Colors.END}")

        return has_package_json
    else:
        print(f"{check_mark(False)} Juice Shop: Not cloned")
        print(f"   {Colors.YELLOW}→ Run: git clone https://github.com/juice-shop/juice-shop.git app/juice-shop{Colors.END}")
        return False

def check_docker():
    """Check if Docker is available"""
    try:
        result = subprocess.run(['docker', 'ps'],
                              capture_output=True, text=True, timeout=5)
        passed = result.returncode == 0
        status = check_mark(passed)

        if passed:
            print(f"{status} Docker: Running")
        else:
            print(f"{status} Docker: Not running (optional)")

        return passed
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"{check_mark(False)} Docker: Not available (optional)")
        return False

def print_next_steps(core_ok, config_ok, packages_ok):
    """Print what to do next based on results"""
    print(f"\n{Colors.BOLD}NEXT STEPS:{Colors.END}")
    print("=" * 60)

    if core_ok and config_ok and packages_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Your setup is ready!{Colors.END}\n")
        print("You can now run the pipeline:")
        print(f"{Colors.GREEN}  ./run_pipeline.sh{Colors.END}")
        print("\nOr on Windows:")
        print(f"{Colors.GREEN}  bash run_pipeline.sh{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}⚠ Please complete these steps:{Colors.END}\n")

        if not core_ok:
            print(f"{Colors.RED}CRITICAL - Core Requirements:{Colors.END}")
            print("  1. Install Python 3.9 or higher")
            print("  2. Install Node.js 18 or higher")
            print("  3. Install Git")
            print()

        if not packages_ok:
            print(f"{Colors.YELLOW}Install Python Packages:{Colors.END}")
            print("  pip install -r requirements.txt")
            print()

        if not config_ok:
            print(f"{Colors.YELLOW}Complete Configuration:{Colors.END}")
            print("  1. Copy .env.example to .env")
            print("  2. Add at least one API key to .env")
            print("  3. Clone Juice Shop:")
            print("     git clone https://github.com/juice-shop/juice-shop.git app/juice-shop")
            print("  4. Install Juice Shop:")
            print("     cd app/juice-shop && npm install")
            print()

def main():
    try:
        print_header("AI-DEVSECOPS PROJECT SETUP VERIFICATION")

        checks = {
            'core': [],
            'tools': [],
            'packages': [],
            'config': [],
            'optional': []
        }

        # Core checks
        print(f"\n{Colors.BOLD}1. Core Requirements{Colors.END}")
        print("-" * 40)
        checks['core'].append(check_python_version())
        checks['core'].append(check_command('node', 'Node.js'))
        checks['core'].append(check_command('npm', 'npm'))
        checks['core'].append(check_command('git', 'Git'))

        # Security tools
        print(f"\n{Colors.BOLD}2. Security Tools{Colors.END}")
        print("-" * 40)
        checks['tools'].append(check_command('semgrep', 'Semgrep'))
        checks['tools'].append(check_command('nodejsscan', 'NodeJsScan'))
        print(f"   {Colors.BLUE}ℹ These will be installed if missing{Colors.END}")

        # Optional tools
        print(f"\n{Colors.BOLD}3. Optional Tools{Colors.END}")
        print("-" * 40)
        checks['optional'].append(check_docker())
        checks['optional'].append(check_command('snyk', 'Snyk'))

        # Python packages
        print(f"\n{Colors.BOLD}4. Python Packages{Colors.END}")
        print("-" * 40)
        required_packages = [
            ('openai', 'openai'),
            ('anthropic', 'anthropic'),
            ('nltk', 'nltk'),
            ('rouge-score', 'rouge_score'),
            ('matplotlib', 'matplotlib'),
            ('pandas', 'pandas'),
            ('requests', 'requests')
        ]

        for display_name, import_name in required_packages:
            checks['packages'].append(check_python_package(display_name, import_name))

        # Configuration
        print(f"\n{Colors.BOLD}5. Configuration{Colors.END}")
        print("-" * 40)
        checks['config'].append(check_env_file())
        checks['config'].append(check_directories())
        checks['config'].append(check_juice_shop())

        # Summary
        print_header("VERIFICATION SUMMARY")

        core_passed = sum(checks['core'])
        tools_passed = sum(checks['tools'])
        packages_passed = sum(checks['packages'])
        config_passed = sum(checks['config'])
        optional_passed = sum(checks['optional'])

        print(f"Core Requirements:  {core_passed}/{len(checks['core'])} passed")
        print(f"Security Tools:     {tools_passed}/{len(checks['tools'])} passed")
        print(f"Python Packages:    {packages_passed}/{len(checks['packages'])} passed")
        print(f"Configuration:      {config_passed}/{len(checks['config'])} passed")
        print(f"Optional Tools:     {optional_passed}/{len(checks['optional'])} passed")

        # Determine overall status
        core_ok = core_passed == len(checks['core'])
        config_ok = config_passed >= 2  # At least directories and some config
        packages_ok = packages_passed >= len(checks['packages']) - 2  # Allow 2 missing

        # Print next steps
        print_next_steps(core_ok, config_ok, packages_ok)

        return 0 if (core_ok and config_ok and packages_ok) else 1

    except Exception as e:
        print(f"\n{Colors.RED}Error during verification: {e}{Colors.END}")
        return 1

    finally:
        # PAUSE - Wait for user input before closing
        print("\n" + "=" * 60)
        input(f"\n{Colors.BOLD}Press ENTER to exit...{Colors.END}")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)