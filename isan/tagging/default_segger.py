from struct import Struct
class Segger:
    stat_fmt=Struct('HccH')
    init_stat=stat_fmt.pack(*(0,b'0',b'0',0))

    def actions_to_result(self,actions,raw):
        sen=[]
        cache=''
        for c,a in zip(raw,actions[1:]):
            cache+=c
            if a=='s':
                sen.append(cache)
                cache=''
        if cache:
            sen.append(cache)
        return sen
    def result_to_actions(self,y):
        actions=['s']
        for w in y:
            for i in range(len(w)-1):
                actions.append('c')
            actions.append('s')
        return actions



    def gen_actions_and_stats(self,stat):
        ind,last,_,wordl=self.stat_fmt.unpack(stat)
        return [('s',self.stat_fmt.pack(ind+1,b's',last,1)),
                ('c',self.stat_fmt.pack(ind+1,b'c',last,wordl+1))]

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
