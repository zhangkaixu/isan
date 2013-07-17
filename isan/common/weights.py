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
        self.data=dict()
        self.s=dict()

    def add_model(self,model):
        for k,v in model.items():
            if v==0 : continue
            if k not in self.data :
                self.data[k]=0
                self.s[k]=0
            self.data[k]=(self.data[k]*self.s[k]+v)/(self.s[k]+1)
            self.s[k]+=1

    def __call__(self,keys):
        return float(sum(self.data.get(k,0) for k in keys))

    def update_weights(self,keys,delta,step):
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

    def un_average_weights(self):
        self.data.clear()
        self.data.update(self._backup)
        self._backup.clear()
