import sys
import isan.common.perceptrons as perceptrons
from isan.parsing.push_down import Push_Down
from isan.parsing.default_dep import Dep



class Decoder:
    def __init__(self,parser=Dep(),beam_width=8):
        self.parser=parser
        self.beam_width=beam_width#搜索柱宽度
        self.actions={}
        self.link()
    def link(self):
        self.init=self.parser.init
        self.actions_to_result=self.parser.actions_to_result
        self.result_to_actions=self.parser.result_to_actions
        self.set_raw=self.parser.set_raw
        self.gen_features=self.parser.gen_features
        self.actions_to_stats=self.parser.actions_to_stats
        self.shift=self.parser.shift
        self.reduce=self.parser.reduce
        self.Eval=self.parser.Eval
        self.codec=self.parser.codec

        self.push_down=Push_Down(self,self.beam_width)

    def unlink(self):
        self.push_down=None
        self.init=None
        self.actions_to_result=None
        self.result_to_actions=None
        self.set_raw=None
        self.gen_features=None
        self.actions_to_stats=None
        self.shift=None
        self.reduce=None
        self.Eval=None
        self.codec=None


    def update(self,x,std_actions,rst_actions,step):
        length=self._update_actions(std_actions,1,step)
        length=self._update_actions(rst_actions,-1,step)
    ### 私有函数 
    def _update_actions(self,actions,delta,step):
        length=0
        for stat,action in zip(self.actions_to_stats(actions),actions):
            fv=self.gen_features(stat)
            if action not in self.actions:
                self.actions.new_action(action)
            self.actions[action].updates(fv,delta,step)
            length+=1
        return length
    def average(self,steps):
        for v in self.actions.values():
            v.average(steps)
    def search(self,raw,_=None):
        self.set_raw(raw)
        self.push_down.set_raw(raw)
        res=self.push_down.forward(lambda x:2*len(x)-1)
        return res

Model=perceptrons.Base_Model
