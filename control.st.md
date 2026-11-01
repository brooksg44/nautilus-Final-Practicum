# control.st — logic as Mermaid

`control.st` is the reference translation of the GRAFCET charts (see
`Spring2026_Final_Practicum_V21.grafcet.md`). It is not scheduled directly:
`main.st` runs every 20 ms and dispatches to `lib/practicum_{st,ld,fbd}`,
which `tools/build_languages.py` generates from this file. The diagrams below
describe the logic all three share.

The chart's steps are held in three integers rather than step flags:
`MainStep` (X1/X2/X3, init 1), `Mode` (0 = none, 4 = Manual, 5 = Auto) and
`AutoStep` (the Automatic chart's step number, init 16).

## 1. One scan, in order

```mermaid
flowchart TD
  A["Blink clock<br/>ClockS += ScanDtS, wraps at 1 s<br/>Blink = first half second"] --> B
  B["Main sequence<br/>update MainStep, then ControlOnPL / StopPL / EStoppedPL"] --> C
  C["Mode select<br/>Mode = 4 Manual, 5 Auto, else 0<br/>(only while MainStep = 3)"] --> D
  D{"Mode changed<br/>since last scan?"} -->|yes| E["Reset children<br/>BeltSpeedRef, LastBeltRefSpeed := 0<br/>AutoStep := 16, timers := 0<br/>RunningPL := FALSE, manual latches := FALSE"]
  D -->|no| F
  E --> F["Clear per-scan outputs<br/>Emitter, WarningLight1, sorter belts,<br/>RejectPusher, lights, Raw/Base/Lid/RejectFlag"]
  F --> G{"MainStep = 3?"}
  G -->|yes| H["Continuous: speed buttons<br/>±10 / ±100 on rising edges<br/>clamp 0..300, remember in LastBeltRefSpeed"]
  G -->|no| I
  H --> I{"Mode"}
  I -->|5| J["Automatic sequence<br/>(section 4)"]
  I -->|4| K["Manual toggles and counter reset<br/>(section 5)"]
  I -->|0| L
  J --> L
  K --> L["Output arbitration<br/>(section 6)"]
  L --> M["Store Prev* values<br/>for next scan's edge detection"]
```

## 2. Main sequence (`MainStep`)

`Stop`, `EmergencyStop` and `EmergencyStop2` are normally closed: TRUE means healthy.
The rules are checked in this priority order every scan.

```mermaid
stateDiagram-v2
  direction LR
  state "1 · EmergencyStop<br/>StopPL on, EStoppedPL blinks" as X1
  state "2 · ControlOff<br/>StopPL on, ControlOnPL blinks" as X2
  state "3 · ControlOn<br/>ControlOnPL steady, StopPL off" as X3
  [*] --> X1
  X1 --> X2 : Stop
  X2 --> X3 : (Reset or Reset2PB) and not ClassifyDefuseSensor and not RejectDiffuseSensor and AtExit
  X3 --> X2 : not Stop
  X2 --> X1 : not EmergencyStop or not EmergencyStop2 or FIOReset
  X3 --> X1 : not EmergencyStop or not EmergencyStop2 or FIOReset
```

## 3. Mode select (`Mode`)

```mermaid
flowchart LR
  S{"MainStep = 3?"} -->|no| M0["Mode 0<br/>belt forced to 0, RunningPL off"]
  S -->|yes| Q{"selector switches"}
  Q -->|"ManualSS and not AutoSS"| M4["Mode 4 · Manual<br/>ManualPL"]
  Q -->|"AutoSS and not ManualSS"| M5["Mode 5 · Auto<br/>AutoPL, StartPL"]
  Q -->|"both or neither"| M0
```

Any change of `Mode` restarts the child sequences (section 1, “Reset children”);
the production counters are kept.

## 4. Automatic sequence (`AutoStep`, Mode 5 only)

The sorting steps are split into three phases by adding 100: 24 → 124 → 224
for Raw, and likewise 27/127/227 for Base and 28/128/228 for Lid.

```mermaid
stateDiagram-v2
  state "16 · start" as A16
  state "21 · wait for Start" as A21
  state "20 · warning<br/>WarningLight1 blinks" as A20
  state "19 · emit / run<br/>Emitter pulses 0.5 s" as A19
  state "22 · classify<br/>belt slowed to 60" as A22
  state "Raw (24 → 124 → 224)<br/>RawSorterBelt CW + Turn, RawLightInd" as RAW
  state "Base (27 → 127 → 227)<br/>BaseSorterBelt CW + Turn, BaseLightInd" as BASE
  state "Lid (28 → 128 → 228)<br/>LidSorterBelt CW + Turn, LidLightInd" as LID
  state "25 · reject: wait for part" as A25
  state "85 · push<br/>RejectPusher, belt stopped" as A85
  state "86 · retract" as A86

  [*] --> A16
  A16 --> A21 : next scan
  A21 --> A20 : Start
  A20 --> A19 : 3 s elapsed, restore belt speed, RunningPL on
  A19 --> A22 : rising ClassifyDefuseSensor
  A22 --> A25 : SendRejectPB or VisionSensor1 in 7..9 (priority)
  A22 --> RAW : SendSortPB and VisionSensor1 = 1 or 4, RawCounter +1
  A22 --> BASE : SendSortPB and VisionSensor1 = 3 or 6, BaseCounter +1
  A22 --> LID : SendSortPB and VisionSensor1 = 2 or 5, LidCounter +1
  A25 --> A85 : RejectDiffuseSensor, belt to 0
  A85 --> A86 : RejPushFrontLimit
  A86 --> A19 : RejPushBackLimit, restore belt speed
  RAW --> A19 : sorted, restore belt speed
  BASE --> A19 : sorted, restore belt speed
  LID --> A19 : sorted, restore belt speed
```

Each sorting branch steps through the same three phases:

```mermaid
stateDiagram-v2
  direction LR
  state "24 / 27 / 28<br/>sorter belt running" as P0
  state "124 / 127 / 128<br/>part has left AtExit" as P1
  state "224 / 227 / 228<br/>settle timer" as P2
  P0 --> P1 : not AtExit
  P1 --> P2 : AtExit, timer := 0
  P2 --> [*] : 0.5 s elapsed, back to 19
```

## 5. Manual (Mode 4 only)

Every manual push button is a rising-edge toggle. Each sorter's CW and CCW
latches lock each other out. The pattern below is the Raw sorter; Base and Lid
are identical, and `RejectPusherManPB` / `BeltConveyor4mManPB` are plain toggles
(the belt toggles between speed 60 and 0).

```mermaid
stateDiagram-v2
  direction LR
  state "Off" as OFF
  state "CW<br/>RawSorterBeltCW" as CW
  state "CCW<br/>RawSorterBeltCCW" as CCW
  [*] --> OFF
  OFF --> CW : ↑ RawSorterBeltCWManPB
  CW --> OFF : ↑ RawSorterBeltCWManPB
  OFF --> CCW : ↑ RawSorterBeltCCWManPB
  CCW --> OFF : ↑ RawSorterBeltCCWManPB
  note right of CW : the opposite button is ignored while latched
```

Holding `Reset` for 5 s in Manual clears `RawCounter`, `BaseCounter` and `LidCounter`.
Leaving Manual clears all latches (section 1).

## 6. Output arbitration (every scan)

```mermaid
flowchart LR
  R["BeltSpeedRef<br/>0..300 cm/s"] -->|"Mode 0 forces 0"| L["LIMIT 0..300"]
  L --> T["TargetBeltSpeed<br/>= BeltSpeedRef × 10 / 300 (V)"]
  T --> B1["BeltConveyor4mSpeed"]
  T --> B2["BeltConveyor4mSpeed2"]
  L --> PL["BeltConveyor4mPL = speed > 0"]
  SW["sorter / pusher commands"] --> PLS["matching *PL indicator lamps"]
  RN["Mode 5 and (RunningPL or Blink)"] --> SP["StartPL"]
```

Fixed scene outputs: `Remover1..3` on; `LabPLCRunning` and `SkidPLCRunning` blink;
the panel-active and speed-button lights mirror their inputs; `StopBlade`, `Spare`
and `ProductionRate` are held at 0.
