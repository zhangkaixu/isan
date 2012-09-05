#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>


namespace isan{


/**
 * 等价于下推自动机的搜索算法
 * */

template <class ACTION, class STATE, class SCORE>
class Push_Down_Data{
public:
    virtual void shift(
            STATE& state, 
            std::vector<ACTION>& actions,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            )=0;
    virtual void reduce(
            const STATE& state, 
            const STATE& predictor,
            std::vector<ACTION>& actions,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            )=0;
};

template <class ACTION, class STATE, class SCORE>
class Push_Down{
public:
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
            //std::cout<<"alpha(xxx)\n";
        };
        Alpha(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,
                int last_ind, STATE last_stat,
                int p_ind,STATE p_stat):
            score(s), sub_score(sub_s), inc(i), action(act), state1(last_stat),
            is_shift(is_sh), ind1(last_ind), ind2(p_ind), state2(p_stat)
            {
            //std::cout<<"alpha(xxx)\n";
        };
        Alpha(){
            score=0;
            sub_score=0;
            inc=0;
        };
    };
    struct State_Info{
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
    typedef __gnu_cxx::hash_map<STATE,State_Info,typename STATE::HASH> My_Map;
    class CompareFoo{
    public:
        bool operator()(const std::pair<STATE,Alpha*>& first, const std::pair<STATE,Alpha*>& second) const{
            if( first.second->score > second.second->score) return true;
            if( first.second->score < second.second->score) return false;
            if( first.second->inc > second.second->inc) return true;
            if( first.second->inc < second.second->inc) return false;
            return false;
        }
    } state_comp_greater;
    
    class CompareFoo2{
    public:
        bool operator()(const std::pair<STATE,Alpha*>& first, const std::pair<STATE,Alpha*>& second) const{
            if( first.second->score < second.second->score) return true;
            if( first.second->score > second.second->score) return false;
            if( first.second->inc < second.second->inc) return true;
            if( first.second->inc > second.second->inc) return false;
            return false;
        }
    } state_comp_less;




public:
    int beam_width;
    Push_Down_Data<ACTION,STATE,SCORE>* data;
    std::vector< My_Map* > sequence;
    
    Push_Down(Push_Down_Data<ACTION,STATE,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    ~Push_Down(){
    };

    /* 
     * 找到
     *
     * */
    inline void thrink(const int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
        //std::cout<<step<<"\n";
        top_n.clear();
        My_Map* map=(this->sequence[step]);
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            if (top_n.size()<this->beam_width){//if top_n is not full
                top_n.push_back(std::pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                if(top_n.size()==this->beam_width){//full, make this a (min)heap
                    make_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }else{
                if(top_n.front().second->score<(*it).second.alphas[0].score){//greater than the top of the heap
                    pop_heap(top_n.begin(),top_n.end(),state_comp_greater);
                    top_n.pop_back();
                    top_n.push_back(std::pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                    push_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }
        };
        sort(top_n.begin(),top_n.end(),state_comp_less);
    };



    void operator()(const STATE& init_key,const int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        
        std::vector<STATE> shifted_states;
        std::vector<STATE> reduced_states;
        
        //clear the sequence, release memory
        if(sequence.size()){
            for(int i=0;i<sequence.size();i++)
                delete sequence[i];
        }
        this->sequence.clear();

        //init the sequence with init_state
        this->sequence.push_back(new My_Map());
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        
        for(int step=0;step<steps;step++){
            //std::cout<<"step "<<step<<"\n";
            thrink(step,beam);//thrink, get beam
            /*gen next step*/
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());

            for(int i=0;i<beam.size();i++){
                //std::cout<<"  i "<<i<<"\n";
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;
                auto& predictors=(*sequence[step])[last_state].predictors;
                
                data->shift(last_state,shift_actions,shifted_states,shift_scores);
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
                    auto& p_state_info=(*sequence[p_step])[p_state];
                    auto& p_score=p_state_info.alphas[0].score;
                    auto& p_sub_score=p_state_info.alphas[0].sub_score;
                    
                    data->reduce(last_state,p_state,reduce_actions,reduced_states,reduce_scores);
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
        thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*sequence[steps])[beam.back().first].alphas[0];

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
        set_result((*sequence[p_ind])[p_state].alphas[0],begin,p_ind,result);
        set_result((*sequence[last_ind])[last_state].alphas[0],p_ind,end-1,result);
    };
};


};//end of namepsace isan
