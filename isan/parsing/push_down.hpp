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
            STATE& state, 
            STATE& predictor,
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
        std::vector<Alpha> alphas;
        typedef __gnu_cxx::hash_map< std::pair<int,STATE> ,int> predictors;
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
    inline void thrink(int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
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



    void operator()(STATE& init_key,int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        
        std::vector<STATE> shifted_states;
        
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
            //std::cout<<step<<"\n";
            thrink(step,beam);//thrink, get beam
            /*gen next step*/
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());

            for(int i=0;i<beam.size();i++){
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;
                
                data->shift(last_state,shift_actions,shifted_states,shift_scores);

            };
        };
        return;
        
        
        //make result
        thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*sequence[steps])[beam.back().first].alphas[0];

        result.resize(steps);
        int ind=steps-1;
        while(ind>=0){
            //std::cout<<ind<<" "<<item.last_action<<"\n";
            result[ind]=item.action;
            item=(*sequence[ind])[item.last_state].alphas[0];
            ind--;
        };
    };
};


};//end of namepsace isan
