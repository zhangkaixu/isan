#!/usr/bin/python3
from struct import Struct
import pickle
import json
import time
import math
import sys
import subprocess
from isan.common.lattice import Lattice_Task as Base_Task
from isan.data.lattice import Lattice as Lattice

class Thulac :
    def __init__(self,model_path,threshold=0,bin_path='bin/predict_c',
            ):
        self.sp=subprocess.Popen(bin_path+r' %s %s '%(
            '--threshold %i'%(threshold) if threshold!=0 else '',
            model_path,),
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                shell=True)
        self.threshold=threshold
    def __call__(self,input):
        input=input.strip()
        self.sp.stdin.write((input+'\n').encode())
        self.sp.stdin.flush()
        output=self.sp.stdout.readline().decode().strip()
        if self.threshold!=0 :
            output=[it.split(',') for it in output.split()]
            output=[[b,e,input[int(b):int(e)],t,i] for b,e,t,i in output]
        else :
            output=[it.split('_') for it in output.split()]
        return output

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


class codec :
    @staticmethod
    def decode(line):
        """
        编码、解码
        从一行文本中，得到输入（raw）和输出（y）
        """

        if not line: return []
        log2=math.log(2)
        line=list(map(lambda x:x.split(','), line.split()))
        line=[[int(label),int(b),int(e),w,t,int(conf)] for label,b,e,w,t,conf in line]
        items=[]
        weights=[]
        y=[]
        for l,b,e,w,t,conf in line :
            if conf != -2:
                items.append([b,e,w,t])
                if conf == -1 :
                    conf = None
                else :
                    conf = str(math.floor(math.log(conf/500+1)))
                weights.append(conf)
            if l ==1 :
                y.append((b,w,t))
        raw=Lattice(items,weights)
        return {'raw':raw,
                'y':y,
                'Y_a' : None,
                'Y_b' : None,
                }
    @staticmethod
    def encode(y):
        return ' '.join(y)

class State :
    init_state=pickle.dumps([(-1,-1)])
    init_stat=pickle.dumps([(-1,-1)])
    def __init__(self,bt,lattice):
        words,*_=pickle.loads(bt)
        self.w1,self.w0=words
        self.lattice=lattice
    def shift(self,wid):
        return pickle.dumps([(self.w0,wid)])
    @staticmethod
    def load(bt):
        return pickle.loads(bt)
    def __str__(self):
        return "【%i %s | %i %s】"%(
                (self.w1),self.lattice.items[self.w1] if self.w1>=0 else '',
                (self.w0),self.lattice.items[self.w0] if self.w0>=0 else '',)

class Path_Finding (Base_Task):
    """
    finding path in a DAG
    """

    def __init__(self):



        self.av={}
        for line in open("av.txt"):
            word,av=line.split()
            av=int(av)
            self.av[word]=str(int(math.log(av+1)*2)).encode()
            #print(word,self.av[word],av)


        self.ae={}
        #for line in open("/home/zkx/wordtype/autoencoder/top4.txt"):
        for line in open("/home/zkx/wordtype/autoencoder/top4.txt"):
            word,*inds=line.split()
            inds=[x.encode() for x in inds]
            self.ae[word]=inds



        #self.sgcount={}
        #for line in open("sg.count.txt"):
        #    word,f15,f0,fw=line.split()
        #    f15=int(f15)
        #    f0=int(f0)
        #    fw=float(fw)
        #    if f0==0 or fw==0 : continue
        #    self.sgcount[word]=[
        #            str(int(math.log(f15))).encode(),
        #            str(int(math.log(f0))).encode(),
        #            str(int(math.log(f0/f15))).encode(),
        #            str(int(math.log(fw/f15))).encode(),
        #            ]

        self.mkcls={}
        for line in open('brown.out'):
            clu,word,_=line.split()
        #for line in open('mkcls.out'):
            #word,clu=line.split()
            #if word not in self.ae : continue
            self.mkcls[word]=str(int(clu)).encode()

        self.thulac_model=Thulac(bin_path='~/minilac/bin/predict_c',
                #model_path='~/minilac/models/pku/model_c',
                model_path='~/thulac/hailiang',
                threshold=0)
        

    codec=codec
    State=State

    def update_moves(self,std_moves,rst_moves) :
        for move in rst_moves :
            if self.stop_step>=0 and move[0]>=self.stop_step : return
            yield move, -1
        for move in std_moves :
            if self.stop_step>=0 and move[0]>=self.stop_step : return
            yield move, 1


    def moves_to_result(self,moves,_):
        if not moves : return []
        actions=list(zip(*moves))[2]
        states=list(zip(*moves))[1]
        states=[self.State.load(x)[0] for x in states]
        inds=[x[1] for x in states[:]]
        result=[
                (self.lattice.items[ind][0],
                    self.lattice.items[ind][2],
                    self.lattice.items[ind][3])
                for ind in inds[1:]]
        return result


    init_state=State.init_state#


    def shift_step(self,step,ind):
        return step+len(self.lattice.items[ind][2])

    def shift(self,step,state):
        state=self.State(state,self.lattice)
        if step not in self.lattice.begins : # 如果没有后续节点，标志为结束
            return [(-1,-1,state.shift(-1))]
        nexts=[]
        for ind3 in self.lattice.begins[step] :
            next_step=self.shift_step(step,ind3)
            n=(
                    ind3, #shift action id
                    next_step,
                    state.shift(ind3)
                )
            #print(n[0],n[1],self.State(n[2],self.lattice))
            nexts.append(n)
        return nexts
    reduce=None


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

        for ind,item in enumerate(self.lattice.items) :
            if not words : break
            if (item[0]==words[-1][0] 
                    and item[2]==words[-1][1]
                    and item[3]==words[-1][2]
                    ) :
                word=words.pop()
                inds.append(ind)
                offset+=len(word[1])
                offsets.append(offset)
        inds.append(-1)
                

        actions=inds[2:]
        moves2=self.actions_to_moves(actions)

        self.oracle={}
        for step,state,action in moves2 :
            self.oracle[step]=self.State.load(state)
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
            next_states=[self.State.load(x) for x in next_states]
            if not (self.oracle[step]in next_states) :
                self.stop_step=step
                return True
        return False

    def set_raw(self,raw,Y):
        self.lattice=raw
        self.words_av = []
        self.ae_inds=[]
        self.seq_mkcls=[]
        result=self.thulac_model(self.lattice.sentence)
        pku={}

        offset=0
        for w,t in result :
            pku[(offset,offset+len(w))]=t.encode()
            offset+=len(w)

        #result=[[int(b),int(e),tag.encode(),int(m)] for b,e,_,tag,m in result]
        #for b,e,tag,m in result:
        #    s=(b,e)
        #    if (s not in pku) or m < pku[s][1]:
        #        pku[s]=(tag,m)
        #pku={k:v[0]+(b'0' if v[1]==0 else b'1') for k,v in pku.items()}

        


        self.pku=[]
        for item in raw.items :
            b=int(item[0])
            e=int(item[1])
            word=item[2]
            if len(word)==1 :
                self.words_av.append(b'~')
                self.ae_inds.append([])
                #self.seq_mkcls.append(b'$')
            else:
                self.words_av.append(self.av.get(word,b'*'))
                self.ae_inds.append(self.ae.get(word,[b'*']))
            self.seq_mkcls.append(self.mkcls.get(word,b'*'))
            self.pku.append(pku.get((b,e),b'*'))

        #print(pku)
        #input()



        #print(raw)
        #print(self.seq_mkcls)

        #print(self.ae_inds)
        #input()
        #sentence=[x.encode() for x in self.lattice.sentence]
        #cb=[]
        #for i in range(len(sentence)):
        #    l2=sentence[i-2] if i-2 >=0 else b'#'
        #    l1=sentence[i-1] if i-1 >=0 else b'#'
        #    m=sentence[i]
        #    r1=sentence[i+1] if i+1<len(sentence) else b'#'
        #    r2=sentence[i+2] if i+2<len(sentence) else b'#'
        #    cb.append([b'u1'+l1,b'u2'+m,b'u3'+r1,
        #            b'b1'+l2+l1,b'b2'+l1+m,
        #            b'b3'+m+r1,b'b4'+r1+r2])

        #self.char_based=[]
        #for item in raw.items :
        #    b=item[0]
        #    e=item[1]
        #    word=item[2]
        #    tag=item[3].encode()
        #    if len(word)==1 :
        #        #self.char_based.append([b'CBs'+tag+f for f in cb[b]])
        #        self.char_based.append([b'CB2s'+f for f in cb[b]])
        #        #self.char_based.append([b'CBs'+tag+f for f in cb[b]]+
        #        #        [b'CB2s'+f for f in cb[b]])
        #    else :
        #        fv=[]
        #        #fv.extend([b'CBb'+tag+f for f in cb[b]])
        #        fv.extend([b'CB2b'+f for f in cb[b]])
        #        for j in range(b+1,e-1) :
        #            #fv.extend([b'CBm'+tag+f for f in cb[j]])
        #            fv.extend([b'CB2m'+f for f in cb[j]])
        #        #fv.extend([b'CBe'+tag+f for f in cb[e-1]])
        #        fv.extend([b'CB2e'+f for f in cb[e-1]])
        #        self.char_based.append(fv)

        #for item,fv in zip(raw.items,self.char_based):
        #    print(item[2],list(map(lambda x:x.decode(),fv)))
        #input()

    def gen_features(self,state,actions):
        fvs=[]
        state=self.State(state,self.lattice)
        ind1,ind2=state.w1,state.w0
        for action in actions :
            ind3=action
            if ind1==-1 :
                w1,t1=b'~',b'~'
                len1=b'0'
                f1,b1=b'~',b'~'
                m1=b''
                pku1=b'^'
            else :
                r=[(self.lattice.items[ind1][0],
                        self.lattice.items[ind1][2],
                        self.lattice.items[ind1][3]),
                        self.lattice.weights[ind1]]#raw[ind1]
                w1,t1=r[0][1].encode(),str(r[0][2]).encode()
                len1=str(len(r[0][1])).encode()
                f1,b1=r[0][1][0].encode(),r[0][1][-1].encode()
                m1=None if r[1] is None else r[1].encode()
                pku1=self.pku[ind1]
            if ind2==-1 :
                w2,t2=b'~',b'~'
                len2=b'0'
                f2,b2=b'~',b'~'
                m2=b''
                w2av=b''
                aeinds2=[]
                mkcls2=b''
                pku2=b'^'
            else :
                r=[(self.lattice.items[ind2][0],
                        self.lattice.items[ind2][2],
                        self.lattice.items[ind2][3]),
                        self.lattice.weights[ind2]]#raw[ind1]
                w2,t2=r[0][1].encode(),str(r[0][2]).encode()
                len2=str(len(r[0][1])).encode()
                f2,b2=r[0][1][0].encode(),r[0][1][-1].encode()
                m2=None if r[1] is None else r[1].encode()
                w2av=self.words_av[ind2]
                aeinds2=self.ae_inds[ind2]
                mkcls2=self.seq_mkcls[ind2]
                pku2=self.pku[ind2]
            if ind3==-1 :
                w3,t3=b'~',b'~'
                len3=b'0'
                f3,b3=b'~',b'~'
                m3=b''
                w3av=b''
                aeinds3=[]
                mkcls3=b''
                pku3=b'^'
                #cb3=[]
            else :
                r=[(self.lattice.items[ind3][0],
                        self.lattice.items[ind3][2],
                        self.lattice.items[ind3][3]),
                        self.lattice.weights[ind3]]#raw[ind1]

                w3,t3=r[0][1].encode(),str(r[0][2]).encode()
                len3=str(len(r[0][1])).encode()
                f3,b3=r[0][1][0].encode(),r[0][1][-1].encode()
                m3=None if r[1] is None else r[1].encode()
                w3av=self.words_av[ind3]
                aeinds3=self.ae_inds[ind3]
                #cb3=self.char_based[ind3]
                mkcls3=self.seq_mkcls[ind3]
                pku3=self.pku[ind3]

            fv=(([b'm3~'+m3,] if m3 is not None else [])+
                    ([b'm3m2~'+m3+b'~'+m2,] if m3 is not None  and m2 is not None else [])+
            [
                    b'w3~'+w3,
                    b't3~'+t3,
                    b'w3t3~'+w3+t3,
                    b'l3~'+len3,
                    b'l3l2~'+len3+b'~'+len2,
                    b'l3l2l1~'+len3+b'~'+len2+b'~'+len1,
                    b'w3l2~'+w3+b'~'+len2,
                    b'w3t3l2~'+w3+t3+b'~'+len2,
                    b'l3t3~'+len3+t3,
                    b'l3w2~'+len3+w2,
                    b'l3t2~'+len3+t2,
                    b'w3w2~'+w3+b"-"+w2,
                    b'w3t3w2~'+w3+t3+w2,
                    b'w3w2t2~'+w3+t2+w2,
                    b't3w2~'+t3+w2,
                    b'w3t2~'+w3+t2,
                    b't3t2~'+t3+t2,
                    b't3t1~'+t3+t1,
                    b't3t2t1~'+t3+t2+t1,

                    #pku
                    #b't3pku3~'+t3+b'~'+pku3,
                    #b't2pku3~'+t2+b'~'+pku3,
                    #b't3pku2~'+t3+b'~'+pku2,
                    #b'w2pku3~'+w2+b'~'+pku3,
                    #b'w3pku2~'+w3+b'~'+pku2,
                    
                    # av
                    #b'w3av~'+w3av,
                    #b't3w3av~'+t3+b'~'+w3av,
                    #b'w2avw3av~'+w2av+b'~'+w3av,
                    #b'w2avt3~'+w2av+b'~'+t3,
                    #b't2w3av~'+t2+b'~'+w3av,

                    #mkcls
                    #b'mk3~'+mkcls3,
                    #b't3mk3~'+t3+mkcls3,
                    #b't2mk3~'+t2+mkcls3,
                    #b't3mk2~'+t3+mkcls2,
                    #b't2mk2mk3~'+t2+mkcls2+b'~'+mkcls3,
                    #b't3mk2mk3~'+t3+mkcls2+b'~'+mkcls3,
                    ])

            #for aeind in aeinds3 :
            #    fv+=[ b't3aeind3'+t3+aeind,
            #            b't2aeind3'+t2+aeind, ]
            #for aeind in aeinds2 :
            #    fv+=[ b't3aeind2'+t3+aeind, ]

            #fv+=cb3
            #print(fv)
            fvs.append(fv)
        return fvs
    Eval=Eval
