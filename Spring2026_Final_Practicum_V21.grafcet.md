# Spring2026_Final_Practicum_V21.grafcet — GRAFCET as Mermaid

Mermaid diagrams of all 11 charts in `Spring2026_Final_Practicum_V21.grafcet`, one section per chart. GitHub, VS Code's Markdown preview and Obsidian all render them.

**Checks:** all 11 diagrams render without errors in Mermaid's own command-line tool. In every chart, the number of arrows equals the number of transitions, so each transition is drawn exactly once. The Main chart was compared against the file by hand and it matches.

## How the charts are split

| Chart | Enclosed by | Steps |
|---|---|---|
| Main | (top level) | 6 |
| Automatic, Automatic-Resets | step 5 (Auto) | 13, 6 |
| Manual-Speeds, Manual-PushPullls, Manual-Counters | step 4 (Manual) | 3, 33, 2 |
| Sort Raw / Sort Base / Sort Lid / Reject | steps 24 / 27 / 28 / 25 | 4, 4, 4, 3 |
| Continuous | (not enclosed) | 7 initial steps, no transitions |

## Reading the diagrams

- **Arrows:** solid arrows are transitions, labelled with their condition. Dashed arrows are jumps, drawn straight to the step they jump to.
- **Boxes:** a double-bordered box is an initial step, and a dashed box is an enclosing step that lists the charts it contains. `*` marks a step that becomes active when its enclosing step activates.
- **Actions in each step:**
  - `N` runs continuously.
  - `C … if` runs only while its condition is true.
  - `↑` runs once when the step activates.
  - `⚡` is an event action, with its trigger shown in brackets when the file gives one. Where the file's trigger is just `1`, it wasn't confirmed exactly when Grafcet-Studio fires it.

## Main

```mermaid
flowchart TD
  FIN12(("end"))
  FIN8(("end"))
  FIN9(("end"))
  SRC21(("start"))
  S1[["1 · EmergencyStop<br/>N StopPL<br/>C EStoppedPL if _SI_1HZ<br/>⚡ BeltSpeedRef:=0<br/>⚡ LastBeltRefSpeed:=BeltSpeedRef<br/>⚡ BeltConveyor4mSpeed:=0<br/>⚡ BeltConveyor4mSpeed2:=0<br/>↑ RunningPL:=0<br/>C ControlOnPL if _SI_1HZ<br/>C ControlOnPL2 if _SI_1HZ<br/>↑ StartPL:=0"]]
  S3["3 · ControlOn<br/>N ControlOnPL<br/>N ControlOnPL2"]
  S5["5 · Auto<br/>⊞ encloses: Automatic, Automatic-Resets<br/>N AutoPL<br/>⚡ BeltConveyor4mSpeed:=TargetBeltSpeed<br/>⚡ BeltConveyor4mSpeed2:=TargetBeltSpeed"]
  S2["2 · ControlOff<br/>⚡ BeltSpeedRef:=0<br/>⚡ LastBeltRefSpeed:=BeltSpeedRef<br/>C ControlOnPL if _SI_1HZ<br/>C ControlOnPL2 if _SI_1HZ<br/>↑ RunningPL:=0<br/>↑ StartPL:=0<br/>N StopPL"]
  S4["4 · Manual<br/>⊞ encloses: Manual-Speeds, Manual-PushPullls, Manual-Counters<br/>N ManualPL<br/>↑ RunningPL:=0<br/>↑ StartPL:=0"]
  S7["7"]
  S1 -->|"Stop*EmergencyStop * EmergencyStop2"| S2
  S7 -->|"ManualSS*!AutoSS"| S4
  S7 -->|"AutoSS*!ManualSS"| S5
  S7 -->|"!ControlOnPL"| FIN8
  S4 -->|"!ControlOnPL"| FIN9
  S4 -.->|"AutoSS*!ManualSS"| S5
  S5 -->|"!ControlOnPL"| FIN12
  S3 -.->|"!EmergencyStop +!EmergencyStop2"| S1
  S3 -.->|"!Stop"| S2
  S2 -->|"(Reset+Reset2PB)*!ClassifyDefuseSensor*!RejectDiffuseSensor*AtExit"| S3
  S2 -.->|"!EmergencyStop +!EmergencyStop2"| S1
  SRC21 -->|"↑X3"| S7
  S5 -.->|"ManualSS*!AutoSS"| S4
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class S1 initial
  class S5,S4 enclosing
  class FIN8,FIN9,FIN12,SRC21 term
```

## Automatic (enclosed by step 5)

```mermaid
flowchart TD
  S19["19"]
  S20["20<br/>C WarningLight1 if !_SI_1HZ"]
  S21["21<br/>⚡[_SI_1HZ] StartPL:=1<br/>⚡[!_SI_1HZ] StartPL:=0"]
  S22["22<br/>↑ LastBeltRefSpeed:=BeltSpeedRef<br/>↑ BeltSpeedRef:=60"]
  S28["28 · Sort Lid<br/>⊞ encloses: Sort Lid"]
  S24["24<br/>⊞ encloses: Sort Raw"]
  S27["27 · Sort Base<br/>⊞ encloses: Sort Base"]
  S25["25 · Rejects<br/>⊞ encloses: Reject"]
  S16["16*"]
  S23["23<br/>↑ RejectFlag:=1"]
  S26["26<br/>↑ LidFlag:=1"]
  S29["29<br/>↑ BaseFlag:=1"]
  S37["37<br/>↑ RawFlag:=1"]
  S20 -->|"3s/X20"| S19
  S21 -->|"Start*ControlOnPL"| S20
  S22 -->|"([VisionSensor1 = 2]+[VisionSensor1 =5 ]) * SendSortPB"| S26
  S25 -.->|"RejPushBackLimit*!RejectFlag"| S19
  S22 -->|"([VisionSensor1 = 1]+[VisionSensor1 = 4]) * SendSortPB"| S37
  S22 -->|"([VisionSensor1=3]+[VisionSensor1=6])*SendSortPB"| S29
  S28 -.->|"!LidFlag"| S19
  S27 -.->|"!BaseFlag"| S19
  S24 -.->|"!RawFlag"| S19
  S19 -->|"↑ClassifyDefuseSensor"| S22
  S22 -->|"([VisionSensor1 = 7]+[VisionSensor1 = 8]+[VisionSensor1 =9]) + SendRejectPB"| S23
  S16 -->|"↑X16"| S21
  S23 -->|"RejectFlag"| S25
  S26 -->|"LidFlag"| S28
  S29 -->|"BaseFlag"| S27
  S37 -->|"RawFlag"| S24
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class S28,S24,S27,S25 enclosing
```

## Automatic-Resets (enclosed by step 5)

```mermaid
flowchart TD
  S9["9<br/>↑ BeltSpeedRef:=0"]
  S10["10"]
  S12["12"]
  S13["13<br/>N Emitter"]
  S8["8*"]
  S11["11*"]
  S9 -->|"1"| S10
  S10 -->|"!ControlOnPL"| S9
  S12 -->|"↑EmitFlag"| S13
  S13 -->|"500ms/X13"| S12
  S8 -->|"↑X8"| S9
  S11 -->|"↑X11"| S12
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
```

## Manual-Speeds (enclosed by step 4)

```mermaid
flowchart TD
  S51["51<br/>↑ BeltSpeedRef:=0<br/>↑ LastBeltRefSpeed:=0"]
  S52["52<br/>⚡ BeltConveyor4mSpeed:=TargetBeltSpeed<br/>⚡ BeltConveyor4mSpeed2:=TargetBeltSpeed"]
  S50["50*"]
  S51 -->|"1"| S52
  S52 -->|"!ControlOnPL"| S51
  S50 -->|"↑X50"| S51
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
```

## Manual-PushPullls (enclosed by step 4)

```mermaid
flowchart TD
  S100["100*"]
  S102["102<br/>N RawSorterBeltCCWPL<br/>N RawSorterBeltCCW"]
  S103["103*"]
  S105["105<br/>N RawSorterBeltCWPL<br/>N RawSorterBeltCW"]
  S106["106*"]
  S108["108<br/>N RawSorterBeltTurnPL<br/>N RawSorterBeltTurn"]
  S109["109*"]
  S111["111<br/>N LidSorterBeltCCWPL<br/>N LidSorterBeltCCW"]
  S112["112*"]
  S114["114<br/>N LidSorterBeltCWPL<br/>N LidSorterBeltCW"]
  S115["115*"]
  S117["117<br/>N LidSorterBeltTurnPL<br/>N LidSorterBeltTurn"]
  S63["63*"]
  S65["65<br/>N BaseSorterBeltCCWPL<br/>N BaseSorterBeltCCW"]
  S66["66*"]
  S68["68<br/>N BaseSorterBeltCWPL<br/>N BaseSorterBeltCW"]
  S69["69*"]
  S71["71<br/>N BaseSorterBeltTurnPL<br/>N BaseSorterBeltTurn"]
  S90["90*"]
  S92["92<br/>N RejectPusherPL<br/>N RejectPusher"]
  S60["60*"]
  S62["62<br/>↑ BeltConveyor4mPL:=1<br/>↑ BeltSpeedRef:=60"]
  S101["101"]
  S104["104"]
  S107["107"]
  S110["110"]
  S113["113"]
  S116["116"]
  S64["64"]
  S67["67"]
  S70["70"]
  S91["91"]
  S61["61<br/>↑ BeltSpeedRef:=0<br/>↑ BeltConveyor4mPL:=0"]
  S102 -->|"↑RawSorterBeltCCWManPB"| S101
  S101 -->|"↑RawSorterBeltCCWManPB*!RawSorterBeltCW"| S102
  S105 -->|"↑RawSorterBeltCWManPB"| S104
  S104 -->|"↑RawSorterBeltCWManPB*!RawSorterBeltCCW"| S105
  S108 -->|"↑RawSorterBeltTurnManPB"| S107
  S107 -->|"↑RawSorterBeltTurnManPB"| S108
  S111 -->|"↑LidSorterBeltCCWManPB"| S110
  S110 -->|"↑LidSorterBeltCCWManPB*!LidSorterBeltCW"| S111
  S114 -->|"↑LidSorterBeltCWManPB"| S113
  S113 -->|"↑LidSorterBeltCWManPB*!LidSorterBeltCCW"| S114
  S117 -->|"↑LidSorterBeltTurnManPB"| S116
  S116 -->|"↑LidSorterBeltTurnManPB"| S117
  S65 -->|"↑BaseSorterBeltCCWManPB"| S64
  S64 -->|"↑BaseSorterBeltCCWManPB*!BaseSorterBeltCW"| S65
  S68 -->|"↑BaseSorterBeltCWManPB"| S67
  S67 -->|"↑BaseSorterBeltCWManPB*!BaseSorterBeltCCW"| S68
  S71 -->|"↑BaseSorterBeltTurnManPB"| S70
  S70 -->|"↑BaseSorterBeltTurnManPB"| S71
  S92 -->|"↑RejectPusherManPB"| S91
  S91 -->|"↑RejectPusherManPB"| S92
  S62 -->|"↑BeltConveyor4mManPB"| S61
  S61 -->|"↑BeltConveyor4mManPB"| S62
  S100 -->|"↑x100"| S101
  S103 -->|"↑X103"| S104
  S106 -->|"↑X106"| S107
  S109 -->|"↑X109"| S110
  S112 -->|"↑X112"| S113
  S115 -->|"↑X115"| S116
  S63 -->|"↑X63"| S64
  S66 -->|"↑X66"| S67
  S69 -->|"↑X69"| S70
  S90 -->|"↑X90"| S91
  S60 -->|"↑X60"| S61
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
```

## Manual-Counters (enclosed by step 4)

```mermaid
flowchart TD
  S57["57*"]
  S58["58<br/>⚡[5s/X58*Reset] RawCounter:=0<br/>⚡[5s/X58*Reset] BaseCounter:=0<br/>⚡[5s/X58*Reset] LidCounter:=0"]
  S57 -->|"↑Reset"| S58
  S58 -->|"↓Reset"| S57
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
```

## Sort Raw (enclosed by step 24)

```mermaid
flowchart TD
  FIN7(("end"))
  S73["73"]
  S74["74"]
  S72["72*<br/>N RawSorterBeltCW<br/>N RawSorterBeltCWPL<br/>N RawSorterBeltTurn<br/>N RawSorterBeltTurnPL<br/>N RawLightInd<br/>↑ RawCounter := RawCounter + 1<br/>↑ BeltSpeedRef:=LastBeltRefSpeed"]
  S75["75<br/>↑ RawFlag:=0"]
  S72 -->|"!Atexit"| S73
  S73 -->|"AtExit"| S74
  S74 -->|"500ms/X74"| S75
  S75 -->|"1"| FIN7
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class FIN7 term
```

## Sort Base (enclosed by step 27)

```mermaid
flowchart TD
  FIN7(("end"))
  S77["77"]
  S78["78"]
  S76["76*<br/>N BaseSorterBeltCW<br/>N BaseSorterBeltCWPL<br/>N BaseSorterBeltTurn<br/>N BaseSorterBeltTurnPL<br/>N BaseLightInd<br/>↑ BaseCounter := BaseCounter + 1<br/>↑ BeltSpeedRef:=LastBeltRefSpeed"]
  S79["79<br/>↑ BaseFlag:=0"]
  S76 -->|"!Atexit"| S77
  S77 -->|"AtExit"| S78
  S78 -->|"500ms/X78"| S79
  S79 -->|"1"| FIN7
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class FIN7 term
```

## Sort Lid (enclosed by step 28)

```mermaid
flowchart TD
  FIN7(("end"))
  S81["81"]
  S82["82"]
  S80["80*<br/>N LidSorterBeltCW<br/>N LidSorterBeltTurn<br/>N LidSorterBeltCWPL<br/>N LidSorterBeltTurnPL<br/>N LidLightInd<br/>↑ LidCounter := LidCounter + 1<br/>↑ BeltSpeedRef:=LastBeltRefSpeed"]
  S83["83<br/>↑ LidFlag:=0"]
  S80 -->|"!Atexit"| S81
  S81 -->|"AtExit"| S82
  S82 -->|"500ms/X82"| S83
  S83 -->|"1"| FIN7
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class FIN7 term
```

## Continuous

```mermaid
flowchart TD
  S46[["46<br/>⚡[↑IncSpdX100 * ControlOnPL] BeltSpeedRef:=BeltSpeedRef+100<br/>⚡[[BeltSpeedRef #gt; 300]] BeltSpeedRef:=300"]]
  S48[["48<br/>⚡[↑IncSpdX10 * ControlOnPL] BeltSpeedRef:=BeltSpeedRef+10<br/>⚡[[BeltSpeedRef #gt; 300]] BeltSpeedRef:=300"]]
  S44[["44<br/>⚡[↑DecSpdX100 * ControlOnPL] BeltSpeedRef:=BeltSpeedRef-100<br/>⚡[[BeltSpeedRef #lt; 0]] BeltSpeedRef:=0"]]
  S14[["14<br/>⚡[↑DecSpdX10 * ControlOnPL] BeltSpeedRef:=BeltSpeedRef-10<br/>⚡[[BeltSpeedRef #lt; 0]] BeltSpeedRef:=0"]]
  S38[["38<br/>⚡[[BeltSpeedRef #gt; 0]] BeltConveyor4mPL:=1<br/>⚡[[BeltSpeedRef = 0]] BeltConveyor4mPL:=0"]]
  S36[["36<br/>⚡ TargetBeltSpeed :=BeltSpeedRef * (27648/300)<br/>⚡ TargetBeltSpeed :=BeltSpeedRef * (10/300)<br/>⚡ TargetBeltSpeed :=BeltSpeedRef * (1000/300)"]]
  S39[["39<br/>⚡[↑DecSpdX10 + ↑DecSpdX100 + ↑IncSpdX10 + ↑IncSpdX100] LastBeltRefSpeed:=BeltSpeedRef"]]
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
  class S46,S48,S44,S14,S38,S36,S39 initial
```

## Reject (enclosed by step 25)

```mermaid
flowchart TD
  S85["85<br/>↑ BeltSpeedRef:=0<br/>N RejectPusherPL<br/>N RejectPusher"]
  S84["84*"]
  S86["86<br/>↑ RejectFlag:=0"]
  S85 -->|"RejPushFrontLimit"| S86
  S84 -->|"RejectDiffuseSensor"| S85
  classDef initial stroke-width:4px
  classDef enclosing stroke-dasharray:6 3
  classDef trans fill:#333,color:#fff,stroke:#333
  classDef term fill:#fff,stroke:#888,color:#555
```
