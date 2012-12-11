import isan.common.perceptrons

class Lattice :
    def __init__(self,l,w):
        self.weights=w
        self.items=l
        chars={}
        begins={}
        for i,item in enumerate(self.items) :
            begin=item[0]
            for j,c in enumerate(item[2]):
                o=j+begin
                if o not in chars: chars[o]=c
            if begin not in begins : begins[begin]=[]
            begins[begin].append(i)
        self.begins=begins
        self.sentence=''.join(x[1] for x in sorted(list(chars.items())))
        self.length=len(self.sentence)
    def arcs_to_result(self,arcs):
        rst=set()
        rst_result=arcs
        std_result=self.items
        for s,d in rst_result :
            s=std_result[s]
            d=std_result[d] if d != -1 else None
            r=(s[:3],s[3],d)
            rst.add(r)
        return rst

class Lattice_Task(isan.common.perceptrons.Task):
    def get_init_states(self) :
        return [self.State.init_stat]

    def moves_to_result(self,moves,_):
        actions=list(zip(*moves))[2]
        arcs=self.Action.actions_to_arcs(actions)
        return self.lattice.arcs_to_result(arcs)

    def result_to_actions(self,result):
        """
        将依存树转化为shift-reduce的动作序列（与动态规划用的状态空间无关）
        在一对多中选择了一个（选择使用栈最小的）
        """
        arcs=self.codec.result_to_arcs(result)
        return self.Action.arcs_to_actions(arcs)
    def actions_to_stats(self,actions):
        """
        动作到状态
        """
        stack=[[0,self.State.init_stat]]#准备好栈
        stats=[]#状态序列
        for action in actions :
            stats.append([stack[-1][0],stack[-1][1]]) #状态
            is_shift,*rest=self.Action.parse_action(action)#解析动作
            if is_shift : # shift动作
                sind=rest[0] # 得到shift的对象
                nexts=self.State(stack[-1][1],self.lattice).shift(sind)
                n=[n for n in nexts if n[0]==action][0]
                stack.append([n[1],n[2]])
            else :
                nexts=self.State(stack[-1][1],self.lattice).reduce(
                        self.State(stack[-2][1],self.lattice),0)
                n=[n for n in nexts if n[0]==action][0]
                stack.pop()
                stack.pop()
                stack.append([n[1],n[2]])
        return stats
    def check(self,std_moves,rst_moves):
        #print('std')
        #for step,state,action in std_moves:
        #    print(step,self.State(state,self),action)
        #print('rst')
        #for step,state,action in rst_moves:
        #    print(step,self.State(state,self),action)

        if len(std_moves)!=len(rst_moves) :return False
        return all(
                std_move[2]==rst_move[2]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )
    def shift(self,last_ind,stat):
        state=self.State(stat,self.lattice)
        shift_inds=self.lattice.begins.get(state.span[1],[])
        rtn=[]
        for shift_ind in shift_inds:
            rtn+=state.shift(shift_ind)
        return rtn

    def reduce(self,last_ind,stat,pred_inds,predictors):
        rtn=[]
        st=self.State(stat,self.lattice)
        for i,predictor in enumerate(predictors) :
            pre_st=self.State(predictor,self.lattice)
            rtn+=st.reduce(pre_st,i)
        return rtn
    ## stuffs about the early update
    def set_oracle(self,raw,y) :
        self.set_raw(raw,None)

        self.std_states=[]
        std_moves=[]
        std_actions=self.result_to_actions(y)#得到标准动作
        for i,stat in enumerate(self.actions_to_stats(std_actions)) :
            step,stat=stat
            std_moves.append([step,stat,std_actions[i]])
            s=self.State.load(stat)#pickle.loads(stat)
            self.std_states.append([step,s])

        for i,x in enumerate(self.std_states) :
            if i>0 :
                self.std_states[i].append(self.std_states[i-1][1])
        self.std_states=list(reversed(self.std_states[1:]))

        self.early_stop_step=0
        return std_moves

    def remove_oracle(self):
        self.std_states=[]
    def early_stop(self,step,next_states,moves):
        if not moves: return False
        if (not hasattr(self,"std_states")) or (not self.std_states) : return False
        if step < self.std_states[-1][0] : return False

        oracle_s=self.std_states[-1][1]
        oracle_p=self.std_states[-1][2]
        if step > self.std_states[-1][0] : 
            return True

        last_steps,last_states,actions=zip(*moves)
        for last_state,action,next_state in zip(last_states,actions,next_states):
            if last_state==b'': return False
            next_state=self.State.load(next_state)#pickle.loads(next_state)
            if next_state == self.std_states[-1][1] : 
        
                last_state=self.State.load(last_state)#pickle.loads(last_state)
                if step==0 or last_state==self.std_states[-1][2] :
                    ps=self.std_states.pop()
                    self.early_stop_step=ps[0]
                    return False
        #print("Eearly STOP!")
        return True
    def update_moves(self,std_moves,rst_moves) :
        #print('update',self.early_stop_step)
        #for std,rst in zip(std_moves,rst_moves) :
        #    if std!= rst :
        #        yield std,1
        #        yield rst,-1
        #        return
        #return
        for std in std_moves:
            if self.early_stop_step == None or self.early_stop_step>=std[0] :
                yield std, 1
            else :
                break
        for rst in rst_moves:
            if self.early_stop_step == None or self.early_stop_step>=rst[0] :
                yield rst, -1
            else :
                break
