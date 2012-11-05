#!/usr/bin/python3
from struct import Struct
import time
import math
import sys
class Path_Finding :
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
            seq=[word.split('_') for word in line.split()]

            raw=[]
            y=[]
            for offset,word,tag,weight,oracle in seq :
                offset=int(offset)
                weight=[math.floor(math.log(int(weight)/1000+1)/log2)] if weight else []
                item=[(offset,word,tag),weight]
                if oracle!='-1': raw.append(item)
                if oracle!='0' : y.append(item[0])

            return {'raw':raw,
                    'y':y,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        @staticmethod
        def encode(y):
            return ' '.join(y)
    def update_moves(self,std_moves,rst_moves) :
        for move in std_moves :
            yield move, 1
        for move in rst_moves :
            yield move, -1
    def set_raw(self,raw,Y):
        self.raw=raw
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

    def moves_to_result(self,moves,raw):
        if not moves : return []
        actions=list(zip(*moves))[2]
        states=list(zip(*moves))[1]
        states=[Struct.unpack(self.stat_fmt,x) for x in states]
        inds=[x[2] for x in states[:]]
        result=[self.raw[ind][0] for ind in inds]
        return result
    def gen_actions_and_stats(self,ind,state):
        state=Struct.unpack(self.stat_fmt,state)
        ind1,ind2,ind3=state
        #print(*(self.raw[i][0] if i>=0 else (None,None,None) for i in state))
        
        next_ind=ind+len(self.raw[ind3][0][1])

        #print(ind,next_ind)
        
        if next_ind not in self.begins : 
            return [(1,-1,Struct.pack(self.stat_fmt,ind2,ind3,-1))]
        nexts=[]
        for ind4 in self.begins[next_ind] :
            n=(1,next_ind,Struct.pack(self.stat_fmt,ind2,ind3,ind4))
            #print(n)
            nexts.append(n)
        #print(nexts)
        return nexts
        pass
    def check(self,std_moves,rst_moves):
        return all(
                std_move[1]==rst_move[1]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )
    def gen_features(self,state):
        state=Struct.unpack(self.stat_fmt,state)
        ind1,ind2,ind3=state
        raw1=self.raw[ind1] if ind1 != -1 else [(-1,'~','~'),[]]
        raw2=self.raw[ind2] if ind2 != -1 else [(-1,'~','~'),[]]
        raw3=self.raw[ind3] if ind3 != -1 else [(-1,'~','~'),[]]
        fv=[]
        fv+=[b'a0~'+str(x).encode() for x in raw3[1]]

        fv+=[
                b'3w~'+raw3[0][1].encode(),
                b'3t~'+raw3[0][2].encode(),
                b'l3~'+str(len(raw3[0][1])).encode(),
                b't3t2~'+raw3[0][2].encode()+b'~'+raw2[0][2].encode(),
                b'w3w2~'+raw3[0][1].encode()+b'~'+raw2[0][1].encode(),
                b'w3t2~'+raw3[0][1].encode()+b'~'+raw2[0][2].encode(),
                b't3w2~'+raw3[0][2].encode()+b'~'+raw2[0][1].encode(),
                b't3t2t1~'+raw3[0][2].encode()+b'~'+raw2[0][2].encode()+b'~'+raw1[0][2].encode(),
                ]

        return fv

    stat_fmt=Struct('hhh')
    def get_init_states(self):
        init_states=[Struct.pack(self.stat_fmt,*(-1,-1,ind)) for ind in self.begins[0]]
        return init_states
        pass

    def set_oracle(self,raw,y):
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
        states=[inds[i:i+3] for i in range(len(inds)-2)]
        states=[Struct.pack(self.stat_fmt,*state) for state in states]
        actions=[1 for x in range(len(states)-1)]
        self.oracle={o:s for o,s in zip(offsets,states)}
        moves=[]
        for state,action in zip(states,actions) :
            _,_,ind3=Struct.unpack(self.stat_fmt,state)
            step=raw[ind3][0]
            moves.append((step,state,action))
        return moves
    def early_stop(self,step,last_states,actions,next_states):
        if not hasattr(self,'oracle') or self.oracle==None : return False
        
        if step in self.oracle :
            if not (self.oracle[step]in next_states) :
                return True
        return False
    def remove_oracle(self):
        self.oracle=None
        pass

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

