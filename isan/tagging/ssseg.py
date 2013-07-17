import isan.tagging.eval as tagging_eval
import argparse
import random
import shlex
import os
import numpy
import gzip
import pickle
import json
import sys


class Indexer(list) :
    def __init__(self):
        self.d=dict()
        pass
    def __call__(self,key):
        if key not in self.d :
            self.d[key]=len(self)
            self.append(key)
        return self.d[key]

class Mapper():
    """
    auto-encoder
    """
    def __init__(self,data=None):
        self.added=False
        if data==None :
            size=50
            self.aew=[Weight_List(size) for i in range(4)] # [tag]
            #load lookup tables for character unigrams and bigrams
            chs={}
            #for line in open('data1.txt'):
            for line in open('1.data4'):
                ch,*v=line.split()
                v=list(map(float,v))[:20]
                chs[ch]=numpy.array([v])

            for line in open('2.data4'):
                b,*v=line.split()
                v=list(map(float,v))[:50]
                chs[b]=numpy.array([v])
            self.chs=chs
            self.zch=numpy.array([[0.0 for i in range(20)]])
            self.zb=numpy.array([[0.0 for i in range(50)]])

            # load weights for the hidden layer
            f=gzip.open('2to3.gz','rb')
            self.Ws=[] # Ws
            self.sWs=[]
            for i in range(7): 
                self.Ws.append(numpy.array(pickle.load(f)))
                self.sWs.append(self.Ws[-1]*0.0)
            self.bs=[] # bs
            self.sbs=[]
            for i in range(7): 
                self.bs.append(numpy.array(pickle.load(f)))
                self.sbs.append(self.bs[-1]*0.0)
        else :
            self.aew,self.chs,self.zch,self.zb,self.Ws,self.bs=data

    def add_model(self,model):
        if self.added : return
        aew,_,_,_,Ws,bs=model
        for a,b in zip(aew,self.aew):
            b.add_model(a)
        for i in range(len(self.Ws)):
            self.Ws[i]=(self.Ws[i]*self.sWs[i]+Ws[i])/(self.sWs[i]+1)
            self.sWs[i]+=1
            self.bs[i]=(self.bs[i]*self.sbs[i]+bs[i])/(self.sbs[i]+1)
            self.sbs[i]+=1
        self.added=True

    def dump(self):
        return [self.aew,self.chs,self.zch,self.zb,self.Ws,self.bs]
    def load(self,data):
        self.aew,self.chs,self.zch,self.zb,self.Ws,self.bs=data

    def find(self,key,miss,inds,v):
        if key in self.chs :
            inds.append(1)
            v.append(self.chs[key])
        else :
            inds.append(0)
            v.append(miss)

    def get_data(self,context):
        inds=[]
        vs=[]
        self.find(context[1],self.zch,inds,vs)
        self.find(context[2],self.zch,inds,vs)
        self.find(context[3],self.zch,inds,vs)
        self.find(context[0:2],self.zb,inds,vs)
        self.find(context[1:3],self.zb,inds,vs)
        self.find(context[2:4],self.zb,inds,vs)
        self.find(context[3:5],self.zb,inds,vs)
        return inds,vs


    def __call__(self,context): # call
        inds,vs=self.get_data(context)
        self.indss.append(inds)
        self.vss.append(vs)

        if all(x==0 for x in inds):
            return numpy.zeros(50)

        #hidden layer
        la=[]
        la=numpy.zeros(50,dtype=float)
        for ind,v,W,b in zip(inds,vs,self.Ws,self.bs):
            if ind ==0 : continue
            la+=numpy.dot(v,W)[0]+b
        la=1/(1+numpy.exp(-la))
        return la

    def update(self,std_tags,rst_tags,delta,step):
        #hidden
        self.dWs=[]
        for x in self.Ws : self.dWs.append(x*0)
        self.dbs=[]
        for x in self.bs : self.dbs.append(x*0)

        for i in range(len(self.conv)):
            if std_tags[i]==rst_tags[i] : continue
            deltas=(self.aew[std_tags[i]].d-self.aew[rst_tags[i]].d)*self.conv[i]*(1-self.conv[i])
            self.update_hidden(i,deltas*0.1)

        for i in range(len(self.Ws)):
            self.Ws[i]+=self.dWs[i]
            self.sWs[i]+=self.dWs[i]*step
            self.bs[i]+=self.dbs[i]
            self.sbs[i]+=self.dbs[i]*step

        #output
        for i in range(len(self.conv)):
            if std_tags[i]==rst_tags[i] : continue
            self.aew[std_tags[i]].update(self.conv[i],delta*0.1,step)
            self.aew[rst_tags[i]].update(self.conv[i],-delta*0.1,step)

    def update_hidden(self,j,deltas):
        inds=self.indss[j]
        vs=self.vss[j]
        for i in range(len(inds)):
            if inds[i]==0 : continue
            self.dbs[i]+=deltas
            self.dWs[i]+=vs[i].T*deltas


    def average_weights(self,step):
        self._backWs=[]
        self._backbs=[]
        for i in range(len(self.Ws)):
            self._backWs.append(numpy.array(self.Ws[i],dtype=float))
            self.Ws[i]-=self.sWs[i]/step
            self._backbs.append(numpy.array(self.bs[i],dtype=float))
            self.bs[i]-=self.sbs[i]/step
        for x in self.aew :
            x.average_weights(step)

    def un_average_weights(self):
        for i in range(len(self.Ws)):
            self.Ws[i]=numpy.array(self._backWs[i])
            self.bs[i]=numpy.array(self._backbs[i])
        for x in self.aew :
            x.un_average_weights()



    def set_raw(self,raw):
        xraw=[c for i,c in enumerate(raw)] + ['#','#']
        contexts=[]
        for ind in range(len(raw)):
            m=xraw[ind]
            l1=xraw[ind-1]
            l2=xraw[ind-2]
            r1=xraw[ind+1]
            r2=xraw[ind+2]
            context=''.join([l2,l1,m,r1,r2])
            contexts.append(context)
        self.conv=[]
        self.indss=[]
        self.vss=[]
        for context in contexts :
            self.conv.append(self(context))
        pass
    def emission(self,emissions):
        for i in range(len(self.conv)):
            for j in range(4):
                emissions[i][j]+=numpy.dot(self.aew[j].d,self.conv[i])


class Weight_List():
    def __init__(self,size):
        self.d=numpy.zeros(size,dtype=float)
        self.s=numpy.zeros(size,dtype=float)
    def __call__(self,fv):
        if fv==None : return 0
        return numpy.dot(self.d,fv)
    def update(self,fv,delta,step):
        if fv==None : return
        if delta == 1:
            self.d+=fv
            self.s+=fv*step
        elif delta ==-1 :
            self.d-=fv
            self.s-=fv*step
        else :
            self.d+=fv*delta
            self.s+=fv*(delta*step)
    def add_model(self,model):
        self.d=(self.d*self.s+model.d)/(self.s+1)
        self.s+=1

    def average_weights(self,step):
        self._backup=numpy.array(self.d,dtype=float)
        self.d-=self.s/step

    def un_average_weights(self):
        self.d=numpy.array(self._backup,dtype=float)


class PCA :
    def __init__(self,ts,data=None):
        self.ts=ts
        if data==None :
            size=50
            self.bi={}
            for line in open('2.data4'):
                bi,*v=line.split()
                v=list(map(float,v))
                self.bi[bi]=numpy.array(v) # bigram embedding

            self.ssw=[[Weight_List(size) for i in range(self.ts)] for j in range(2)] # [pos][tag]
        else :
            self.bi,self.ssw=data

    def add_model(self,model):
        _,ssw=model
        for a,b in zip(self.ssw,ssw):
            for c,d in zip(a,b):
                c.add_model(d)

    def set_raw(self,raw):
        self.raw=raw
        self.bis=[]
        for ind in range(len(raw)-1):
            big=raw[ind:ind+2]
            self.bis.append(self.bi.get(big,None))
    def emission(self,emissions):
        for i in range(len(self.raw)-1):
            for j in range(self.ts):
                emissions[i][j]+=self.ssw[0][j](self.bis[i])
        for i in range(1,len(self.raw)):
            for j in range(self.ts):
                emissions[i][j]+=self.ssw[1][j](self.bis[i-1])
    def update(self,std_tags,rst_tags,delta,step):
        for i in range(len(self.raw)-1):
            if std_tags[i]==rst_tags[i] : continue
            self.ssw[0][std_tags[i]].update(self.bis[i],delta*0.1,step)
            self.ssw[0][rst_tags[i]].update(self.bis[i],-delta*0.1,step)

        for i in range(1,len(self.raw)):
            if std_tags[i]==rst_tags[i] : continue
            self.ssw[1][std_tags[i]].update(self.bis[i-1],delta*0.1,step)
            self.ssw[1][rst_tags[i]].update(self.bis[i-1],-delta*0.1,step)

    def average_weights(self,step):
        for x in self.ssw:
            for y in x:
                y.average_weights(step)

    def un_average_weights(self):
        for x in self.ssw:
            for y in x:
                y.un_average_weights()
    def dump(self):
        return [self.bi,self.ssw]
    def load(self,data):
        self.bi,self.ssw=data

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        seq=[(word.partition('_')) for word in seq]
        seq=[(w,t) for w,_,t in seq]
        raw=''.join(x[0] for x in seq)

        return {'raw':raw, 'y': seq, 'Y_a': 'y'}
        """
        seq=[word for word in line.split()]
        raw=''.join(seq)
        return {'raw':raw, 'y': seq, 'Y_a': 'y'}"""


    @staticmethod
    def encode(y):
        return ' '.join(y)


class Character:
    def __init__(self,ts,model=None,):
        self.ts=ts
        self.uni_d={}
        self.bi_d={}
        self.uni_s={}
        self.bi_s={}

        if model==None :
            pass
        else :
            self.weights.data.update(model)

    def add_model(self,model):
        self.weights.add_model(model)

    def dump(self):
        return None

    def set_raw(self,raw):
        self.raw=raw
        self.uni=['#']+list(raw)+['#']
        self.bi=''.join(['#','#']+list(raw)+['#','#'])
        self.bi=[self.bi[i:i+2] for i in range(len(self.bi)-1)]

    
    def emission(self,emissions):
        l=len(self.raw)
        for i,k in enumerate(self.uni) :
            # : # x x x '#'
            # : x x x
            if k not in self.uni_d : continue
            v=self.uni_d[k]
            if i-2 >=0 : emissions[i-2]+=v[0]
            if i-1 >=0 and i-1 < l: emissions[i-1]+=v[1]
            if i< l: emissions[i]+=v[2]

        for i,k in enumerate(self.bi) :
            # : ## #x xx xx x# ##
            # : x  x  x
            if k not in self.bi_d : continue
            v=self.bi_d[k]
            if i-3 >=0 : emissions[i-3]+=v[0]
            if i-2 >=0 and i-2 < l: emissions[i-2]+=v[1]
            if i-1 >=0 and i-1 < l: emissions[i-1]+=v[2]
            if i< l: emissions[i]+=v[3]


    def update(self,std_tags,rst_tags,delta,step):
        l=len(self.raw)
        for i,k in enumerate(self.uni) :
            if k not in self.uni_d : 
                self.uni_d[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float)]
                self.uni_s[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float)]
            v=self.uni_d[k]
            s=self.uni_s[k]
            if i-2 >=0 :
                v[0][std_tags[i-2]]+=1
                v[0][rst_tags[i-2]]-=1
                s[0][std_tags[i-2]]+=step
                s[0][rst_tags[i-2]]-=step
            if i-1 >=0 and i-1<l: 
                v[1][std_tags[i-1]]+=1
                v[1][rst_tags[i-1]]-=1
                s[1][std_tags[i-1]]+=step
                s[1][rst_tags[i-1]]-=step
            if i<len(self.raw) :
                v[2][std_tags[i]]+=1
                v[2][rst_tags[i]]-=1
                s[2][std_tags[i]]+=step
                s[2][rst_tags[i]]-=step

        for i,k in enumerate(self.bi) :
            if k not in self.bi_d : 
                self.bi_d[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float)]
                self.bi_s[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float)]
            v=self.bi_d[k]
            s=self.bi_s[k]
            if i-3 >=0 :
                v[0][std_tags[i-3]]+=1
                v[0][rst_tags[i-3]]-=1
                s[0][std_tags[i-3]]+=step
                s[0][rst_tags[i-3]]-=step
            if i-2 >=0 and i-2<l: 
                v[1][std_tags[i-2]]+=1
                v[1][rst_tags[i-2]]-=1
                s[1][std_tags[i-2]]+=step
                s[1][rst_tags[i-2]]-=step
            if i-1 >=0 and i-1<l: 
                v[2][std_tags[i-1]]+=1
                v[2][rst_tags[i-1]]-=1
                s[2][std_tags[i-1]]+=step
                s[2][rst_tags[i-1]]-=step
            if i<l :
                v[3][std_tags[i]]+=1
                v[3][rst_tags[i]]-=1
                s[3][std_tags[i]]+=step
                s[3][rst_tags[i]]-=step


    def average_weights(self,step):
        self.uni_b={}
        for k,v in self.uni_d.items():
            self.uni_b[k]=[numpy.copy(x)for x in v]
            for i in range(len(self.uni_b[k])):
                self.uni_d[k][i]-=self.uni_s[k][i]/step
        self.bi_b={}
        for k,v in self.bi_d.items():
            self.bi_b[k]=[numpy.copy(x)for x in v]
            for i in range(len(self.bi_b[k])):
                self.bi_d[k][i]-=self.bi_s[k][i]/step

    def un_average_weights(self):
        for k,v in self.uni_b.items():
            self.uni_d[k]=[numpy.copy(x)for x in v]
        for k,v in self.bi_b.items():
            self.bi_d[k]=[numpy.copy(x)for x in v]



class Task  :
    name="sub-symbolic Character-based CWS"

    codec=codec
    Eval=tagging_eval.TaggingEval

    def get_init_states(self) :
        return None

    def set_oracle(self,raw,y) :
        tags=[]
        for w,t in y :
            if len(w)==1 :
                tags.append('S'+'-'+t)
            else :
                tags.append('B'+'-'+t)
                for i in range(len(w)-2):
                    tags.append('M'+'-'+t)
                tags.append('E'+'-'+t)
        """
        for w in y :
            if len(w)==1 :
                tags.append(3)
            else :
                tags.append(0)
                for i in range(len(w)-2):
                    tags.append(1)
                tags.append(2)"""

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
        """
        results=[]
        cache=[]
        for i,t in enumerate(tags):
            cache.append(self.raw[i])
            if t in [2,3] :
                results.append(''.join(cache))
                cache=[]
        if cache : results.append(''.join(cache))
        return results"""



    def check(self,std_moves,rst_moves):
        return std_moves[0][-1]==rst_moves[0][-1]

    def update_moves(self,std_moves,rst_moves,step) :
        self.emission(self.raw,std_moves[0][-1],rst_moves[0][-1],1,step)
        self.transition(self.raw,std_moves[0][-1],1,step)
        self.transition(self.raw,rst_moves[0][-1],-1,step)


    def remove_oracle(self):
        self.oracle=None

    def __init__(self,model=None,args=''):
        self.indexer=Indexer()
        self.corrupt_x=0
        self.feature_class={'ae':Mapper,'pca':lambda :PCA(self.ts),'base':Character}
        if model==None :
            parser=argparse.ArgumentParser(
                    formatter_class=argparse.RawDescriptionHelpFormatter,
                    description=r"""""",)
            parser.add_argument('--corrupt_x',default=0,type=float, help='',metavar="")
            parser.add_argument('--use_ae',default=False,action='store_true')
            parser.add_argument('--use_pca',default=False,action='store_true',help='')
            parser.add_argument('--pre',default=None,type=str,help='')
            args=parser.parse_args(shlex.split(args))
            self.corrupt_x=args.corrupt_x

            if args.pre :
                for line in open(args.pre) :
                    x=self.codec.decode(line)
                    self.set_oracle(x['raw'],x['y'])[0][-1]
            self.ts=len(self.indexer)
            self.trans=[[0.0 for i in range(self.ts)] for j in range(self.ts)]
            self.trans_s=[[0.0 for i in range(self.ts)] for j in range(self.ts)]
            self.feature_models={'base':Character(self.ts)}

            if args.use_pca :
                self.feature_models['pca']=self.feature_class['pca']()
            if args.use_ae :
                self.feature_models['ae']=self.feature_class['ae']()
        else :
            features=model
            for k,v in features.items():
                self.feature_models[k]=self.feature_class[k](v)

    def add_model(self,features):
        for k,v in features[1].items() :
            self.feature_models[k].add_model(v)


    def dump_weights(self):
        others={k:v.dump() for k,v in self.feature_models.items()}
        features=[others]
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
        self.raw=raw
        for sm in self.feature_models.values() : sm.set_raw(raw)


    def emission(self,raw,std_tags=None,rst_tags=None,delta=0,step=0):
        if delta==0 :
            emissions = [numpy.zeros(self.ts,dtype=float) for i in range(len(self.raw))]
            for sm in self.feature_models.values() : sm.emission(emissions)
            return [x.tolist() for x in emissions]
        else :
            for sm in self.feature_models.values() : sm.update(std_tags,rst_tags,delta,step)


    def transition(self,_,tags=None,delta=0,step=0):
        if delta==0 :
            return self.trans
        else :
            for i in range(len(tags)-1):
                self.trans[tags[i]][tags[i+1]]+=delta
                self.trans_s[tags[i]][tags[i+1]]+=delta*step
