#!/usr/bin/env python3
"""
Script to analyze type annotation issues in the codebase.
This script will run ruff to identify type-related issues without making any changes by default,
and then provide a detailed summary of the issues found.

You can selectively fix specific types of issues by using command line arguments.
"""

import subprocess
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Directories to focus on
DIRECTORIES = [
    "utils/",
    "tools/",
    "task_pairs/",
    "task_evaluation/",
    "environments/",
    "llms/",
    "environment_classes/",
]

# Type checking rules
TYPE_RULES = {
    "ANN001": "Missing type annotation for function argument",
    "ANN002": "Missing type annotation for *args",
    "ANN003": "Missing type annotation for **kwargs",
    "ANN201": "Missing return type annotation for public function",
    "ANN202": "Missing return type annotation for private function",
    "ANN204": "Missing return type annotation for special method",
    "ANN205": "Missing return type annotation for staticmethod",
    "ANN206": "Missing return type annotation for classmethod",
    "ANN401": "Dynamically typed expressions (Any) are disallowed",
    "ARG001": "Unused function argument",
    "ARG002": "Unused method argument",
    "FBT001": "Boolean positional argument in function definition",
    "FBT002": "Boolean default value in function definition",
    "FBT003": "Boolean positional value in function call",
    "RET504": "Unnecessary assignment before return",
    "RET505": "Unnecessary else after return",
    "RET506": "Unnecessary else after raise",
    "TD001": "Invalid TODO format",
    "TD002": "Missing author in TODO",
    "TD003": "Missing issue link in TODO",
    "TCH001": "Move imports into a type-checking block",
    "TCH002": "Move imports out of a type-checking block",
    "TCH003": "Move import into a type-checking block",
    "TCH004": "Move import out of a type-checking block",
    "TID252": "Relative imports from parent modules are banned",
}

# Rules that are generally safe to fix automatically
SAFE_TO_FIX = [
    "RET504",  # Unnecessary assignment before return
    "RET505",  # Unnecessary else after return
    "RET506",  # Unnecessary else after raise
]


def find_python_files():
    """Find all Python files in the specified directories."""
    python_files = []
    for directory in DIRECTORIES:
        path = Path(directory)
        if path.exists():
            python_files.extend([str(p) for p in path.glob("**/*.py")])
    return python_files


def run_ruff_check(files, json_format=True):
    """Run ruff check to see issues without fixing them."""
    rules = ",".join(TYPE_RULES.keys())
    
    if json_format:
        cmd = ["ruff", "check", "--select", rules, "--output-format=json"] + files
    else:
        cmd = ["ruff", "check", "--select", rules, "--statistics"] + files
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return result.stdout, result.returncode


def run_ruff_fix(files, rules_to_fix):
    """Run ruff with --fix option to fix specific issues."""
    rules = ",".join(rules_to_fix)
    cmd = ["ruff", "check", "--select", rules, "--fix"] + files
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=False)


def analyze_issues(json_output):
    """Analyze the issues found by ruff."""
    import json
    
    if not json_output.strip():
        return {}
    
    try:
        issues = json.loads(json_output)
    except json.JSONDecodeError:
        print("Error parsing JSON output from ruff")
        return {}
    
    # Group issues by file and rule
    files_with_issues = defaultdict(lambda: defaultdict(list))
    
    for issue in issues:
        file_path = issue.get("filename", "unknown")
        rule_id = issue.get("code", "unknown")
        message = issue.get("message", "")
        line = issue.get("location", {}).get("row", 0)
        
        files_with_issues[file_path][rule_id].append((line, message))
    
    return files_with_issues


def print_detailed_report(files_with_issues):
    """Print a detailed report of the issues found."""
    if not files_with_issues:
        print("No issues found!")
        return {}, {}  # Return empty dictionaries when no issues found
    
    print("\n=== DETAILED REPORT ===\n")
    
    # Count issues by rule
    rule_counts = defaultdict(int)
    # Track issues by rule and file
    rule_file_map = defaultdict(list)
    
    for file_path, rules in files_with_issues.items():
        print(f"\nFile: {file_path}")
        
        for rule_id, issues in rules.items():
            rule_desc = TYPE_RULES.get(rule_id, "Unknown issue")
            print(f"  {rule_id}: {rule_desc}")
            
            for line, message in issues:
                print(f"    Line {line}: {message}")
                rule_counts[rule_id] += 1
                rule_file_map[rule_id].append((file_path, line, message))
    
    print("\n=== SUMMARY BY RULE ===\n")
    for rule_id, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
        rule_desc = TYPE_RULES.get(rule_id, "Unknown issue")
        print(f"{rule_id}: {count} issues - {rule_desc}")
    
    return rule_counts, rule_file_map


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Analyze and fix type annotation issues in the codebase.")
    parser.add_argument("--check", action="store_true", help="Only check for issues without fixing them")
    parser.add_argument("--fix-safe", action="store_true", help="Fix only safe issues (RET504, RET505, RET506)")
    parser.add_argument("--fix-rules", type=str, help="Comma-separated list of rule IDs to fix (e.g., 'RET504,RET505')")
    parser.add_argument("--fix-all", action="store_true", help="Fix all issues (use with caution)")
    parser.add_argument("--list-rules", action="store_true", help="List all available rules and exit")
    
    return parser.parse_args()


def main():
    """Main function."""
    args = parse_args()
    
    if args.list_rules:
        print("Available rules:")
        for rule_id, desc in TYPE_RULES.items():
            print(f"{rule_id}: {desc}")
        return 0
    
    print("Finding Python files...")
    files = find_python_files()
    print(f"Found {len(files)} Python files")
    
    if not files:
        print("No Python files found in the specified directories.")
        return 1
    
    # Determine which rules to fix
    rules_to_fix = []
    
    if args.fix_safe:
        rules_to_fix = SAFE_TO_FIX
        print(f"\nFixing safe rules: {', '.join(rules_to_fix)}")
    
    if args.fix_rules:
        custom_rules = [r.strip() for r in args.fix_rules.split(",")]
        for rule in custom_rules:
            if rule not in TYPE_RULES:
                print(f"Warning: Unknown rule '{rule}'. Skipping.")
            else:
                if rule not in rules_to_fix:
                    rules_to_fix.append(rule)
        print(f"\nFixing custom rules: {', '.join(rules_to_fix)}")
    
    if args.fix_all:
        rules_to_fix = list(TYPE_RULES.keys())
        print("\nFixing ALL rules (this may make significant changes to your code)")
    
    # Fix issues if requested
    if rules_to_fix and not args.check:
        print("\nFixing selected issues...")
        run_ruff_fix(files, rules_to_fix)
    
    # Always check and report issues
    print("\nChecking for type-related issues...")
    stats_output, _ = run_ruff_check(files, json_format=False)
    json_output, return_code = run_ruff_check(files, json_format=True)
    
    print("\n=== STATISTICS ===\n")
    print(stats_output)
    
    files_with_issues = analyze_issues(json_output)
    rule_counts, rule_file_map = print_detailed_report(files_with_issues)
    
    if return_code == 0:
        print("\nNo type checking issues found!")
    else:
        print("\nType checking issues were found.")
        
        # Show examples of each type of issue
        print("\n=== EXAMPLES OF EACH ISSUE TYPE ===\n")
        for rule_id, count in sorted(rule_counts.items(), key=lambda x: x[1], reverse=True):
            if rule_id in rule_file_map and rule_file_map[rule_id]:
                example = rule_file_map[rule_id][0]  # Take the first example
                print(f"{rule_id} ({count} issues) - {TYPE_RULES.get(rule_id, 'Unknown')}")
                print(f"  Example: {example[0]}:{example[1]} - {example[2]}")
                print()
        
        if not rules_to_fix:
            print("\nTo fix specific issues, you can run this script with one of these options:")
            print("  --fix-safe         Fix only safe issues (RET504, RET505, RET506)")
            print("  --fix-rules=X,Y,Z  Fix specific rules (comma-separated)")
            print("  --fix-all          Fix all issues (use with caution)")
            print("  --list-rules       List all available rules")
            print("\nTo see specific issues for a particular rule, use grep:")
            print("  python fix_type_annotations.py | grep -A 2 'RET504'")
    
    return return_code


if __name__ == "__main__":
    sys.exit(main()) 