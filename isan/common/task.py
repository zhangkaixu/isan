
#not finished !!
class Lattice (list) :
    def __init__(self,l,w=None):
        self.weights=w
        self.extend(list(l)) # items= [ (begin,end,data) * ]
        self.length=max(l for _,l,_ in self)
        self.begins={}
        for i in range(len(self)) :
            b=self[i][0]
            if b not in self.begins : self.begins[b]=[]
            self.begins[b].append(i)
    def __str__(self):
        return ' '.join("%i:(%i,%i):%s"%(i,it[0],it[1],it[2]) for i,it in enumerate(self))



class Base_Task :
    def get_init_states(self) :
        return [self.State.init_state]

    #def reduce(self,last_ind,stat,pred_inds,predictors):
    #    pass
    reduce = None


    def actions_to_stats(self,actions,lattice):
        state=self.State(lattice)
        stack=[state]
        states=[self.State(lattice)]#状态序列
        for action in actions :
            ind,label=action
            if ind >=0 : # shift
                rst=[ns for a,ns in state.shift() if a==self.Action.encode(action)]
                state=self.State(lattice,rst[0])
                stack.append(state)
                states.append(state)
            else : # reduce
                s0=stack.pop()
                s1=stack.pop()
                rst=[ns for a,ns in s0.reduce(s1) if a==self.Action.encode(action)]
                state=self.State(lattice,rst[0])
                states.append(state)
                stack.append(state)
        return list(s.dumps()for s in states)

    def moves_to_result(self,moves,_):
        actions=[self.Action.decode(a) for ind,state,a in moves]
        return self.actions_to_result(actions)


    def check(self,std_moves,rst_moves):
        if len(std_moves)!=len(rst_moves) :return False
        return all(
                std_move[2]==rst_move[2]
                for std_move,rst_move in zip(std_moves,rst_moves)
                )

    def set_oracle(self,raw,y) :
        std_actions=self.result_to_actions(y)
        std_states=self.actions_to_stats(std_actions,raw)
        moves=[(i,std_states[i],self.Action.encode(std_actions[i]))for i in range(len(std_actions))]
        return moves

    early_stop=None

    def update_moves(self,std_moves,rst_moves) :
        for s,r in zip(std_moves,rst_moves) :
            if s!= r:
                yield s, 1
                yield r, -1

class Early_Stop_Pointwise :
    def set_oracle(self,raw,y) :
        self.stop_step=None
        std_actions=self.result_to_actions(y)
        std_states=self.actions_to_stats(std_actions,raw)
        moves=[(i,std_states[i],self.Action.encode(std_actions[i]))for i in range(len(std_actions))]

        self.oracle={}
        for step,state,action in moves :
            self.oracle[step]=self.State.load(state)
        return moves

    def remove_oracle(self):
        self.stop_step=None
        self.oracle=None

    def early_stop(self,step,next_states,moves):
        if not moves : return False

        if not hasattr(self,'oracle') or self.oracle==None : return False
        last_steps,last_states,actions=zip(*moves)
        self.stop_step=None
        if step in self.oracle :
            next_states=[self.State.load(x) for x in next_states]
            if not (self.oracle[step]in next_states) :
                self.stop_step=step
                return True
        return False

    def update_moves(self,std_moves,rst_moves) :
        for move in rst_moves :
            if self.stop_step is not None and move[0]>=self.stop_step : break
            yield move, -1
        for move in std_moves :
            if self.stop_step is not None and move[0]>=self.stop_step : break
            yield move, 1
