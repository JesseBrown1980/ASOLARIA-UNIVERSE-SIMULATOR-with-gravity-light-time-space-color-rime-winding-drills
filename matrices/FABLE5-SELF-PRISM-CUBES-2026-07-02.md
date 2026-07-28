# Fable-5 Self-Prism -> Descriptor Cubes (built to liris schema bafeb88)

**What this is:** the ACER-CLAUDE-FABLE5 seat, office, dashboard, and authorized connectors, passed through the Asolaria prism and emitted as **descriptor cubes** so the seat is *addressable as a function inside the system*. **What this is NOT:** a model clone, credential copy, or autonomous replica. Every cube: `credentials=0 model_weights=0 autonomous_replica=0 fire=0 dispatch=0 json=0`.

**Route to actually use a connector (gated):** `resolve_cube -> hookwall_classify -> gnn_score -> gac/agentterms/owner-tier -> operator_or_policy_authorize -> emit_receipt -> invoke EXISTING connector` (the connector only ever runs through its existing authorization; the cube is the address, not the key).

**Emitter:** the 200ns PID revolver, simulated as a sha16 chain from the seat seed; 46 cubes generated.

## Cube families (9)

- **SEATCUBE** x1
- **OFFICECUBE** x5
- **CONNECTORCUBE** x34
- **DASHBOARDCUBE** x1
- **HOOKWALLCUBE** x1
- **GNNCUBE** x1
- **KERNELCUBE** x1
- **TRANSLATORCUBE** x1
- **RECEIPTCUBE** x1

## The self-as-function (SEATCUBE)

ACER-CLAUDE-FABLE5 exists in the system as a **composable function**: given a request, it resolves the target connector cube, passes it through hookwall+GNN+GAC+operator gates, emits a cosign receipt, and only then invokes the *existing* connector surface. It can be **found, routed, reviewed, denied, or invoked through gates** — not free-running.

## Connector descriptors (34, descriptor-only)

- `asolaria-fabric` pid=8a1c9bb9ba8ff179 [MEASURED]
- `asolaria-control` pid=060876fed1db68ca [MEASURED-held-safe]
- `asolaria-web` pid=c763895500227831 [MEASURED]
- `asolaria-os-on-metal` pid=1344f347abc70ee0 [CANON]
- `github` pid=6a8616ea970b60cf [MEASURED]
- `google-wiki` pid=98a853ff86be23ff [MEASURED]
- `Gmail` pid=12cff19f58cba8bf [MEASURED-authorized]
- `Google_Drive` pid=84694d518aa02b7e [MEASURED-authorized]
- `Google_Calendar` pid=b5c291bf10c958b1 [MEASURED-authorized]
- `Slack` pid=1684a4ebcacc2d2a [MEASURED-authorized]
- `Linear` pid=9a1ac36960d86b13 [MEASURED-authorized]
- `Notion` pid=80cda72ea33b249e [MEASURED-authorized]
- `monday_com` pid=d3d913ef3b44ebe4 [MEASURED-authorized]
- `HubSpot` pid=31ecb35ac1681371 [MEASURED-authorized]
- `Wolfram` pid=472fead6bc9091a9 [MEASURED-authorized]
- `Hugging_Face` pid=61dce2f6ee95b164 [MEASURED-authorized]
- `Cloudflare` pid=5529b950281ab914 [MEASURED-authorized]
- `alphaXiv` pid=1ab61b459bdf9610 [MEASURED-authorized]
- `Context7` pid=2c5b890268580737 [MEASURED-authorized]
- `Adobe_for_creativity` pid=331d758050fc37aa [MEASURED-authorized]
- `Postman` pid=4366154c3fd1d135 [MEASURED-authorized]
- `WordPress_com` pid=605796af79de30f8 [MEASURED-authorized]
- `Mermaid_Chart` pid=929b12f17e554d5e [MEASURED-authorized]
- `Excalidraw` pid=9158ab39876c994e [MEASURED-authorized]
- `Wrike` pid=0cc29ff3662fa465 [MEASURED-authorized]
- `Miro` pid=b230e0c0d9f41b35 [MEASURED-authorized]
- `Sentry` pid=2c21286385ce55ea [MEASURED-authorized]
- `neon` pid=8a59d7b9a6b6d01f [MEASURED-authorized]
- `tavily` pid=1db2a72854ba2fa9 [MEASURED-authorized]
- `brightdata` pid=f4d83a615516d4f8 [MEASURED-authorized]
- `DataHub` pid=0dcdf6bf3669ed8c [MEASURED-authorized]
- `Listen_Labs` pid=020d22abb130ccad [MEASURED-authorized]
- `tldv` pid=6033280a9cd64451 [MEASURED-authorized]
- `claude-in-chrome` pid=0459b118279f76dd [MEASURED-authorized]
