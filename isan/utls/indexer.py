#!/usr/bin/python3
class Indexer(list) :
    def __init__(self):
        self.d=dict()
        pass
    def __call__(self,key):
        if key not in self.d :
            self.d[key]=len(self)
            self.append(key)
        return self.d[key]

