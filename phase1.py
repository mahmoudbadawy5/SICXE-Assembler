import sys

instructions={}
codeLines=[]
codeInstructions=[]
finalCodeInstructions=[]
extDef = []
extRef = []
programName=''
startAddress=0
symbolTable={}
equTable={}
ltTable={}
ltQueue = []
section = False

def loadInstructions():
	### Loads SIC/XE instructions from a prewritten file
	global instructions
	insFile=open('instructionSet.txt','r') #File containing SIC/XE instruction set
	for line in insFile:
		sp=line.split('\t')
		if len(sp)<3: # An empty line
			continue
		for x in range(3):
			sp[x]=sp[x].strip() # Remove unwanted spaces
		instructions[sp[0]]={'format':sp[1],'code':int(sp[2],16)}

def conc(arr,index):
	### Helper function that concatenates string starting from index and split them by spaces
	res=''
	for i in range(index,len(arr)):
		if i != index:
			res=res+' '
		res=res+arr[i]
	return res

def normalize(inst):
	### Removes special characters +,&, $ from instruction
	### and turns it to uppercase
	if not inst[0].isalpha(): # removes first character if not letter
		inst=inst[1::]
	inst=inst.upper()
	return inst


def handleLine(line):
	### Assumes line is correct, label can't be an instruction name
	global programName,section
	global startAddress
	lineParts=line.split()
	if len(lineParts) == 0:
		return None
	for i in range(len(lineParts)):
		lineParts[i]=lineParts[i].strip()
	
	# Special cases (Start,end and base)
	directives = ['BASE','LTORG','END','EQU','EXTDEF','EXTREF']
	if len(lineParts) > 1 and normalize(lineParts[1]) == 'START':
		programName=lineParts[0]
		startAddress=int(lineParts[2],16)
		return None
	if len(lineParts) > 1 and normalize(lineParts[1]) == 'CSECT':
		programName=lineParts[0]
		startAddress=0
		section = True
		return None
	if normalize(lineParts[0]) in directives:
		return {'label':'','name':lineParts[0],'param':conc(lineParts,1)}
	instruction={}
	if normalize(lineParts[0]) in instructions: # No label
		instruction['label']=''
		instruction['name']=lineParts[0]
		instruction['param']=conc(lineParts,1)
	else: #starts with label
		instruction['label']=lineParts[0]
		instruction['name']=lineParts[1]
		instruction['param']=conc(lineParts,2)
	return instruction

def getInstructionLen(instruction):
	### Gets instruction length,
	### Also handlign byte,word,resb,resw and assembler directives
	nrm = normalize(instruction['name'])
	directives = ['BASE','LTORG','END','EQU','EXTDEF','EXTREF']
	if nrm in directives:
		return 0
	elif nrm == 'BYTE' or instruction['name'] == '*':
		if instruction['param'][0].lower()=='c':
			return len(instruction['param'])-3 # remove c'' from the length
		else: # got x''
			return (len(instruction['param'])-3+1)//2 #Each 2 characters make one byte, round up
	elif nrm == 'WORD':
		return 3
	elif nrm == 'RESB':
		return 1*int(instruction['param'])
	elif nrm == 'RESW':
		return 3*int(instruction['param'])
	informat = instructions[nrm]['format']
	if informat == '1':
		return 1
	elif informat == '2':
		return 2
	else:
		sym=instruction['name'][0]
		if sym == '+' or sym == '$':
			return 4
		else:
			return 3

def myhex(val, nbits):
  return hex((val + (1 << nbits)) % (1 << nbits))

def gethex(x,d=4):
	a=myhex(x,(d//2)*8)
	a=a[2::]
	while len(a)<d:
		a="0"+a
	return a.upper()

def formatLine(*args):
	### Adds tabs between args to be printed correctly to a file
	arr=[]
	arr.extend([*list(args)])
	res=str(arr[0])
	for i in range(1,len(arr)):
		res=res+'\t'+str(arr[i])
	return res+'\n'

def handleLt(inst,curloc,out):
	global ltQueue, ltTable, finalCodeInstructions
	used = {}
	nrm = normalize(inst['name'])
	if(nrm == 'LTORG' or nrm == 'END'):
		while len(ltQueue) > 0:
			cur = ltQueue.pop(0)
			if cur in used:
				continue
			used[cur] = True
			ltTable[cur] = curloc
			out.write(formatLine(gethex(curloc),'*',cur))
			inst={'name':'*','param':cur,'loc':curloc,'label':''}
			instLen=getInstructionLen(inst)
			inst['PC']=curloc+instLen
			finalCodeInstructions.append(inst)
			curloc += instLen
	if(len(inst['param']) > 0 and inst['param'][0]=='='):
		ltQueue.append(inst['param'][1::])
	return curloc

def calExpr(expr, start,loc , lev=0):
	expr=expr.strip()
	global symbolTable,equTable
	try:
		me=int(expr)
		return me
	except:
		pass

	if lev>=20:
		# must have invalid referces
		return -1
	if expr in extRef:
		return 0
	if expr in symbolTable:
		return symbolTable[expr]+start
	if expr in equTable:
		loc=equTable[expr]['loc']
		expr=equTable[expr]['expr']
	if expr == '*':
		return loc+start
	symbols = []
	curst=''
	operations = '+-*/()'
	for i in range(len(expr)):
		if expr[i] in operations:
			symbols.append(curst)
			symbols.append(expr[i])
			curst=""
		else:
			curst+=expr[i]
	if len(curst) > 0:
		symbols.append(curst)
	resexp = ""
	for i in range(len(symbols)):
		if symbols[i] in operations:
			resexp += symbols[i]
			if symbols[i] == '/':
				resexp+='/' #To make it integer division
		else:
			resexp += str(calExpr(symbols[i],start,loc,lev+1))
	return eval(resexp)

def removeRed(arr):
	# Simplifies the expression (removes + elements with - ones)
	tot={}
	for elem in arr:
		rel=elem[1:]
		if not rel in tot:
			tot[rel]=0
		if elem[0] == '+':
			tot[rel]+=1
		else:
			tot[rel]-=1
	ret=[]
	for elem in tot:
		for i in range(abs(tot[elem])):
			if tot[elem]>0:
				ret.append("+"+elem)
			else:
				ret.append("-"+elem)
	return ret

def invert(op):
	res=""
	for i in op:
		if i == '+':
			res+='-'
		elif i == '-':
			res+='+'
		else:
			res+=i
	return res

def getExtr(expr,lev=0):
	expr=expr.strip()
	if lev > 10:
		return []
	#print("EXPR: "+expr,extRef)
	if expr in extRef:
		return ["+"+expr]
	if expr in symbolTable or expr in equTable:
		return []
	try:
		x = int(expr)
		return []
	except:
		pass
	symbols = []
	curst=''
	operations = '+-()' #Assuming only addition and subtraction is allowed
	for i in range(len(expr)):
		if expr[i] in operations:
			if len(curst)>0:
				symbols.append(curst)
			symbols.append(expr[i])
			curst=""
		else:
			curst+=expr[i]
	if len(curst) > 0:
		symbols.append(curst)
	res=[]
	lass = "+"
	opStack = []
	for i in range(len(symbols)):
		if symbols[i] == '(':
			opStack.append(lass)
			lass='+'
		elif symbols[i] == ')':
			opStack.pop(len(opStack)-1)
		elif symbols[i] in operations:
			lass = symbols[i]
		else:
			ret=getExtr(symbols[i],lev+1)
			evop = lass
			for i in opStack:
				if i == '-':
					evop=invert(evop)
			if evop == '-':
				for i in range(len(ret)):
					ret[i]=invert(ret[i])
			for i in ret:
				res.append(i)
	return removeRed(res)


def handleEqu(instruction):
	global symbolTable,equTable
	if normalize(instruction['name'])!='EQU':
		return
	lab=instruction['label']
	equTable[lab]={'loc':instruction['loc']}
	equTable[lab]['expr'] = instruction['param']
	val = calExpr(instruction['param'],startAddress,instruction['loc'])
	val2 = calExpr(instruction['param'],startAddress+1000,instruction['loc'])
	equTable[lab]['value'] = val
	equTable[lab]['isAbsloute'] = (val==val2)

def handleExternal(instruction):
	global extRef,extDef
	nrm = normalize(instruction['name'])
	if nrm == 'EXTREF':
		refs = instruction['param'].split(',')
		for i in refs:
			extRef.append(i.strip())
	if nrm == 'EXTDEF':
		defs = instruction['param'].split(',')
		for i in defs:
			extDef.append(i.strip())


def phase1_main():
	### Main driver for phase 1
	global instructions,codeLines,codeInstructions,finalCodeInstructions
	global programName,startAddress,symbolTable

	if len(sys.argv) < 2:
		print("Please spacify the file to be compiled")
		print("Usage: "+sys.argv[0]+" file.asm")
		exit()
	loadInstructions()
	file=open(sys.argv[1])
	codeLines=file.readlines()
	for line in codeLines: # Parsing lines
		inst=handleLine(line)
		if inst != None: 
			codeInstructions.append(inst)
	out = open('out.txt','w')
	symbTableFile = open('symbTable.txt','w')
	if section:
		out.write(formatLine(gethex(startAddress),programName,'CSECT'))
	out.write(formatLine(gethex(startAddress),programName,'START',gethex(startAddress)))
	curloc = startAddress
	for inst in codeInstructions:
		finalCodeInstructions.append(inst)
		if inst['name'] != 'END':
			out.write(formatLine(gethex(curloc),inst['label'],inst['name'],inst['param']))
		if inst['label'] != '' and normalize(inst['name'])!='EQU':
			symbolTable[inst['label']]=curloc
			symbTableFile.write(formatLine(gethex(curloc),inst['label']))
		instLen=getInstructionLen(inst)
		inst['loc']=curloc
		inst['PC']=curloc+instLen
		curloc=handleLt(inst,curloc,out)
		curloc+=instLen
		handleEqu(inst)
		handleExternal(inst)
	out.write(formatLine(gethex(curloc),'END',programName))
	out.close()
	symbTableFile.close()

if __name__ == '__main__':
	phase1_main()