#!/usr/bin/python3
import collections
class Features(collections.defaultdict):
    def __init__(self):
        super().__init__(int)
        self.acc=collections.defaultdict(int)
    def update(self,feature,delta=0,step=0):
        self[feature]+=delta
        self.acc[feature]+=step*delta
    def updates(self,features,delta=0,step=0):
        for feature in features:
            self[feature]+=delta
            self.acc[feature]+=step*delta
    def average(self,step):
        for k in self.acc:
            self[k]=self[k]-self.acc[k]/step
            if self[k]==0:del self[k]
        del self.acc
