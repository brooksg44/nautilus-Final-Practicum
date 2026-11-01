PROGRAM Main
VAR_EXTERNAL
    LanguageSelect : INT;
    ActiveLanguage : INT;
    LanguageValid : BOOL;
    RawFlag : BOOL;
    BaseFlag : BOOL;
    LidFlag : BOOL;
    RejectFlag : BOOL;
    EmitFlag : BOOL;

    MainStep : INT;
    AutoStep : INT;
    Mode : INT;
    BeltSpeedRef : INT;
    LastBeltRefSpeed : INT;
    TargetBeltSpeed : REAL;
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
    BeltConveyor4mSpeed : REAL;
    ProductionRate : INT;
    BeltConveyor4mSpeed2 : REAL;
END_VAR
VAR
    stController : PracticumST;
    ldController : PracticumLD;
    fbdController : PracticumFBD;
    Initialized : BOOL;
    Changed : BOOL;
END_VAR

LanguageValid := (LanguageSelect >= 1) AND (LanguageSelect <= 3);
Changed := Initialized AND (LanguageSelect <> ActiveLanguage);
IF NOT Initialized OR Changed OR NOT LanguageValid THEN
    (* Reset dormant instances too, so their edge/timer/latch histories
       cannot survive a language switch. Counter totals remain shared. *)
    stController(ResetState := TRUE);
    ldController(ResetState := TRUE);
    fbdController(ResetState := TRUE);
    MainStep := 1;
    AutoStep := 16;
    Mode := 0;
    BeltSpeedRef := 0;
    LastBeltRefSpeed := 0;
    TargetBeltSpeed := 0.0;
    RawFlag := FALSE;
    BaseFlag := FALSE;
    LidFlag := FALSE;
    RejectFlag := FALSE;
    EmitFlag := FALSE;

END_IF;
IF LanguageValid THEN ActiveLanguage := LanguageSelect; ELSE ActiveLanguage := 0; END_IF;
IF Changed OR NOT LanguageValid THEN
    BaseLightInd := FALSE;
    BaseSorterBeltCCW := FALSE;
    BaseSorterBeltCW := FALSE;
    BaseSorterBeltTurn := FALSE;
    DecSpdX10Light := FALSE;
    DecSpdX100Light := FALSE;
    Emitter := FALSE;
    Spare := FALSE;
    IncSpdX1Light := FALSE;
    IncSpdX10Light := FALSE;
    LabPLCRunning := FALSE;
    LidLightInd := FALSE;
    LidSorterBeltCCW := FALSE;
    LidSorterBeltCW := FALSE;
    LidSorterBeltTurn := FALSE;
    LocalPanelActive := FALSE;
    RawLightInd := FALSE;
    RawSorterBeltTurn := FALSE;
    RawSorterBeltCCW := FALSE;
    RawSorterBeltCW := FALSE;
    RejectPusher := FALSE;
    RemotePanelActive := FALSE;
    Remover1 := FALSE;
    Remover2 := FALSE;
    Remover3 := FALSE;
    ControlOnPL := FALSE;
    SkidPLCRunning := FALSE;
    StartPL := FALSE;
    StopBlade := FALSE;
    StopPL := TRUE;
    WarningLight1 := FALSE;
    AutoPL := FALSE;
    RawSorterBeltCCWPL := FALSE;
    RawSorterBeltCWPL := FALSE;
    RawSorterBeltTurnPL := FALSE;
    BaseSorterBeltCCWPL := FALSE;
    BaseSorterBeltCWPL := FALSE;
    BaseSorterBeltTurnPL := FALSE;
    LidSorterBeltCCWPL := FALSE;
    LidSorterBeltCWPL := FALSE;
    LidSorterBeltTurnPL := FALSE;
    ManualPL := FALSE;
    BeltConveyor4mPL := FALSE;
    RejectPusherPL := FALSE;
    ControlOnPL2 := FALSE;
    EStoppedPL := FALSE;
    RunningPL := FALSE;
    BeltConveyor4mSpeed := 0.0;
    BeltSpeedRef := 0;
    ProductionRate := 0;
    BeltConveyor4mSpeed2 := 0.0;
ELSE
    (* Exactly one normal controller invocation per scan. *)
    CASE ActiveLanguage OF
    1: stController(ResetState := FALSE);
    2: ldController(ResetState := FALSE);
    3: fbdController(ResetState := FALSE);
    END_CASE;
END_IF;
Initialized := TRUE;
END_PROGRAM
