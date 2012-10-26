#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>
namespace isan{

template <class ACTION, class STATE, class SCORE>
class Searcher_Data{
public:
    /* 搜索是否需要提前终止
     * */
    virtual bool early_stop(
            int step,
            const std::vector<STATE>& last_states,
            const std::vector<ACTION>& actions,
            const std::vector<STATE>& states
            ){
        return false;
    };
    
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


/*
 * 线性搜索的alpha
 * */
template<class ACTION,class STATE,class SCORE>
struct Alpha_t{
    SCORE score;// score now
    SCORE inc;// score of last action
    ACTION action;//last action
    STATE state1;//last state
    Alpha_t(){
        this->score=0;
    };
    Alpha_t(SCORE score,SCORE inc,ACTION la,STATE lk){
        this->score=score;
        this->inc=inc;
        this->action=la;
        this->state1=lk;
    };
    virtual inline bool operator > (const Alpha_t& right){
        if( this->score > right.score) return true;
        if( this->score < right.score) return false;
        return false;
    };
    static class CompareFoo{
    public:
        inline bool operator()(const std::pair<STATE,Alpha_t*>& first, const std::pair<STATE,Alpha_t*>& second) const{
            if( first.second->score > second.second->score) return true;
            if( first.second->score < second.second->score) return false;
            //if( first.second->inc > second.second->inc) return true;
            //if( first.second->inc < second.second->inc) return false;
            return false;
        }
    } state_comp_greater;

    static class CompareFoo2{
    public:
        inline bool operator()(const std::pair<STATE,Alpha_t*>& first, const std::pair<STATE,Alpha_t*>& second) const{
            if( first.second->score < second.second->score) return true;
            if( first.second->score > second.second->score) return false;
            //if( first.second->inc < second.second->inc) return true;
            //if( first.second->inc > second.second->inc) return false;
            return false;
        }
    } state_comp_less;
};

template<class ACTION,class STATE,class SCORE>
struct Alpha_s : public Alpha_t<ACTION,STATE,SCORE>{
    SCORE sub_score;
    bool is_shift;
    int ind1;
    int ind2;
    STATE state2;
    Alpha_s(){
        this->score=0;
    };
    Alpha_s(SCORE score,SCORE inc,ACTION la,STATE lk){
        this->score=score;
        this->inc=inc;
        this->action=la;
        this->state1=lk;
    };
    Alpha_s(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,int last_ind, STATE last_stat)
        {
        this->score=(s);
        this->sub_score=(sub_s);
        this->inc=(i);
        this->action=(act);
        this->state1=(last_stat);
        this->is_shift=(is_sh);
        this->ind1=(last_ind);
    };
    Alpha_s(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,
            int last_ind, STATE last_stat,
            int p_ind,STATE p_stat)
        {
        this->score=(s);
        this->sub_score=(sub_s);
        this->inc=(i);
        this->action=(act);
        this->state1=(last_stat);
        this->is_shift=(is_sh);
        this->ind1=(last_ind);
        this->ind2=(p_ind);
        this->state2=(p_stat);
    };
    inline bool operator > (const Alpha_s& right){
        if( this->score > right.score) return true;
        if( this->score < right.score) return false;
        if( this->sub_score > right.sub_score) return true;
        if( this->sub_score < right.sub_score) return false;
        return false;
    };
    static class CompareFoo{
    public:
        inline bool operator()(const std::pair<STATE,Alpha_s*>& first, const std::pair<STATE,Alpha_s*>& second) const{
            return (*first.second) > *(second.second);
        }
    } state_comp_greater;

    static class CompareFoo2{
    public:
        inline bool operator()(const std::pair<STATE,Alpha_s*>& first, const std::pair<STATE,Alpha_s*>& second) const{
            return (*second.second) > *(first.second);
        }
    } state_comp_less;
};

template<class ACTION,class STATE,class SCORE, template <class,class,class>class ALPHA>
struct State_Info{
    typedef ALPHA<ACTION,STATE,SCORE> Alpha;
    std::vector<Alpha> alphas;
    std::vector<Alpha> betas;
    inline void max_top(){
        if(alphas.size()==0)
            return;
        int max_ind=0;
        for(int ind=1;ind<alphas.size();ind++)
            if (alphas[ind]>alphas[max_ind])
                max_ind=ind;
        if(max_ind)
            std::swap(alphas[max_ind],alphas[0]);
    };
    inline void max_top_beta(){
        if(betas.size()==0)
            return;
        int max_ind=0;
        for(int ind=1;ind<betas.size();ind++)
            if (betas[max_ind].score < betas[ind].score)
                max_ind=ind;
        if(max_ind)
            std::swap(betas[max_ind],betas[0]);
    };
};

template<class ACTION,class STATE,class SCORE>
struct State_Info_t : public State_Info<ACTION,STATE,SCORE,Alpha_t> {
};

template<class ACTION,class STATE,class SCORE>
struct State_Info_s : public State_Info<ACTION,STATE,SCORE,Alpha_s> {
    __gnu_cxx::hash_map< STATE, std::pair<int, SCORE>, typename STATE::HASH> predictors;
};





template <class ACTION, class STATE, class SCORE,
         template<class,class,class>class STATE_INFO
         >
class Searcher{
    typedef STATE_INFO< ACTION, STATE, SCORE> my_STATE_INFO;
public:
    int beam_width;
    Searcher_Data<ACTION,STATE,SCORE>* data;
    Searcher(){
    };
    Searcher(Searcher_Data<ACTION,STATE,SCORE>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };
    typedef STATE_INFO<ACTION,STATE,SCORE> State_Info;
    typedef __gnu_cxx::hash_map<STATE,my_STATE_INFO,typename STATE::HASH> My_Map;
    typedef typename STATE_INFO<ACTION, STATE, SCORE>::Alpha Alpha;

    std::vector< My_Map* > sequence;

    inline void thrink(int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
        top_n.clear();
        
        My_Map* map=(this->sequence[step]);
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            if (top_n.size()<this->beam_width){//if top_n is not full
                top_n.push_back(std::pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                if(top_n.size()==this->beam_width){//full, make this a (min)heap
                    make_heap(top_n.begin(),top_n.end(),Alpha::state_comp_greater);
                }
            }else{
                if(top_n.front().second->score<(*it).second.alphas[0].score){//greater than the top of the heap
                    pop_heap(top_n.begin(),top_n.end(),Alpha::state_comp_greater);
                    top_n.pop_back();
                    top_n.push_back(std::pair<STATE,Alpha*>((*it).first,&(*it).second.alphas[0]));
                    push_heap(top_n.begin(),top_n.end(),Alpha::state_comp_greater);
                }
            }
        };
        sort(top_n.begin(),top_n.end(),Alpha::state_comp_less);
    };
    void _print_beam(std::vector<std::pair<STATE,SCORE> >& beam){
        for(int j=0;j<beam.size();j++){
            std::cout<<j<<":"<<(int)beam[j].second<<" ";
        }
        std::cout<<"\n";
        int x;
        std::cin>>x;
    };

    /*
     * beta
     * */
    void cal_betas(){
        int ind=this->sequence.size()-1;
        My_Map* map=(this->sequence[ind]);
        for(auto iter=map->begin();iter!=map->end();++iter){
            iter->second.betas.push_back(Alpha());
        };
        while(ind){
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                if(!iter->second.betas.size())continue;
                auto alphas=iter->second.alphas;
                auto beta=iter->second.betas[0];
                for(auto alpha=alphas.begin();alpha!=alphas.end();++alpha){
                    (*this->sequence[ind-1])[alpha->state1].betas.push_back(Alpha(
                                beta.score+alpha->inc,
                                alpha->inc,
                                alpha->action,
                                iter->first
                                ));
                };
            };
            ind--;
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                iter->second.max_top_beta();
            };
        };
    };
    void get_states(std::vector<STATE>& states,std::vector<SCORE>& scores){
        states.clear();
        scores.clear();
        //std::cout<<this->sequence.size()<<"\n";
        for(int ind = 0; ind < this->sequence.size(); ind++){
            My_Map* map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                if(iter->second.alphas.size() && iter->second.betas.size()){
                    states.push_back(iter->first);
                    scores.push_back(iter->second.alphas[0].score+iter->second.betas[0].score);
                };
            };
        };
    };

    /*
     * 线性搜索
     * */
    void call(STATE& init_key,int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> next_actions;
        std::vector<STATE> next_keys;
        std::vector<SCORE> scores;
        typename My_Map::iterator got;
        
        //初始化sequence
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)
                delete this->sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new My_Map());
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        
        //
        int step=0;
        while(true){
            this->thrink(step,beam);//thrink, get beam
            if(step==steps||early_stop(step,beam)) break;

            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());
            //gen_next
            for(int i=0;i<beam.size();i++){
                STATE& last_key=beam[i].first;
                SCORE& last_score=beam[i].second->score;

                this->data->shift(last_key,next_actions,next_keys,scores);
                
                for(int j=0;j<next_actions.size();j++){
                    STATE& key=next_keys[j];
                    got=this_map.find(key);
                    if(got==this_map.end()){
                        this_map[key]=State_Info();
                        got=this_map.find(key);
                    };
                    got->second.alphas.push_back(Alpha(
                                last_score+scores[j],
                                scores[j],
                                next_actions[j],
                                last_key
                                ));
                };
            };
            step++;
        };
        //make result
        sort(beam.begin(),beam.end(),Alpha::state_comp_less);
        Alpha* item=&((*this->sequence[step])[beam.back().first].alphas[0]);


        result.resize(step);
        int ind=step-1;
        while(ind>=0){
            result[ind]=item->action;
            item=&((*this->sequence[ind])[item->state1].alphas[0]);
            ind--;
        };
    };


    inline bool early_stop(int step,std::vector<std::pair<STATE,Alpha*> >& top_n){
        //return false;
        std::vector<STATE> last_states;
        std::vector<ACTION> actions;
        std::vector<STATE> next_states;

        for(auto iter=top_n.begin();iter!=top_n.end();++iter){
            next_states.push_back(iter->first);
            actions.push_back((*(iter->second)).action);
            last_states.push_back((*(iter->second)).state1);
        };
        return this->data->early_stop(step,last_states,actions,next_states);
    };

    /*
     * 二叉树搜索
     * */
    void operator()(const STATE& init_key,const int steps,std::vector<ACTION>& result){
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<STATE> shifted_states;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        std::vector<STATE> reduced_states;

        typename My_Map::iterator got;

        
        //clear and init the sequence, release memory
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)
                delete this->sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new My_Map());
        (*this->sequence.back())[init_key]=State_Info();
        (*this->sequence.back())[init_key].alphas.push_back(Alpha());
        
        int step=0;
        while(true){
            this->thrink(step,beam);//thrink, get beam
            if(step==steps||early_stop(step,beam)) break;

            /*gen next step*/
            this->sequence.push_back(new My_Map());
            My_Map& this_map=(*this->sequence.back());

            for(int i=0;i<beam.size();i++){
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;

                auto& predictors=(*this->sequence[step])[last_state].predictors;
                
                this->data->shift(last_state,shift_actions,shifted_states,shift_scores);
                for(int j=0;j<shift_actions.size();j++){
                    const auto& next_state=shifted_states[j];
                    got=this_map.find(next_state);
                    if(got==this_map.end()){
                        this_map[next_state]=State_Info();
                        got=this_map.find(next_state);
                    };
                    got->second.predictors[last_state]=std::pair<int, SCORE>(step,shift_scores[j]);
                    got->second.alphas.push_back(Alpha(
                                last_score+shift_scores[j],//prefix score
                                0,//inner score
                                shift_scores[j],//delta score
                                true,//is_shift
                                shift_actions[j],//shift action
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

                        got=this_map.find(next_state);
                        if(got==this_map.end()){
                            this_map[next_state]=State_Info();
                            got=this_map.find(next_state);
                        };
                        auto& next_state_info=got->second;
                        for(auto it=p_state_info.predictors.begin();
                                it!=p_state_info.predictors.end();
                                ++it){
                            //auto ggt=next_state_info.predictors.find(it->first);
                            //if(ggt != next_state_info.predictors.end()){
                            //    assert(next_state_info.predictors[it->first].second == it->second.second);
                            //    std::cout<<next_state_info.predictors[it->first].second<< " "<<it->second.second<<"\n";
                            //};
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
            step++;
        };
        
        //make result
        sort(beam.begin(),beam.end(),Alpha::state_comp_less);
        const Alpha* item=&(*this->sequence[step])[beam.back().first].alphas[0];
        
        result.resize(step);
        set_result(item,0,step,result);
    };
    /*
     * beta
     * */
    void pushdown_cal_betas(){
        int ind=this->sequence.size()-1;
        My_Map* map=(this->sequence[ind]);
        for(auto iter=map->begin();iter!=map->end();++iter){
            iter->second.betas.push_back(Alpha());
        };
        while(ind){
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                if(!iter->second.betas.size())continue;
                auto alphas=iter->second.alphas;
                auto beta=iter->second.betas[0];
                for(auto alpha=alphas.begin();alpha!=alphas.end();++alpha){
                    (*this->sequence[ind-1])[alpha->state1].betas.push_back(Alpha(
                                beta.score+alpha->inc,
                                alpha->inc,
                                alpha->action,
                                iter->first
                                ));
                };
            };
            ind--;
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                iter->second.max_top_beta();
            };
        };
    };
    void set_result(const Alpha* alpha,int begin,int end, std::vector<ACTION>& result){
        result[end-1]=alpha->action;
        while(((begin+1)!=end)&&(alpha->is_shift)){
            
            end--;
            alpha=&(*this->sequence[alpha->ind1])[alpha->state1].alphas[0];
            result[end-1]=alpha->action;
        };
        if(begin==end)return;
        if(alpha->is_shift)return;
        int last_ind=alpha->ind1;
        const STATE& last_state=alpha->state1;
        int p_ind=alpha->ind2;
        const STATE& p_state=alpha->state2;
        set_result(&(*this->sequence[p_ind])[p_state].alphas[0],begin,p_ind,result);
        set_result(&(*this->sequence[last_ind])[last_state].alphas[0],p_ind,end-1,result);
        alpha++;
    };
};
};//isan
