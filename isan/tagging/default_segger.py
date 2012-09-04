from struct import Struct
import isan.tagging.eval as tagging_eval


"""
You do the best, we do the rest!

来看看如何建造一个中文分词模型
只需要编写最核心的代码，其它代码我都已经编好了
"""
class Segger:
    class codec:
        @staticmethod
        def decode(line):
            if not line: return []
            seq=[word for word in line.split()]
            raw=''.join(seq)
            return {'raw':raw,
                    'y':seq,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        def encode():
            pass


    sep=11
    com=22
    def actions_to_result(self,actions,raw):
        last_sep=0
        sen=[]
        for i,a in enumerate(actions[1:]):
            if a==self.sep or i==len(actions)-2:
                sen.append(raw[last_sep:i+1])
                last_sep=i+1
        return sen
    
    def result_to_actions(self,y):
        return sum(([self.com]*(len(w)-1)+[self.sep] for w in y),[self.sep])


    stat_fmt=Struct('hcch')
    init_stat=stat_fmt.pack(*(0,b'0',b'0',0))

    def set_Y(self,Y):
        pass

    def gen_actions_and_stats(self,stat):
        ind,last,_,wordl=self.stat_fmt.unpack(stat)
        return [(self.sep,self.stat_fmt.pack(ind+1,b's',last,1)),
                (self.com,self.stat_fmt.pack(ind+1,b'c',last,wordl+1))]

    def set_raw(self,raw):
        self.raw=raw
        self.uni_chars=list(x.encode() for x in '###'+raw+'##')
        self.bi_chars=[self.uni_chars[i]+self.uni_chars[i+1]
                for i in range(len(self.uni_chars)-1)]

    def gen_features(self,span):
        span=self.stat_fmt.unpack(span)
        uni_chars=self.uni_chars
        bi_chars=self.bi_chars

        c_ind=span[0]+2
        ws_current=span[1]
        ws_left=span[2]
        w_current=self.raw[span[0]-span[3]:span[0]]

        fv=[ 
                b'0'+ws_current+ws_left,
                b"1"+uni_chars[c_ind]+ws_current,
                b"2"+uni_chars[c_ind+1]+ws_current,
                b'3'+uni_chars[c_ind-1]+ws_current,
                b"a"+bi_chars[c_ind]+ws_current,
                b"b"+bi_chars[c_ind-1]+ws_current,
                b"c"+bi_chars[c_ind+1]+ws_current,
                b"d"+bi_chars[c_ind-2]+ws_current,
                b"w"+w_current.encode(),
                ]
        return fv
    Eval=tagging_eval.TaggingEval
