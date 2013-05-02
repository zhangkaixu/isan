from struct import Struct
from isan.common.task import Lattice, Base_Task, Early_Stop_Pointwise
import isan.tagging.eval as tagging_eval

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        seq=[tuple(word.split('_')) for word in seq]

        raw=[(i,i+1,c) for i,c in enumerate(''.join(w for w,_ in seq))]
        raw=Lattice(raw)

        return {'raw':raw, 'y': seq }

    @staticmethod
    def encode(y):
        return ' '.join(y)

class Action :
    indexer=dict()
    reverse_indexer=dict()
    SBs=[]
    EMs=[]
    @staticmethod
    def encode(action):
        label=action[1]
        if label not in Action.indexer :
            v=len(Action.indexer)
            Action.reverse_indexer[v]=label
            if label[0] in 'SB' :
                Action.SBs.append((v,label[1:]))
            else :
                Action.EMs.append((v,label[1:]))
            Action.indexer[label]=v
        return Action.indexer[label]
    @staticmethod
    def decode(action):
        return (None,Action.reverse_indexer[action])

class State (list):
    Action=Action
    stat_fmt=Struct('hh')
    init_state=stat_fmt.pack(*(0,-1))

    def __init__(self,_,bt=init_state):
        self.extend(self.stat_fmt.unpack(bt))

    def shift(self):
        step=self[0]
        next_step=step+1
        last=self[1]
        la=Action.reverse_indexer.get(last,'')

        if not la or la[0] in 'SE' : # start a new word
            return([ (v,self.stat_fmt.pack(next_step,v)) 
                        for v,_ in Action.SBs ])
        else : # in the same word
            return([ (v,self.stat_fmt.pack(next_step,v)) 
                        for v,tag in Action.EMs if tag==la[1:] ])
        
    @staticmethod
    def load(bt):
        return State.stat_fmt.unpack(bt)
    def dumps(self):
        return self.stat_fmt.pack(*self)


class Task (Early_Stop_Pointwise, Base_Task) : ## mind the order !!
    name="Character based POS tagging"

    codec=codec
    State=State
    Action=Action
    Eval=tagging_eval.TaggingEval

    def actions_to_result(self,actions):
        raw=[c for _,_,c in self.lattice]
        word=[]
        sen=[]
        for i in range(len(actions)):
            a=actions[i][1]
            c=raw[i]
            word.append(c)
            if word and (a[0] in 'ES' or i+1==len(actions)):
                sen.append((''.join(word),a[1:]))
                word=[]
        return sen

    def result_to_actions(self,result):
        actions=[]
        for word,tag in result :
            if len(word)==1 : actions.append('S'+tag)
            else : actions.extend(['B'+tag]+['M'+tag]*(len(word)-2)+['E'+tag])
        actions=[tuple(x) for x in enumerate(actions)]
        ea=[Action.encode(a) for a in actions]
        return actions
    

    def shift(self,last_ind,stat):
        next_ind=last_ind+1
        if next_ind==len(self.lattice) : next_ind=-1 # -1 means the last step
        state=self.State(self.lattice,stat)
        rtn=[(a,next_ind,s) for a,s in state.shift()]
        return rtn

    
    # haha, set_raw() and gen_features() are exactly the same with those in cb_cws.py
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
            fv= [ b'T'+str(stat[1]).encode() ]+self.ngram_fv[ind]
        else :
            fv= self.ngram_fv[ind]

        fvs=[]
        for action in actions:
            action=str(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

