"""Entrypoint script for RunPod serverless workers.

This repository already contains a *local* package called ``runpod`` which holds
our project-specific worker code.  Unfortunately, the official **RunPod Python
SDK** that provides ``runpod.serverless.start`` is published on PyPI under the
*same* top-level module name (``runpod``).  When Python tries to ``import
runpod`` it therefore loads *our* local package first and the submodules from
the SDK (``runpod.serverless`` et al.) are **not found**, causing the worker to
crash during cold-start.

To resolve the namespace clash we:
1. Import the local package (this is automatic because we are inside the
   project root).
2. Detect the path of the *installed* SDK distribution using ``pkg_resources``.
3. Append that path to ``runpod.__path__`` so that its submodule search scope
   includes the SDK files as well.

With this patch, ``import runpod.serverless`` succeeds even though the top-level
package originates from our codebase.
"""

import os
import sys
from pathlib import Path

# Step-1: Import LOCAL package first (this happens implicitly, but we keep the
# explicit import for clarity and to obtain a reference to the module object).
import runpod  # noqa: E402

# ---------------------------------------------------------------------------
# Step-2: Extend package __path__ to include SDK implementation
# ---------------------------------------------------------------------------

try:
    import pkg_resources  # Part of setuptools

    dist = pkg_resources.get_distribution("runpod")  # The *SDK* distribution
    sdk_pkg_path = Path(dist.location) / "runpod"

    # Ensure path exists and is not already part of the search path.
    if sdk_pkg_path.exists() and str(sdk_pkg_path) not in runpod.__path__:
        runpod.__path__.append(str(sdk_pkg_path))

except Exception as exc:  # pragma: no cover – best-effort patch
    # If we fail to locate the SDK we still proceed; an AttributeError will be
    # raised later when we attempt to access ``runpod.serverless`` which will
    # surface a clear error in the logs.
    print(f"[runpod_handler] Warning: could not patch SDK path – {exc}", file=sys.stderr)

# Now that the SDK path is part of the package namespace we can safely import
# the serverless sub-module.
from runpod.worker.main_handler import handler  # noqa: E402

try:
    from runpod import serverless as rp_serverless  # noqa: E402
except (ImportError, AttributeError) as err:
    print("[runpod_handler] ERROR: RunPod SDK not available – check image dependencies.", file=sys.stderr)
    raise err

# ---------------------------------------------------------------------------
# RunPod Serverless Entrypoint
# ---------------------------------------------------------------------------
# When this file is executed inside a RunPod serverless worker, it simply
# forwards the call to the real `handler` function defined in
# `runpod/worker/main_handler.py`.
# 
# IMPORTANT: The handler module (main_handler.py) now starts the serverless
# worker itself, so we only need this wrapper for local testing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Allow local testing via `python runpod_handler.py --rp_serve_api`.
    if "--rp_serve_api" in sys.argv:
        import os
        os.environ['LOCAL_TESTING'] = '1'
        rp_serverless.start({"handler": handler})
    else:
        # Production path - the handler module will start serverless itself
        # Just import to trigger the module-level serverless.start()
        pass
