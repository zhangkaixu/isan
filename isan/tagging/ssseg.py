import isan.tagging.eval as tagging_eval
import argparse
import random
import shlex
import os
import numpy
import gzip
import pickle

class Mapper():
    """
    auto-encoder
    """
    def __init__(self):
        size=50
        self.aew=[Weight_List(size) for i in range(4)] # [tag]

        #load lookup tables for character unigrams and bigrams
        chs={}
        for line in open('data1.txt'):
            ch,*v=line.split()
            v=list(map(float,v))[:20]
            chs[ch]=numpy.array([v])

        for line in open('data2.txt'):
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

    def set_raw(self,contexts):
        self.contexts=contexts
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

    def average_weights(self,step):
        self._backup=numpy.array(self.d,dtype=float)
        self.d-=self.s/step

    def un_average_weights(self):
        self.d=numpy.array(self._backup,dtype=float)

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        raw=''.join(seq)
        return {'raw':raw, 'y': seq, 'Y_a': 'y'}

    @staticmethod
    def encode(y):
        return ' '.join(y)


class Task  :
    name="sub-symbolic Character-based CWS"

    codec=codec
    Eval=tagging_eval.TaggingEval

    def get_init_states(self) :
        return None

    def moves_to_result(self,moves,_):
        _,_,tags=moves[0]

        results=[]
        cache=[]
        for i,t in enumerate(tags):
            cache.append(self.raw[i])
            if t in [2,3] :
                results.append(''.join(cache))
                cache=[]
        if cache : results.append(''.join(cache))
        return results


    def check(self,std_moves,rst_moves):
        return std_moves[0][-1]==rst_moves[0][-1]
        return False

    def update_moves(self,std_moves,rst_moves,step) :
        self.emission(self.raw,std_moves[0][-1],rst_moves[0][-1],1,step)
        self.transition(self.raw,std_moves[0][-1],1,step)
        self.transition(self.raw,rst_moves[0][-1],-1,step)

    def set_oracle(self,raw,y) :
        tags=[]
        for w in y :
            if len(w)==1 :
                tags.append(3)
            else :
                tags.append(0)
                for i in range(len(w)-2):
                    tags.append(1)
                tags.append(2)
        self.oracle=[None]
        return [(0,'',tags)]

    def remove_oracle(self):
        self.oracle=None

    def __init__(self,args=''):
        parser=argparse.ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=r"""""",)
        parser.add_argument('--corrupt_x',default=0,type=float, help='',metavar="")
        parser.add_argument('--use_ae',default=False,type=bool, help='',metavar="")
        parser.add_argument('--use_pca',default=False,type=bool, help='',metavar="")
        args=parser.parse_args(shlex.split(args))
        self.corrupt_x=args.corrupt_x
        self.weights={}

        self.use_ae_features=args.use_ae
        self.use_pca_features=args.use_pca
        self.use_hiddens=True
        self.bi={}
        size=50

        if self.use_pca_features :
            for line in open('data2.txt'):
                bi,*v=line.split()
                v=list(map(float,v))
                self.bi[bi]=numpy.array(v)
            self.ssw=[[Weight_List(size) for i in range(4)] for j in range(2)] # [pos][tag]

        if self.use_ae_features:
            self.mapper=Mapper()
        pass

    def average_weights(self,step):
        self.weights.average_weights(step)
        if self.use_pca_features :
            for x in self.ssw:
                for y in x:
                    y.average_weights(step)

        if self.use_ae_features:
            pass
        if self.use_hiddens :
            self.mapper.average_weights(step)

    def un_average_weights(self):
        self.weights.un_average_weights()
        if self.use_pca_features :
            for x in self.ssw:
                for y in x:
                    y.un_average_weights()

        if self.use_ae_features:
            pass
        if self.use_hiddens :
            self.mapper.un_average_weights()

    
    def set_raw(self,raw,Y):
        self.raw=raw
        xraw=[c for i,c in enumerate(self.raw)] + ['#','#']
        self.ngram_fv=[]
        self.contexts=[]
        for ind in range(len(raw)):
            m=xraw[ind]
            l1=xraw[ind-1]
            l2=xraw[ind-2]
            r1=xraw[ind+1]
            r2=xraw[ind+2]
            if self.use_ae_features :
                context=''.join([l2,l1,m,r1,r2])
                self.contexts.append(context)
            self.ngram_fv.append([
                    '1'+m, '2'+l1, '3'+r1,
                    '4'+l2+l1, '5'+l1+m,
                    '6'+m+r1, '7'+r1+r2,
                ])
        if self.use_ae_features :
            self.mapper.set_raw(self.contexts)

        self.bis=[]
        for ind in range(len(raw)-1):
            big=raw[ind:ind+2]
            self.bis.append(self.bi.get(big,None))


    def emission(self,raw,std_tags=None,rst_tags=None,delta=0,step=0):
        if delta==0 :
            emissions = [ [
                self.weights([action+f for f in fv])
                        for action  in 'BMES']
                    for fv in self.ngram_fv]
            if self.use_pca_features :
                for i in range(len(self.raw)-1):
                    for j in range(4):
                        emissions[i][j]+=self.ssw[0][j](self.bis[i])
                for i in range(1,len(self.raw)):
                    for j in range(4):
                        emissions[i][j]+=self.ssw[1][j](self.bis[i-1])
            if self.use_ae_features :
                self.mapper.emission(emissions)
            return emissions
        else :
            ts='BMES'
            for fv,s_tag,r_tag in zip(self.ngram_fv,std_tags,rst_tags) :
                if s_tag==r_tag : continue
                tag=ts[s_tag]
                self.weights.update_weights([tag+f for f in fv],delta,step)
                tag=ts[r_tag]
                self.weights.update_weights([tag+f for f in fv],-delta,step)


            if self.use_pca_features :
                for i in range(len(self.raw)-1):
                    if std_tags[i]==rst_tags[i] : continue
                    self.ssw[0][std_tags[i]].update(self.bis[i],delta,step)
                    self.ssw[0][rst_tags[i]].update(self.bis[i],-delta,step)

                for i in range(1,len(self.raw)):
                    if std_tags[i]==rst_tags[i] : continue
                    self.ssw[1][std_tags[i]].update(self.bis[i-1],delta,step)
                    self.ssw[1][rst_tags[i]].update(self.bis[i-1],-delta,step)

            if self.use_ae_features :
                self.mapper.update(std_tags,rst_tags,delta,step)



    def transition(self,_,tags=None,delta=0,step=0):
        if delta==0 :
            trans=[[self.weights([a+b]) for b in 'BMES'] for a in 'BMES']
            return trans
        else :
            ts='BMES'
            self.weights.update_weights([
                ts[tags[i]]+ts[tags[i+1]] for i in range(len(tags)-1)
                ],delta,step)
