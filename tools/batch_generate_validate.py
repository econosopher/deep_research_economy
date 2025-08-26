#!/usr/bin/env python3
"""
Batch generator + validator for multiple games.

Usage:
  python3 tools/batch_generate_validate.py manifest.json --provider gemini [--no-pr] [--model gemini-1.5-pro] [--depth N] [--retries N] [--fix]

Manifest format (JSON):
{
  "entries": [
    {"markdown": "palia_input.md", "title": "Palia"},
    {"markdown": "rainbow_six_siege_input.md", "title": "Rainbow Six Siege"}
  ]
}

Writes a summary report to output/batch_report.json
"""

import os
import sys
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 tools/batch_generate_validate.py manifest.json [--provider gemini] [--no-pr] [--model MODEL]")
        sys.exit(1)
    manifest = Path(sys.argv[1])
    args = sys.argv[2:]
    run_fix = False
    if '--fix' in args:
        run_fix = True
        args = [a for a in args if a != '--fix']

    try:
        spec = json.loads(manifest.read_text())
    except Exception as e:
        print(f"Failed to read manifest: {e}")
        sys.exit(1)

    entries = spec.get('entries', [])
    if not entries:
        print("No entries in manifest")
        sys.exit(1)

    out_dir = ROOT / 'output'
    out_dir.mkdir(exist_ok=True)

    report = {"results": []}
    for item in entries:
        md = item.get('markdown')
        title = item.get('title')
        if not md or not title:
            report['results'].append({"title": title or "(missing)", "status": "skipped", "reason": "missing markdown/title"})
            continue
        md_path = ROOT / md
        if not md_path.exists():
            report['results'].append({"title": title, "status": "skipped", "reason": f"missing file: {md}"})
            continue

        gen_cmd = [sys.executable, str(ROOT / 'economy_json_builder.py'), 'generate', md, title]
        # pass through optional args
        gen_cmd += args

        print(f"\nGenerating: {title}")
        code, out, err = run(gen_cmd)
        gen_log = out + err
        status = "generated" if code == 0 else "failed"

        # Attempt to detect output filename
        out_file = None
        for line in out.splitlines():
            if line.startswith('JSON saved successfully: '):
                out_file = line.split(': ', 1)[1].strip()
                break

        lint_res = None
        val_res = None
        fix_res = None
        if out_file and Path(out_file).exists():
            print(f"Linting: {out_file}")
            code_l, out_l, err_l = run([sys.executable, str(ROOT / 'economy_json_builder.py'), 'lint', out_file])
            lint_res = {"code": code_l, "out": out_l, "err": err_l}
            print(f"Validating: {out_file}")
            code_v, out_v, err_v = run([sys.executable, str(ROOT / 'economy_json_builder.py'), 'validate', out_file])
            val_res = {"code": code_v, "out": out_v, "err": err_v}
            if run_fix and code_v != 0:
                print(f"Attempting auto-fix: {out_file}")
                code_f, out_f, err_f = run([sys.executable, str(ROOT / 'economy_json_builder.py'), 'validate', '--fix', out_file])
                fix_res = {"code": code_f, "out": out_f, "err": err_f}

        report['results'].append({
            "title": title,
            "markdown": md,
            "status": status,
            "output": out_file,
            "generate": {"code": code, "out": out, "err": err},
            "lint": lint_res,
            "validate": val_res,
            "fix": fix_res,
        })

    report_path = out_dir / 'batch_report.json'
    report_path.write_text(json.dumps(report, indent=2))
    print(f"\nBatch report written to: {report_path}")

if __name__ == '__main__':
    main()
