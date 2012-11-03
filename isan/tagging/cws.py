from struct import Struct
import isan.tagging.eval as tagging_eval
import isan.tagging.cwstask as cwstask


"""
You do the best, we do the rest!

来看看如何建造一个中文分词模型
只需要编写最核心的代码，其它代码我都已经编好了
"""
class Task:
    xa,xb=3,3
    """告诉isan，这是个什么task"""
    name='中文分词'
    
    class codec:
        """
        任务的输入和输出是什么，如何从数据文件中获得
        """
        @staticmethod
        def decode(line):
            """
            编码、解码
            从一行文本中，得到输入（raw）和输出（y）
            """
            if not line: return []
            seq=[word for word in line.split()]
            raw=''.join(seq)
            return {'raw':raw,
                    'y':seq,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        @staticmethod
        def encode(y):
            return ' '.join(y)
        @staticmethod
        def candidates_encode(y):
            return ' '.join(str(i[0])+'_'+i[1]+('_'+str(s)) for i,s in y)

    """
    下面不妨给动作（一个unsigned char类型）定义一下名字
    分词中有两个动作：断与连
    """
    sep=11
    com=22

    def actions_to_result(self,actions,raw):
        """
        告诉isan，有了输入和动作序列，输出该是什么
        """
        last_sep=0
        sen=[]
        for i,a in enumerate(actions[1:]):
            if a==self.sep or i==len(actions)-2:
                sen.append(raw[last_sep:i+1])
                last_sep=i+1
        return sen
    
    def result_to_actions(self,y):
        """
        有了输出，需要怎样的动作序列才能得到
        """
        return sum(([self.com]*(len(w)-1)+[self.sep] for w in y),[self.sep])

    """
    在isan中，状态是一个bytes对象，但Python中tuple好处理一些，
    在此规定一种从tuple到bytes对象的转换规则
    """
    stat_fmt=Struct('hcchh')
    """分词搜索时的初始状态"""
    init_stat=stat_fmt.pack(*(0,b'0',b'0',0,0))

    def gen_actions_and_stats(self,ind,stat):
        """
        根据当前状态，能产生什么动作，并且后续的状态是什么，就由这个函数决定了
        """
        ind,last,_,wordl,lwordl=self.stat_fmt.unpack(stat)
        next_ind=ind+1 if ind+1 <= len(self.raw) else -1
        #print(ind,self.raw,next_ind)
        return [(self.sep,next_ind,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                (self.com,next_ind,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]

    def init(self):
        """
        分词搜索时的初始状态
        """
        self.init_stat,self.gen_actions_and_stats,self.gen_features=cwstask.new()
        #self.set_raw=
        #self.init_stat,self.gen_actions_and_stats,_=cwstask.new()
        pass

    def actions_to_stats(self,raw,actions):
        """
        维特比解码中，状态根据动作而转移，
        有了动作序列，就能确定一个状态序列
        """
        stat=self.init_stat
        for action in actions:
            yield stat
            for a,s in self._gen_actions_and_stats(stat):
                if action==a:
                    stat=s
        yield stat
    ## stuffs about the early update
    def set_oracle(self,raw,y) :
        std_actions=self.result_to_actions(y)#得到标准动作
        return std_actions
    #def early_stop(self,step,last_states,actions,next_states):
    #    return False
    #    if (not hasattr(self,"std_states")) or (not self.std_states) : return False
    #    for last_state,action,next_state in zip(last_states,actions,next_states):
    #        if last_state==b'': return False
    #        action=chr(action)
    #        if next_state == self.std_states[step] : 
    #            if step==0 or last_state==self.std_states[step-1] :
    #                return False
    #    return True
    def remove_oracle(self):
        pass

    def _gen_actions_and_stats(self,stat):
        """
        根据当前状态，能产生什么动作，并且后续的状态是什么，就由这个函数决定了
        """
        ind,last,_,wordl,lwordl=self.stat_fmt.unpack(stat)
        return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                (self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
    def set_raw(self,raw,_):
        """
        这个函数用来在每次新到一个输入的时候，做一些预处理，一般为了加快特征向量生成的速度
        """
        self.raw=raw
        uni_chars=list(x.encode() for x in '###'+raw+'##')
        bi_chars=[uni_chars[i]+uni_chars[i+1]
                for i in range(len(uni_chars)-1)]
        self.uni_chars=uni_chars
        self.uni_fv=[]
        for ind in range(len(raw)+1):
            c_ind=ind+2
            self.uni_fv.append([])
            for ws_current in [b'0',b'1',b'2']:
                self.uni_fv[-1].append([
                    b"1"+uni_chars[c_ind]+ws_current,
                    b"2"+uni_chars[c_ind+1]+ws_current,
                    b'3'+uni_chars[c_ind-1]+ws_current,
                    b"a"+bi_chars[c_ind]+ws_current,
                    b"b"+bi_chars[c_ind-1]+ws_current,
                    b"c"+bi_chars[c_ind+1]+ws_current,
                    b"d"+bi_chars[c_ind-2]+ws_current,
                ])


    def gen_features(self,span):
        """
        告诉isan，一个状态能生成哪些特征向量，每个特征也是一个bytes类型，且其中不能有0
        """
        span=self.stat_fmt.unpack(span)
        ind,ws_current,ws_left,sep_ind,sep_ind2=span

        w_current=self.raw[ind-sep_ind:ind]
        w_last=self.raw[ind-sep_ind-sep_ind2:ind-sep_ind]
        w_c_len=chr(len(w_current)+1).encode()
        w_l_len=chr(len(w_last)+1).encode()
        w_l=b' '
        w_r=b' '
        w2_l=b' '
        w2_r=b' '
        if(len(w_current)>0):
            w_l=w_current[0].encode()
            w_r=w_current[-1].encode()
        if(len(w_last)>0):
            w2_l=w_last[0].encode()
            w2_r=w_last[-1].encode()

        fv=(self.uni_fv[ind][ws_current[0]-48]+
                [ 
                b"0"+ws_current+ws_left,
                b"w"+w_current.encode(),
                b"l"+w_c_len,

                b"lw0"+w_l+w_c_len,
                b"lw-1"+w_r+w_c_len,

                b"w_0w_-1"+w_l+w_r,
                b"w2_-1w_-1"+w2_r+w_r,
                b"w_0c"+w_l+self.uni_chars[ind+3],
                b"w_-1c"+w_r+self.uni_chars[ind+3],

                b"wl2"+w_current.encode()+w_l_len,
                b"w2l"+w_last.encode()+w_c_len,
                ]
                )
        return fv
    """
    最后告诉isan，如何评价模型的输出和标准答案的输出的好坏。具体可以看这个class
    """
    Eval=tagging_eval.TaggingEval

    def gen_candidates(self,states,threshold=10):
        threshold=threshold*1000
        raw=self.raw
        cands={}
        for state,score in states :
            ind,last,_,sep_ind,sep_ind2=self.stat_fmt.unpack(state)
            w_current=self.raw[ind-sep_ind:ind]
            w_last=self.raw[ind-sep_ind-sep_ind2:ind-sep_ind]
            if not w_last : continue
            key=(ind-sep_ind-sep_ind2,w_last)
            if key not in cands or cands[key]<score :
                cands[key]=score
        
        s=max(cands.values())
        cands=list((k,v-s)for k,v in cands.items() if v+threshold>s)
        cands.sort()
        return cands
