import isan.tagging.eval as tagging_eval
import argparse
import random
import shlex

class Indexer(list) :
    def __init__(self):
        self.d=dict()
        pass
    def __call__(self,key):
        if key not in self.d :
            self.d[key]=len(self)
            self.append(key)
        return self.d[key]

class codec:
    @staticmethod
    def decode(line):
        if not line: return None
        seq=[word for word in line.split()]
        seq=[tuple(word.split('_')) for word in seq]
        raw=''.join(x[0] for x in seq)
        return {'raw':raw, 'y': seq, 'Y_a': 'y'}

    @staticmethod
    def encode(y):
        return ' '.join(y)


class Task  :
    name="Character-based CWS"

    codec=codec
    Eval=tagging_eval.TaggingEval

    def get_init_states(self) :
        return None

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


    def check(self,std_moves,rst_moves):
        return std_moves[0][-1]==rst_moves[0][-1]
        return False

    def update_moves(self,std_moves,rst_moves) :
        return [(std_moves[0],1),
            (rst_moves[0],-1)]

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
        tags=list(map(self.indexer,tags))
        self.oracle=[None]
        self.set_raw(raw,y)
        return [(0,'',tags)]

    def remove_oracle(self):
        self.oracle=None

    def __init__(self,args=''):
        parser=argparse.ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=r"""用于中文自然语言理解的统计机器学习工具包  作者：张开旭""",)
        parser.add_argument('--corrupt_x',default=0,type=float, help='',metavar="")
        args=parser.parse_args(shlex.split(args))
        self.corrupt_x=args.corrupt_x
        self.weights={}
        self.indexer=Indexer()
        pass
    
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


    def emission(self,raw,tags=None,delta=0,step=0):
        if delta==0 :
            emisions = [ [
                self.weights([action+f for f in fv])
                        for action in self.indexer ]
                    for fv in self.ngram_fv]
            return emisions
        else :
            for fv,tag in zip(self.ngram_fv,tags) :
                tag=self.indexer[tag]
                self.weights.update_weights([tag+f for f in fv],delta,step)

    def transition(self,_,tags=None,delta=0,step=0):
        if delta==0 :
            trans=[[self.weights([a+b]) for b in self.indexer] for a in self.indexer]
            return trans
        else :
            self.weights.update_weights([
                self.indexer[tags[i]]+self.indexer[tags[i+1]] for i in range(len(tags)-1)
                ],delta,step)
