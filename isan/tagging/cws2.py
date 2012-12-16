from struct import Struct
import isan.tagging.eval as tagging_eval
import isan.data.lattice
from isan.common.lattice import Lattice_Task as Base_Task
#import isan.tagging.cwstask as cwstask


class CWS_Lattice (isan.data.lattice.Data) :
    @staticmethod
    def load_from_string(line):
        data=[]
        offset=0
        for w in line.split():
            item={'key':(offset,offset+1,w[0]),'gold':'s'}
            data.append(item)
            for i in range(1,len(w)):
                item={'key':(offset+i,offset+i+1,w[i]),'gold':'c'}
                data.append(item)
            offset+=len(w)
        data.append({'key':(offset,offset+1,''),'gold':'s'})
        return data
    def __init__(self,line):
        print(line)
    
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
        data=CWS_Lattice.load_from_string(line)
        raw2=CWS_Lattice.to_train(data)
        
        seq=[word for word in line.split()]
        raw=''.join(seq)
        return {'raw':raw2,#raw,
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
    @staticmethod
    def result_to_arcs(result):
        arcs=[]
        for w in result:
            arcs.append('s')
            for i in range(1,len(w)):arcs.append('c')
        arcs.append('s')
        return arcs

    @staticmethod
    def arcs_to_result(arcs,lattice):
        last_sep=0
        sen=[]
        for i,a in enumerate(arcs[1:]):
            if a=='s' or i==len(arcs)-2:
                sen.append(lattice.sentence[last_sep:i+1])
                last_sep=i+1
        return sen

class Action :
    sep=11
    com=22
    number_to_string={sep:'s',com:'c'}
    string_to_number={v:k for k,v in number_to_string.items()}

    @staticmethod
    def parse_action(action):
        return True,action

    @staticmethod
    def actions_to_arcs(actions):
        arcs=list(map(lambda x:Action.number_to_string[x],actions))
        return arcs
    @staticmethod
    def arcs_to_actions(arcs):
        actions=list(map(lambda x:Action.string_to_number[x],arcs))
        return actions

class State(Action):
    stat_fmt=Struct('hcchh')
    init_stat=stat_fmt.pack(*(0,b'0',b'0',0,0))

    @staticmethod
    def load(bt):
        span=State.stat_fmt.unpack(bt)
        return span

    def __init__(self,bt,lattice):
        self.data=State.load(bt)
        self.span=[self.data[0]-1,self.data[0]]
        self.lattice=lattice
        self.stop_step=self.lattice.length+1
    def shift(self,shift_ind):
        ind,last,_,wordl,lwordl=self.data
        next_ind=ind+1
        if next_ind==self.stop_step : next_ind=-1
        rtn= [(self.sep,next_ind,self.stat_fmt.pack(ind+1,b'1',last,1,wordl)),
                (self.com,next_ind,self.stat_fmt.pack(ind+1,b'2',last,wordl+1,lwordl))]
        return rtn


class Task (Base_Task):
    name='中文分词' ##name
    
    Action=Action
    State=State
    codec=codec
    Eval=tagging_eval.TaggingEval

    reduce=None

    def update_moves(self,std_moves,rst_moves) :
        for move in std_moves :
            yield move, 1
        for move in rst_moves :
            yield move, -1
        pass

    """
    stuffs about the early update
    """
    early_stop=None


    """
    stuffs about the feature generation
    """
    def set_raw(self,raw,_):
        """
        这个函数用来在每次新到一个输入的时候，做一些预处理，一般为了加快特征向量生成的速度
        """
        self.lattice=raw
        raw=''.join(x[2] for x in raw.items)
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

        span=self.State.load(span)
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

