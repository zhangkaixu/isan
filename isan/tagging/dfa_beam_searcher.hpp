#include <vector>
#include <map>
//#include <unordered_map>
#include <ext/hash_map>
#include <algorithm>




template<class KEY,class ACTION,class SCORE>
struct Triple{
    KEY key;
    ACTION action;
    SCORE score;
};

template<class KEY,class ACTION,class SCORE>
class DFA_Beam_Searcher_Data{
public:
    virtual void gen_next(KEY&,std::vector<ACTION>&, std::vector<KEY>&, std::vector<SCORE>&){std::cout<<"oh no\n";};
};



template<class KEY,class ACTION,class SCORE>
class DFA_Beam_Searcher{
public:
    
    
    struct Alpha{
        SCORE score;
        SCORE inc;
        ACTION last_action;
        KEY last_key;
        Alpha(){
        };
        Alpha(SCORE score,SCORE inc,ACTION la,KEY lk){
            this->score=score;
            this->inc=inc;
            this->last_action=la;
            this->last_key=lk;
        };
        
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
    //typedef std::map<KEY,State_Info> my_map;
    typedef __gnu_cxx::hash_map<KEY,State_Info,typename KEY::HASH> my_map;
    //bool state_comp_less(const std::pair<KEY,State_Info>& first, const std::pair<KEY,State_Info>& second) const{
    //    return first.second.alphas[0].score < second.second.alphas[0].score;
    //};
    class CompareFoo{
    public:
        bool operator()(const std::pair<KEY,SCORE>& first, const std::pair<KEY,SCORE>& second) const{
            return first.second > second.second;
        }
    } state_comp_greater;
    
    class CompareFoo2{
    public:
        bool operator()(const std::pair<KEY,SCORE>& first, const std::pair<KEY,SCORE>& second) const{
            return first.second < second.second;
        }
    } state_comp_less;
    
    int beam_width;
    DFA_Beam_Searcher_Data<KEY,ACTION,SCORE>* data;
    std::vector< my_map* > sequence;
    
    DFA_Beam_Searcher(DFA_Beam_Searcher_Data<KEY,ACTION,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    ~DFA_Beam_Searcher(){
    };
    
    void _print_beam(std::vector<std::pair<KEY,SCORE> >& beam){
        for(int j=0;j<beam.size();j++){
            std::cout<<j<<":"<<(int)beam[j].second<<" ";
        }
        std::cout<<"\n";
        int x;
        std::cin>>x;
    };
    
    inline void thrink(int step,std::vector<std::pair<KEY,SCORE> >& top_n){
        top_n.clear();
        
        my_map* map=(this->sequence[step]);
        typename my_map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            //std::cout<<"in thrink "<<it->second.alphas.size()<<"\n";
            if (top_n.size()<this->beam_width){//if top_n is not full
                top_n.push_back(std::pair<KEY,SCORE>((*it).first,(*it).second.alphas[0].score));
                if(top_n.size()==this->beam_width){//full, make this a (min)heap
                    make_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }else{
                if(top_n.front().second<(*it).second.alphas[0].score){//greater than the top of the heap
                    pop_heap(top_n.begin(),top_n.end(),state_comp_greater);
                    top_n.pop_back();
                    top_n.push_back(std::pair<KEY,SCORE>((*it).first,(*it).second.alphas[0].score));
                    push_heap(top_n.begin(),top_n.end(),state_comp_greater);
                }
            }
        };
        sort(top_n.begin(),top_n.end(),state_comp_less);
    };
    void call(KEY& init_key,int steps,std::vector<ACTION>& result){
        std::vector<std::pair<KEY,SCORE> > beam;
        std::vector<ACTION> next_actions;
        std::vector<KEY> next_keys;
        std::vector<SCORE> scores;
        typename my_map::iterator got;
        
        if(sequence.size()){
            for(int i=0;i<sequence.size();i++)
                delete sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new my_map());
        
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        (*this->sequence.back())[init_key].alphas[0].score=0;
        
        for(int step=0;step<steps;step++){
            thrink(step,beam);//thrink, get beam
            //print_beam(beam);
            //std::cout<<step<<" "<<beam.size()<<" here\n";
            this->sequence.push_back(new my_map());
            my_map& this_map=(*this->sequence.back());
            //gen_next
            for(int i=0;i<beam.size();i++){
                //std::cout<<"beam "<<i<<"\n";
                KEY& last_key=beam[i].first;
                SCORE& last_score=beam[i].second;

                //std::cout<<"key "<<(int)*(char*)&last_key<<"\n";
                //std::cout<<"call gen_next "<<"\n";
                this->data->gen_next(last_key,next_actions,next_keys,scores);
                //std::cout<<"gen_next ed "<<"\n";
                
                for(int j=0;j<next_actions.size();j++){
                    //std::cout<<"    next "<<j<<"\n";
                    KEY& key=next_keys[j];
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
