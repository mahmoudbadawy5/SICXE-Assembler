prog1 START 0000
EXTDEF ALPHA, MAX
EXTREF INF, ZERO
LDS #3
LDT #300
LDX #0
CLOOP LDA ALPHA, X
COMP MAX
+JLT NOCH
STA MAX
NOCH ADDR S, X
COMPR X, T
JLT CLOOP
ALPHA RESW 100
MAX WORD ZERO - INF