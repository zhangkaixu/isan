
import collections
import isan.parsing.pushdown as pd

class Push_Down:
    def __init__(self,schema,beam_width):
        self.pushdown=pd.new(beam_width,schema.init,schema.shift,schema.reduce,
                schema.gen_features)
    def set_raw(self,raw):
        self.raw=raw

    def forward(self,get_step=lambda x:len(x)+1):
        c_rst=pd.search(self.pushdown,get_step(self.raw))
        return c_rst
