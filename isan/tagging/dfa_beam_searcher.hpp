#include <vector>
#include <map>
#include <ext/hash_map>
#include <algorithm>
#include "isan/common/searcher.hpp"


namespace isan{

template<class ACTION,class STATE,class SCORE>
struct State_Info_t{
    struct Alpha{
        SCORE score;
        SCORE inc;
        ACTION last_action;
        STATE last_key;
        Alpha(){
            this->score=0;
        };
        Alpha(SCORE score,SCORE inc,ACTION la,STATE lk){
            this->score=score;
            this->inc=inc;
            this->last_action=la;
            this->last_key=lk;
        };
    };

    std::vector<Alpha> alphas;
    void max_top(){
        if(alphas.size()==0){
            return;
        };
        int max_ind=0;
        for(int ind=1;ind<alphas.size();ind++){
            if (alphas[max_ind].score < alphas[ind].score){
                max_ind=ind;
            }
        }
        if(max_ind){
            std::swap(alphas[max_ind],alphas[0]);
        }
    };
};




template<class ACTION,class STATE,class SCORE>
class DFA_Beam_Searcher : public Searcher<ACTION, STATE,SCORE,State_Info_t> {
    typedef State_Info_t<ACTION,STATE,SCORE> State_Info;
    typedef typename Searcher<ACTION, STATE,SCORE,State_Info_t>::Alpha Alpha;
    typedef typename Searcher<ACTION, STATE,SCORE,State_Info_t>::My_Map My_Map;
public:
    DFA_Beam_Searcher(Searcher_Data<ACTION,STATE,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };

    typename Searcher<ACTION, STATE,SCORE,State_Info_t>::CompareFoo state_comp_greater;
    typename Searcher<ACTION, STATE,SCORE,State_Info_t>::CompareFoo2 state_comp_less;
    
    
    void call(STATE& init_key,int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> next_actions;
        std::vector<STATE> next_keys;
        std::vector<SCORE> scores;
        typename My_Map::iterator got;
        
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)
                delete this->sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new My_Map());
        
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        (*this->sequence.back())[init_key].alphas[0].score=0;
        
        for(int step=0;step<steps;step++){
            this->thrink(step,beam);//thrink, get beam
            //print_beam(beam);
            //std::cout<<step<<" "<<beam.size()<<" here\n";
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());
            //gen_next
            for(int i=0;i<beam.size();i++){
                //std::cout<<"beam "<<i<<"\n";
                STATE& last_key=beam[i].first;
                SCORE& last_score=beam[i].second->score;

                //std::cout<<"key "<<(int)*(char*)&last_key<<"\n";
                //std::cout<<"call gen_next "<<"\n";
                this->data->shift(last_key,next_actions,next_keys,scores);
                //std::cout<<"gen_next ed "<<"\n";
                
                for(int j=0;j<next_actions.size();j++){
                    //std::cout<<"    next "<<j<<"\n";
                    STATE& key=next_keys[j];
                    got=this_map.find(key);
                    if(got==this_map.end()){
                        this_map[key]=State_Info();
                    }
                    //std::cout<<"here\n";
                    this_map[key].alphas.push_back(Alpha(
                                last_score+scores[j],
                                scores[j],
                                next_actions[j],
                                last_key
                                ));
                };
            };
        };
        //make result
        this->thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*this->sequence[steps])[beam.back().first].alphas[0];

        result.resize(steps);
        int ind=steps-1;
        while(ind>=0){
            //std::cout<<ind<<" "<<item.last_action<<"\n";
            result[ind]=item.last_action;
            item=(*this->sequence[ind])[item.last_key].alphas[0];
            ind--;
        };
    };
};
};//isan
