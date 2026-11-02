# Develop a Nautilus controller from a GRAFCET specification

Use this procedure when a GRAFCET describes the required machine behavior
and the deliverable is a maintainable Nautilus controller. Treat the chart
as a behavioral specification: recover its intent, make the execution rules
explicit, and design an implementation that can be tested and maintained.

This procedure allows reorganizing the implementation while preserving the
required observable behavior. It does not promise a mechanically identical
GRAFCET execution engine. If exact GRAFCET execution semantics are a project
requirement, establish those semantics first and validate against the source
simulator or an independently reviewed execution model.

## 1. Establish the project inputs and limits

Collect the GRAFCET project, a readable chart view, the machine or simulator
scene, its I/O configuration, and any operating instructions. Record which
Nautilus checkout or release will run the controller.

Preserve the original files. Generate modified simulator scenes as separate
files. Keep device addresses and deployment settings separate from generated
logic so regeneration cannot overwrite a working connection.

Write down:

- What the machine does, what starts a cycle, and what completes it.
- Operator modes, commands, indications and reset requirements.
- What must stop immediately, what may finish its current cycle, and what
  requires a deliberate restart.
- Which measurements and counters must survive a mode change or restart.
- Whether ST alone is required or equivalent LD/FBD implementations are needed.
- Whether the target is a simulator or physical equipment. For physical
  equipment, identify the independently designed safety system; ordinary
  application logic and Modbus commands do not establish a safety function.

Deliverable: a short project brief with the source filenames, target,
required behavior, assumptions and unresolved questions.

## 2. Recover the complete chart structure

Inspect the actual file format before writing an extractor. A `.grafcet`
extension does not establish a universal schema. Read the encoding from the
actual bytes as well as the XML declaration; investigate discrepancies rather
than applying a fixed encoding replacement to every project.

For each chart, extract:

| Element | Information to preserve |
| --- | --- |
| Step | ID, number/name, initial or starting status, enclosing scope |
| Transition | ID, condition, predecessor steps, successor steps |
| Action | Owning step, qualifier/type, condition, expression, order if defined |
| Connection | Endpoints, direction, branches, joins, jumps and targets |
| Group/subchart | Parent activation, initialization, deactivation and completion |
| Symbol | Name, type, address, direction, units and comments |
| Runtime setting | Timing, scan behavior, system bits and initialization |

Retain the original expressions and source IDs in an inventory. Normalize
names for implementation only through an explicit alias table.

**Drawing order and item positions are not sufficient proof of connectivity.**
Use explicit links where available. Resolve connections stored as geometry
by reconstructing endpoints and checking the rendered chart. Flag ambiguous
crossings, joins and action ownership for review. Do not infer the sequence
from step numbers alone.

Deliverable: a chart inventory with a validated connection graph and a list
of unresolved structures. An inventory that omits connections is useful for
inspection but is not a complete executable model.

## 3. Describe the machine behavior in plain language

Read each chart as an operating procedure before choosing program structure.
For example:

> After the operator enables automatic mode and presses Start, warn for
> three seconds. Feed one item, detect its arrival, classify it, route it,
> confirm that it has cleared the station, then permit the next item.

Identify reusable machine responsibilities: conveyor control, a diverter,
a reject pusher, counters, operator commands and indication. Separate the
machine's required behavior from the particular arrangement of the drawing.

Prepare a behavior table:

| Situation/state | Entry action | Continuous behavior | Exit condition | Next behavior |
| --- | --- | --- | --- | --- |
| Waiting | Clear pending cycle | Motion disabled | Start and permissives | Warning |
| Warning | Reset warning elapsed time | Warning indication | Specified delay elapsed | Feed |
| Feed | Start one feed pulse | Convey item | Arrival edge | Classify |
| Classify | Capture required measurements | Apply classification speed | Valid routing decision | Route |
| Route | Register the routing operation | Drive selected mechanism | Completion feedback | Settle |
| Settle | Reset settling elapsed time | Defined resting outputs | Specified delay elapsed | Feed |

The rows above are an example, not default requirements for every machine.
Replace them with behavior supported by the project's source.

## 4. Resolve execution semantics and design choices

For every source construct, define how it behaves in the target controller:

| Concern | Questions to resolve |
| --- | --- |
| Initial state | Which steps initialize at startup or when a parent activates? |
| Entry action | Does it run once on activation, including reactivation? |
| Continuous action | Is it recomputed each scan? What clears it? |
| Stored action | What explicitly clears the stored value? |
| Conditional/event action | Is it level-triggered, edge-triggered or entry-triggered? |
| Transition | Can several fire together? Is priority specified? |
| Scan evolution | One transition per scan, or repeated evolution until stable? |
| Parallel branches | Which states coexist and how is synchronization joined? |
| Enclosing chart | What resets, freezes or terminates when the parent leaves? |
| Edge history | What happens when an input is held during activation? |
| Timer | When does timing start, pause, reset or expire? |
| Counter | What physical or logical event is counted? |
| Stop/restart | Which state and commands remain after stop, reset or reconnect? |

Do not flatten parallel branches into a single state variable unless you
can demonstrate equivalent behavior. Use separate concurrent state machines
or an active-step set when the source requires simultaneous activity.

Keep a decision log:

| ID | Topic | Source evidence | Classification | Target behavior | Validation |
| --- | --- | --- | --- | --- | --- |
| D01 | Stop polarity | Symbol/configuration and observed contact | Source requirement | Define TRUE/healthy meaning | Contact test |
| D02 | Conflicting commands | No priority specified | Design choice | Document selected priority | Simultaneous-command test |
| D03 | Missing calculation | Symbol exists; no action defines it | Unresolved requirement | Obtain definition or label a temporary behavior | Review |

Classify each decision as a **source requirement**, **implementation design
choice**, **assumption needing confirmation**, or **intentional deviation**.
When requirements are missing, make the incomplete behavior visible. Do not
silently invent production calculations, actuator commands or restart rules.

## 5. Build an I/O contract independently of the sequence

Create an I/O crosswalk using the actual target scene or device:

| Symbol | Meaning | Direction | Type | Units/polarity | Target tag/key | Protocol address | Scaling |
| --- | --- | --- | --- | --- | --- | --- | --- |
| StopHealthy | Stop contact healthy | Input | BOOL | TRUE = healthy | Verified contact | Verified address | None |
| ConveyorCmd | Conveyor speed | Output | REAL | V, 0–10 | Verified actuator | Verified address | Defined below |

Verify physical/tag identity rather than relying on matching names or
similar positions. Resolve spare bits, packed outputs, aliases, duplicate
keys and different address conventions explicitly.

For Modbus, record the device's role, host, port, unit ID, table, zero-based
PDU address, width, signedness, byte/word order, scale and write policy.
For the common arrangement where Nautilus is the client and the simulator
is the server, sensors may be discrete inputs/input registers and actuators
coils/holding registers. Verify the actual configured tables.

Define scaling algebraically, with worked endpoints. For example, **only if
the actuator specification defines this relationship**:

```text
Engineering command: 0–300 cm/s
Actuator command:    0–10 V
V = speed_cm_s × 10.0 / 300.0
If the server's floating-value scale is 100:
raw_register = V × 100
At 60 cm/s: V = 2.0; raw_register = 200
```

Specify clamping, rounding and out-of-range behavior. Check integer-division
rules, register limits and whether scaling applies to floats, integers or
both in the target driver.

Deliverables: typed tags, I/O crosswalk and protocol bindings. Keep these
reviewable without reading the sequence implementation.

## 6. Design the controller around responsibilities

A useful structure is:

1. Acquire and normalize inputs, including contact polarity.
2. Update edge detectors once per scan.
3. Apply stop/reset and mode management.
4. Evaluate sequence transitions using a documented input/state snapshot.
5. Apply entry actions once for states entered in this scan.
6. Compute continuous commands and timers.
7. Apply interlocks, arbitration and output limits.
8. Publish outputs and diagnostic state.

Adjust the order to the established semantics and document any differences.
Give each actuator one final output assignment point or one explicit owner.
Keep status lamps separate from motion permissives: a flashing lamp must
not become a periodic enable signal.

Choose names that describe machine behavior, such as `WaitingForPart` and
`RejectExtending`. Preserve original step numbers in comments or a mapping
when that helps review; the implementation need not mimic every drawing
node or temporary graphical step.

Separate state by lifetime: scan-local calculations, sequence state,
operator setpoints, accumulated totals and retained restart state. Initialize
every externally bound value that may be read before its first assignment.

A documented single-transition-per-scan pattern might look like this:

```iecst
(* Illustrative pattern; declarations, entry actions and output logic omitted. *)
NextState := State;
CASE State OF
    10: (* Wait *)
        IF StartEdge AND Permissive THEN NextState := 20; END_IF;
    20: (* Warn *)
        IF WarningElapsed >= WarningDelay THEN NextState := 30; END_IF;
END_CASE;
StateChanged := NextState <> State;
State := NextState;
```

This pattern is a design option, not a general replacement for all GRAFCET
semantics. Resolve immediate transitions and parallel evolution explicitly.

## 7. Implement against the installed Nautilus version

Inspect the local examples, compiler and manifest schema before selecting
syntax or library functions. Verify task timing, tag roles, timer behavior,
function-block interfaces and runtime initialization in that version.

Use `nautilus.yaml` to schedule the controller and declare deployment
configuration. Keep the sequence, transport configuration and any simulator
support logic in clearly identified files.

If ST, LD and FBD variants are required, choose between hand-maintained
implementations or a carefully scoped generator. State which representation
is authoritative, preserve scan ordering, and execute the same behavioral
tests against each variant. A native LD/FBD solution should implement its
logic in rungs/blocks rather than merely call the complete ST controller.

A language selector should invoke exactly one normal implementation per
scan. Define what happens to motion, timers, edge history and counters on
selection changes and invalid values; do not resume dormant state by accident.

## 8. Validate against independently described behavior

Write scenarios from the behavior table and decision log, ideally before
implementation. Do not define success solely as reproducing the code's own
branches. Where possible, compare observable traces against the source
GRAFCET simulator or have another reviewer derive expected outcomes from
the source chart.

Cover:

- Startup, reset permissives and each normal operating path.
- Every classification/routing result and invalid measurements.
- Entry actions firing exactly once and held commands not repeating edges.
- Timer behavior just before, at and after the required delay.
- Repeated cycles, shared sensors and parallel-branch synchronization.
- Conflicting commands, mode changes and held inputs across activation.
- Stop conditions, emergency-stop inputs and restart policy.
- Actuator interlocks, missing feedback and any specified timeouts.
- Counter events, retention, reset hold and overflow limits.
- Communication interruption/recovery and last-command behavior.
- Scaling endpoints and intermediate values, including raw register values.
- Language equivalence and switching behavior when multiple variants exist.

Use three distinct validation levels:

| Level | Establishes | Does not establish |
| --- | --- | --- |
| Compile and virtual-time tests | Syntax and tested logical behavior | Actual I/O mapping or source equivalence |
| Protocol integration with a test peer | Real reads/writes, addressing and encoding | Simulator mechanics or physical timing |
| Target commissioning | Actual mappings, mechanics and observed operation | Exhaustive correctness or safety certification |

For a Nautilus project, start with:

```sh
naut check .
naut test .
```

Add project-specific protocol tests and commissioning checks. Do not report
simulated tests as a live-machine test or claim formal equivalence from
passing tests derived from the implementation itself.

## 9. Commission and document the result

Verify connectivity before diagnosing sequence logic: confirm the server is
listening on the reachable network adapter, the address/port are correct,
and a TCP connection can be made. Then verify the protocol table and tag map.

Check inputs and outputs individually, confirm polarity and scaling, run
manual functions, and then exercise the automatic paths. Record the actual
stop, disconnect and restart behavior. A server can retain its last output
values after network loss; design and verify the required watchdog/recovery
behavior rather than assuming a stopped client clears remote outputs.

Deliver a startup guide, state/transition description, I/O map, decision log,
validation results and outstanding limitations. Record what was observed on
the target separately from what was only simulated.

## Suggested project artifacts

```text
sources/                    Original GRAFCET and scene/device exports
requirements.md             Machine behavior, semantics and decision log
chart_inventory.json        Extracted source records and validated links
io_map.csv                  Symbol-to-target protocol contract
control.st                  Reviewed reference implementation
main.st                     Optional dispatcher / final arbitration
lib/                        Optional reusable blocks and LD/FBD variants
nautilus.yaml               Task and runtime configuration
tags/                       Typed tags and initial values
modbus_manifest.yaml        Protocol bindings, if using Modbus
*_test.yaml                 Behavioral scenarios
tools/                      Scoped extraction/generation/integration tools
README.md                   Deployment, operation and commissioning
```

Use this layout as a starting point, not a naming requirement.

## Reusable request for a future project

Copy the following into a new project and supply its filenames and target:

> Develop a Nautilus controller using `<GRAFCET file>` as the behavioral
> specification and `<scene/device configuration>` as the I/O target.
> Implement the machine's intent in maintainable control logic; reorganize
> the drawing into suitable state machines and reusable blocks where the
> required behavior is preserved.
>
> First inspect the source format, recover chart connectivity and action
> ownership, and describe the machine behavior. Resolve parallel branches,
> action qualifiers, timing, initialization and scan evolution explicitly.
> Separate source requirements, design choices, assumptions and deviations.
> Flag missing or ambiguous requirements instead of silently inventing them.
>
> Build an independent I/O crosswalk with polarity, units, addresses and
> scaling. Inspect the installed Nautilus APIs and syntax. Implement explicit
> startup, stop/reset, mode, edge, timer and output-ownership behavior. Keep
> deployment settings separate from generated artifacts and preserve source
> files and working endpoint settings.
>
> Derive tests from the source behavior and decision log, validate protocol
> encoding separately, and provide a target commissioning procedure. Report
> the evidence and limitations without claiming unverified source equivalence.
> If LD/FBD are requested, supply complete implementations and run the same
> scenarios against each, including safe language-selection behavior.
>
> Follow `GRAFCET_PROJECT_WORKFLOW.md`. Deliver the implementation, source
> traceability, I/O map, decision log, tests and operating instructions.

## What can be reused from the Final Practicum project

The reusable part is the workflow and its separation of source intent,
execution semantics, implementation, mapping and validation.

The existing scripts have narrower scopes:

- `tools/convert.py` extracts selected XML records and builds this scene's
  mapping. It hardcodes filenames, symbol exceptions, address conventions
  and the output crosswalk. It does not recover a complete connection graph
  or generate `control.st`. Adapt and validate it before using another source.
  Running it here also restores default endpoint settings.
- `tools/build_languages.py` generates this project's ST/LD/FBD blocks from
  an already reviewed `control.st`. It supports a restricted expression and
  statement subset and project-specific declarations/reset handling. It is
  not a general ST compiler or GRAFCET converter.
- `tools/make_tests.py` encodes this machine's expected scenarios. Reuse the
  test structure, but derive new expectations from the new machine's source.
- `tools/modbus_smoke.py` exercises this project's map against a test peer.
  A new project needs its own tag set, value encoding and acceptance checks.

For this project's historical translation choices and operating behavior,
see [README.md](README.md). Neither these scripts nor this guide replace
review of a new project's chart semantics and machine requirements.
