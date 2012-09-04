
class Push_Down:
    def __init__(self,schema,beam_width):
        self.schema=schema
        self.beam_width=beam_width
        self.init_data=self.schema.init_data
        self.init=self.schema.init
        self.gen_features=self.schema.gen_features
        self.shift=self.schema.shift
        self.reduce=self.schema.reduce
        self.actions=self.schema.actions
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
        #betas=stat_info.setdefault('betas',{})
        predictors=stat_info['pi']
        c,v=alphas[0][0],alphas[0]['v']
        #shift
        key=self.shift(self.raw,stat)
        if key:
            if key not in self.sequence[ind+1]:
                self.sequence[ind+1][key]={'pi':set(),'alphas':[]}
            new_stat_info=self.sequence[ind+1][key]
            new_stat_info['pi'].add((ind,stat))
            #xi=self.shift_weights(fv)
            xi=self.actions['s'](fv)
            new_stat_info['alphas'].append({
                        0:c+xi,
                        'v':0,
                        'a':'s',
                        'p':((ind,stat),)})
            #betas['s']=[key]
        for p_step,predictor in predictors:
            last_stat_info=self.sequence[p_step][predictor]
            last_fv=self.gen_features(predictor)
            #last_xi=self.shift_weights(last_fv)
            last_xi=self.actions['s'](last_fv)
            last_c,last_v=last_stat_info['alphas'][0][0],last_stat_info['alphas'][0]['v']
            lkey,rkey=self.reduce(self.raw,stat,predictor)
            #left-reduce
            if lkey :
                if lkey not in self.sequence[ind+1]:
                    self.sequence[ind+1][lkey]={'pi':set(),'alphas':[]}
                new_stat_info=self.sequence[ind+1][lkey]
                new_stat_info['pi'].update(last_stat_info['pi'])
                #lamda=self.lreduce_weights(fv)
                lamda=self.actions['l'](fv)
                delta=lamda+last_xi
                new_stat_info['alphas'].append({
                            0:last_c+v+delta,
                            'v':last_v+v+delta,
                            'a':'l',
                            'p':((ind,stat),(p_step,predictor))})
                #betas['l']=[lkey]

            #right-reduce
            if rkey:
                if rkey not in self.sequence[ind+1]:
                    self.sequence[ind+1][rkey]={'pi':set(),'alphas':[]}
                new_stat_info=self.sequence[ind+1][rkey]
                new_stat_info['pi'].update(last_stat_info['pi'])
                #rho=self.rreduce_weights(fv)
                rho=self.actions['r'](fv)
                delta=rho+last_xi
                new_stat_info['alphas'].append({
                            0:last_c+v+delta,
                            'v':last_v+v+delta,
                            'a':'r',
                            'p':((ind,stat),(p_step,predictor))})
                #betas['r']=[rkey]
    def _find_result(self,step,stat,begin,end,actions,stats):
        if begin==end: return
        info=self.sequence[step][stat]
        alpha=info['alphas'][0]
        action=alpha['a']
        actions[end-1]=alpha['a']
        if alpha['a']=='s': 
            last_ind,last_stat=alpha['p'][0]
            stats[last_ind]=last_stat
            return
        last,reduced=alpha['p']
        r_ind,r_stat=reduced
        last_ind,last_stat=last
        actions[r_ind]='s'
        stats[last_ind]=last_stat
        stats[r_ind]=r_stat
        self._find_result(r_ind,r_stat,begin,r_ind,actions,stats)
        self._find_result(last_ind,last_stat,r_ind+1,end-1,actions,stats)

    def make_result(self):
        """
        由alphas中间的记录计算actions
        """
        raw=self.raw
        stat=self.thrink(len(self.sequence)-1)[0]
        #stat=self.find_thrink(len(raw)*2-1)[0]
        step=len(raw)*2-1
        actions=[None for x in range(step)]
        stats=[None for x in range(step)]
        self._find_result(step,stat,0,step,actions,stats)
        return actions    
