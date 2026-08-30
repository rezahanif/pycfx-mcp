#!/usr/bin/env python3
"""CFX MCP server entrypoint (AiConnect-managed).

Builds the server directly rather than going through `ansys.cfx.mcp.cli.run_cfx`
(the standalone CLI entry point) because `run_cfx` has no hook between building
the server and running it — the licence gate and envelope wrap must install on
the server object before `.run()` is called. This mirrors the pattern every
other AiConnect-adapted connector's `run_server.py` uses (see Skills_SAP,
CAE-Control-MCP): build → install adapter (no-op unless AICONNECT_ENABLE=1) → run.
"""
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

_ROOT = Path(__file__).resolve().parent

# `src/` — the connector's own code. This file previously had NO sys.path setup at
# all, so `from ansys.cfx.mcp import CFXMCP` below only resolved when the project had
# been `pip install`ed. The gateway does not install anything: it spawns
# `python run_server.py` in the unpacked package directory, where `src/` is not on the
# path. Every other AiConnect connector's entry script does this; this one was missed.
_SRC = _ROOT / "src"
if _SRC.is_dir():
    sys.path.insert(0, str(_SRC))

# Vendored dependencies (`stage-python-vendor.py`), shipped inside the package.
# AI CONNECT bundles the INTERPRETER; the connector brings its own LIBRARIES.
# Appended rather than inserted, so a populated dev virtualenv and the host-injected
# `mcp_license_sdk` both keep priority — `_vendor/` is the floor, not an override.
_VENDOR = _ROOT / "_vendor"
if _VENDOR.is_dir():
    sys.path.append(str(_VENDOR))

from ansys.cfx.mcp import CFXMCP  # noqa: E402

if __name__ == "__main__":
    server = CFXMCP(name="ansys-cfx-mcp")

    try:
        from ansys.cfx.mcp.aioconnect import ensure_licensed, install_envelope_middleware

        ensure_licensed()
        if not install_envelope_middleware(server):
            import logging

            logging.getLogger("ansys-cfx-mcp").info(
                "aioconnect: envelope middleware not installed (disabled or unsupported server)"
            )
    except ImportError:
        pass  # adapter absent -> plain upstream server

    server.run(transport="stdio")
