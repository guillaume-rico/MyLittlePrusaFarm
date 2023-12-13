

; external perimeters extrusion width = 0.45mm
; perimeters extrusion width = 0.45mm
; infill extrusion width = 0.45mm
; solid infill extrusion width = 0.45mm
; top infill extrusion width = 0.40mm
; first layer extrusion width = 0.42mm

M73 P0 R2
M201 X1250 Y1250 Z400 E5000 ; sets maximum accelerations, mm/sec^2
M203 X180 Y180 Z12 E80 ; sets maximum feedrates, mm/sec
M204 P1250 R1250 T1250 ; sets acceleration (P, T) and retract acceleration (R), mm/sec^2
M205 X8.00 Y8.00 Z2.00 E10.00 ; sets the jerk limits, mm/sec
M205 S0 T0 ; sets the minimum extruding and travel feed rate, mm/sec
M107
;TYPE:Custom
G90 ; use absolute coordinates
M83 ; extruder relative mode
M140 S60 ; set bed temp
M190 S60
G1 F0.01
M73 P5 R95 ; Affichage avancement
G1 X70
M73 P10 R90 ; Affichage avancement
G1 X90
M73 P15 R85 ; Affichage avancement
G1 X70
M73 P20 R80 ; Affichage avancement
G1 X90
M73 P25 R75 ; Affichage avancement
G1 X70
M73 P30 R70 ; Affichage avancement
G1 X90
M73 P35 R65 ; Affichage avancement
G1 X70
M73 P40 R60 ; Affichage avancement
G1 X90
M73 P45 R55 ; Affichage avancement
G1 X70
M73 P50 R50 ; Affichage avancement
G1 X90
M73 P55 R45 ; Affichage avancement
G1 X70
M73 P60 R40 ; Affichage avancement
G1 X90
M73 P65 R35 ; Affichage avancement
G1 X70
M73 P70 R30 ; Affichage avancement
G1 X90
M73 P75 R25 ; Affichage avancement
G1 X70
M73 P80 R20 ; Affichage avancement
G1 X90
M73 P85 R15 ; Affichage avancement
G1 X70
M73 P90 R10 ; Affichage avancement
G1 X90
M73 P95 R5 ; Affichage avancement
G1 X70
