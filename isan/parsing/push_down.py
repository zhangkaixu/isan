import isan.parsing.pushdown as pd

class Push_Down:
    def __init__(self,schema,beam_width):
        self.pushdown=pd.new(beam_width,schema.init,schema.shift,schema.reduce,
                schema.gen_features)
    def set_raw(self,raw):
        self.raw=raw

    def search(self):
        c_rst=pd.search(self.pushdown,2*len(self.raw)-1)
        return c_rst
    
    def update_action(self,stat,action,delta,step):
        pd.update_action(self.pushdown,stat,action,delta,step)

