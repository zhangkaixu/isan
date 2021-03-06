import numpy as np
import collections

from isan.common.parameters import _Base_Dict
from isan.common.parameters import _Base_ndarray



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
                self[k]*=0.99
            self._delta.clear()

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
            self*=0.99
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
