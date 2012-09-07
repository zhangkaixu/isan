#include <vector>
#include <map>
#include <ext/hash_map>
#include <algorithm>
#include "isan/common/searcher.hpp"



template<class ACTION,class STATE,class SCORE>
struct Alpha_t{
    SCORE score;
    SCORE inc;
    ACTION last_action;
    STATE last_key;
    Alpha_t(){
    };
    Alpha_t(SCORE score,SCORE inc,ACTION la,STATE lk){
        this->score=score;
        this->inc=inc;
        this->last_action=la;
        this->last_key=lk;
    };
};





template<class ACTION,class STATE,class SCORE>
class DFA_Beam_Searcher : public Searcher<ACTION, STATE,SCORE,
            Alpha_t> {
public:
    typedef Alpha_t<ACTION,STATE,SCORE> Alpha;
    DFA_Beam_Searcher(Searcher_Data<ACTION,STATE,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    
    
    
    struct State_Info{
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
    //typedef std::map<STATE,State_Info> My_Map;
    typedef __gnu_cxx::hash_map<STATE,State_Info,typename STATE::HASH> My_Map;
    //bool state_comp_less(const std::pair<STATE,State_Info>& first, const std::pair<STATE,State_Info>& second) const{
    //    return first.second.alphas[0].score < second.second.alphas[0].score;
    //};
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
    
    std::vector< My_Map* > sequence;
    
    
    
    void _print_beam(std::vector<std::pair<STATE,SCORE> >& beam){
        for(int j=0;j<beam.size();j++){
            std::cout<<j<<":"<<(int)beam[j].second<<" ";
        }
        std::cout<<"\n";
        int x;
        std::cin>>x;
    };
    
    inline void thrink(int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
        top_n.clear();
        
        My_Map* map=(this->sequence[step]);
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            //std::cout<<"in thrink "<<it->second.alphas.size()<<"\n";
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
    void call(STATE& init_key,int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> next_actions;
        std::vector<STATE> next_keys;
        std::vector<SCORE> scores;
        typename My_Map::iterator got;
        
        if(sequence.size()){
            for(int i=0;i<sequence.size();i++)
                delete sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new My_Map());
        
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        (*this->sequence.back())[init_key].alphas[0].score=0;
        
        for(int step=0;step<steps;step++){
            thrink(step,beam);//thrink, get beam
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
        thrink(steps,beam);
        sort(beam.begin(),beam.end(),state_comp_less);
        Alpha& item=(*sequence[steps])[beam.back().first].alphas[0];

        result.resize(steps);
        int ind=steps-1;
        while(ind>=0){
            //std::cout<<ind<<" "<<item.last_action<<"\n";
            result[ind]=item.last_action;
            item=(*sequence[ind])[item.last_key].alphas[0];
            ind--;
        };
    };
    
};

int main(){
    return 0;
};
