(* Ladder implementation of the practicum controller. It follows control.st
   section by section and must stay behaviourally identical to it (the
   acceptance tests run every scenario in ST, LD and FBD).

   Every stored bit below is built from /ResetState, directly or through
   ControlOn, so while ResetState is TRUE every coil drops and only the
   shared totals and step numbers are left alone. *)
FUNCTION_BLOCK PracticumLD
VAR_EXTERNAL
    AtExit : BOOL;
    AutoSS : BOOL;
    RejectDiffuseSensor : BOOL;
    DecSpdX10 : BOOL;
    DecSpdX100 : BOOL;
    EmergencyStop : BOOL;
    EmergencyStop2 : BOOL;
    FIOPaused : BOOL;
    FIOReset : BOOL;
    FIORunning : BOOL;
    IncSpdX100 : BOOL;
    IncSpdX10 : BOOL;
    LocalControlPanel : BOOL;
    ManualSS : BOOL;
    RejPushBackLimit : BOOL;
    RejPushFrontLimit : BOOL;
    RemoteControlPanel : BOOL;
    Reset : BOOL;
    Start : BOOL;
    Stop : BOOL;
    ClassifyDefuseSensor : BOOL;
    BaseSorterBeltCCWManPB : BOOL;
    BaseSorterBeltCWManPB : BOOL;
    BaseSorterBeltTurnManPB : BOOL;
    LidSorterBeltCCWManPB : BOOL;
    LidSorterBeltCWManPB : BOOL;
    LidSorterBeltTurnManPB : BOOL;
    RawSorterBeltCCWManPB : BOOL;
    RawSorterBeltCWManPB : BOOL;
    RawSorterBeltTurnManPB : BOOL;
    BeltConveyor4mManPB : BOOL;
    RejectPusherManPB : BOOL;
    SendSortPB : BOOL;
    SendRejectPB : BOOL;
    Reset2PB : BOOL;
    VisionSensor1 : INT;
    BaseLightInd : BOOL;
    BaseSorterBeltCCW : BOOL;
    BaseSorterBeltCW : BOOL;
    BaseSorterBeltTurn : BOOL;
    DecSpdX10Light : BOOL;
    DecSpdX100Light : BOOL;
    Emitter : BOOL;
    Spare : BOOL;
    IncSpdX1Light : BOOL;
    IncSpdX10Light : BOOL;
    LabPLCRunning : BOOL;
    LidLightInd : BOOL;
    LidSorterBeltCCW : BOOL;
    LidSorterBeltCW : BOOL;
    LidSorterBeltTurn : BOOL;
    LocalPanelActive : BOOL;
    RawLightInd : BOOL;
    RawSorterBeltTurn : BOOL;
    RawSorterBeltCCW : BOOL;
    RawSorterBeltCW : BOOL;
    RejectPusher : BOOL;
    RemotePanelActive : BOOL;
    Remover1 : BOOL;
    Remover2 : BOOL;
    Remover3 : BOOL;
    ControlOnPL : BOOL;
    SkidPLCRunning : BOOL;
    StartPL : BOOL;
    StopBlade : BOOL;
    StopPL : BOOL;
    WarningLight1 : BOOL;
    AutoPL : BOOL;
    RawSorterBeltCCWPL : BOOL;
    RawSorterBeltCWPL : BOOL;
    RawSorterBeltTurnPL : BOOL;
    BaseSorterBeltCCWPL : BOOL;
    BaseSorterBeltCWPL : BOOL;
    BaseSorterBeltTurnPL : BOOL;
    LidSorterBeltCCWPL : BOOL;
    LidSorterBeltCWPL : BOOL;
    LidSorterBeltTurnPL : BOOL;
    ManualPL : BOOL;
    BeltConveyor4mPL : BOOL;
    RejectPusherPL : BOOL;
    ControlOnPL2 : BOOL;
    EStoppedPL : BOOL;
    RunningPL : BOOL;
    BaseCounter : INT;
    BeltConveyor4mSpeed : REAL;
    BeltSpeedRef : INT;
    LidCounter : INT;
    ProductionRate : INT;
    RawCounter : INT;
    BeltConveyor4mSpeed2 : REAL;
    RejectFlag : BOOL;
    EmitFlag : BOOL;
    RawFlag : BOOL;
    BaseFlag : BOOL;
    LidFlag : BOOL;
    LastBeltRefSpeed : INT;
    TargetBeltSpeed : REAL;
    ScanDtS : REAL;
    MainStep : INT;
    AutoStep : INT;
    Mode : INT;
END_VAR
VAR_INPUT
    ResetState : BOOL;
END_VAR
VAR CONSTANT
    BlinkPeriodS : REAL := 1.0;
    BlinkOnS : REAL := 0.5;
    WarningTimeS : REAL := 3.0;
    EmitPulseS : REAL := 0.5;
    SortSettleS : REAL := 0.5;
    ResetHoldS : REAL := 5.0;
    MetalCodeMin : INT := 7;
    MetalCodeMax : INT := 9;
    ClassifySpeed : INT := 60;
    JogSpeed : INT := 60;
    MaxBeltSpeed : INT := 300;
END_VAR
VAR
    ClockS : REAL;
    Blink : BOOL;
    AutoElapsed : REAL;
    EmitRemaining : REAL;
    SortElapsed : REAL;
    ResetHeld : REAL;
    PrevMode : INT;
    AutoStepAtScanStart : INT;
    SafetyHealthy : BOOL;
    WasEStopped : BOOL;
    WasAwaitingReset : BOOL;
    ControlOn : BOOL;
    ManualMode : BOOL;
    AutoMode : BOOL;
    ModeChanged : BOOL;
    Warning : BOOL;
    WarningDone : BOOL;
    Classifying : BOOL;
    MetalDetected : BOOL;
    RejectCall : BOOL;
    SortCall : BOOL;
    SortSettling : BOOL;
    RawDiverting : BOOL;
    BaseDiverting : BOOL;
    LidDiverting : BOOL;
    beltJog : ToggleLatch;
    rejectJog : ToggleLatch;
    rawCcw : ToggleLatch;
    rawCw : ToggleLatch;
    rawTurn : ToggleLatch;
    baseCcw : ToggleLatch;
    baseCw : ToggleLatch;
    baseTurn : ToggleLatch;
    lidCcw : ToggleLatch;
    lidCw : ToggleLatch;
    lidTurn : ToggleLatch;
END_VAR

LD
  RUNG reset_timers (* a language switch must not inherit another run's timers or mode history *)
    ResetState { ClockS := 0.0; AutoElapsed := 0.0; EmitRemaining := 0.0; SortElapsed := 0.0; ResetHeld := 0.0; PrevMode := 0 }

  // ---- Main chart X1/X2/X3. Stop and both emergency stops are NC:
  // TRUE = healthy. FIOReset restarts the sequence but keeps the totals.
  RUNG blink_clock (* free-running clock behind every flashing pilot light *)
    /ResetState { ClockS := ClockS + ScanDtS }

  RUNG blink_wrap (* restart the clock each period *)
    /ResetState GE(ClockS, BlinkPeriodS) { ClockS := ClockS - BlinkPeriodS }

  RUNG blink (* on for the first half of each period *)
    /ResetState LT(ClockS, BlinkOnS) ( Blink )

  RUNG safety_healthy (* both e-stop chains made and the scene not being reset *)
    /ResetState EmergencyStop EmergencyStop2 /FIOReset ( SafetyHealthy )

  RUNG was_estopped (* remember X1 before the rungs below move the step *)
    SafetyHealthy EQ(MainStep, 1) ( WasEStopped )

  RUNG was_awaiting_reset (* remember X2 with Stop healthy, before the step moves *)
    SafetyHealthy Stop EQ(MainStep, 2) ( WasAwaitingReset )

  RUNG estop_trip (* any e-stop or a scene reset drops to X1 from anywhere *)
    /ResetState /SafetyHealthy { MainStep := 1 }

  RUNG estop_cleared (* X1 to X2 once the e-stops and Stop are healthy *)
    WasEStopped Stop { MainStep := 2 }

  RUNG stop_pressed (* Stop drops a running machine back to X2 *)
    SafetyHealthy /WasEStopped /Stop { MainStep := 2 }

  RUNG control_reset (* X2 to X3: Reset is accepted only with the conveyor clear and the exit made *)
    WasAwaitingReset [ Reset | Reset2PB ] /ClassifyDefuseSensor /RejectDiffuseSensor AtExit { MainStep := 3 }

  RUNG control_on (* X3 is the only motion permissive; the blinking pilot light is never used as one *)
    /ResetState EQ(MainStep, 3) ( ControlOn )

  RUNG control_on_light (* steady when control is on, flashing while it waits *)
    [ ControlOn | Blink ] ( ControlOnPL ) ( ControlOnPL2 )

  RUNG stop_light (* lit whenever control is off *)
    /ResetState /ControlOn ( StopPL )

  RUNG estopped_light (* flashes while an e-stop holds the machine in X1 *)
    Blink EQ(MainStep, 1) ( EStoppedPL )

  RUNG manual_mode (* manual needs control on and an unambiguous selector *)
    ControlOn ManualSS /AutoSS ( ManualMode ) ( ManualPL )

  RUNG auto_mode (* automatic needs control on and an unambiguous selector *)
    ControlOn AutoSS /ManualSS ( AutoMode ) ( AutoPL )

  RUNG mode_none (* no mode unless a rung below selects one *)
    /ResetState { Mode := 0 }

  RUNG mode_manual (* publish X4 *)
    ManualMode { Mode := 4 }

  RUNG mode_auto (* publish X5 *)
    AutoMode { Mode := 5 }

  // ---- Enclosing steps X4/X5: leaving a mode deactivates its child chart.
  RUNG mode_changed (* one scan on every mode change *)
    /ResetState NE(Mode, PrevMode) ( ModeChanged )

  RUNG mode_change_clear (* the new mode starts stopped, at the first automatic step *)
    ModeChanged { BeltSpeedRef := 0; LastBeltRefSpeed := 0; AutoStep := 16; AutoElapsed := 0.0; EmitRemaining := 0.0; SortElapsed := 0.0 }

  // ---- Continuous: +/-10 and +/-100 cm/s per press, clamped 0..300.
  RUNG speed_up_10 (* one step per press, only with control on *)
    ControlOn +IncSpdX10 { BeltSpeedRef := BeltSpeedRef + 10 }

  RUNG speed_up_100 (* one step per press, only with control on *)
    ControlOn +IncSpdX100 { BeltSpeedRef := BeltSpeedRef + 100 }

  RUNG speed_down_10 (* one step per press, only with control on *)
    ControlOn +DecSpdX10 { BeltSpeedRef := BeltSpeedRef - 10 }

  RUNG speed_down_100 (* one step per press, only with control on *)
    ControlOn +DecSpdX100 { BeltSpeedRef := BeltSpeedRef - 100 }

  RUNG speed_clamp (* keep the operator's reference inside the drive's range *)
    ControlOn { BeltSpeedRef := LIMIT(0, BeltSpeedRef, MaxBeltSpeed) }

  RUNG speed_remember (* an operator change becomes the speed to return to after classifying *)
    ControlOn [ +IncSpdX10 | +IncSpdX100 | +DecSpdX10 | +DecSpdX100 ] { LastBeltRefSpeed := BeltSpeedRef }

  // ---- Automatic: X16/X21 wait, X20 three second warning, X19 emit, X22
  // classify, X24/X27/X28 sorting, X25/X85/X86 rejection.
  RUNG auto_step_snapshot (* every transition below tests the step the scan started in, so one step moves per scan *)
    AutoMode { AutoStepAtScanStart := AutoStep }

  RUNG auto_armed (* X16 to X21: wait for Start *)
    AutoMode EQ(AutoStepAtScanStart, 16) { AutoStep := 21 }

  RUNG auto_start (* X21 to X20: Start begins the warning period *)
    AutoMode EQ(AutoStepAtScanStart, 21) Start { AutoStep := 20; AutoElapsed := 0.0 }

  RUNG warning (* X20: warn before the conveyor moves *)
    AutoMode EQ(AutoStepAtScanStart, 20) ( Warning )

  RUNG warning_light (* flashes opposite the pilot lights during the warning *)
    Warning /Blink ( WarningLight1 )

  RUNG warning_timer (* time the warning *)
    Warning { AutoElapsed := AutoElapsed + ScanDtS }

  RUNG warning_done (* the warning has run its full time *)
    Warning GE(AutoElapsed, WarningTimeS) ( WarningDone )

  RUNG auto_run (* X20 to X19: emit the first part and bring the belt to its remembered speed *)
    WarningDone { AutoStep := 19; EmitRemaining := EmitPulseS; BeltSpeedRef := LastBeltRefSpeed }

  RUNG running_light (* seals in from the end of the warning until automatic is left *)
    AutoMode /ModeChanged [ WarningDone | RunningPL ] ( RunningPL )

  RUNG emit_step (* X19: a part is on its way to the classifier *)
    AutoMode EQ(AutoStepAtScanStart, 19) ( EmitFlag )

  RUNG part_arrived (* X19 to X22: slow the belt while the part is classified *)
    EmitFlag +ClassifyDefuseSensor { LastBeltRefSpeed := BeltSpeedRef; BeltSpeedRef := ClassifySpeed; AutoStep := 22 }

  RUNG classifying (* X22: the part is under the vision sensor *)
    AutoMode EQ(AutoStepAtScanStart, 22) ( Classifying )

  RUNG metal_detected (* vision codes 7..9 are metal, which is always rejected *)
    GE(VisionSensor1, MetalCodeMin) LE(VisionSensor1, MetalCodeMax) ( MetalDetected )

  RUNG reject_call (* reject wins if the operator presses both commands *)
    Classifying [ SendRejectPB | MetalDetected ] ( RejectCall )

  RUNG sort_call (* the operator releases a part that is not being rejected *)
    Classifying /RejectCall SendSortPB ( SortCall )

  RUNG to_reject (* X22 to X25 *)
    RejectCall { AutoStep := 25 }

  RUNG to_raw (* X22 to X24: count the raw part and resume belt speed *)
    SortCall [ EQ(VisionSensor1, 1) | EQ(VisionSensor1, 4) ] { AutoStep := 24; RawCounter := RawCounter + 1; BeltSpeedRef := LastBeltRefSpeed }

  RUNG to_base (* X22 to X27: count the base and resume belt speed *)
    SortCall [ EQ(VisionSensor1, 3) | EQ(VisionSensor1, 6) ] { AutoStep := 27; BaseCounter := BaseCounter + 1; BeltSpeedRef := LastBeltRefSpeed }

  RUNG to_lid (* X22 to X28: count the lid and resume belt speed *)
    SortCall [ EQ(VisionSensor1, 2) | EQ(VisionSensor1, 5) ] { AutoStep := 28; LidCounter := LidCounter + 1; BeltSpeedRef := LastBeltRefSpeed }

  RUNG sort_leaving (* the part has left the exit sensor: stop diverting and wait for it to clear *)
    AutoMode [ EQ(AutoStepAtScanStart, 24) | EQ(AutoStepAtScanStart, 27) | EQ(AutoStepAtScanStart, 28) ] /AtExit { AutoStep := AutoStep + 100 }

  RUNG sort_cleared (* exit sensor made again: start the settling time *)
    AutoMode [ EQ(AutoStepAtScanStart, 124) | EQ(AutoStepAtScanStart, 127) | EQ(AutoStepAtScanStart, 128) ] AtExit { AutoStep := AutoStep + 100; SortElapsed := 0.0 }

  RUNG sort_settling (* any of the three sorters is settling *)
    AutoMode [ EQ(AutoStepAtScanStart, 224) | EQ(AutoStepAtScanStart, 227) | EQ(AutoStepAtScanStart, 228) ] ( SortSettling )

  RUNG sort_settle_timer (* time the settling *)
    SortSettling { SortElapsed := SortElapsed + ScanDtS }

  RUNG sort_done (* back to X19: emit the next part *)
    SortSettling GE(SortElapsed, SortSettleS) { AutoStep := 19; EmitRemaining := EmitPulseS; BeltSpeedRef := LastBeltRefSpeed }

  RUNG reject_at_pusher (* X25 to X85: stop the belt with the part in front of the pusher *)
    AutoMode EQ(AutoStepAtScanStart, 25) RejectDiffuseSensor { AutoStep := 85; BeltSpeedRef := 0 }

  RUNG reject_pushed (* X85 to X86: pusher fully out, let it retract *)
    AutoMode EQ(AutoStepAtScanStart, 85) RejPushFrontLimit { AutoStep := 86 }

  RUNG reject_done (* X86 to X19: pusher home, emit the next part *)
    AutoMode EQ(AutoStepAtScanStart, 86) RejPushBackLimit { AutoStep := 19; EmitRemaining := EmitPulseS; BeltSpeedRef := LastBeltRefSpeed }

  RUNG raw_flag (* a raw part is being sorted, from divert to settled *)
    AutoMode [ EQ(AutoStep, 24) | EQ(AutoStep, 124) | EQ(AutoStep, 224) ] ( RawFlag )

  RUNG base_flag (* a base is being sorted, from divert to settled *)
    AutoMode [ EQ(AutoStep, 27) | EQ(AutoStep, 127) | EQ(AutoStep, 227) ] ( BaseFlag )

  RUNG lid_flag (* a lid is being sorted, from divert to settled *)
    AutoMode [ EQ(AutoStep, 28) | EQ(AutoStep, 128) | EQ(AutoStep, 228) ] ( LidFlag )

  RUNG reject_flag (* a part is being rejected, until the pusher is out *)
    AutoMode [ EQ(AutoStep, 25) | EQ(AutoStep, 85) ] ( RejectFlag )

  RUNG raw_diverting (* X24: the raw sorter diverts, and its light shows it *)
    AutoMode EQ(AutoStep, 24) ( RawDiverting ) ( RawLightInd )

  RUNG base_diverting (* X27: the base sorter diverts, and its light shows it *)
    AutoMode EQ(AutoStep, 27) ( BaseDiverting ) ( BaseLightInd )

  RUNG lid_diverting (* X28: the lid sorter diverts, and its light shows it *)
    AutoMode EQ(AutoStep, 28) ( LidDiverting ) ( LidLightInd )

  RUNG emitter (* emit for as long as the pulse has time left *)
    AutoMode GT(EmitRemaining, 0.0) ( Emitter )

  RUNG emit_pulse_timer (* run the emit pulse down *)
    Emitter { EmitRemaining := EmitRemaining - ScanDtS }

  // ---- Manual-PushPulls and Manual-Counters: each button is push-on /
  // push-off, CW and CCW exclude each other, and every latch drops on
  // leaving manual. Holding Reset five seconds clears the three totals.
  RUNG belt_jog (* manual belt on/off *)
    ManualMode beltJog:ToggleLatch(Press := BeltConveyor4mManPB)

  RUNG belt_jog_on (* latching the belt on runs it at jog speed *)
    beltJog.Flipped beltJog.Q { BeltSpeedRef := JogSpeed }

  RUNG belt_jog_off (* latching it off stops it *)
    beltJog.Flipped /beltJog.Q { BeltSpeedRef := 0 }

  RUNG reject_jog (* manual pusher out/in *)
    ManualMode rejectJog:ToggleLatch(Press := RejectPusherManPB)

  RUNG raw_ccw (* manual raw sorter CCW, refused while CW is latched *)
    ManualMode rawCcw:ToggleLatch(Press := RawSorterBeltCCWManPB, Inhibit := rawCw.Q) ( RawSorterBeltCCW ) ( RawSorterBeltCCWPL )

  RUNG raw_cw_jog (* manual raw sorter CW, refused while CCW is latched *)
    ManualMode rawCw:ToggleLatch(Press := RawSorterBeltCWManPB, Inhibit := rawCcw.Q)

  RUNG raw_turn_jog (* manual raw sorter turn *)
    ManualMode rawTurn:ToggleLatch(Press := RawSorterBeltTurnManPB)

  RUNG raw_cw (* automatic divert or the manual latch *)
    [ RawDiverting | rawCw.Q ] ( RawSorterBeltCW ) ( RawSorterBeltCWPL )

  RUNG raw_turn (* automatic divert or the manual latch *)
    [ RawDiverting | rawTurn.Q ] ( RawSorterBeltTurn ) ( RawSorterBeltTurnPL )

  RUNG base_ccw (* manual base sorter CCW, refused while CW is latched *)
    ManualMode baseCcw:ToggleLatch(Press := BaseSorterBeltCCWManPB, Inhibit := baseCw.Q) ( BaseSorterBeltCCW ) ( BaseSorterBeltCCWPL )

  RUNG base_cw_jog (* manual base sorter CW, refused while CCW is latched *)
    ManualMode baseCw:ToggleLatch(Press := BaseSorterBeltCWManPB, Inhibit := baseCcw.Q)

  RUNG base_turn_jog (* manual base sorter turn *)
    ManualMode baseTurn:ToggleLatch(Press := BaseSorterBeltTurnManPB)

  RUNG base_cw (* automatic divert or the manual latch *)
    [ BaseDiverting | baseCw.Q ] ( BaseSorterBeltCW ) ( BaseSorterBeltCWPL )

  RUNG base_turn (* automatic divert or the manual latch *)
    [ BaseDiverting | baseTurn.Q ] ( BaseSorterBeltTurn ) ( BaseSorterBeltTurnPL )

  RUNG lid_ccw (* manual lid sorter CCW, refused while CW is latched *)
    ManualMode lidCcw:ToggleLatch(Press := LidSorterBeltCCWManPB, Inhibit := lidCw.Q) ( LidSorterBeltCCW ) ( LidSorterBeltCCWPL )

  RUNG lid_cw_jog (* manual lid sorter CW, refused while CCW is latched *)
    ManualMode lidCw:ToggleLatch(Press := LidSorterBeltCWManPB, Inhibit := lidCcw.Q)

  RUNG lid_turn_jog (* manual lid sorter turn *)
    ManualMode lidTurn:ToggleLatch(Press := LidSorterBeltTurnManPB)

  RUNG lid_cw (* automatic divert or the manual latch *)
    [ LidDiverting | lidCw.Q ] ( LidSorterBeltCW ) ( LidSorterBeltCWPL )

  RUNG lid_turn (* automatic divert or the manual latch *)
    [ LidDiverting | lidTurn.Q ] ( LidSorterBeltTurn ) ( LidSorterBeltTurnPL )

  RUNG reject_pusher (* automatic push at X85 or the manual latch *)
    [ AutoMode EQ(AutoStep, 85) | rejectJog.Q ] ( RejectPusher ) ( RejectPusherPL )

  RUNG reset_hold_timer (* time how long Reset has been held in manual *)
    ManualMode Reset { ResetHeld := ResetHeld + ScanDtS }

  RUNG reset_hold_clear (* releasing Reset or leaving manual restarts the hold *)
    /ResetState [ /ManualMode | /Reset ] { ResetHeld := 0.0 }

  RUNG totals_clear (* a full hold clears the three production totals *)
    ManualMode GE(ResetHeld, ResetHoldS) { RawCounter := 0; BaseCounter := 0; LidCounter := 0 }

  // ---- Output arbitration: no mode, no motion.
  RUNG no_mode_stop (* without a mode the belt reference is zero *)
    /ResetState EQ(Mode, 0) { BeltSpeedRef := 0 }

  RUNG belt_speed (* clamp, then scale 0..300 cm/s to the drive's 0..10 V *)
    /ResetState { BeltSpeedRef := LIMIT(0, BeltSpeedRef, MaxBeltSpeed); TargetBeltSpeed := BeltSpeedRef * 10.0 / 300.0 }

  RUNG belt_drive (* both analog channels follow the same target *)
    /ResetState { BeltConveyor4mSpeed := TargetBeltSpeed; BeltConveyor4mSpeed2 := TargetBeltSpeed }

  RUNG belt_light (* lit while the belt has a speed reference *)
    /ResetState GT(BeltSpeedRef, 0) ( BeltConveyor4mPL )

  RUNG start_light (* flashes while automatic waits for Start, steady once running *)
    AutoMode [ RunningPL | Blink ] ( StartPL )

  // ---- Scene support outputs absent from the chart's actions.
  RUNG removers (* the scene's removers run whenever this controller does *)
    /ResetState ( Remover1 ) ( Remover2 ) ( Remover3 )

  RUNG local_panel (* echo the panel selector *)
    /ResetState LocalControlPanel ( LocalPanelActive )

  RUNG remote_panel (* echo the panel selector *)
    /ResetState RemoteControlPanel ( RemotePanelActive )

  RUNG inc_100_light (* each speed button lights while pressed *)
    /ResetState IncSpdX100 ( IncSpdX1Light )

  RUNG inc_10_light (* each speed button lights while pressed *)
    /ResetState IncSpdX10 ( IncSpdX10Light )

  RUNG dec_10_light (* each speed button lights while pressed *)
    /ResetState DecSpdX10 ( DecSpdX10Light )

  RUNG dec_100_light (* each speed button lights while pressed *)
    /ResetState DecSpdX100 ( DecSpdX100Light )

  RUNG unused_outputs (* the stop blade and the spare are never used; hold them off *)
    /ResetState ( R StopBlade ) ( R Spare )

  RUNG scan_end (* no rate is calculated; remember the mode for the next scan's change detection *)
    /ResetState { ProductionRate := 0; PrevMode := Mode }
END_LD
END_FUNCTION_BLOCK
