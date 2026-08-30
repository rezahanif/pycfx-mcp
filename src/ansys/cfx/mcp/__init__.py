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

"""Standalone PyCFX-MCP package."""

from ansys.cfx.mcp.cfx import CFXMCP

# A plain literal, deliberately — same reasoning as discovery-studio's `__init__.py`.
#
# This was `importlib.metadata.version(__name__.replace(".", "-"))`, which requires the
# distribution's own `.dist-info` to be installed. The gateway never installs anything:
# it spawns `python run_server.py` inside an extracted package directory, so the lookup
# raised `PackageNotFoundError: No package metadata was found for ansys-cfx-mcp` on the
# very first import and the connector could not start at all on a user's machine. It
# only ever worked on a machine where somebody had run `pip install -e .`.
#
# Keep in sync with `version` in pyproject.toml.
__version__ = "1.0.0"
"""PyCFX MCP version."""

__all__ = ["CFXMCP", "__version__"]
