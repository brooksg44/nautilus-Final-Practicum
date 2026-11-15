FUNCTION_BLOCK ToggleLatch
(* Push-on / push-off latch for one manual pushbutton: each new press flips
   Q. Rung power is IN; without it Q drops, so leaving manual mode
   releases every latch. Inhibit refuses a press (the opposite direction is
   running) without disturbing Q. *)
VAR_INPUT
    IN : BOOL;
    Press : BOOL;
    Inhibit : BOOL;
END_VAR
VAR_OUTPUT
    Q : BOOL;
    Flipped : BOOL;
END_VAR
VAR
    PrevPress : BOOL;
END_VAR

LD
  RUNG accept (* one scan per accepted press, so a held button flips Q once *)
    IN Press /PrevPress /Inhibit ( Flipped )

  RUNG latch (* an accepted press inverts Q; otherwise Q holds while enabled *)
    IN [ Flipped /Q | /Flipped Q ] ( Q )

  RUNG remember (* tracked even while disabled: a button held on entry is not a new press *)
    Press ( PrevPress )
END_LD
END_FUNCTION_BLOCK
