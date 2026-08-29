# Typeractive Corne

Two physical units (Typeractive Corne, nice!nano v2 halves). All three
firmware builds below run on the same halves — pick one and flash it.

| Build | Topology | Notes |
| --- | --- | --- |
| `prospector/` | Dongle = central, both halves = peripherals | Needs the Prospector dongle. Keyboard dead without it. |
| `standalone/` | Left = central, right = peripheral | Works on its own, no dongle. |
| `scanner/` | Left = central, right = peripheral + passive Prospector | Keyboard independent; Prospector just displays status. |

Firmware: **ZMK**. CI builds each under its own job.
