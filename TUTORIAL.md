# Ansys CFX Connection Setup Guide

## 1. Prerequisites

- **Ansys CFX** installed on Windows, including CFX-Pre, the CFX Solver and CFD-Post.
  A full Ansys installation covering the CFX components is required for live sessions.
- **Python 3.10 or later** (the connector declares `Python >= 3.10`).
- **AiConnect Desktop** running.

> Linux note: the bundled PyCFX backend covers non-GUI operations, but Linux is not a published
> target for this connector yet. Use Windows for the full CFX-Pre / Solver / CFD-Post workflow.

## 2. Install the Connector

1. Open **AiConnect Desktop** and go to the **Marketplace**.
2. Find **Ansys CFX Computational Fluid Dynamics** and click **Install**.
3. Wait for the download to complete and the connector card to appear in **My Connectors**.

## 3. Point the Connector at Your Ansys Bridge

The connector talks to Ansys over a local TCP bridge. Both settings are optional and only need
changing if you have moved the bridge off its defaults.

| Setting | Default | What it is |
|---|---|---|
| `ANSYS_MCP_HOST` | `127.0.0.1` | Host running the Ansys bridge |
| `ANSYS_MCP_PORT` | `48152` | TCP port the Ansys bridge listens on |

1. Open the connector's **Settings** in AiConnect Desktop.
2. Leave both fields empty to use the defaults above, or enter your own values.
3. Click **Save**.

## 4. Start Ansys CFX

1. Launch **Ansys CFX** and open (or create) the case you want to work on.
2. Keep the application open — the connector drives your live session; it does not launch one
   for you.

## 5. Verify the Connection

1. Return to **AiConnect Desktop**.
2. Enable the **Ansys CFX** connector.
3. The connector card switches to `● Connected`.
4. Ask your AI assistant something read-only to confirm the link, for example:
   *"What is the current CFX model context?"*

## 6. What You Can Do

- Author and modify CFX-Pre simulation cases
- Launch, monitor and stop CFX solver runs
- Extract quantitative results through CFD-Post
- Inspect model context and mesh state
- Drive multi-step CFD workflows end to end

## Troubleshooting

**The card never reaches `● Connected`.**
Confirm Ansys CFX is actually running, and that nothing else is bound to port `48152`. On Windows:
`netstat -ano | findstr 48152`.

**Tools return errors mentioning a missing session.**
The connector needs an open CFX case. Open one in CFX-Pre and try again.

**Results tools return nothing.**
CFD-Post reads solver output — make sure the run has produced results before querying them.
