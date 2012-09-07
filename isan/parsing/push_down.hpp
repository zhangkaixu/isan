#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>
#include "isan/common/searcher.hpp"


namespace isan{

template<class ACTION,class STATE,class SCORE>
struct State_Info_t{
    struct Alpha{
        SCORE score;
        SCORE sub_score;
        SCORE inc;
        bool is_shift;
        ACTION action;
        int ind1;
        STATE state1;
        int ind2;
        STATE state2;
        Alpha(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,int last_ind, STATE last_stat):
            score(s), sub_score(sub_s), inc(i), action(act), state1(last_stat),
            is_shift(is_sh), ind1(last_ind)
            {
        };
        Alpha(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,
                int last_ind, STATE last_stat,
                int p_ind,STATE p_stat):
            score(s), sub_score(sub_s), inc(i), action(act), state1(last_stat),
            is_shift(is_sh), ind1(last_ind), ind2(p_ind), state2(p_stat)
            {
        };
        Alpha(){
            score=0;
            sub_score=0;
            inc=0;
        };
    };

    std::vector<Alpha> alphas;
    __gnu_cxx::hash_map< STATE, std::pair<int, SCORE>, typename STATE::HASH> predictors;
    /*  */
    void max_top(){
        if(alphas.size()==0)return;
        int max_ind=0;
        for(int ind=1;ind<alphas.size();ind++)
            if (alphas[max_ind].score < alphas[ind].score)
                max_ind=ind;
        if(max_ind)std::swap(alphas[max_ind],alphas[0]);
    };
};


template <class ACTION, class STATE, class SCORE>
class Push_Down : public Searcher<ACTION,STATE,SCORE,State_Info_t> {
    typedef State_Info_t<ACTION,STATE,SCORE> State_Info;
    typedef typename State_Info::Alpha Alpha;
public:
    typedef __gnu_cxx::hash_map<STATE,State_Info,typename STATE::HASH> My_Map;
    typename Searcher<ACTION, STATE,SCORE,State_Info_t>::CompareFoo state_comp_greater;
    typename Searcher<ACTION, STATE,SCORE,State_Info_t>::CompareFoo2 state_comp_less;



public:
    
    Push_Down(Searcher_Data<ACTION,STATE,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    ~Push_Down(){
    };

    void operator()(const STATE& init_key,const int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<STATE> shifted_states;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        std::vector<STATE> reduced_states;
        
        //clear the sequence, release memory
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)
                delete this->sequence[i];
        }
        this->sequence.clear();

        //init the sequence with init_state
        this->sequence.push_back(new My_Map());
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        
        for(int step=0;step<steps;step++){
            //std::cout<<"step "<<step<<"\n";
            this->thrink(step,beam);//thrink, get beam
            /*gen next step*/
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());

            for(int i=0;i<beam.size();i++){
                //std::cout<<"  i "<<i<<"\n";
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;
                auto& predictors=(*this->sequence[step])[last_state].predictors;
                
                this->data->shift(last_state,shift_actions,shifted_states,shift_scores);
                this->data->shift(last_state,shift_actions,shifted_states,shift_scores);
                for(int j=0;j<shift_actions.size();j++){
                    //std::cout<<"    j "<<j<<"\n";
                    auto& next_state=shifted_states[j];
                    auto got=this_map.find(next_state);
                    if(got==this_map.end()){
                        this_map[next_state]=State_Info();
                    };
                    auto& next_state_info=this_map[next_state];
                    next_state_info.predictors[last_state]=std::pair<int, SCORE>(step,shift_scores[j]);
                    next_state_info.alphas.push_back(Alpha(
                                last_score+shift_scores[j],
                                0,
                                shift_scores[j],
                                true,
                                shift_actions[j],
                                step,
                                last_state
                                ));

                };
                for(auto p=predictors.begin();p!=predictors.end();++p){
                    auto& p_state=p->first;
                    auto& p_step=p->second.first;
                    auto& p_inc=p->second.second;
                    auto& p_state_info=(*this->sequence[p_step])[p_state];
                    auto& p_score=p_state_info.alphas[0].score;
                    auto& p_sub_score=p_state_info.alphas[0].sub_score;
                    
                    this->data->reduce(last_state,p_state,reduce_actions,reduced_states,reduce_scores);
                    for(int j=0;j<reduce_actions.size();j++){
                        auto& next_state=reduced_states[j];
                        auto& next_action=reduce_actions[j];

                        auto got=this_map.find(next_state);
                        if(got==this_map.end()){
                            this_map[next_state]=State_Info();
                        };
                        auto& next_state_info=this_map[next_state];
                        for(auto it=p_state_info.predictors.begin();
                                it!=p_state_info.predictors.end();
                                ++it){
                            next_state_info.predictors[it->first]=it->second;
                        };
                        next_state_info.alphas.push_back(Alpha(
                                    p_score+last_sub_score+reduce_scores[j]+p_inc,
                                    p_sub_score+last_sub_score+reduce_scores[j]+p_inc,
                                    reduce_scores[j],
                                    false,
                                    next_action,
                                    step,
                                    last_state,
                                    p_step,
                                    p_state
                                    ));
                        
                    };
                };

            };
        };
        
        
        //make result
        this->thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*this->sequence[steps])[beam.back().first].alphas[0];

        result.resize(steps);
        set_result(item,0,steps,result);
    };
    void set_result(const Alpha& alpha,int begin,int end, std::vector<ACTION>& result){
        result[end-1]=alpha.action;
        if(begin==end)return;
        if(alpha.is_shift)return;
        int last_ind=alpha.ind1;
        const STATE& last_state=alpha.state1;
        int p_ind=alpha.ind2;
        const STATE& p_state=alpha.state2;
        set_result((*this->sequence[p_ind])[p_state].alphas[0],begin,p_ind,result);
        set_result((*this->sequence[last_ind])[last_state].alphas[0],p_ind,end-1,result);
    };
};


};//end of namepsace isan
