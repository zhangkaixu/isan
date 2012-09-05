
import pickle
import collections
import isan.parsing.pushdown as pd
class Weights(dict):
    """
    感知器特征的权重
    """
    def __init__(self):
        self.acc=collections.defaultdict(int)
    def update(self,feature,delta=0,step=0):
        self.setdefault(feature,0)
        self[feature]+=delta
        self.acc[feature]+=step*delta
    def __call__(self,fv):
        return sum(self.get(x,0)for x in fv)
    def updates(self,features,delta=0,step=0):
        for feature in features:
            self.setdefault(feature,0)
            self[feature]+=delta
            self.acc[feature]+=step*delta
    def average(self,step):
        for k in self.acc:
            self[k]=(self[k]-self.acc[k]/step)
            if self[k]==0:del self[k]
        del self.acc

class Push_Down:
    def cshift(self,stat):
        stat=pickle.loads(stat)
        raw=self.raw
        ind,_,stack_top=stat
        if ind>=len(raw): return []
        rtn= [
                ('s',
                (ind+1,
                (ind,ind+1),
                ((raw[ind][0],raw[ind][1],None,None),
                        stack_top[0],
                        stack_top[1][1] if stack_top[1] else None)
                ))
                ]
        rtn= [(ord(k),pickle.dumps(s)) for k,s in rtn]
        return rtn


    def __init__(self,schema,beam_width):
        self.schema=schema
        self.beam_width=beam_width
        self.init=self.schema.init
        self.gen_features=self.schema.gen_features
        self.shift=self.schema.shift
        self.reduce=self.schema.reduce
        self.actions=self.schema.actions
        self.init_data={'pi':set(),
                    'alphas':[{0 : 0, 'v' : 0, 'a': None }]}#初始状态
        self.pushdown=pd.new(self.beam_width,pickle.dumps(self.init),self.cshift,self.reduce,
                self.gen_features)
    def set_raw(self,raw):
        self.raw=raw
        self.sequence=[{} for i in range(2*len(raw))]

    def thrink(self,ind):
        #找到最好的alphas
        for k,v in self.sequence[ind].items():
            v['alphas'].sort(reverse=True,key=lambda x:x[0])
        #构造beam
        beam=sorted(list(self.sequence[ind].items()),key=lambda x:x[1]['alphas'][0][0],reverse=True)
        beam=beam[:min(len(beam),self.beam_width)]
        return [stat for stat,_ in beam]
    def forward(self,get_step=lambda x:len(x)+1):
        pd.search(self.pushdown,get_step(self.raw))
        #前向搜索
        self.sequence[0][self.init]=dict(self.init_data)#初始化第一个状态
        for ind in range(get_step(self.raw)):
            for stat in self.thrink(ind):
                self.gen_next(ind,stat)
        return self.make_result()
    def gen_next(self,ind,stat):
        """
        根据第ind步的状态stat，产生新状态，并计算data
        """
        fv=self.gen_features(stat)#得到当前状态的特征向量

        stat_info=self.sequence[ind][stat]
        alphas=stat_info['alphas']
        predictors=stat_info['pi']
        c,v=alphas[0][0],alphas[0]['v']
        #shift
        for sa,key in self.shift(stat):
            if sa not in self.actions : self.actions[sa]=Weights()
            if key not in self.sequence[ind+1]:
                self.sequence[ind+1][key]={'pi':set(),'alphas':[]}
            new_stat_info=self.sequence[ind+1][key]
            new_stat_info['pi'].add((ind,stat))
            xi=self.actions[sa](fv)
            new_stat_info['alphas'].append({
                        0:c+xi,
                        'v':0,
                        'a':sa,
                        'type':'shift',
                        'p':((ind,stat),)})

        for p_step,predictor in predictors:
            last_stat_info=self.sequence[p_step][predictor]
            last_fv=self.gen_features(predictor)
            last_xi=self.actions['s'](last_fv)
            last_c,last_v=last_stat_info['alphas'][0][0],last_stat_info['alphas'][0]['v']
            reduces=self.reduce(stat,predictor)
            for ra,rk in reduces:
                if ra not in self.actions : self.actions[ra]=Weights()
                if rk not in self.sequence[ind+1]:
                    self.sequence[ind+1][rk]={'pi':set(),'alphas':[]}
                new_stat_info=self.sequence[ind+1][rk]
                new_stat_info['pi'].update(last_stat_info['pi'])
                lamda=self.actions[ra](fv)
                delta=lamda+last_xi
                new_stat_info['alphas'].append({
                            0:last_c+v+delta,
                            'v':last_v+v+delta,
                            'a':ra,
                            'type':'reduce',
                            'p':((ind,stat),(p_step,predictor))})

    def _find_result(self,step,stat,begin,end,actions):
        info=self.sequence[step][stat]
        alpha=info['alphas'][0]
        actions[end-1]=alpha['a']
        if begin==end : return
        if alpha['type']=='shift': 
            last_ind,last_stat=alpha['p'][0]
            return
        last,reduced=alpha['p']
        r_ind,r_stat=reduced
        last_ind,last_stat=last
        self._find_result(r_ind,r_stat,begin,r_ind,actions)
        self._find_result(last_ind,last_stat,r_ind+1,end-1,actions)

    def make_result(self):
        """
        由alphas中间的记录计算actions
        """
        stat=self.thrink(len(self.sequence)-1)[0]
        step=len(self.raw)*2-1
        actions=[None for x in range(step)]
        self._find_result(step,stat,0,step,actions)
        return actions    
