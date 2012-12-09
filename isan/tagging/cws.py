from struct import Struct
import isan.tagging.eval as tagging_eval
#import isan.tagging.cwstask as cwstask


class Task:
    """ 介绍一下这个最基本的task--中文分词吧

    来看看如何建造一个中文分词模型
    只需要编写最核心的代码，其它代码我都已经编好了

    :py:attr:`name`

    :py:func:`init`

    :py:func:`shift` and
    :py:func:`reduce`

    """
    xa,xb=3,3
    name='中文分词' ##name
    
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

    def moves_to_result(self,moves,raw):
        """
        告诉isan，有了输入和动作序列，输出该是什么
        """
        actions=list(zip(*moves))[2]
        #print(actions)
        last_sep=0
        sen=[]
        for i,a in enumerate(actions[1:]):
            if a==self.sep or i==len(actions)-2:
                sen.append(raw[last_sep:i+1])
                last_sep=i+1
        return sen
    

    def result_to_moves(self,y) :
        def _gen_actions_and_stats(stat):
            ind,last,_,wordl,lwordl=self.stat_fmt.unpack(stat)
            return [(self.sep,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                    (self.com,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
        actions=sum(([self.com]*(len(w)-1)+[self.sep] for w in y),[self.sep])
        states=[]
        stat=self.init_stat
        for action in actions:
            states.append(stat)
            for a,s in _gen_actions_and_stats(stat):
                if action==a:
                    stat=s
        states.append(stat)

        moves=[(i,states[i],actions[i])for i in range(len(actions))]

        return moves


    stat_fmt=Struct('hcchh')
    """
    在isan中，状态是一个bytes对象，但Python中tuple好处理一些，
    在此规定一种从tuple到bytes对象的转换规则
    """

    init_stat=stat_fmt.pack(*(0,b'0',b'0',0,0))
    """分词搜索时的初始状态"""

    def get_init_states(self) :
        return [self.init_stat]

    def shift(self,last_ind,stat):
        """
        根据当前状态，能产生什么动作，并且后续的状态是什么，就由这个函数决定了
        """
        ind,last,_,wordl,lwordl=self.stat_fmt.unpack(stat)
        next_ind=last_ind+1 if last_ind+1 <= len(self.raw) else -1
        return [(self.sep,next_ind,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                (self.com,next_ind,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
    reduce=None

    def check(self,std_moves,rst_moves):
        return all(
                std_move[2]==rst_move[2]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )

    def update_moves(self,std_moves,rst_moves) :
        for move in std_moves :
            yield move, 1
        for move in rst_moves :
            yield move, -1
        pass

    def init(self):
        """
        分词搜索时的初始状态
        """
        #self.init_stat,self.shift,self.gen_features=cwstask.new()
        #self.init_stat,self.gen_actions_and_stats,_=cwstask.new()
        pass

    """
    stuffs about the early update
    """
    def set_oracle(self,raw,y) :
        return self.result_to_moves(y)

    def remove_oracle(self):
        pass

    """
    stuffs about the feature generation
    """
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


    def gen_features(self,span,actions):
        fvs=[]
        fv=self.gen_features_one(span)
        for action in actions:
            action=chr(action).encode()
            fvs.append([action+x for x in fv])
        return fvs

    def gen_features_one(self,span):
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

    Eval=tagging_eval.TaggingEval
    """
    最后告诉isan，如何评价模型的输出和标准答案的输出的好坏。具体可以看这个class
    """


    """
    用于生成lattice
    """
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
