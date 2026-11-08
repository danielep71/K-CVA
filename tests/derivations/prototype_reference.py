from pathlib import Path
import json
from decimal import Decimal as D, getcontext
getcontext().prec=50
root=Path(__file__).resolve().parents[2]
def df(m):
 m=D(str(m));return (1-(-D('.05')*m).exp())/(D('.05')*m)
def cap(s,hedges=[],index=D(0)):
 ds=D('.65');rho=D('.5')
 def quad(x):return sum(a*a for a in x)+2*rho*rho*sum(x[i]*x[j] for i in range(len(x)) for j in range(i))
 u=ds*quad(s).sqrt()
 if not hedges and not index:return u
 offsets=[D(0)]*len(s);basis=D(0)
 for c,h,r in hedges:
  offsets[c]+=h*r;basis+=(1-r*r)*h*h
 residual=[a-b for a,b in zip(s,offsets)]
 q=quad(residual)-2*rho*sum(residual)*index+index*index+basis
 return D('.25')*u+ds*D('.75')*q.sqrt()
a=D('.05')*3*10000000*df(3)/D('1.4');b=D('.02')*2*5000000/D('1.4')
h=D('.05')*3*2000000*df(3);ih=D('.7')*(D('.6')*D('.05')+D('.4')*D('.02'))*4*1000000*df(4)
vals=[cap([a]),cap([a,b]),cap([a,b],[(0,h,D(1))]),cap([a,b],[(0,h,D('.8'))]),cap([a,b],[(0,h,D('.5'))]),cap([a,b],[],ih),cap([a,b],[(0,h,D('.8'))],ih),cap([a*2,b]),cap([D(0)]),cap([a,b],[(0,h*10,D(1))])]
names=['Single counterparty','Two counterparties / IMM','Direct single-name hedge','Related-name hedge','Sector hedge','Mixed index constituents','Single-name and index hedges','Two netting sets, one counterparty','Zero EAD','Overhedge remains in variance']
(root/'tests/expected/prototype/expected.json').write_text(json.dumps(dict(zip(names,map(float,vals))),indent=2)+'\n')
