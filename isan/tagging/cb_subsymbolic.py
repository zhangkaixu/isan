import numpy
import gzip
import pickle

class Mapper():
    """
    auto-encoder
    """
    def __init__(self,ts,data=None,args={}):
        self.ts=ts
        self.added=False
        if data==None :
            #load lookup tables for character unigrams and bigrams
            chs={}
            for line in open(args['unigram']):
                ch,*v=line.split()
                v=list(map(float,v))[:20]
                chs[ch]=numpy.array([v])

            for line in open(args['bigram']):
                b,*v=line.split()
                v=list(map(float,v))[:50]
                chs[b]=numpy.array([v])
            self.chs=chs
            self.zch=numpy.array([[0.0 for i in range(20)]])
            self.zb=numpy.array([[0.0 for i in range(50)]])

            # load weights for the hidden layer
            f=gzip.open(args['hidden'],'rb')
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

            size=self.bs[0].shape[0]
            self.size=size
            self.second_d=numpy.zeros((self.ts,size))
            self.second_s=numpy.zeros((self.ts,size))
        else :
            self.second_d,self.chs,self.zch,self.zb,self.Ws,self.bs=data

    def add_model(self,model):
        if self.added : return
        self.second_d,_,_,_,Ws,bs=model
        for i in range(len(self.Ws)):
            self.Ws[i]=(self.Ws[i]*self.sWs[i]+Ws[i])/(self.sWs[i]+1)
            self.sWs[i]+=1
            self.bs[i]=(self.bs[i]*self.sbs[i]+bs[i])/(self.sbs[i]+1)
            self.sbs[i]+=1
        self.added=True

    def dump(self):
        return [self.second_d,self.chs,self.zch,self.zb,self.Ws,self.bs]
    def load(self,data):
        self.second_d,self.chs,self.zch,self.zb,self.Ws,self.bs=data

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
        inds[0]=0
        inds[1]=0
        inds[2]=0
        inds[3]=0
        inds[6]=0
        return inds,vs


    def __call__(self,context): # call
        inds,vs=self.get_data(context)
        self.indss.append(inds)
        self.vss.append(vs)

        if all(x==0 for x in inds):
            return numpy.zeros(self.size)

        #hidden layer
        la=[]
        la=numpy.zeros(self.size,dtype=float)
        for ind,v,W,b in zip(inds,vs,self.Ws,self.bs):
            if ind ==0 : continue
            la+=numpy.dot(v,W)[0]+b
        la=1/(1+numpy.exp(-la))
        return la

    def update(self,std_tags,rst_tags,delta,step):

        #"""#hidden
        self.dWs=[]
        for x in self.Ws : self.dWs.append(x*0)
        self.dbs=[]
        for x in self.bs : self.dbs.append(x*0)

        for i in range(len(self.conv)):
            if std_tags[i]==rst_tags[i] : continue
            deltas=(self.second_d[std_tags[i]]-self.second_d[rst_tags[i]])*self.conv[i]*(1-self.conv[i])
            self.update_hidden(i,deltas)

        for i in range(len(self.Ws)):
            self.Ws[i]+=self.dWs[i]
            self.sWs[i]+=self.dWs[i]*step
            self.bs[i]+=self.dbs[i]
            self.sbs[i]+=self.dbs[i]*step
        #"""

        #output
        for i in range(len(self.conv)):
            if std_tags[i]==rst_tags[i] : continue
            self.second_d[std_tags[i]]+=delta*self.conv[i]
            self.second_d[rst_tags[i]]-=delta*self.conv[i]

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

        self.second_b=self.second_d.copy()
        self.second_d-=self.second_s/step

    def un_average_weights(self):
        for i in range(len(self.Ws)):
            self.Ws[i]=numpy.array(self._backWs[i])
            self.bs[i]=numpy.array(self._backbs[i])
        self.second_d=self.second_b.copy()



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
            emissions[i]+=numpy.dot(self.second_d,self.conv[i])

class PCA :
    def __init__(self,ts,data=None,args={}):
        self.ts=ts
        if data==None :
            self.bi={}
            for line in open(args['bigram']):
                bi,*v=line.split()
                v=list(map(float,v))[:30]
                size=len(v)
                self.bi[bi]=numpy.array(v) # bigram embedding

            self.d=[numpy.zeros((self.ts,size)) for j in range(4)] # [pos][tag]
            self.s=[numpy.zeros((self.ts,size)) for j in range(4)] # [pos][tag]
        else :
            self.ts,self.bi,self.d=data

    def dump(self):
        return [self.ts,self.bi,self.d]

    def load(self,data):
        self.ts,self.bi,self.d=data

    def add_model(self,model):
        self.ts,_,d=model
        if type(self.s)==list :
            self.d=d
            self.s=1
        else :
            for i in range(len(self.d)):
                self.d[i]=(self.d[i]*self.s+d[i])/(self.s+1)
            self.s+=1

    def set_raw(self,raw):
        self.raw=raw
        self.bis=[]
        for ind in range(len(raw)-1):
            big=raw[ind:ind+2]
            self.bis.append(self.bi.get(big,None))
    def emission(self,emissions):
        for i in range(len(self.raw)-1):
            if self.bis[i]!=None:
                x=numpy.dot(self.d[0],self.bis[i])
                emissions[i]+=x
        for i in range(1,len(self.raw)):
            if self.bis[i-1]!=None:
                x=numpy.dot(self.d[1],self.bis[i-1])
                emissions[i]+=x
        """
        for i in range(len(self.raw)-2):
            if self.bis[i+1]!=None:
                x=numpy.dot(self.d[2],self.bis[i+1])
                emissions[i]+=x
        for i in range(2,len(self.raw)):
            if self.bis[i-2]!=None:
                x=numpy.dot(self.d[3],self.bis[i-2])
                emissions[i]+=x#"""
    def update(self,std_tags,rst_tags,delta,step):

        for i in range(len(self.raw)-1):
            if std_tags[i]==rst_tags[i] or self.bis[i]==None : continue
            d=delta*self.bis[i]
            self.d[0][std_tags[i]]+=d
            self.d[0][rst_tags[i]]-=d
            d=d*step
            self.s[0][std_tags[i]]+=d
            self.s[0][rst_tags[i]]-=d

        for i in range(1,len(self.raw)):
            if std_tags[i]==rst_tags[i] or self.bis[i-1]==None : continue
            d=delta*self.bis[i-1]
            self.d[1][std_tags[i]]+=d
            self.d[1][rst_tags[i]]-=d
            d*=step
            self.s[1][std_tags[i]]+=d
            self.s[1][rst_tags[i]]-=d
        """
        for i in range(len(self.raw)-2):
            if std_tags[i]==rst_tags[i] or self.bis[i+1]==None : continue
            d=delta*self.bis[i+1]
            self.d[2][std_tags[i]]+=d
            self.d[2][rst_tags[i]]-=d
            d=d*step
            self.s[2][std_tags[i]]+=d
            self.s[2][rst_tags[i]]-=d
        for i in range(2,len(self.raw)):
            if std_tags[i]==rst_tags[i] or self.bis[i-2]==None : continue
            d=delta*self.bis[i-2]
            self.d[3][std_tags[i]]+=d
            self.d[3][rst_tags[i]]-=d
            d*=step
            self.s[3][std_tags[i]]+=d
            self.s[3][rst_tags[i]]-=d#"""

    def average_weights(self,step):
        self.b=[x.copy()for x in self.d]
        for d,s in zip(self.d,self.s):
            d-=s/step

    def un_average_weights(self):
        self.d=[x.copy()for x in self.b]
