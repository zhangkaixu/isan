import collections

class Weights :
    def items(self):
        for k,v in self.data.items():
            yield k,v
    def __init__(self):
        self.data=dict()
        self.s=dict()
        pass
    def __call__(self,keys):
        #return float(sum(self.data.get(k,0) for k in keys))
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
        for k,v in self.data.items():
            self.data[k]=self.data[k]-self.s[k]/(step)

    def un_average_weights(self):
        self.data.clear()
        self.data.update(self._backup)
        self._backup.clear()
        pass
    pass
