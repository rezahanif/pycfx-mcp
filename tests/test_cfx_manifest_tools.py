# Copyright (C) 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Coverage for the CFX-specific tools added in c74703d.

Every one of them shipped with no dedicated test: `test_all_tools.py` loops over
`_exposed` but swallows exceptions and is gated behind `-m integration`, so a tool
could return an error envelope for every call and stay green. These assert the
tool -> backend wiring and the disconnected-state contract without needing CFX.
"""

from __future__ import annotations

from typing import Any

import pytest

from ansys.cfx.mcp import CFXMCP
from ansys.cfx.mcp.cfx.backend import CFXBackend


async def _call(leaf: CFXMCP, name: str, **kwargs: Any) -> Any:
    tool = await leaf.get_tool(name)
    assert tool is not None, f"{name} is not exposed"
    return await tool.fn(**kwargs)


# --- the surviving CFX tools are all registered ------------------------------

CFX_TOOLS = (
    "connect_cfx",
    "get_setup",
    "set_setup",
    "save_case",
    "start_solve",
    "get_solve_status",
    "stop_solve",
    "get_results",
    "disconnect_cfx",
    "list_cfx_api_categories",
)


@pytest.mark.parametrize("name", CFX_TOOLS)
@pytest.mark.asyncio
async def test_cfx_tool_is_registered_and_callable(name: str) -> None:
    tool = await CFXMCP().get_tool(name)
    assert tool is not None
    assert tool.description


@pytest.mark.parametrize("name", CFX_TOOLS)
def test_cfx_tool_is_declared_in_a_toolset(name: str) -> None:
    leaf = CFXMCP()
    catalogued: set[str] = set()
    for toolset in leaf.build_toolsets():
        catalogued.update(toolset["tools"])
    assert name in catalogued


# --- backend helpers added by c74703d ---------------------------------------


class _Node:
    def __init__(self) -> None:
        self.applied: list[Any] = []

    def set_state(self, value: Any) -> None:
        self.applied.append(value)


class _FrozenNode:
    """A CCL node with no set_state - the branch that must not raise."""


@pytest.mark.asyncio
async def test_set_state_requires_a_session() -> None:
    backend = CFXBackend()
    result = await backend.set_state(path="domain.x", value=1)
    assert result["status"] == "error"
    assert "No active CFX session" in result["message"]


@pytest.mark.asyncio
async def test_set_state_applies_the_value(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = CFXBackend()
    node = _Node()
    monkeypatch.setattr(backend, "is_connected", lambda: True)
    monkeypatch.setattr(backend, "_resolve_live_path", lambda path: node)

    result = await backend.set_state(
        path="domain.fluid_models.turbulence_model.option", value="SST"
    )

    assert result == {
        "status": "ok",
        "path": "domain.fluid_models.turbulence_model.option",
        "value": "SST",
    }
    assert node.applied == ["SST"]


@pytest.mark.asyncio
async def test_set_state_reports_a_path_that_cannot_be_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = CFXBackend()
    monkeypatch.setattr(backend, "is_connected", lambda: True)
    monkeypatch.setattr(backend, "_resolve_live_path", lambda path: _FrozenNode())

    result = await backend.set_state(path="domain.readonly", value=1)

    assert result["status"] == "error"
    assert "set_state" in result["message"]


@pytest.mark.asyncio
async def test_set_state_turns_a_backend_exception_into_an_envelope(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = CFXBackend()

    def _boom(path: str) -> Any:
        raise RuntimeError("CCL path not found")

    monkeypatch.setattr(backend, "is_connected", lambda: True)
    monkeypatch.setattr(backend, "_resolve_live_path", _boom)

    result = await backend.set_state(path="nope", value=1)

    assert result["status"] == "error"
    assert result["path"] == "nope"
    assert "CCL path not found" in result["message"]


@pytest.mark.parametrize(
    ("method", "kwargs"),
    [
        ("save_case", {"path": "case.cfx"}),
        ("start_solve", {"def_file": "case.def"}),
        ("stop_solve", {}),
        ("get_results", {}),
    ],
)
@pytest.mark.asyncio
async def test_session_bound_helpers_degrade_without_a_session(
    method: str, kwargs: dict[str, Any]
) -> None:
    """Disconnected must be a typed envelope, never a traceback."""
    result = await getattr(CFXBackend(), method)(**kwargs)
    assert isinstance(result, dict)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_list_cfx_api_categories_groups_the_catalog() -> None:
    result = await CFXBackend().list_cfx_api_categories()

    assert result["status"] == "ok"
    categories = result["categories"]
    assert categories, "the 20-entry catalog must yield at least one category"
    stages = {c["stage"] if isinstance(c, dict) else c for c in categories}
    assert {"pre", "solver", "post"} & stages


@pytest.mark.asyncio
async def test_get_results_prefers_the_active_solver_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = CFXBackend()

    class _Solver:
        def get_results_file_name(self) -> str:
            return "/tmp/run_001.res"

    monkeypatch.setattr(backend, "is_connected", lambda: True)
    monkeypatch.setattr(
        backend, "_active_solver", lambda: _Solver(), raising=False
    )
    result = await backend.get_results()
    assert isinstance(result, dict)
    assert result["status"] in {"ok", "error"}
