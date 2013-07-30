import isan.common.pushdown as pushdown
import isan.common.dfabeam as dfabeam
import isan.common.first_order_linear as first_order_linear


class Searcher:
    def set_action(self,d):
        self.searcher.set_action(self.handler,d)
    def set_step(self,step):
        self.searcher.set_step(self.handler,step)
    def get_states(self):
        return self.searcher.get_states(self.handler)
    def set_raw(self,raw):
        self.raw=raw
        if self.do_set_raw :
            self.searcher.set_raw(self.handler,raw)
    def __del__(self):
        self.searcher.delete(self.handler)
    def search(self):
        x=self.searcher.search(self.handler,self.get_init_states())
        return x

    def __init__(self,schema,beam_width):
        self.do_set_raw=True
        if hasattr(schema,'do_not_set_raw_for_searcher') : self.do_set_raw=False
        self.get_init_states=schema.get_init_states
        self.handler=self.searcher.new(
                beam_width,
                schema.early_stop if hasattr(schema,'early_stop') else None,
                schema.shift,
                schema.reduce,
                schema.gen_features,
                )

class DFA(Searcher):
    name='状态转移'
    searcher=dfabeam
class Push_Down(Searcher):
    name='Shift-Reduce'
    searcher=pushdown
class First_Order_Linear(Searcher):
    name='first order linear'
    searcher=first_order_linear
    def cal_margins(self):
        return self.searcher.cal_margins(self.handler)
    def __init__(self,schema,beam_width):
        self.get_init_states=schema.get_init_states
        self.do_set_raw=True
        self.handler=self.searcher.new(
                1,
                schema.emission,
                schema.transition
                )
    def update_action(self,move,delta,step):
        self.searcher.update_action(self.handler,move[2],delta,step)
