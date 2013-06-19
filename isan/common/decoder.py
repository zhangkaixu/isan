import isan.common.pushdown as pushdown
import isan.common.dfabeam as dfabeam


class Searcher:
    def set_action(self,d):
        self.searcher.set_action(self.handler,d)
    def set_step(self,step):
        self.searcher.set_step(self.handler,step)
    def set_penalty(self,penalty,value=0):
        self.searcher.set_penalty(self.handler,penalty,value)
    def set_weights(self,weights):
        self.searcher.set_weights(self.handler,weights)
    def export_weights(self):
        return self.searcher.export_weights(self.handler)
    def average_weights(self,step):
        self.searcher.average_weights(self.handler,step)
    def sum_weights(self,stat,action):
        return self.searcher.sum_weights(self.handler,stat,action)
    def un_average_weights(self):
        self.searcher.un_average_weights(self.handler)
    def update_action(self,move,delta,step):
        self.searcher.update_action(self.handler,move[1],move[2],delta,step)
    def make_dat(self):
        self.searcher.make_dat(self.handler)
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
