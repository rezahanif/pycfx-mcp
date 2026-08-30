#!/usr/bin/env python3
"""Generate `aiconnect-capabilities.json` - the tier-2 shadow index the gateway
reads via `manifest.tool_index.capabilities_file`.

Two sources, deliberately labelled apart:

  verified   the 20 hand-maintained `_CFX_API_CATALOG` entries. Each one has a
             curated description and token set and is exercised by the connector's
             own find_api/get_help.
  documented reflected from the shipped CFX schema dumps (config/*_info.json).
             Reflection yields EXISTENCE, not correctness.

sap2000 measured that indexing an unverified doc corpus alongside a verified one
costs negative controls - the ability to say "no tool for that" - for a handful of
extra tier-2 hits. Keep the split so that trade can be re-measured per connector
instead of assumed.
"""
import argparse, ast, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "src/ansys/cfx/mcp/cfx/backend.py"
CONFIG = ROOT / "src/ansys/cfx/mcp/config"
OUT = ROOT / "src/ansys/cfx/mcp/aiconnect-capabilities.json"


def verified():
    for node in ast.walk(ast.parse(BACKEND.read_text())):
        if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", "") == "_CFX_API_CATALOG":
            return [{"name": e["path"], "kind": e["kind"], "stage": e["stage"],
                     "description": e["description"], "verification_status": "verified"}
                    for e in ast.literal_eval(node.value)]
    raise SystemExit("_CFX_API_CATALOG not found")


def documented(limit=None):
    """Reflect the shipped CFX schema dumps.

    The dumps nest under `children` and carry prose in `help`, so a name with no
    `help` string is an existence claim with nothing to retrieve on and is skipped.
    """
    out, seen = [], set()
    for f in sorted(CONFIG.glob("*_info.json")):
        stage = f.stem.replace("_info", "")
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue

        stack = [(data, stage)]
        while stack:
            node, path = stack.pop()
            if limit and len(out) >= limit:
                break
            if not isinstance(node, dict):
                continue
            for key in ("children", "commands", "queries"):
                kids = node.get(key)
                if not isinstance(kids, dict):
                    continue
                for name, child in kids.items():
                    p = f"{path}.{name}"
                    if p in seen:
                        continue
                    seen.add(p)
                    help_text = child.get("help") if isinstance(child, dict) else None
                    if isinstance(help_text, str) and help_text.strip():
                        out.append({"name": p,
                                    "kind": {"commands": "Command", "queries": "Query"}
                                            .get(key, "Parameter"),
                                    "stage": stage,
                                    "description": " ".join(help_text.split())[:300],
                                    "verification_status": "documented"})
                    stack.append((child, p))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-docs", action="store_true",
                    help="also index the reflected schema entries (measure before shipping)")
    ap.add_argument("--doc-limit", type=int, default=2000)
    a = ap.parse_args()
    caps = verified()
    n_v = len(caps)
    if a.include_docs:
        caps += documented(a.doc_limit)
    OUT.write_text(json.dumps({"exec_tool": "run_code", "capabilities": caps}, indent=1))
    print(f"{OUT.relative_to(ROOT)}: {len(caps)} capabilities "
          f"({n_v} verified, {len(caps) - n_v} documented)")


if __name__ == "__main__":
    main()
