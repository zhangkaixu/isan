#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>
namespace isan{

template <class ACTION, class STATE, class SCORE>
class Searcher_Data{
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
            ){return;};
};


template <class ACTION, class STATE, class SCORE,
         template<class _t_a,class _t_b,class _t_c>class STATE_INFO
         >
class Searcher{
    typedef STATE_INFO< ACTION, STATE, SCORE> my_STATE_INFO;
public:
    int beam_width;
    Searcher_Data<ACTION,STATE,SCORE>* data;
    typedef STATE_INFO<ACTION,STATE,SCORE> State_Info;
    typedef __gnu_cxx::hash_map<STATE,my_STATE_INFO,typename STATE::HASH> My_Map;
    typedef typename STATE_INFO<ACTION, STATE, SCORE>::Alpha Alpha;

    std::vector< My_Map* > sequence;

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
    inline void thrink(int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
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
    void _print_beam(std::vector<std::pair<STATE,SCORE> >& beam){
        for(int j=0;j<beam.size();j++){
            std::cout<<j<<":"<<(int)beam[j].second<<" ";
        }
        std::cout<<"\n";
        int x;
        std::cin>>x;
    };
};
};//isan
