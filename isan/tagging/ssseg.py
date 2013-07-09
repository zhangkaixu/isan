import isan.tagging.eval as tagging_eval
import argparse
import random
import shlex
import os
import numpy


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
        args=parser.parse_args(shlex.split(args))
        self.corrupt_x=args.corrupt_x
        self.weights={}

        self.bi={}
        size=0
        for line in open('data2.txt'):
            bi,*v=line.split()
            v=list(map(float,v))
            self.bi[bi]=numpy.array(v)
            size=max(size,len(v))
        print(size)
        self.ssw=[[Weight_List(size) for i in range(4)] for j in range(2)] # [pos][tag]
        pass

    def average_weights(self,step):
        self.weights.average_weights(step)
        for x in self.ssw:
            for y in x:
                y.average_weights(step)

    def un_average_weights(self):
        self.weights.un_average_weights()
        for x in self.ssw:
            for y in x:
                y.un_average_weights()
    
    def set_raw(self,raw,Y):
        self.raw=raw
        xraw=[c for i,c in enumerate(self.raw)] + ['#','#']
        self.ngram_fv=[]
        for ind in range(len(raw)):
            m=xraw[ind]
            l1=xraw[ind-1]
            l2=xraw[ind-2]
            r1=xraw[ind+1]
            r2=xraw[ind+2]
            self.ngram_fv.append([
                    '1'+m, '2'+l1, '3'+r1,
                    '4'+l2+l1, '5'+l1+m,
                    '6'+m+r1, '7'+r1+r2,
                ])

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
            for i in range(len(self.raw)-1):
                for j in range(4):
                    emissions[i][j]+=self.ssw[0][j](self.bis[i])
            for i in range(1,len(self.raw)):
                for j in range(4):
                    emissions[i][j]+=self.ssw[1][j](self.bis[i-1])
            return emissions
        else :
            ts='BMES'
            for fv,s_tag,r_tag in zip(self.ngram_fv,std_tags,rst_tags) :
                if s_tag==r_tag : continue
                tag=ts[s_tag]
                self.weights.update_weights([tag+f for f in fv],delta,step)
                tag=ts[r_tag]
                self.weights.update_weights([tag+f for f in fv],-delta,step)

            for i in range(len(self.raw)-1):
                if std_tags[i]==rst_tags[i] : continue
                self.ssw[0][std_tags[i]].update(self.bis[i],delta,step)
                self.ssw[0][rst_tags[i]].update(self.bis[i],-delta,step)

            for i in range(1,len(self.raw)):
                if std_tags[i]==rst_tags[i] : continue
                self.ssw[1][std_tags[i]].update(self.bis[i-1],delta,step)
                self.ssw[1][rst_tags[i]].update(self.bis[i-1],-delta,step)

    def transition(self,_,tags=None,delta=0,step=0):
        if delta==0 :
            trans=[[self.weights([a+b]) for b in 'BMES'] for a in 'BMES']
            return trans
        else :
            ts='BMES'
            self.weights.update_weights([
                ts[tags[i]]+ts[tags[i+1]] for i in range(len(tags)-1)
                ],delta,step)
