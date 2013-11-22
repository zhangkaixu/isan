import numpy as np
import collections

from isan.common.parameters import Para_Dict

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
        #print(keys,delta)
        #input()
        #delta*=0.1
        for f in keys :
            if f not in self._delta :
                self._delta[f]=.0
            self._delta[f]+=delta
        self._paras._dirty.append(self)

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

class Ada_Grad :
    name='Ada Grad'
    class d(_Base_Dict):
        def __init__(self,dic):
            self.update(dic)
            self._s=dict(dic)

        def _update(self,step):
            for k,v in self._delta.items():
                if np.all(v==0) : continue
                if k not in self : 
                    self[k]=0
                if k not in self._s :
                    self._s[k]=0
                self._s[k]+=v**2
                _s=self._s[k]
                _delta=np.where(_s,1/np.sqrt(_s+(_s==0)),0)*v
                self[k]+=_delta
                #self[k]*=0.9995
            self._delta.clear()
            """
            if '的' in self._s :
                print(sum(np.abs(self['的'])),sum(np.abs(self._s['的'])))"""

    class ndarray(_Base_ndarray):
        def init(self,paras):
            self._s=0
            self._delta=0
            self.paras=paras
        def _update(self,step) :
            if np.all(self._delta==0) : return
            self._s+=self._delta**2
            delta=np.where(self._s,1/np.sqrt(self._s+(self._s==0)),0)*self._delta
            self+=delta
            #self*=0.9995
            self._delta=0
        
class Default :
    name='naive'
    class d(_Base_Dict):
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


    class ndarray(_Base_ndarray):
        def init(self,paras):
            self._delta=0
            self.paras=paras
        def _update(self,step) :
            self+=self._delta
            self._delta=0

class Averaged :
    name='Averaged'
    class d(_Base_Dict):
        def __init__(self,dic):
            self.update(dic)
            self._s=dict(dic)

        def _update(self,step):
            #print(self._delta)
            #input()
            for k,v in self._delta.items():
                #if v ==0 : continue
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

    class ndarray(_Base_ndarray):
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
