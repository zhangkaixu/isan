import time
class Times (dict) :
    def __call__(self,key):
        if key not in self :
            self[key]=[0,None]
        data=self[key]
        if data[1]==None :
            data[1]=time.time()
        else :
            data[0]+=time.time()-data[1]
            data[1]=None
    def __repr__(self):
        return '\n'.join(str(k)+":"+str(v[0]) for k,v in self.items())
