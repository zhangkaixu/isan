#!/usr/bin/python3

import time

class Eval:
    @staticmethod
    def make_color(s):
        return '\033[36;01m%s\033[1;m'%s #blue
    def __init__(self):
        self.std=0
        self.cor=0
        self.non_root_std=0
        self.non_root_cor=0
        self.root_std=0
        self.root_cor=0
        self.start_time=time.time()
    def __call__(self,std_result,rst_result):
        #std_result=[ind for _,_,ind,_ in std_result]
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
    def print_result(self):
        duration=time.time()-self.start_time
        print("std:%d non-root正确率:\033[32;01m%.4f\033[1;m root正确率:\033[32;01m%.4f\033[1;m 历时:%.2f 现时:%s"%(
                self.std,
                self.non_root_cor/self.non_root_std,
                self.root_cor/self.root_std,
                duration,
                time.strftime("%H:%M:%S")))

if __name__ == '__main__':
    pass


