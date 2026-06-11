"""
pipeline.py — CI/CD Pipeline Runner

Mirrors exactly the flow from your CI/CD diagram:
  Developer → Push code → Build → Run tests → Package → Deploy
                                      ↓ fail           ↓ pass
                               pipeline stops     code released

Run it:  python pipeline.py
"""

import subprocess
import sys
import shutil
import os
import zipfile
import datetime
import json

# ── ANSI colors ────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

ROOT = os.path.dirname(os.path.abspath(__file__))

def log(icon, label, message, color=RESET):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"{color}{BOLD}[{ts}] {icon}  {label:<22}{RESET}{color}{message}{RESET}")

def section(title):
    width = 60
    print(f"\n{BLUE}{BOLD}{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}{RESET}\n")

def fail(reason):
    print(f"\n{RED}{BOLD}✖  PIPELINE FAILED — {reason}{RESET}\n")
    sys.exit(1)

def run(cmd, cwd=ROOT):
    """Run a shell command, return (success, stdout+stderr)."""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True
    )
    return result.returncode == 0, result.stdout + result.stderr


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1 — BUILD  (install dependencies)
# ══════════════════════════════════════════════════════════════════════════════
def stage_build():
    section("STAGE 1 · BUILD")
    log("📦", "Installing deps", "pip install flask pytest ...", YELLOW)

    ok, out = run(f"{sys.executable} -m pip install flask pytest --quiet")
    if not ok:
        log("✖", "Install failed", out, RED)
        fail("Dependency installation failed")

    log("✔", "Dependencies", "Flask + pytest installed", GREEN)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 2 — TEST  (run the test suite)
# ══════════════════════════════════════════════════════════════════════════════
def stage_test():
    section("STAGE 2 · RUN TESTS")
    log("🧪", "Running tests", "pytest tests/ -v", YELLOW)

    test_dir = os.path.join(ROOT, "tests")
    ok, out = run(f"{sys.executable} -m pytest {test_dir} -v --tb=short")

    # Print pytest output indented
    for line in out.splitlines():
        prefix = "  "
        if "PASSED" in line:
            print(f"{GREEN}{prefix}{line}{RESET}")
        elif "FAILED" in line or "ERROR" in line:
            print(f"{RED}{prefix}{line}{RESET}")
        else:
            print(f"{prefix}{line}")

    if not ok:
        log("✖", "Tests failed", "Deployment blocked ❌", RED)
        fail("Test suite failed — deployment stopped")

    log("✔", "All tests passed", "Proceeding to package ✅", GREEN)


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — PACKAGE  (zip the app artifact)
# ══════════════════════════════════════════════════════════════════════════════
def stage_package():
    section("STAGE 3 · PACKAGE")
    log("🗜 ", "Packaging", "Creating deployment artifact ...", YELLOW)

    dist_dir = os.path.join(ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    artifact_name = f"task_manager_v{datetime.date.today().strftime('%Y%m%d')}.zip"
    artifact_path = os.path.join(dist_dir, artifact_name)

    files_to_package = ["app.py"]          # extend with requirements.txt etc.
    missing = [f for f in files_to_package if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        fail(f"Cannot package — missing files: {missing}")

    with zipfile.ZipFile(artifact_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_package:
            zf.write(os.path.join(ROOT, fname), arcname=fname)
            log("  +", fname, "added to artifact", RESET)

    size_kb = os.path.getsize(artifact_path) / 1024
    log("✔", "Artifact created", f"{artifact_name}  ({size_kb:.1f} KB)", GREEN)
    return artifact_path


# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — DEPLOY  (simulate staging → production promotion)
# ══════════════════════════════════════════════════════════════════════════════
def stage_deploy(artifact_path):
    section("STAGE 4 · DEPLOY")

    # ── Staging ──
    log("🚀", "Deploying to STAGING", "Uploading artifact ...", YELLOW)
    staging_dir = os.path.join(ROOT, "environments", "staging")
    os.makedirs(staging_dir, exist_ok=True)
    shutil.copy(artifact_path, staging_dir)
    log("✔", "Staging", "Artifact deployed", GREEN)

    # Simulate a health-check / smoke test on staging
    log("🩺", "Health check", "GET /health → 200 OK  (simulated)", YELLOW)

    # Write a fake deployment receipt
    receipt = {
        "environment": "staging",
        "artifact":    os.path.basename(artifact_path),
        "deployed_at": datetime.datetime.now().isoformat(),
        "status":      "healthy",
    }
    with open(os.path.join(staging_dir, "deployment_receipt.json"), "w") as f:
        json.dump(receipt, f, indent=2)

    log("✔", "Smoke test", "Staging environment healthy", GREEN)

    # ── Production ──
    log("🚀", "Promoting to PRODUCTION", "Copying from staging ...", YELLOW)
    prod_dir = os.path.join(ROOT, "environments", "production")
    os.makedirs(prod_dir, exist_ok=True)
    shutil.copy(artifact_path, prod_dir)

    receipt["environment"] = "production"
    receipt["deployed_at"] = datetime.datetime.now().isoformat()
    with open(os.path.join(prod_dir, "deployment_receipt.json"), "w") as f:
        json.dump(receipt, f, indent=2)

    log("✔", "Production", "App is LIVE ✅", GREEN)


# ══════════════════════════════════════════════════════════════════════════════
# PIPELINE ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════
def run_pipeline():
    print(f"\n{BOLD}{BLUE}╔══════════════════════════════════════════════════════╗")
    print(f"║       CI/CD PIPELINE  —  Task Manager API            ║")
    print(f"╚══════════════════════════════════════════════════════╝{RESET}")
    print(f"  Triggered by: developer push → branch: main")
    print(f"  Started at:   {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    start = datetime.datetime.now()

    stage_build()
    stage_test()
    artifact = stage_package()
    stage_deploy(artifact)

    elapsed = (datetime.datetime.now() - start).seconds

    print(f"\n{GREEN}{BOLD}{'═' * 60}")
    print(f"  ✅  PIPELINE SUCCEEDED  ({elapsed}s)")
    print(f"  Code is live in production.")
    print(f"{'═' * 60}{RESET}\n")


if __name__ == "__main__":
    run_pipeline()
