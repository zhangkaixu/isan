#!/usr/bin/python3

import time

class Eval:
    @staticmethod
    def make_color(s):
        return '\033[36;01m%s\033[1;m'%s #blue
    def __init__(self):
        self.std=0
        self.cor=0
        self.start_time=time.time()
    def __call__(self,std_result,rst_result):
        std_result=[ind for _,_,ind,_ in std_result]
        self.std+=len(std_result)
        self.cor+=sum(1 if s==r else 0 for s,r in zip(std_result,rst_result))
        pass
    def print_result(self):
        duration=time.time()-self.start_time
        print("std:%d rst:%d 正确率:\033[32;01m%.4f\033[1;m 历时:%.2f 现时:%s"%(
                self.std,
                self.cor,
                self.cor/self.std,
                duration,
                time.strftime("%H:%M:%S")))

if __name__ == '__main__':
    pass


