import phase1

instructions={}
codeInstructions=[]
programName=''
startAddress=0
symbolTable={}
ltTable={}
equTable={}
extRef = []
extDef = []
registers={}
baseLoc = 0
Trecords = []
Mrecords = []

def initPhase2(_instructions,_codeInstructions,_programName,
			_startAddress,_symbolTable,_ltTable,
			_equTable,_extRef,_extDef):
	global instructions,codeInstructions,programName
	global startAddress,symbolTable,ltTable
	global equTable, extRef, extDef
	instructions=_instructions
	codeInstructions=_codeInstructions
	programName=_programName
	startAddress=_startAddress
	symbolTable=_symbolTable
	ltTable=_ltTable
	equTable=_equTable
	extRef=_extRef
	extDef=_extDef
	f = open('registers.txt','r')
	for i in f:
		x=i.split()
		if(len(x)<2):
			continue
		registers[x[0]]=int(x[1])

def getLongHex(*args):
	### get a hexadecimal equivelent of array of ints
	arr=[]
	arr.extend([*list(args)])
	res=0
	# Each arg is a byte (8-bits)
	for i in arr:
		res<<=8
		res+=i
	return phase1.gethex(res,len(arr)*2);

def getByte(param):
	if param[0]=='X':
		return param[2:len(param)-1]
	s=param[2:len(param)-1]
	res=""
	for i in s:
		res+=phase1.gethex(ord(i),2)
	return res


def getFormat1(instruction):
	nm = phase1.normalize(instruction['name'])
	return getLongHex(instructions[nm]['code'])

def getFormat2(instruction):
	nm = phase1.normalize(instruction['name'])
	fr = instruction['param'].split(',')
	for i in range(len(fr)):
		fr[i].strip()
	while len(fr)<2:
		fr.append('A') # Register with value 0
	regs=0
	for i in fr:
		regs<<=4
		regs+=registers[phase1.normalize(i)]
	return getLongHex(instructions[nm]['code'],regs)

def getMask(l,r):
	#gets a mask of bits from l to r
	res=0
	for i in range(l,r+1):
		res|=(1<<i)
	return res

def formatInst(code,flags,target):
	FB = code|(flags['n']<<1)|flags['i']
	SB = (flags['x']<<3)|(flags['b']<<2)|(flags['p']<<1)|(flags['e'])
	SB <<= 4
	TB = 0
	FoB = 0
	if flags['e'] == 0:
		mask = getMask(8,11)
		SB |= ((target&mask)>>8) # Get bits (8-11)
		TB |= (target&getMask(0,7)) # Rest of bits in third byte
		return getLongHex(FB,SB,TB)
	else:
		mask = getMask(16,19)
		SB |= ((target&mask)>>16) # Get bits (16-19)
		mask = getMask(8,15)
		TB |= (target&mask)>>8
		mask = getMask(0,7)
		FoB |= (target&mask)
		return getLongHex(FB,SB,TB,FoB)

def getWord(param,loc):
	val = phase1.calExpr(param,0,0)	
	v2 = phase1.calExpr(param,1000,0)
	PA = (v2-val)//1000
	for i in range(abs(PA)):
		if PA > 0:
			Mrecords.append("M."+phase1.gethex(loc)+".06+"+programName)
		else:
			Mrecords.append("M."+phase1.gethex(loc)+".06-"+programName)
	mod = phase1.getExtr(param)
	for i in mod:
		Mrecords.append("M."+phase1.gethex(loc)+".06"+i)
	return val

def getRealVal(param,loc):
	val = phase1.calExpr(param,0,0)
	v2=phase1.calExpr(param,1000,0)
	if val!=v2 and loc!=-1:
		Mrecords.append("M."+phase1.gethex(loc+1)+".05")
	mod = phase1.getExtr(param)
	if loc != -1:
		for i in mod:
			Mrecords.append("M."+phase1.gethex(loc+1)+".05"+i)
	return val

def getTarget(param,loc=-1):
	# returns [target, n, i, (is number)]
	if param[0]=='=':
		return [ltTable[param[1::]],1,1]
	if param[0]=='#':
		param = param[1::]
		try: #Try to interpret it as number
			x = int(param)
			return [x,0,1,1]
		except:
			return [getRealVal(param,loc),0,1,0]
	elif param[0] == '@':
		param=param[1::]
		return [getRealVal(param,loc),1,0]
	return [getRealVal(param,loc),1,1]

def getFormat3(instruction):
	# code(6) n i | x p b e disp(0-3) | disp(4-11)
	# SPECIAL CASE (RSUB)
	flags={'n':1,'i':1,'x':0,'b':0,'p':0,'e':0}
	
	nm = phase1.normalize(instruction['name'])
	if nm == 'RSUB':
		return formatInst(instructions[nm]['code'],flags,0)
	# Handling x
	par=instruction['param'].split(',')
	for i in range(len(par)):
		par[i]=par[i].strip()
	tarRet = []
	if(len(par)>1 and phase1.normalize(par[1]) == 'X'):
		flags['x']=1
		tarRet = getTarget(par[0])
	else:
		tarRet=getTarget(instruction['param'])
	target = tarRet[0]
	flags['n'] = tarRet[1]
	flags['i'] = tarRet[2]
	# Try PC relative:
	disp=0
	if tarRet[1] == 0 and tarRet[2]==1 and tarRet[3] == 1:
		disp = target
		flags['p']=0
		flags['b']=0
	else:
		disp = target-instruction['PC']
		flags['p']=1
		flags['b']=0
	if not (-2048<=disp and disp <= 2047):
		# PC relative failed
		flags['p']=0
		flags['b']=1
		disp = target - baseLoc
	return formatInst(instructions[nm]['code'],flags,disp)

def getFormat4(instruction):
	flags={'n':1,'i':1,'x':0,'b':0,'p':0,'e':1}
	nm = phase1.normalize(instruction['name'])
	par=instruction['param'].split(',')
	for i in range(len(par)):
		par[i]=par[i].strip()
	tarRet = []
	if(len(par)>1 and phase1.normalize(par[1]) == 'X'):
		flags['x']=1
		tarRet = getTarget(par[0],instruction['loc'])
	else:
		tarRet=getTarget(instruction['param'],instruction['loc'])
	target = tarRet[0]
	flags['n'] = tarRet[1]
	flags['i'] = tarRet[2]
	return formatInst(instructions[nm]['code'],flags,target)

def getFormat5(instruction):
	#      F1     F2                      F3
	flags={'n':0,'i':0,'x':0,'b':0,'p':0,'e':0}
	
	nm = phase1.normalize(instruction['name'])
	if nm == 'RSUB':
		return formatInst(instructions[nm]['code'],flags,0)
	# Handling x
	par=instruction['param'].split(',')
	for i in range(len(par)):
		par[i]=par[i].strip()
	tarRet = []
	if(len(par)>1 and phase1.normalize(par[1]) == 'X'):
		flags['x']=1
		tarRet = getTarget(par[0])
	else:
		tarRet=getTarget(instruction['param'])
	target = tarRet[0]
	# Try PC relative:
	disp=0
	if tarRet[1] == 0 and tarRet[2]==1 and tarRet[3] == 1:
		disp = target
		if disp % 2 == 0: #F1
			flags['n'] = 1 
		if disp <= 0: #F2
			flags['i'] = 1
		if disp == 0: #F3
			flags['e'] = 1
		flags['p']=0
		flags['b']=0
	else:
		disp = target-instruction['PC']
		if disp % 2 == 0: #F1
			flags['n'] = 1 
		if disp <= 0: #F2
			flags['i'] = 1
		if disp == 0: #F3
			flags['e'] = 1
		flags['p']=1
		flags['b']=0
	if not (-2048<=disp and disp <= 2047):
		# PC relative failed
		flags['p']=0
		flags['b']=1
		disp = target - baseLoc
		if disp % 2 == 0: #F1
			flags['n'] = 1 
		if disp <= 0: #F2
			flags['i'] = 1
		if disp == 0: #F3
			flags['e'] = 1
	return formatInst(instructions[nm]['code'],flags,disp)

def getFormat6(instruction):
	#                         F4    F5    F6 
	flags={'n':1,'i':1,'x':0,'b':0,'p':0,'e':0}
	nm = phase1.normalize(instruction['name'])
	par=instruction['param'].split(',')
	for i in range(len(par)):
		par[i]=par[i].strip()
	tarRet = []
	if(len(par)>1 and phase1.normalize(par[1]) == 'X'):
		flags['x']=1
		tarRet = getTarget(par[0],instruction['loc'])
	else:
		tarRet=getTarget(instruction['param'],instruction['loc'])
	target = tarRet[0]
	flags['n'] = tarRet[1]
	flags['i'] = tarRet[2]
	if target % 2 != 0:
		flags['b']=1
	if target != 0:
		flags['p']=1
	if target != baseLoc:
		flags['e']=1
	return formatInst(instructions[nm]['code'],flags,target)

def getLoc(inst):
	#To print the real value of the location of inst is an EQU
	if phase1.normalize(inst['name']) == 'EQU':
		return equTable[inst['label']]['value']
	return inst['loc']

phase1.phase1_main()
initPhase2(phase1.instructions,phase1.finalCodeInstructions
	,phase1.programName,phase1.startAddress,phase1.symbolTable,phase1.ltTable,
	phase1.equTable,phase1.extRef,phase1.extDef)

# print(symbolTable)
# print(extDef)
# print(extRef)

def normalizeName(name):
	if len(name) > 6:
		return name[0:6]
	while len(name)<6:
		name+='X'
	return name


curlen=0
curRec=""

out = open("out_phase2.txt","w")
out.write(phase1.formatLine(phase1.gethex(startAddress),programName,'START',phase1.gethex(startAddress)))

lasloc=0

for i in codeInstructions:
	nrm = phase1.normalize(i['name'])
	myVal=""
	lasloc = max(lasloc,i['PC'])
	if nrm == 'END':
		continue
	elif nrm == 'RESW' or nrm == 'RESB':
		if curlen>0:
			Trecords.append(curRec)
			curRec=""
			curlen=0
	elif nrm == 'BASE':
		baseLoc = symbolTable[i['param']]
	elif nrm=='BYTE' or i['name'] == '*':
		myVal+=getByte(i['param'])
	elif nrm == 'WORD':
		myVal+=phase1.gethex(getWord(i['param'],i['loc']),6)
	elif nrm in instructions:
		if instructions[nrm]['format'] == '1':
			#print("1: ",end='')
			#print(i,end=' ')
			myVal+=getFormat1(i)
		elif instructions[nrm]['format'] == '2':
			#print("2: ",end='')
			#print(i,end=' ')
			myVal+=getFormat2(i)
		elif i['name'][0]!='+' and i['name'][0]!='$' and i['name'][0] != '&':
			#print("3: ",end='')
			#print(i,end=' ')
			myVal+=getFormat3(i)
		elif i['name'][0]=='+':
			#print("4: ",end='')
			#print(i,end=' ')
			myVal+=getFormat4(i)
		elif i['name'][0]=='&':
			#print("4: ",end='')
			#print(i,end=' ')
			myVal+=getFormat5(i)
		elif i['name'][0]=='$':
			#print("4: ",end='')
			#print(i,end=' ')
			myVal+=getFormat6(i)
	out.write(phase1.formatLine(phase1.gethex(getLoc(i)),i['label'],i['name'],i['param'],myVal))
	if len(myVal) == 0:
		continue
	if len(curRec) == 0:
		curRec+=phase1.gethex(i['loc'],6)
	if curlen + len(myVal) <= 60:
		curRec+=myVal+"."
		curlen+=len(myVal)
	else:
		Trecords.append(curRec)
		curRec=phase1.gethex(i['loc'],6)+myVal+"."
		curlen=len(myVal)
if len(curRec)>0:
	Trecords.append(curRec)

out.write(phase1.formatLine(phase1.gethex(lasloc),'END',programName))
out.close()

HTE = open('HTE.txt','w')

# H record

HTE.write("H."+normalizeName(programName)+"."+phase1.gethex(startAddress,6)+"."+phase1.gethex(lasloc,6)+'\n')

# D record

if len(extDef) > 0:
	HTE.write('D')
for i in extDef:
	HTE.write('.'+normalizeName(i)+'.'+phase1.gethex(getRealVal(i,-1),6))
HTE.write('\n')

# R record

if len(extRef) > 0:
	HTE.write('R')

for i in extRef:
	HTE.write('.'+normalizeName(i))
HTE.write('\n')

# T records

for i in Trecords:
	HTE.write("T."+i[0:6]+"."+phase1.gethex((len(i)-6-i.count('.'))//2,2)+"."+i[6:len(i)-1]+"\n")

# M records

for i in Mrecords:
	HTE.write(i+"\n")

# E record

HTE.write('E.'+phase1.gethex(startAddress,6)+"\n")