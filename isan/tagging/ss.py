import sys
import json
import gzip
import numpy as np
import pickle
import random

class Word : 
    def __init__(self,args={},model=None,paras=None):
        self.paras=paras

        self.hf_words=set()
        self.hfw_d=self.paras.add({})
        """ ### 对高频词的embedding做学习
        for line in open('hf_words.txt') :
            word,freq=line.split()
            if int(freq)<50 : break
            self.hf_words.add(word)
        print(len(self.hf_words),file=sys.stderr)#"""



        self.s={} ## ??
        if model == None :
            words={}
            size=0
            for line in open(args['words']) :
                word,*vs = line.split()
                vs=list(map(float,vs))
                size=len(vs)
                words[word]=np.array(vs)

                if word in self.hf_words :
                    self.hfw_d[word]=words[word]

            self.words=words
            self.zw=np.zeros(size)
            self.size=size

            

            self.d=self.paras.add({})

            

            self.s={k:v.copy()for k,v in self.d.items()}

        else :
            if type(model)==list :
                self.use_hidden=False
                self.size,self.d,self.words,self.zw=model
            else :
                for k,v in model.items():
                    setattr(self,k,v)

    def add_model(self,model):
        if type(model)==list :
            d=model[1]
        else :
            d=model['d']
        for k,v in d.items():
            #print(k)
            if k not in self.d :
                self.d[k]=v*0
                self.s[k]=0
            self.d[k]=(self.d[k]*self.s[k]+v)/(self.s[k]+1)
            self.s[k]+=1
        
    def dump_weights(self):
        if not self.use_hidden :
            return [self.size,self.d,self.words,self.zw]
        else :
            d={}
            for k in ['use_hidden','size','d','words','zw','tags','zt','sizet']:
                d[k]=getattr(self,k)
            return d


    def set_raw(self,atoms):
        self.atoms=atoms

    def __call__(self,ind1,ind2,ind3,delta=0) :
        w2,t2,*_=self.atoms[ind2] # word on the top of the stack
        w3,t3,*_=self.atoms[ind3] # next word
        word2=w2
        word3=w3
        # get the vector
        if w2 in self.hfw_d :
            w2=self.hfw_d[w2]
        else :
            w2=self.words.get(w2,self.zw) 
        if w3 in self.hfw_d :
            w3=self.hfw_d[w3]
        else :
            w3=self.words.get(w3,self.zw) # get the vector

        score=0

        if delta ==0 : # cal the network, not update
            if t3 in self.d :
                score+=np.dot(w3,self.d([t3]))
            if t2!='~' :
                if t2 in self.d :
                    score+=np.dot(w3,self.d(['l'+t2]))
                if t3 in self.d :
                    score+=np.dot(w2,self.d(['r'+t3]))
        else :  # cal the grad
            self.d.add_delta([t3],w3*delta)
            if word3 in self.hfw_d :
                self.hfw_d.add_delta([word3],self.d([t3])*delta)
            if t2!='~' :
                if word3 in self.hfw_d :
                    self.hfw_d.add_delta([word3],self.d(['l'+t2])*delta)
                self.d.add_delta(['l'+t2],w3*delta)
                if word2 in self.hfw_d :
                    self.hfw_d.add_delta([word2],self.d(['r'+t3])*delta)
                self.d.add_delta(['r'+t3],w2*delta)
        return score
