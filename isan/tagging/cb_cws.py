from struct import Struct
from isan.common.task import Lattice, Base_Task
import isan.tagging.eval as tagging_eval

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        raw=[(i,i+1,c) for i,c in enumerate(''.join(seq))]
        raw=Lattice(raw)
        return {'raw':raw, 'y': seq }

    @staticmethod
    def encode(y):
        return ' '.join(y)

class Action :
    @staticmethod
    def encode(action):
        return ord(action[1])

class State (list):
    stat_fmt=Struct('hc')
    init_state=stat_fmt.pack(*(0,b'-'))

    def __init__(self,_,bt=init_state):
        self.extend(self.stat_fmt.unpack(bt))

    def shift(self):
        step=self[0]
        next_step=step+1
        return([
                (ord('B'),self.stat_fmt.pack(next_step,b'B')),
                (ord('M'),self.stat_fmt.pack(next_step,b'M')),
                (ord('E'),self.stat_fmt.pack(next_step,b'E')),
                (ord('S'),self.stat_fmt.pack(next_step,b'S')),
                ])
        
    def dumps(self):
        return self.stat_fmt.pack(*self)


class Task (Base_Task) :
    name="Character based CWS"

    codec=codec
    State=State
    Action=Action
    Eval=tagging_eval.TaggingEval

    def actions_to_result(self,actions):
        raw=[c for _,_,c in self.lattice]
        word=[]
        sen=[]
        for i in range(len(raw)):
            a=actions[i]
            c=raw[i]
            word.append(c)
            if word and (a in 'ES' or i+1==len(raw)):
                sen.append(''.join(word))
                word=[]
        return sen

    def result_to_actions(self,result):
        actions=[]
        for word in result :
            if len(word)==1 : actions.append('S')
            else : actions.extend(['B']+['M']*(len(word)-2)+['E'])
        actions=[tuple(x) for x in enumerate(actions)]
        return actions
    

    def shift(self,last_ind,stat):
        next_ind=last_ind+1
        if next_ind==len(self.lattice) : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat)
        rtn=[(a,next_ind,s) for a,s in state.shift()]
        return rtn

    
    def set_raw(self,raw,Y):
        self.lattice=raw
        self.raw=''.join(c for b,e,c in raw)
        xraw=[c.encode() for i,c in enumerate(self.raw)] + [b'#',b'#']
        self.ngram_fv=[]
        for ind in range(len(raw)):
            m=xraw[ind]
            l1=xraw[ind-1]
            l2=xraw[ind-2]
            r1=xraw[ind+1]
            r2=xraw[ind+2]
            self.ngram_fv.append([
                    b'1'+m, b'2'+l1, b'3'+r1,
                    b'4'+l2+l1, b'5'+l1+m,
                    b'6'+m+r1, b'7'+r1+r2,
                ])

    def gen_features(self,stat,actions):
        stat=self.State(self.lattice,stat)
        ind=stat[0]
        if ind > 0 :
            fv= [ b'T'+stat[1] ]+self.ngram_fv[ind]
        else :
            fv= self.ngram_fv[ind]

        fvs=[]
        for action in actions:
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs
