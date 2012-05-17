#!/usr/bin/python3
class Features(dict):
    def __init__(self):
        self.acc=dict()
    def __missing__(self,key):
        return 0
    def update(self,feature,delta=0,step=0):
        self.setdefault(feature,0)
        self.acc.setdefault(feature,0)
        self[feature]+=delta
        self.acc[feature]+=step*delta
    def updates(self,features,delta=0,step=0):
        for feature in features:
            self.setdefault(feature,0)
            self.acc.setdefault(feature,0)
            self[feature]+=delta
            self.acc[feature]+=step*delta
    def average(self,step):
        for k in self.acc:
            self[k]=self[k]-self.acc[k]/step
            if self[k]==0:del self[k]
        del self.acc
