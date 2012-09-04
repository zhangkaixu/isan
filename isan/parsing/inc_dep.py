import collections
import pickle
import sys
import isan.parsing.dep_codec as codec
import isan.parsing.eval as eval
import isan.common.perceptrons as perceptrons
from isan.parsing.push_down import Push_Down


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
        #return 0
        return sum(self.get(x,0)for x in fv)
        #return sum(map(lambda x:self.get(x,0),fv))
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


class Decoder:
    """
    线性搜索
    value = [alphas,betas]
    alpha = [score, delta, action, link]
    """
    init=(0,(0,0),(None,None,None))
    def shift(self,raw,stat):
        ind,_,stack_top=stat
        if ind>=len(raw): return None
        return (ind+1,
                (ind,ind+1),
                ((raw[ind][0],raw[ind][1],None,None),
                        stack_top[0],
                        stack_top[1][1] if stack_top[1] else None)
                )
    def reduce(self,raw,stat,predictor):
        ind,span,stack_top=stat
        _,p_span,_=predictor
        s0,s1,s2=stack_top
        if s0==None or s1==None:return None,None
        return ((ind,
                (p_span[0],span[1]),
                ((s1[0],s1[1],s1[2],s0[1]),predictor[2][1],predictor[2][2])),
             (ind,
                (p_span[0],span[1]),
                ((s0[0],s0[1],s1[1],s0[3]),predictor[2][1],predictor[2][2])),)
    def gen_next_stats(self,stat):
        #print(stat)
        yield 's',self.shift(self.raw,stat)
        l,r=self.reduce(self.raw,stat)
        yield 'l',l
        yield 'r',r
    def back_gen_next_stats(self,stat):
        """
        由现有状态产生合法新状态
        """
        ind,last,_,wordl=stat
        yield 's',(ind+1,'s',last,1)
        yield 'c',(ind+1,'c',last,wordl+1)
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

    def new_action(self,action):
        self.actions[action]=perceptrons.Weights()
    def _actions_to_stats(self,actions):
        #print(actions)
        sn=sum(1 if a=='s' else 0 for a in actions)
        assert(sn*2-1==len(actions))
        stat=None
        stack=[]
        ind=0
        for action in actions:
            stat=(ind,(0,0),(tuple(stack[-1]) if len(stack)>0 else None,
                        tuple(stack[-2]) if len(stack)>1 else None,
                        tuple(stack[-3][1]) if len(stack)>2 else None,
                        ))
            yield stat
            if action=='s':
                stack.append([self.raw[ind][0],self.raw[ind][1],None,None])
                ind+=1
            else:
                left=stack[-2][0]
                right=stack[-1][1]
                if action=='l':
                    stack[-2][3]=stack[-1][1]
                    stack.pop()
                if action=='r':
                    stack[-1][2]=stack[-2][1]
                    stack[-2]=stack[-1]
                    stack.pop()
    def update(self,x,std_actions,rst_actions,step):
        length=self._update_actions(std_actions,1,step)
        length=self._update_actions(rst_actions,-1,step)
    ### 私有函数 
    def _update_actions(self,actions,delta,step):
        length=0
        for stat,action in zip(self._actions_to_stats(actions),actions):
            fv=self.gen_features(stat)
            if action not in self.actions:
                self.actions.new_action(action)
            self.actions[action].updates(fv,delta,step)
            length+=1
        return length
    
    def __init__(self,beam_width=8):
        self.beam_width=beam_width#搜索柱宽度
        self.init_data={'pi':set(),
                    'alphas':[{0 : 0, 'v' : 0, 'a': None }]}#初始状态
        self.actions={}
        
        self.actions['s']=Weights()#特征
        self.actions['l']=Weights()#特征
        self.actions['r']=Weights()#特征
    
    Eval=eval.Eval
    def link(self):
        pass
    def unlink(self):
        pass
    def average(self,steps):
        for v in self.actions.values():
            v.average(steps)
    def set_raw(self,raw):
        """
        对需要处理的句子做必要的预处理（如缓存特征）
        """
        self.raw=raw
    def gen_features(self,stat):
        ind,_,stack_top=stat
        s0,s1,s2_t=stack_top
        s0_w,s0_t,s0l_t,s0r_t=None,None,None,None
        if s0:
            s0_w,s0_t,s0l_t,s0r_t=s0
        s1_w,s1_t,s1l_t,s1r_t=None,None,None,None
        if s1:
            s1_w,s1_t,s1l_t,s1r_t=s1
        q0_w,q0_t=self.raw[ind] if ind<len(self.raw) else (None,None)
        q1_w,q1_t=self.raw[ind+1] if ind+1<len(self.raw) else (None,None)
        
        fv=[('s1w',s0_w),('s1t',s0_t),('s1ws1t',s0_w,s0_t),
            ('s2w',s1_w),('s2t',s1_t),('s2ws2t',s1_w,s1_t),
            ('q0w',q0_w),('q0t',q0_t),('q0wq0t',q0_w,q0_t),
            ('s1ws2w',s0_w,s1_w),('s1ts2t',s0_t,s1_t),
            ('s1tq0t',s0_t,q0_t),('s1ws1ts2t',s0_w,s0_t,s1_t),
            ('s1ts2ws2t',s0_t,s1_w,s1_t),('s1ws1ts2w',s0_w,s0_t,s1_w),
            ('s1ws2ws2t',s0_w,s1_w,s1_t),('s1ws1ts2ws2t',s0_w,s0_t,s1_w,s1_t),
            ('s1tq0tq1t',s0_t,q0_t,q1_t),('s1ts2tq0t',s0_t,s1_t,q0_t),
            ('s1wq0tq1t',s0_w,q0_t,q1_t),('s1ws2tq0t',s0_w,s1_t,q0_t),
            ('s0ts1ts0lt',s0_t,s1_t,s0l_t),('s0ts1ts0rt',s0_t,s1_t,s0r_t),
            ('s0ts1ts1lt',s0_t,s1_t,s1l_t),('s0ts1ts1rt',s0_t,s1_t,s1r_t),
            ('s0ts0ws0lt',s0_t,s0_w,s0l_t),('s0ts0ws0rt',s0_t,s0_w,s0r_t),
            ('s0ts1ts2t',s0_t,s1_t,s2_t),
                ]
        return fv
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

    def search(self,raw,_=None):
        self.raw=raw
        self.set_raw(raw)
        self.sequence=[{} for i in range(2*len(raw))]
        #self.sequence[0][self.stats.init]={'pi':set(),
        #            'alphas':[{'c' : 0, 'v' : 0, 'a': None }]}#初始状态
        self.forward(lambda x:2*len(x)-1)
        res=self.make_result()
        return res

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

    @staticmethod
    def actions_to_result(actions,raw):
        #print(actions,raw)
        ind=0
        stack=[]
        arcs=[]
        for a in actions:
            if a=='s':
                stack.append(ind)
                ind+=1
            elif a=='l':
                arcs.append((stack[-1],stack[-2]))
                stack.pop()
            elif a=='r':
                arcs.append((stack[-2],stack[-1]))
                stack[-2]=stack[-1]
                stack.pop()
        arcs.append((stack[-1],-1))
        arcs.sort()
        arcs=[x for _,x in arcs]
        #print(arcs)
        return arcs

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
    @staticmethod
    def result_to_actions(result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（没搞清楚相关工作怎么弄的）
        """
        stack=[]
        actions=[]
        #print(result)
        result=[ind for _,_,ind,_ in result]
        record=[[ind,head,0] for ind,head in enumerate(result)]
        for ind,head,_ in record:
            if head!=-1 :
                record[head][2]+=1
        for ind,head in enumerate(result):
            actions.append('s')
            stack.append([ind,result[ind],record[ind][2]])
            while len(stack)>=2:
                if stack[-1][2]==0 and stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                #if stack[-1][1]!=-1 and stack[-1][1]==stack[-2][0]:
                    actions.append('l')
                    stack.pop()
                    stack[-1][2]-=1
                #elif stack[-2][2]==0 and stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                elif stack[-2][1]!=-1 and stack[-2][1]==stack[-1][0]:
                    actions.append('r')
                    stack[-2]=stack[-1]
                    stack.pop()
                    stack[-1][2]-=1
                else:
                    break
        #print(stack)
        #print(len(actions),len(result))
        #print(*enumerate(result))
        assert(len(actions)==2*len(result)-1)
        return actions

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

    codec=codec

class Model(perceptrons.Base_Model):
    """
    模型
    """
    def __init__(self,model_file,schema=None):
        """
        初始化
        """
        super(Model,self).__init__(model_file,schema)

