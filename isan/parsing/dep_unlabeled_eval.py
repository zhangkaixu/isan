#!/usr/bin/python3

import time


class PRF :
    def __init__(self):
        self.std=0
        self.rst=0
        self.cor=0
    def __call__(self,std,rst):
        self.std+=len(std)
        self.rst+=len(rst)
        self.cor+=len(std&rst)
    def prf(self):
        self.p=0
        self.r=0
        self.f=0
        if self.std : self.r=self.cor/self.std
        if self.rst : self.p=self.cor/self.rst
        if self.p and self.r : self.f=self.p*self.r*2/(self.p+self.r)
    def __str__(self):
        self.prf()
        return ("""std: %d rst: %d cor: %d p: %.4f r: %.4f f: %.4f"""
                %(self.std,self.rst,self.cor,self.p,self.r,self.f))

class Eval:
    @staticmethod
    def make_color(s):
        return '\033[36;01m%s\033[1;m'%s #blue
    def __init__(self):
        self.std=0
        self.cor=0
        self.cmpl_std=0
        self.cmpl_cor=0
        self.non_root_std=0
        self.non_root_cor=0
        self.root_std=0
        self.root_cor=0
        self.start_time=time.time()
        self.base=PRF()
    def __call__(self,std_result,rst_result):
        raw=' '.join(x[0] for x in std_result)
        #print(raw)
        std=set((k,v[2]) for k,v in enumerate(std_result) if v[1]!='PU')
        kset=set(k for k,v in std)
        #rst=set((k,v) for k,v in enumerate(rst_result) if k in kset)
        rst=set((k,v[2]) for k,v in enumerate(rst_result) if v[1]!='PU')
        self.base(std,rst)
        
        #self.std+=sum(1 for s in std_result if s[1]!='PU')
        self.std+=len(std)
        self.cmpl_std+=1
        flag=True
        for s,r in zip(std_result,rst_result) : 
            if s[1]=='PU' : continue
            if s[2]!=-1 :
                self.non_root_std+=1
                if s[2]==r[2] : self.non_root_cor+=1
                else : flag=False
            else :
                self.root_std+=1
                if s[2]==r[2] : self.root_cor+=1
                else : flag=False
        if flag : self.cmpl_cor+=1
    def print_result(self):
        duration=time.time()-self.start_time
        #print(self.base)
        print("word正确率:\033[32;01m%.4f\033[1;m non-root正确率:%.4f root正确率:%.4f 整句正确率:%.4f 历时:%.2f 现时:%s"%(
                (self.root_cor+self.non_root_cor)/(self.non_root_std+self.root_std),
                self.non_root_cor/self.non_root_std,
                self.root_cor/self.root_std,
                self.cmpl_cor/self.cmpl_std,
                duration,
                time.strftime("%H:%M:%S")))
