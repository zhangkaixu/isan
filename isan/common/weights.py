import collections
import isan.common.feature_dict as feature_dict


class FD :
    def __init__(self):
        self.fd=feature_dict.new()

    def size(self):
        return feature_dict.size(self.fd)

    def set_weights(self,d):
        return feature_dict.set_weights(self.fd,d)

    def cal_fv(self,fv):
        return feature_dict.cal_fv(self.fd,fv)

    def update_fv(self,fv,delta):
        feature_dict.update_fv(self.fd,fv,delta)

    def to_dict(self):
        return feature_dict.to_dict(self.fd)

    def get(self,key):
        return feature_dict.get(self.fd,key)

    def clear(self):
        feature_dict.clear(self.fd)

    def __del__(self):
        feature_dict.delete(self.fd)

class Weights :
    def items(self):
        for k,v in self.data.items():
            yield k,v
    def __init__(self):
        #self.d=FD()
        self.data=dict()
        self.s=dict()
        #self.ss=FD()
        pass
    def __call__(self,keys):
        return float(sum(self.data.get(k,0) for k in keys))
        s=self.d.cal_fv(keys)
        return s

    def update_weights(self,keys,delta,step):
        #self.ss.update_fv(keys,delta)
        #self.d.update_fv(keys,delta)
        for f in keys :
            if f not in self.data :
                self.data[f]=0
                self.s[f]=0
            self.data[f]+=delta
            self.s[f]+=delta*(step)

    def average_weights(self,step):
        self._backup=dict(self.data)
        for k,v in self._backup.items():
            self.data[k]=self.data[k]-self.s[k]/step
        
        return 
        self._backup=self.d.to_dict()
        tmp={}
        for k,v in self._backup.items():
            #if(self.s[k]!=self.ss.get(k)):
            #    print(k)
            tmp[k]=self._backup[k]-self.s[k]/step
            #tmp[k]=self._backup[k]-self.ss.get(k)/step
        self.d.set_weights(tmp)

    def un_average_weights(self):
        self.data.clear()
        self.data.update(self._backup)
        self._backup.clear()
        return 
        self.d.clear()
        self.d.set_weights(self._backup)
        self._backup.clear()
    pass
