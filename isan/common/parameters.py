import collections
import sys
import numpy as np


"""

"""

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

class Base_Dict (dict):
    def init(self,paras):
        self._delta={}
        self._paras=paras
    def __call__(self,keys):
        return sum(self.get(k,0) for k in keys)

    def add_delta(self,keys,delta):
        for f in keys :
            if f not in self._delta :
                self._delta[f]=0
            self._delta[f]+=delta
        self._paras._dirty.append(self)

class Base_ndarray(np.ndarray):
    def init(self,paras):
        self._s=0
        self._delta=0
        self.paras=paras

    def add_delta(self,delta) :
        self._delta+=delta
        self.paras._dirty.append(self)
    pass

class Ada_Grad :
    class d(Base_Dict):
        def __init__(self,dic):
            self.update(dic)
            self._s=dict(dic)

        def _update(self,step):
            for k,v in self._delta.items():
                if k not in self : 
                    self[k]=0
                    self._s[k]=0
                self._s[k]+=v**2
                _s=self._s[k]
                _delta=np.where(_s,1/np.sqrt(_s+(_s==0)),0)*v
                self[k]+=_delta

            self._delta.clear()

    class ndarray(Base_ndarray):
        def _update(self,step) :
            if np.sum(np.abs(self._delta))==0 : return
            self._s+=self._delta**2
            self+=np.where(self._s,1/np.sqrt(self._s+(self._s==0)),0)*self._delta
            self._delta=0
        

class Averaged :
    class d(Base_Dict):
        def __init__(self,dic):
            self.update(dic)
            self._s=dict(dic)

        def _update(self,step):
            for k,v in self._delta.items():
                if k not in self : 
                    self[k]=0
                    self._s[k]=0
                self[k]+=v
                self._s[k]+=v*step
            self._delta.clear()

        def final(self,step):
            self._backup=dict(self)
            for k,v in self._backup.items():
                self[k]=self[k]-self._s[k]/step

        def un_final(self):
            self.clear()
            self.update(self._backup)
            self._backup.clear()

    class ndarray(Base_ndarray):
        def _update(self,step) :
            self+=self._delta
            self._s+=self._delta*step
            self._delta=0

        def final(self,step):
            self._d=self*1
            self-=self._s/step

        def un_final(self):
            self*=0
            self+=self._d
