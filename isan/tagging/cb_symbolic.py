import numpy
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
            self.ts,self.uni_d,self.bi_d=model

    def add_model(self,model):
        self.ts,uni,bi=model
        for k,v in uni.items():
            if k not in self.uni_d :
                self.uni_d[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float)]
                self.uni_s[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float)]
            for j in range(3):
                for i in range(len(self.uni_d[k][j])):
                    if v[j][i]==0 : continue
                    self.uni_d[k][j][i]=(self.uni_d[k][j][i]*self.uni_s[k][j][i]+v[j][i])/(self.uni_s[k][j][i]+1)
                    self.uni_s[k][j][i]+=1
        for k,v in bi.items():
            if k not in self.bi_d :
                self.bi_d[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float)]
                self.bi_s[k]=[numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float),numpy.zeros(self.ts,dtype=float),
                    numpy.zeros(self.ts,dtype=float)]
            for j in range(4):
                for i in range(len(self.bi_d[k][j])):
                    if v[j][i]==0 : continue
                    self.bi_d[k][j][i]=(self.bi_d[k][j][i]*self.bi_s[k][j][i]+v[j][i])/(self.bi_s[k][j][i]+1)
                    self.bi_s[k][j][i]+=1

    def dump(self):
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


    def update(self,std_tags,rst_tags,delta,step):
        l=len(self.raw)
        for i,k in enumerate(self.uni) :
            #if chr(0) in k : continue
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
            #if chr(0) in k : continue
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
