#pragma once
#include <ext/hash_map>
#include <algorithm>


namespace isan{

typedef std::pair pair;

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
        Alpha(){
            score=0;
            sub_score=0;
            inc=0;
        };
    };
    struct State_Info{
        VECTOR<Alpha> alphas;
        My_Map< pair<int,STATE> ,int> predictors;
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
        bool operator()(const pair<STATE,Alpha*>& first, const pair<STATE,Alpha*>& second) const{
            if( first.second->score > second.second->score) return true;
            if( first.second->score < second.second->score) return false;
            if( first.second->inc > second.second->inc) return true;
            if( first.second->inc < second.second->inc) return false;
            return false;
        }
    } state_comp_greater;
    
    class CompareFoo2{
    public:
        bool operator()(const pair<STATE,Alpha*>& first, const pair<STATE,Alpha*>& second) const{
            if( first.second->score < second.second->score) return true;
            if( first.second->score > second.second->score) return false;
            if( first.second->inc < second.second->inc) return true;
            if( first.second->inc > second.second->inc) return false;
            return false;
        }
    } state_comp_less;




public:

    int beam_width;
    Push_Down_Data<STATE,ACTION,SCORE>* data;
    VECTOR< My_Map* > sequence;
    
    Push_Down(Push_Down_Data<STATE,ACTION,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    ~Push_Down(){
    };

    /* 
     * 找到
     *
     * */
    inline void thrink(int step,VECTOR<pair<STATE,Alpha*> >& top_n){
        top_n.clear();
        My_Map* map=(this->sequence[step]);
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            if (top_n.size()<this->beam_width){//if top_n is not full
                top_n.push_back(pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                if(top_n.size()==this->beam_width){//full, make this a (min)heap
                    make_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }else{
                if(top_n.front().second->score<(*it).second.alphas[0].score){//greater than the top of the heap
                    pop_heap(top_n.begin(),top_n.end(),state_comp_greater);
                    top_n.pop_back();
                    top_n.push_back(pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                    push_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }
        };
        sort(top_n.begin(),top_n.end(),state_comp_less);
    };



    void operator()(STATE& init_key,int steps,VECTOR<ACTION>& result){
        VECTOR<pair<STATE,Alpha*> > beam;
        VECTOR<ACTION> shift_actions;
        VECTOR<SCORE> shift_scores;
        VECTOR<ACTION> reduce_actions;
        VECTOR<SCORE> reduce_scores;
        
        VECTOR<STATE>& shifted_states;
        
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
            thrink(step,beam);//thrink, get beam
            /*gen next step*/
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());

            for(int i=0;i<beam.size();i++){
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;

                this->data->gen_actions(last_state,
                        shift_actions, shift_scores,
                        reduce_actions, reduce_scores);
                
                this->data->gen_shifted_states(last_state,
                        shift_actions,
                        shifted_states);
                for(int j=0;j<next_actions.size();j++){
                    STATE& state=shifted_states[j];
                    auto got=this_map.find(state);
                    if(got==this_map.end())this_map[state]=State_Info();
                    
                    this_map[state].alphas.push_back(Alpha(
                                last_score+shifted_scores[j],
                                0,
                                shifted_scores[j],
                                shift_actions[j],
                                last_state
                                ));
                };
            };
        };
        
        
        //make result
        thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*sequence[steps])[beam.back().first].alphas[0];

        result.resize(steps);
        int ind=steps-1;
        while(ind>=0){
            //std::cout<<ind<<" "<<item.last_action<<"\n";
            result[ind]=item.last_action;
            item=(*sequence[ind])[item.last_state].alphas[0];
            ind--;
        };
    };
};


};//end of namepsace isan
