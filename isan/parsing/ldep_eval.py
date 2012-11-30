#!/usr/bin/python3

import time

class Eval:
    @staticmethod
    def make_color(s):
        return '\033[36;01m%s\033[1;m'%s #blue
    def __init__(self):
        self.dep_src=[0,0,0]
        self.tag_src=[0,0,0]
        self.seg_src=[0,0,0]
        self.std=0
        self.cor=0
        self.non_root_std=0
        self.non_root_cor=0
        self.root_std=0
        self.root_cor=0
        self.start_time=time.time()
    def cal_src(self,s1,s2,src) :
        src[0]+=len(s1)
        src[1]+=len(s2)
        src[2]+=len(s1&s2)
        return 
    def __call__(self,std_result,rst_result):
        rst=rst_result
        #rst=set()
        #for s,d in rst_result :
        #    s=std_result[s][0]
        #    d=std_result[d][0]
        #    r=(s[:3],s[3],d)
        #    rst.add(r)
        #print(rst)
        #input()
        std=[(x[0][:3],x[0][3],x[1]['dep'][1]) for x in std_result if 'dep' in x[1]]
        std=set(std)
        self.cal_src({(w,d[:3] if d else None) for w,t,d in std},
                {(w,d[:3] if d else None) for w,t,d in rst},
                self.dep_src)
        std=set(x[:2] for x in std)
        rst=set(x[:2] for x in rst)
        self.cal_src(std,rst,self.tag_src)
        std=set(x[:1] for x in std)
        rst=set(x[:1] for x in rst)
        self.cal_src(std,rst,self.seg_src)



        return
        raw=' '.join(x[0] for x in std_result)
        #print(raw)
        self.std+=sum(1 for s in std_result if s[1]!='PU')
        for s,r in zip(std_result,rst_result) : 
            if s[1]=='PU' : continue
            if s[2]!=-1 :
                self.non_root_std+=1
                if s[2]==r : self.non_root_cor+=1
            else :
                self.root_std+=1
                if s[2]==r : self.root_cor+=1
        pass
    def print_src(self,src):
        std,rst,cor=src
        p=cor/rst
        r=cor/std
        f=2*p*r/(p+r)
        print(std,rst,cor,p,r,f)
    def print_result(self):
        duration=time.time()-self.start_time
        print(duration)
        self.print_src(self.dep_src)
        self.print_src(self.tag_src)
        self.print_src(self.seg_src)

        return
        print("std:%d non-root正确率:\033[32;01m%.4f\033[1;m root正确率:\033[32;01m%.4f\033[1;m 历时:%.2f 现时:%s"%(
                self.std,
                self.non_root_cor/self.non_root_std,
                self.root_cor/self.root_std,
                duration,
                time.strftime("%H:%M:%S")))

class Eval_With_Result(Eval) :
    pass
if __name__ == '__main__':
    pass


