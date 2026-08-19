"""
Phase L.9.4 — Production Provider Readiness Diagnostic CLI.

Validates provider credentials, network latency, model authorization,
and minimal generation health without exposing secrets.

Generates backend/provider_readiness.json.
"""

from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.ai.providers.provider_readiness import (
    ProviderReadinessService,
    ProviderReadinessStatus,
)
from app.core.config import settings


async def main() -> int:
    print("=" * 60, flush=True)
    print("DhanSarthi AI Provider Readiness Diagnostics", flush=True)
    print("=" * 60, flush=True)

    service = ProviderReadinessService()
    diag = await service.check_all_configured()

    primary_res = diag["primary_result"]
    has_key = bool(settings.ai_provider_api_key)
    key_display = "CONFIGURED" if has_key else "NOT CONFIGURED"

    print(f"\nProvider:       {diag['provider']}", flush=True)
    print(f"Primary Model:  {diag['primary_model']}", flush=True)
    print(f"API Key:        {key_display}", flush=True)
    print(f"Authentication: {'PASS' if primary_res['authenticated'] else 'FAIL'}", flush=True)
    print(f"Model Access:   {'PASS' if primary_res['model_accessible'] else 'FAIL' if primary_res['authenticated'] else 'UNKNOWN'}", flush=True)
    print(f"Test Gen:       {'PASS' if primary_res['test_generation'] else 'SKIPPED' if not primary_res['model_accessible'] else 'FAIL'}", flush=True)
    print(f"Status:         {primary_res['status']}", flush=True)
    if primary_res.get("safe_error_message"):
        print(f"Details:        {primary_res['safe_error_message']}", flush=True)

    if diag.get("fallback_model"):
        fb_res = diag["fallback_result"]
        print("\n--- Fallback Diagnostic Model ---", flush=True)
        print(f"Fallback Model: {diag['fallback_model']}", flush=True)
        print(f"Fallback Status:{fb_res['status']}", flush=True)
        if fb_res.get("safe_error_message"):
            print(f"Details:        {fb_res['safe_error_message']}", flush=True)

    # Save to provider_readiness.json
    output_path = "provider_readiness.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2)

    print(f"\nDiagnostic results saved to {output_path}", flush=True)
    print("=" * 60, flush=True)

    return 0 if primary_res["status"] == ProviderReadinessStatus.READY.value else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
