COPY Start 0000
EXTREF helloworld, hellomahmoud
EXTDEF CLOOP, ENDFIL 
FIRST STL RETADR
LDB #LENGTH
BASE LENGTH
CLOOP +JSUB RDREC
LDA LENGTH
COMP #0
$JEQ ENDFIL
+JSUB WRREC
&J CLOOP
ENDFIL LDA =C'EOF'
STA BUFFER
LDA #3
STA LENGTH
+JSUB WRREC
J @RETADR
LTORG
RETADR RESW 1
LENGTH RESW 1
BUFFER RESB 4096
BUFFEND EQU *
MAXLEN EQU BUFFEND-BUFFER
MXLENN WORD BUFFEND-BUFFER
RDREC CLEAR X
CLEAR A
CLEAR S
+LDT #MAXLEN
RLOOP TD INPUT
JEQ RLOOP
RD INPUT
COMPR A,S
JEQ EXIT
STCH BUFFER,X
TIXR T
JLT RLOOP
EXIT STX LENGTH
RSUB
INPUT BYTE X'F1'
WRREC CLEAR X
LDT LENGTH
WLOOP TD =X'05'
JEQ WLOOP
LDCH BUFFER,X
WD =X'05'
TIXR T
JLT WLOOP
RSUB
END FIRST
