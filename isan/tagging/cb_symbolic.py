import numpy
import pickle


class Tag_Bigram :
    def __init__(self,ts,paras,model=None):
        self.ts=ts
        self.paras=paras

        if model==None :
            self.trans=self.paras.add(numpy.zeros((self.ts,self.ts)))
            pass
        else :
            self.ts,self.trans=model

    
    
    def dump(self):
        return [self.ts,self.trans.output_obj()]

    def set_raw(self,*x):
        pass

    def cal_delta(self,std_tags,rst_tags,delta):
        trans_delta=self.trans*0
        for i in range(len(std_tags)-1):
            trans_delta[std_tags[i]][std_tags[i+1]]+=1
            trans_delta[rst_tags[i]][rst_tags[i+1]]-=1
        self.trans.add_delta(trans_delta)

    def transition(self,*_):
        return self.trans

class Character:
    def __init__(self,ts,paras,model=None,):
        self.paras=paras
        self.ts=ts
        self.uni_d={}
        self.bi_d={}

        self.uni_s={}
        self.bi_s={}

        if model==None :
            pass
        else :
            self.ts,self.uni_d,self.bi_d=model


    _new_vec=lambda self : numpy.zeros(self.ts,dtype=float)

    def add_model(self,model):
        self.ts,uni,bi=model
        new_vec=self._new_vec
        for k,v in uni.items():
            if k not in self.uni_d :
                self.uni_d[k]=[new_vec(),new_vec(),new_vec()]
                self.uni_s[k]=[new_vec(),new_vec(),new_vec()]
            for j in range(3):
                ind=numpy.abs(numpy.sign(v[j]))
                self.uni_d[k][j]=numpy.where(ind,
                        (self.uni_d[k][j]*self.uni_s[k][j]+v[j])/(self.uni_s[k][j]+1),
                        self.uni_d[k][j],)
                self.uni_s[k][j]+=ind
        for k,v in bi.items():
            if k not in self.bi_d :
                self.bi_d[k]=[new_vec(),new_vec(),new_vec(),new_vec()]
                self.bi_s[k]=[new_vec(),new_vec(),new_vec(),new_vec()]
            for j in range(4):
                ind=numpy.abs(numpy.sign(v[j]))
                self.bi_d[k][j]=numpy.where(ind,
                        (self.bi_d[k][j]*self.bi_s[k][j]+v[j])/(self.bi_s[k][j]+1),
                        self.bi_d[k][j],)
                self.bi_s[k][j]+=ind

    def dump(self):
        self.uni_d={k:[x.output_obj()for x in v] for k,v in self.uni_d.items()}
        self.bi_d={k:[x.output_obj()for x in v] for k,v in self.bi_d.items()}
        return [self.ts,self.uni_d,self.bi_d]

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


    def cal_delta(self,std_tags,rst_tags,delta):
        l=len(self.raw)
        dv=[self._new_vec() for i in range(len(std_tags))]
        for i in range(len(std_tags)) :
            dv[i][std_tags[i]]+=1
            dv[i][rst_tags[i]]-=1
        for i,k in enumerate(self.uni) :
            if chr(0) in k : continue # used for dropout
            if k not in self.uni_d : 
                self.uni_d[k]=[self.paras.add(self._new_vec()) for v in range(3)]
            v_para=self.uni_d[k]
            if i-2 >=0 :
                v_para[0].add_delta(dv[i-2])
            if i-1 >=0 and i-1<l: 
                v_para[1].add_delta(dv[i-1])
            if i<len(self.raw) :
                v_para[2].add_delta(dv[i])


        for i,k in enumerate(self.bi) :
            if chr(0) in k : continue # used for dropout
            if k not in self.bi_d : 
                self.bi_d[k]=[self.paras.add(self._new_vec()) for v in range(4)]
            v_para=self.bi_d[k]
            if i-3 >=0 :
                v_para[0].add_delta(dv[i-3])
            if i-2 >=0 and i-2<l: 
                v_para[1].add_delta(dv[i-2])
            if i-1 >=0 and i-1<l: 
                v_para[2].add_delta(dv[i-1])
            if i<l :
                v_para[3].add_delta(dv[i])

