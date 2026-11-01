# Final Practicum — Nautilus / Factory I/O over Modbus TCP

This project translates `Spring2026_Final_Practicum_V21.grafcet` into a
Nautilus Structured Text controller for the supplied V20 Factory I/O scene.
The original input files are preserved. Use the generated
`Spring2026_Final_Practicum_Modbus.factoryio` scene for the complete I/O map.

Architecture: Nautilus (Modbus TCP client) → Factory I/O (Modbus TCP server).
The controller runs every 20 ms. The driver polls every 20 ms and reasserts
outputs every 100 ms. This project was checked with Nautilus 0.19.0 and the
local joyautomation/nautilus checkout.

## Choose ST, LD, or FBD

`main.st` is the only scheduled program. It dispatches to one native
implementation per scan using the writable `LanguageSelect` setpoint:

| LanguageSelect | Implementation | Source |
| ---: | --- | --- |
| 1 | Structured Text (default) | `lib/practicum_st.st` |
| 2 | Ladder Diagram | `lib/practicum_ld.ld` |
| 3 | Function Block Diagram | `lib/practicum_fbd.fbd` |

Start with `naut run .`, then edit `LanguageSelect` on the dashboard at
<http://127.0.0.1:8080>. `ActiveLanguage` reports the selected implementation;
`LanguageValid` reports whether the selection is 1–3. To select LD using
the tag API:

```sh
curl -X POST http://127.0.0.1:8080/api/tags \
  -H 'Content-Type: application/json' \
  -d '{"name":"LanguageSelect","value":2}'
```

Use value `3` for FBD or `1` for ST. To change the startup default, edit
`LanguageSelect`'s `init` in `nautilus.yaml` and restart the controller.
The selector is a Nautilus setpoint; it does not consume a Factory I/O coil
or register and requires no changes to the working scene or Modbus map.

Changing languages clears motion commands, timers, button history and manual
latches. It returns `MainStep` to 1 and requires the normal reset sequence
before running again; the three production counters are preserved. An
invalid selection disables all three implementations. Stop the scene before
restarting Nautilus to load this update.

The LD implementation contains native rungs, Boolean contacts/coils, SEL
blocks and enabled assignment boxes. The FBD implementation contains native
SEL, comparison, Boolean and arithmetic blocks. Both implement the complete
sequence directly. Each has independent private state; no ST controller is
called from LD or FBD. Use the Nautilus VS Code extension's **Open With →
Ladder Diagram / Function Block Diagram** editors to view these library files.

`control.st` remains the readable reference implementation. The scoped
`tools/build_languages.py` translator generates all three function blocks
from its assignments, IF branches and CASE branches. It captures branch
conditions before writes so the diagrams preserve ST scan ordering; it
rejects unsupported statements. Generated `BranchNNN` coils and `CaseValueNNN`
variables hold those decisions. Edit the reference and regenerate rather
than modifying generated library files.

## Run

1. Open `Spring2026_Final_Practicum_Modbus.factoryio` in Factory I/O.
2. Under **File → Drivers**, explicitly select **Modbus TCP/IP Server**.
   The scene retains the original selected-driver ID, whose enum is not
   documented; selecting the server in the UI is required on first use.
3. Configure the server as follows, and verify the generated assignments in
   its I/O mapping view:

   | Setting | Value |
   | --- | --- |
   | Port | 502 |
   | Slave ID | 1 |
   | Write Digital (sensors) | Inputs / discrete inputs |
   | Read Digital (actuators) | Coils |
   | Write Register (sensors) | Input Registers |
   | Read Register (actuators) | Holding Registers |
   | Scale | 100 |
   | Digital inputs | offset 0, count 35 |
   | Digital outputs | offset 0, count 47 |
   | Register inputs | offset 0, count 1 |
   | Register outputs | offset 0, count 7 |

4. In `modbus_manifest.yaml`, set `host` to the Factory I/O PC's IP address.
   `127.0.0.1` works only when both programs run on the same computer. Match
   the port and unit ID to Factory I/O, and allow inbound TCP on that port
   on the Factory I/O PC. Connect the driver and put the scene in Run mode.
5. From this directory:

   ```sh
   naut check .
   naut test .
   naut run .
   ```

   The dashboard and tag API are at <http://127.0.0.1:8080>. Driver status is
   available at `/api/drivers`. With the repository's Go toolchain, the
   equivalent command is `go run ../../cmd/naut run .`.

6. Release both emergency stops and the Stop button. The contacts must read
   TRUE when healthy. Clear the classification and reject sensors; AtExit
   must be TRUE (clear). Press either Reset button to enable control.
7. Select **Auto** with Manual deselected. Use the +10 / +100 speed buttons
   to set a nonzero reference, then press Start. After the three second
   warning, the emitter produces a 500 ms pulse. At classification the belt
   slows to 60 cm/s; press Send Sort for values 1–6 or Send Reject to reject.
   Vision values 7–9 automatically select rejection. Speed restores after
   sorting/rejection and the next part is emitted.
8. In **Manual**, the conveyor button toggles between zero and 60 cm/s;
   speed buttons adjust the reference. Sorter and reject buttons toggle
   their actuators. CW and CCW exclude each other. Hold local Reset for five
   continuous seconds to clear the three part counters.

Stop or either emergency stop removes the controller's motion commands and
requires reset before restart. Selectors both on or both off disable motion.
Switching modes clears manual latches and restarts the automatic sequence.

## Files and mapping

| File | Purpose |
| --- | --- |
| `control.st` | Reference translation of all 11 charts |
| `main.st` | Language selector, switching reset and output arbitration |
| `lib/practicum_st.st` | ST controller function block |
| `lib/practicum_ld.ld` | Complete native LD controller function block |
| `lib/practicum_fbd.fbd` | Complete native FBD controller function block |
| `nautilus.yaml` | Main scan task, selector, tag files, driver and dashboard |
| `modbus_manifest.yaml` | TCP endpoint and 89 field bindings |
| `tags/io.yaml` | Symbols, types, initial values and roles |
| `io_map.csv` | Full symbol → scene tag → PDU address crosswalk |
| `chart_inventory.json` | Original steps, transitions and actions by chart |
| `practicum_test.yaml` | 61 virtual-time acceptance scenarios |
| `tools/convert.py` | Rebuild mapping, scene copy and chart inventory |
| `tools/build_languages.py` | Generate ST/LD/FBD implementations from the reference ST |
| `tools/modbus_smoke.py` | Real TCP integration test with a simulated peer |

All Modbus addresses in the manifest and CSV are **zero-based PDU addresses**.
The digital outputs keep the V21 spare Q0.7, so addresses after it differ
from the original scene's packed Modbus client map. The generated server
scene fixes that mismatch. The original MHJ mapping also duplicates the
StopPL key at the StopBlade position; the generated map uses the actual
StopBlade scene key. `IncSpdX1Light` is the V21 spelling of the +100 lamp.

The numeric map is:

| Table | Address | Tag | Raw representation |
| --- | ---: | --- | --- |
| Input | 0 | VisionSensor1 | signed 16-bit integer |
| Holding | 0 | BaseCounter | signed 16-bit integer |
| Holding | 1 | BeltConveyor4mSpeed | voltage × 100 |
| Holding | 2 | BeltSpeedRef | cm/s integer |
| Holding | 3 | LidCounter | signed 16-bit integer |
| Holding | 4 | ProductionRate | zero, no chart formula supplied |
| Holding | 5 | RawCounter | signed 16-bit integer |
| Holding | 6 | BeltConveyor4mSpeed2 | voltage × 100 |

Both conveyor outputs use `V = cm/s × 10.0 / 300.0`, clamped to 0–10 V.
The manifest's 0.01 engineering scale converts volts to raw hundredths;
Factory I/O's scale 100 divides those raw values back into volts. Integer
counters and displays are not multiplied by 100.

## Chart translation decisions

This is a scene-specific implementation, not a general-purpose GRAFCET XML
compiler. `chart_inventory.json` preserves the source conditions for review.

- **Main**: `MainStep` 1 = emergency/off, 2 = waiting for reset, 3 = control
  enabled. `Mode` 4/5 activates the manual/automatic child charts. The
  blinking control lamps are indication only; actual state enables motion.
- **Automatic / Automatic-Resets**: `AutoStep` retains the main source step
  numbers. Step 19 emits once per entry. Steps 24/27/28 call raw/base/lid
  sorting, and 25/85/86 run rejection and wait for the pusher back limit.
- **Sort Raw / Base / Lid**: actuators run in the first sort step; AtExit
  must go FALSE then TRUE, followed by a 500 ms settling interval. The
  diagnostic steps 124/127/128 and 224/227/228 represent those two waits.
  Counters increment once when the sort chart starts, as in the source.
- **Manual-Speeds / Manual-PushPullls / Manual-Counters**: explicit latches,
  global button edge history, reverse exclusion and five second reset hold.
- **Continuous**: one consistent Modbus scale replaces the source's three
  competing platform examples (1000/300, 27648/300 and 10/300). Real division
  avoids integer truncation. +/− commands operate once per rising edge.

Deterministic resolutions: Reject takes priority over Sort when both are
requested; unknown vision codes wait for an operator command. Mode changes
clear speed and pending actuator commands. FIOReset returns to the main
reset sequence without clearing production counters. Button edges held
across a mode change must be released and pressed again for manual toggles.

The source defines no ProductionRate calculation, StopBlade action, or
panel-selection arbitration. ProductionRate is zero and StopBlade is FALSE;
panel-active lamps mirror their selector inputs. Removers are enabled and
PLC-running lamps blink as scene support outputs. These support choices
are explicit in `control.st` and should be checked during commissioning.
Local/remote selection does not filter commands because no such filtering
is specified by the supplied charts. Counter registers are signed 16-bit;
reset totals before exceeding 32767.

## Verification and regeneration

```sh
naut check .
naut test .
python3 tools/modbus_smoke.py --language 1
python3 tools/modbus_smoke.py --language 2
python3 tools/modbus_smoke.py --language 3
```

The same 19 scenarios run through Main for each of ST, LD and FBD. Four
additional scenarios verify switching, preserved totals, reset and invalid
selection handling. They cover all nine vision classes, operator rejection,
warning and emitter timing, sort completion, pusher limits, manual reverse
interlocks, reset hold timing, speed clamping/scaling, selector conflict,
and both emergency stops plus Stop. The TCP test launches an isolated
`naut run` against an ephemeral local Modbus peer and verifies FC02/04
reads, output writes, raw speed registers and emergency-stop output clearing.
It requires permission to bind localhost; it does not connect to Factory I/O.

To rebuild artifacts after editing the source files:

```sh
python3 tools/convert.py
python3 tools/build_languages.py
python3 tools/make_tests.py
naut check .
naut test .
```

The converter rewrites the endpoint to its localhost defaults; reapply your
PC address afterward. It does not regenerate `control.st`: sequence changes
require reviewing the ST translation and updating the behavioral tests.

The existing ST setup has been reported working in Factory I/O. The new
LD/FBD implementations passed offline and simulated TCP tests; confirm their
behavior in the live scene. Confirm the selected driver,
serialized mapping settings, NC contact behavior, voltage scaling, diverter
routing and item travel timing in the application. Network loss can leave
the server's last actuator values latched; this controller has no independent
communication watchdog. Stop/reset the scene after a disconnect before
reconnecting. Pause/run status is mapped for inspection but does not gate
the sequence, matching the supplied chart's lack of such conditions.

References: [Nautilus](https://github.com/joyautomation/nautilus),
[Factory I/O Modbus TCP server configuration](https://docs.factoryio.com/manual/drivers/modbus-server/).
