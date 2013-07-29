import isan.tagging.eval as tagging_eval
import argparse
import random
import shlex
import numpy
import gzip
import pickle
import sys
import json
from isan.utls.indexer import Indexer
from isan.tagging.cb_subsymbolic import Mapper as Mapper
from isan.tagging.cb_subsymbolic import PCA as PCA
from isan.tagging.cb_symbolic import Character as Character

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        seq=[(word.partition('_')) for word in seq]
        seq=[(w,t) for w,_,t in seq]
        raw=''.join(x[0] for x in seq)
        return {'raw':raw, 'y': seq, 'Y_a': 'y'}
    @staticmethod
    def encode(y):
        return ' '.join(x[0]+ '_'+x[1] if x[1] else '' for x in y)

    @staticmethod
    def encode_candidates(x):
        raw,candidates=x
        return(' '.join(("%d,%d,%s,%s,%0.4f"%(b,e,raw[b:e],t,m))for b,e,t,m in candidates))
            
        pass

class Task  :
    name="sub-symbolic Character-based CWS"

    codec=codec
    Eval=tagging_eval.TaggingEval

    def get_init_states(self) : return None

    def set_oracle(self,raw,y) :
        tags=[]
        for w,t in y :
            if len(w)==1 : tags.append('S'+'-'+t)
            else :
                tags.append('B'+'-'+t)
                for i in range(len(w)-2): tags.append('M'+'-'+t)
                tags.append('E'+'-'+t)
        self.oracle=[None]
        tags=list(map(self.indexer,tags))
        return [(0,'',tags)]

    def moves_to_result(self,moves,_):
        _,_,tags=moves[0]
        tags=list(map(lambda x:self.indexer[x],tags))
        results=[]
        cache=[]
        for i,t in enumerate(tags):
            cache.append(self.raw[i])
            p,tg=t.split('-')
            if p in ['E','S'] :
                results.append((''.join(cache),tg))
                cache=[]
        if cache : results.append((''.join(cache),tg))
        return results

    def gen_candidates(self,margins,threshold):
        score,margins=margins
        candidates=[]
        cands=[]
        for i,ml in enumerate(margins):
            cands.append([])
            for j,it in enumerate(ml):
                a,e,b=it
                if(a+b+e+threshold < score ) : continue
                cands[-1].append((j,a,e,b))

        for i,column in enumerate(cands):
            for a_tid,a_alpha,a_e,a_beta in column :
                a_t=self.indexer[a_tid]
                if a_t[0]=='S' or (i==0 and a_t[0]=='E') or (i+1==len(cands) and a_t[0]=='B'):
                    candidates.append((i,i+1,a_t[2:],score-(a_alpha+a_beta+a_e)))
                elif a_t[0]=='B' or (i==0 and a_t[0]=='M'):
                    value=a_alpha+a_e
                    tag=a_t[2:]
                    last_tid=a_tid
                    for j in range(i+1,len(margins)):
                        flag=False
                        for b_tid,b_alpha,b_e,b_beta in cands[j]:
                            b_t=self.indexer[b_tid]
                            if b_t[2:]!=tag : continue
                            if b_t[0]=='E' or (j+1==len(cands) and b_t[0]=='M'):
                                s=value+b_e+b_beta+self.trans[last_tid][b_tid]
                                if s+threshold >= score :
                                    candidates.append((i,j+1,tag,score-s))
                            if b_t[0]=='M' :
                                value+=b_e+self.trans[last_tid][b_tid]
                                last_tid=b_tid
                                flag=True
                        if flag==False : break

        return self.raw,candidates

    def check(self,std_moves,rst_moves):
        return std_moves[0][-1]==rst_moves[0][-1]

    #"""
    def update_moves(self,std_moves,rst_moves,step) :
        std_tags=std_moves[0][-1]
        rst_tags=rst_moves[0][-1]
        for sm in self.feature_models.values() : 
            sm.update(std_tags,rst_tags,self.eta,step)

        for i in range(len(std_tags)-1):
            self.trans[std_tags[i]][std_tags[i+1]]+=1
            self.trans_s[std_tags[i]][std_tags[i+1]]+=1*step
            self.trans[rst_tags[i]][rst_tags[i+1]]-=1
            self.trans_s[rst_tags[i]][rst_tags[i+1]]-=1*step#"""



    def remove_oracle(self):
        self.oracle=None

    def __init__(self,model=None,cmd_args='',**others):
        class Args :
            pass
        self.indexer=Indexer() # index of tags

        self.logger=others.get('logger',None)

        self.corrupt_x=0
        self.feature_class={
                'ae': lambda x,args={} : Mapper(self.ts,x,args) ,
                'pca': lambda x,args={} : PCA(self.ts,x,args),
                'base':lambda x : Character(self.ts,x)}
        self.feature_models={}

        if model==None :
            args=Args()
            args.eta=0.001
            args.use_pca=False
            args.use_ae=False
            if hasattr(cmd_args,'task_seg'):
                for k,v in cmd_args.task_seg.items():
                    setattr(args,k,v)
            
            dargs=vars(args)



            for train in cmd_args.train :
                for line in open(train) :
                    x=self.codec.decode(line)
                    self.set_oracle(x['raw'],x['y'])[0][-1]


            self.corrupt_x=dargs.get('noise_rate',0)
            self.ts=len(self.indexer)
            self.trans=[[0.0 for i in range(self.ts)] for j in range(self.ts)]
            self.trans_s=[[0.0 for i in range(self.ts)] for j in range(self.ts)]
            self.feature_models['base']=self.feature_class['base'](None)

            if self.logger :
                self.logger.debug('eta: %f'%args.eta)
            self.eta=args.eta

            if args.use_pca :
                self.feature_models['pca']=self.feature_class['pca'](None,args=args.use_pca)
            if args.use_ae :
                self.feature_models['ae']=self.feature_class['ae'](None,args=args.use_ae)
        else :
            self.oracle=None
            self.indexer,self.ts,self.trans,features=model
            for k,v in features.items():
                self.feature_models[k]=self.feature_class[k](v)

    def add_model(self,features):
        self.indexer,self.ts,trans,others=features
        if len(self.trans)==0 :
            self.trans=trans
            self.trans_s=1
        else :
            for i,a in enumerate(self.trans):
                for j,b in enumerate(a):
                    self.trans[i][j]=(self.trans[i][j]*self.trans_s+trans[i][j])/(self.trans_s+1)
            self.trans_s+=1
        for k,v in others.items() :
            self.feature_models[k].add_model(v)

    def dump_weights(self):
        others={k:v.dump() for k,v in self.feature_models.items()}
        features=[self.indexer,self.ts,self.trans,others]
        return features

    def average_weights(self,step):
        self.trans_d=list(list(x) for x in self.trans)
        for i in range(self.ts):
            for j in range(self.ts):
                self.trans[i][j]-=self.trans_s[i][j]/step
        for sm in self.feature_models.values() : sm.average_weights(step)

    def un_average_weights(self):
        self.trans=list(list(x) for x in self.trans_d)
        for sm in self.feature_models.values() : sm.un_average_weights()
    
    def set_raw(self,raw,Y):
        raw=raw[:]
        if self.oracle and self.corrupt_x :
            raw=''.join(c if random.random()>self.corrupt_x else chr(0)  for c in raw)
        self.raw=raw
        for sm in self.feature_models.values() : sm.set_raw(raw)

    def emission(self,raw):
        emissions = [numpy.zeros(self.ts,dtype=float) for i in range(len(self.raw))]
        for sm in self.feature_models.values() : sm.emission(emissions)
        return [x.tolist() for x in emissions]

    def transition(self,_):
        return self.trans
