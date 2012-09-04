#pragma once
#include <algorithm>

/**
 * 等价于下推自动机的搜索算法
 * */

template <class ACTION, class STATE, class SCORE, class VECTOR>
class Push_Down_Data{
public:
    virtual void gen_actions(
                    STATE& state,
                    VECTOR<ACTION>& shift_actions, VECTOR<SCORE>& shift_scores,
                    VECTOR<ACTION>& reduce_actions, VECTOR<SCORE>& reduce_socres
            )=0;
    virtual void gen_shifted_states(
                    STATE& state,
                    VECTOR<ACTION>& shift_actions,
                    VECTOR<STATE>& shifted_states
            )=0;
    virtual void gen_reduced_states(
                    STATE& state,
                    VECTOR<ACTION>& reduce_actions,
                    VECTOR<STATE>& reduced_states
            )=0;
};

template <class ACTION, class STATE, class SCORE, class VECTOR>
class Push_Down{
public:
    struct Alpha{
        SCORE score;
        SCORE sub_score;
        SCORE inc;
        ACTION action;
        STATE last_state;
        Alpha(SCORE s,SCORE sub_s,SCORE i, ACTION act,STATE last_stat):
            score(s), sub_score(sub_s), inc(i), action(act), last_state(last_stat){
            };
    };
    struct State_Info{
        VECTOR<Alpha> alphas;
        void max_top(){
            if(alphas.size()==0)return;
            int max_ind=0;
            for(int ind=1;ind<alphas.size();ind++)
                if (alphas[max_ind].score < alphas[ind].score)
                    max_ind=ind;
            if(max_ind)std::swap(alphas[max_ind],alphas[0]);
        };
    };
    typedef std::map<STATE,State_Info> my_map;

    class CompareFoo{
    public:
        bool operator()(const std::pair<STATE,SCORE>& first, const std::pair<STATE,SCORE>& second) const{
            return first.second > second.second;
        }
    } state_comp_greater;
    
    class CompareFoo2{
    public:
        bool operator()(const std::pair<STATE,SCORE>& first, const std::pair<STATE,SCORE>& second) const{
            return first.second < second.second;
        }
    } state_comp_less;

};
