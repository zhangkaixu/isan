
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


    def actions_to_moves(self,actions,lattice):
        state=self.State(lattice)
        stack=[state]
        moves=[[None,None,action] for action in actions]
        moves[0][0]=0
        moves[0][1]=self.State.init_state
        for i in range(len(moves)-1) :
            move=moves[i]
            step,state,action=move
            ind,label=action
            if ind >=0 : # shift
                rst=[[nstep,ns] for a,nstep,ns in self.shift(step,state) if a==self.Action.encode(action)]
                moves[i+1][0],moves[i+1][1]=rst[0]
                stack.append(rst[0][1])
            else : # reduce 
                s0=stack.pop()
                s1=stack.pop()
                rst=[[nstep,ns] for a,nstep,ns,_ in self.reduce(step,s0,[0],[s1]) if a==self.Action.encode(action)]
                moves[i+1][0],moves[i+1][1]=rst[0]
                stack.append(rst[0][1])
                pass
        for move in moves:
            move[2]=self.Action.encode(move[2])

        moves=list(map(tuple,moves))
        return moves

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
        self.set_raw(raw,y)
        std_actions=self.result_to_actions(y)
        moves=self.actions_to_moves(std_actions,raw)
        return moves

    early_stop=None

    def update_moves(self,std_moves,rst_moves) :
        for s,r in zip(std_moves,rst_moves) :
            if s!= r:
                yield s, 1
                yield r, -1

class Early_Stop_Pointwise :
    def set_oracle(self,raw,y) :
        self.set_raw(raw,y)
        self.stop_step=None
        std_actions=self.result_to_actions(y)
        moves=self.actions_to_moves(std_actions,raw)

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
