import json

"""
item= begin,end,*
weights = []
gold=

eval


[item]

"""
class Lattice :
    def __init__(self,l,w):
        self.weights=w
        self.items=l
        chars={}
        begins={}
        for i,item in enumerate(self.items) :
            begin=item[0]
            for j,c in enumerate(item[2]):
                o=j+begin
                if o not in chars: chars[o]=c
            if begin not in begins : begins[begin]=[]
            begins[begin].append(i)
        self.begins=begins
        self.sentence=''.join(x[1] for x in sorted(list(chars.items())))
        self.length=len(self.sentence)
    def __str__(self):
        items=' '.join('_'.join(map(str,item)) for item in self.items)
        s='lattice of: %s\nitems: %s'%(self.sentence,items)
        return s

"""
[{'start': ,'end':,'key','info','gold'}]
"""
class Data :
    @staticmethod
    def to_train(data):
        train=[]
        for item in data:
            train.append(item['key'])
        lattice=Lattice(train,None)
        return lattice
    pass

