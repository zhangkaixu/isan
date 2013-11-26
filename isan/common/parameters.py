import numpy as np
"""

"""

class Para_Dict (dict):
    def __call__(self,keys):
        return sum(self.get(k,0) for k in keys)

class Parameters :
    def __init__(self,para_class):
        self.para_class=para_class
        self._list=list()
        self._dirty=list()

    def add(self,value):
        if type(value)== dict :
            p=self.para_class.d(value)
            p.init(self)
        else :
            p=value.view(self.para_class.ndarray)
            p.init(self)
        self._list.append(p)
        return p

    def update(self,step=0) :
        for p in self._dirty :
            p._update(step)
        del self._dirty[:]

    def final(self,step):
        for p in self._list :
            if hasattr(p,'final') :
                p.final(step)

    def un_final(self):
        for p in self._list :
            if hasattr(p,'un_final') :
                p.un_final()


class _Base_Dict (Para_Dict):
    def init(self,paras):
        self._delta={}
        self._paras=paras

    def output_obj(self):
        for k,v in self.items():
            if hasattr(v,'output_obj') :
                self[k]=v.output_obj()
        return Para_Dict(self)

    def add_delta(self,keys,delta):
        for f in keys :
            if f not in self._delta :
                self._delta[f]=.0
            self._delta[f]+=delta
        self._paras._dirty.append(self)

    def add_model(self,model):
        for k,v in model.items():
            if k not in self :
                self[k]=0
                self._delta[k]=0
            self[k]=(self[k]*self._delta[k]+v)/(self._delta[k]+1)
            self._delta[k]+=1

class _Base_ndarray(np.ndarray):
    def init(self,paras):
        self._s=0
        self._delta=0
        self.paras=paras

    def add_delta(self,delta) :
        self._delta+=delta
        self.paras._dirty.append(self)

    def output_obj(self):
        return np.array(self)
