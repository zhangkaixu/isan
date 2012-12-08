#!/usr/bin/python3
from isan.utls.indexer import Indexer
from struct import Struct
import pickle
import json
import time
import math
import sys

class Raw_Data :
    def __init__(self,raw,indexer):
        self.raw=raw
        self.weights=[]
        self.words=[]
        self.tags=[]
        self.tag_ids=[]
        self.offsets=[]
        for k,weight in raw :
            self.weights.append(weight)
            offset,word,tag=k
            self.words.append(word)
            self.tags.append(tag)
            self.tag_ids.append(indexer(tag))
            self.offsets.append(offset)
        self.begins={}
        self.ends={}
        max_ind=0
        for ind,item in enumerate(raw) :
            b,word,tag=item[0]
            e=b+len(word)
            if max_ind<e : max_ind=e
            if b not in self.begins : self.begins[b]=[]
            if e not in self.ends : self.ends[e]=[]
            self.begins[b].append(ind)
            self.ends[e].append(ind)

class Path_Finding :
    def __init__(self):
        self.indexer=Indexer()
        pass
    do_not_set_raw_for_searcher=None
    """
    finding path in a DAG
    """
    class codec :
        @staticmethod
        def decode(line):
            """
            编码、解码
            从一行文本中，得到输入（raw）和输出（y）
            """

            if not line: return []
            log2=math.log(2)
            ldep=json.loads(line)
            raw=[]
            y=[]
            #print(ldep)
            for k,v in ldep :
                if 'tag-weight' in v or v.get('is_test',True)==False :
                    weight=v.get('tag-weight',None)
                    weight=[math.floor(math.log(int(weight)+1)/log2)] if weight!=None else []
                    raw.append([(k[0],k[2],k[3]),weight])
                if 'dep' in v :
                    #y.append((k[0],k[2],k[3],v['dep'][1],v['dep'][0]))
                    y.append((k[0],k[2],k[3]))
            #print(raw)
            #print(y)
            #input()
            return {'raw':raw,
                    'y':y,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
            seq=[word.split('_') for word in line.split()]


            raw=[]
            y=[]
            for offset,word,tag,weight,oracle in seq :
                offset=int(offset)
                weight=[math.floor(math.log(int(weight)+1)/log2)] if weight else []
                item=[(offset,word,tag),weight]
                if oracle!='-1': raw.append(item)
                if oracle!='0' : y.append(item[0])

            print(raw)
            print(y)
            input()

            return {'raw':raw,
                    'y':y,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        @staticmethod
        def encode(y):
            return ' '.join(y)
    def update_moves(self,std_moves,rst_moves) :
        #print('update')
        for move in rst_moves :
            yield move, -1
        for move in std_moves :
            if self.stop_step>=0 and move[0]>=self.stop_step : return
            yield move, 1

    def set_raw(self,raw,Y):
        self.raw_data=Raw_Data(raw,self.indexer)

    def moves_to_result(self,moves,raw):
        if not moves : return []
        actions=list(zip(*moves))[2]
        states=list(zip(*moves))[1]
        #states=[pickle.loads(x) for x in states]
        states=[pickle.loads(x)[0] for x in states]
        inds=[x[1] for x in states[:]]
        result=[
                self.raw_data.raw[ind][0]
                for ind in inds[1:]]
        return result

    
    def load_state(self,data):
        state=pickle.loads(data)
        d=object()
        d.w0=state[0][1]
        d.w1=state[0][0]
        return d

    class State :
        def __init__(self,data=None):

            #self.fmt=Struct("iiiiiiiiiii")
            if data :
                state=pickle.loads(data)
                self.w0=state[0][1]
                self.w1=state[0][0]
                #data=self.fmt.unpack(data)
                #self.w0=data[0]
                #self.w1=-1
                #self.span=(0,0)
                #self.s0=(-1,-1,-1)
                #self.s1=(-1,-1,-1)
                #self.s2=-1
            else :
                self.w0=-1
                self.w1=-1
                self.span=(0,0)
                self.s0=(-1,-1,-1)
                self.s1=(-1,-1,-1)
                self.s2=-1
            pass
        def dump(self):
            return pickle.dumps([(self.w1,self.w0)])
            #return self.fmt.pack(
            #        self.w0,self.w1,
            #        self.span[0],self.span[1],
            #        self.s0[0],self.s0[1],self.s0[2],
            #        self.s1[0],self.s1[1],self.s1[2],
            #        self.s2
            #        )

    init_state=pickle.dumps([(-1,-1),(0,0),(None,None,None)])
    def get_init_states(self):
        init_states=[self.init_state]
        return init_states

    def shift(self,ind,state):
        #sdata=self.State(state)
        #sdata=self.load_state(state)
        state=pickle.loads(state)
        #print(state)
        ind1,ind2=state[0]
        #ind2=sdata.w0
        #span=state[1]
        #s0,s1,s2=state[2]
        #if s1 :
        #    s1_tag=self.raw_data.tags[s1[0]]#self.raw[s1[0]][0][2]
        #else :
        #    s1_tag=None
        if ind not in self.raw_data.begins : 
            return [(-1,-1,pickle.dumps([(ind2,-1)]))]
        nexts=[]
        for ind3 in self.raw_data.begins[ind] :
            sw=self.raw_data.words[ind3]
            so=self.raw_data.offsets[ind3]
            #print(sw)
            next_span=(so,so+len(sw))
            #print(next_span)
            #input()
        
            n=(ind3,ind+len(self.raw_data.words[ind3]),
                    pickle.dumps(
                        [
                            (ind2,ind3),
                            #next_span,
                            #((ind3,None,None),s0,s1_tag),
                        ]
                        )
                )
            nexts.append(n)
        return nexts
    reduce=None
    def check(self,std_moves,rst_moves):
        return all(
                std_move[1]==rst_move[1]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )
    def gen_features(self,state,actions):
        fvs=[]
        state=pickle.loads(state)[0]
        for action in actions :
            ind1,ind2=state
            ind3=action
            if ind1==-1 :
                w1,t1=b'~',b'~'
                len1=b'0'
                f1,b1=b'~',b'~'
                m1=b''
            else :
                r=[(self.raw_data.offsets[ind1],
                        self.raw_data.words[ind1],
                        self.raw_data.tag_ids[ind1]),
                        self.raw_data.weights[ind1]]#raw[ind1]
                w1,t1=r[0][1].encode(),str(r[0][2]).encode()
                len1=str(len(r[0][1])).encode()
                f1,b1=r[0][1][0].encode(),r[0][1][-1].encode()
                m1=b'' if not r[1] else str(r[1][0]).encode()
            if ind2==-1 :
                w2,t2=b'~',b'~'
                len2=b'0'
                f2,b2=b'~',b'~'
                m2=b''
            else :
                r=[(self.raw_data.offsets[ind2],
                        self.raw_data.words[ind2],
                        self.raw_data.tag_ids[ind2]),
                        self.raw_data.weights[ind2]]#raw[ind1]
                w2,t2=r[0][1].encode(),str(r[0][2]).encode()
                len2=str(len(r[0][1])).encode()
                f2,b2=r[0][1][0].encode(),r[0][1][-1].encode()
                m2=b'' if not r[1] else str(r[1][0]).encode()
            if ind3==-1 :
                w3,t3=b'~',b'~'
                len3=b'0'
                f3,b3=b'~',b'~'
                m3=b''
            else :
                r=[(self.raw_data.offsets[ind3],
                        self.raw_data.words[ind3],
                        self.raw_data.tag_ids[ind3]),
                        self.raw_data.weights[ind3]]#raw[ind1]

                w3,t3=r[0][1].encode(),str(r[0][2]).encode()
                len3=str(len(r[0][1])).encode()
                f3,b3=r[0][1][0].encode(),r[0][1][-1].encode()
                m3=b'' if not r[1] else str(r[1][0]).encode()

            fv=[
                    b'm3~'+m3,
                    b'm3m2~'+m3+b'~'+m2,
                    b'w3~'+w3,
                    b't3~'+t3,
                    b'w3t3~'+w3+t3,
                    b'l3~'+len3,
                    b'l3t3~'+len3+t3,
                    b'l3w2~'+len3+w2,
                    b'l3t2~'+len3+t2,
                    b'w3w2~'+w3+b"-"+w2,
                    b'w3t3w2~'+w3+t3+w2,
                    b'w3w2t2~'+w3+t2+w2,
                    b't3w2~'+t3+w2,
                    b'w3t2~'+w3+t2,
                    b'w3t3~'+w3+t3,
                    b't3t2~'+t3+t2,
                    b't3t1~'+t3+t1,
                    b't3t2t1~'+t3+t2+t1,
                    
                    ]
            fvs.append(fv)
        return fvs


    def actions_to_moves(self,actions):

        state=self.init_state
        step=0
        moves=[]
        for action in actions :
            moves.append((step,state,action))
            for a,n,s in self.shift(step,state) :
                if a == action :
                    step=n
                    state=s
        return moves

        


    def set_oracle(self,raw,y):
        self.set_raw(raw,None)
        words=list(reversed(y[:]))
        inds=[-1,-1]
        offset=0
        offsets=[offset]
        for ind,item in enumerate(raw) :
            if not words : break
            if item[0]==words[-1] :
                word=words.pop()
                inds.append(ind)
                offset+=len(word[1])
                offsets.append(offset)
        inds.append(-1)
                

        actions=inds[2:]
        moves2=self.actions_to_moves(actions)

        self.oracle={}
        for step,state,action in moves2 :
            self.oracle[step]=pickle.loads(state)
        
        return moves2
    def remove_oracle(self):
        self.oracle=None
        pass
    def early_stop(self,step,next_states,moves):
        if not moves : return False
        last_steps,last_states,actions=zip(*moves)
        if not hasattr(self,'oracle') or self.oracle==None : return False
        self.stop_step=-1
        if step in self.oracle :
            next_states=[pickle.loads(x) for x in next_states]
            if not (self.oracle[step]in next_states) :
                self.stop_step=step
                return True
        return False

    class Eval :
        def __init__(self):
            """
            初始化
            """
            self.otime=time.time()
            self.std,self.rst=0,0
            self.cor,self.seg_cor=0,0
            self.characters=0
            self.overlaps=0
            self.with_tags=True
        def __call__(self,std,rst):
            std=[x[:3] for x in std]
            #print(std)
            #print(rst)

            std=set(std)
            rst=set(rst)
            self.std+=len(std)
            self.rst+=len(rst)
            self.cor+=len(std&rst)
            self.characters+=sum(len(w)for _,w,_ in std)
            self.seg_cor+=len({(b,e) for b,e,t in std}&{(b,e) for b,e,t in rst})
        def print_result(self):
            """
            打印结果
            """
            time_used=time.time()-self.otime
            speed=self.characters/time_used

            cor=self.cor
            p=cor/self.rst if self.rst else 0
            r=cor/self.std if self.std else 0
            f=2*p*r/(r+p) if (r+p) else 0

            if self.with_tags :
                seg_cor=self.seg_cor
                p=seg_cor/self.rst if self.rst else 0
                r=seg_cor/self.std if self.std else 0
                seg_f=2*p*r/(r+p) if (r+p) else 0

            if self.with_tags :
                line=("标准: %d 输出: %d seg正确: %d 正确: %d seg_f1: \033[32;01m%.4f\033[1;m tag_f1: \033[32;01m%.4f\033[1;m ol: %d 时间: %.4f (%.0f字/秒)"
                            %(self.std,self.rst,self.seg_cor,self.cor,seg_f,f,self.overlaps,time_used,speed))
            else :
                line=("标准: %d 输出: %d 正确: %d f1: \033[32;01m%.4f\033[1;m ol: %d 时间: %.4f (%.0f字/秒)"
                            %(self.std,self.rst,self.cor,f,self.overlaps,time_used,speed))
            print(line,file=sys.stderr)
            sys.stderr.flush()
            pass
        
if __name__ == '__main__':
    pf=Path_Finding()
    for line in open('/home/zkx/lattice/test.lat') :
        line=line.strip()
        pf.codec.decode(line)

