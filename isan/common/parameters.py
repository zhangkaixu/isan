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
        p=value.view(self.para_class)
        p.init(self)
        self._list.append(p)
        return p

    def update(self,step=0) :
        for p in self._dirty :
            p.update(step)
        del self._dirty[:]

    def final(self,step):
        for p in self._list :
            p.final(step)

    def un_final(self):
        for p in self._list :
            p.un_final()

class Ada_Grad (np.ndarray) :
    def init(self,paras):
        self._s=0
        self._delta=0
        self.paras=paras

    def add_delta(self,delta) :
        self._delta+=delta
        self.paras._dirty.append(self)

    def update(self,step) :
        if np.sum(np.abs(self._delta))==0 : return
        self._s+=self._delta**2
        self+=np.where(self._s,1/np.sqrt(self._s+(self._s==0)),0)*self._delta
        #self+=self._delta
        self._delta=0

    def final(self,step):
        pass

    def un_final(self):
        pass
        

class Averaged (np.ndarray) :
    def init(self,paras):
        self._s=0
        self._delta=0
        self.paras=paras

    def add_delta(self,delta) :
        self._delta+=delta
        self.paras._dirty.append(self)

    def update(self,step) :
        self+=self._delta
        self._s+=self._delta*step
        self._delta=0

    def final(self,step):
        #return
        self._d=self*1
        self-=self._s/step

    def un_final(self):
        #return
        self*=0
        self+=self._d

