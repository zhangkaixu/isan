#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <vector>
namespace isan{


template <class ALPHA>
class Searcher_Data{
public :
    typedef typename ALPHA::Action ACTION;
    typedef typename ALPHA::State STATE;
    typedef typename ALPHA::Score SCORE;
    typedef ALPHA Alpha;
    int max_step;
public:
    /* 搜索是否需要提前终止
     * */
    Searcher_Data(){
        use_early_stop=false;
    };
    bool use_early_stop;
    virtual bool early_stop(
            int step,
            const std::vector<Alpha*>& last_alphas,
            const std::vector<STATE>& states
            ){
        return false;
    };
    
    virtual void shift(
            const int& ind,
            STATE& state, 
            std::vector<ACTION>& actions,
            std::vector<int>& next_inds,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            )=0;

    virtual void reduce(
            const int state_ind,
            const STATE& state, 
            const int predictor_ind,
            const STATE& predictor,
            std::vector<ACTION>& actions,
            std::vector<int>& next_inds,
            std::vector<STATE>& next_states,
            std::vector<SCORE>& scores
            )=0;
};


/*
 * 线性搜索的alpha
 * */
template<class ACTION,class STATE,class SCORE>
struct Alpha_t{
    typedef ACTION Action;
    typedef STATE State;
    typedef SCORE Score;

    SCORE score;// score now
    SCORE inc;// score of last action
    ACTION action;//last action
    int ind1;//index of last state
    STATE state1;//last state
    Alpha_t(){
        this->ind1=-1;
        this->score=0;
    };
    Alpha_t(SCORE score,SCORE inc,ACTION la,int ind1,STATE lk){
        this->score=score;
        this->inc=inc;
        this->action=la;
        this->ind1=ind1;
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
            return false;
        }
    } state_comp_greater;

    static class CompareFoo2{
    public:
        inline bool operator()(const std::pair<STATE,Alpha_t*>& first, const std::pair<STATE,Alpha_t*>& second) const{
            if( first.second->score < second.second->score) return true;
            if( first.second->score > second.second->score) return false;
            return false;
        }
    } state_comp_less;
};

template<class ACTION,class STATE,class SCORE>
struct Alpha_s : public Alpha_t<ACTION,STATE,SCORE>{
    typedef ACTION Action;
    typedef STATE State;
    typedef SCORE Score;
    SCORE sub_score;
    bool is_shift;
    STATE state2;
    int ind2;
    Alpha_s(){
        this->score=0;
    };
    Alpha_s(SCORE score,SCORE inc,ACTION la,int,STATE lk){
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

template<class ALPHA>
struct State_Info{
    typedef ALPHA Alpha;
    typedef typename Alpha::Action ACTION;
    typedef typename Alpha::State STATE;
    typedef typename Alpha::Score SCORE;
    std::vector<Alpha> alphas;
    std::vector<Alpha> betas;
    inline void max_top(){
        if(alphas.size()==0){
            std::cout<<"zero alphas!!!\n";
            return;
        }
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

template<class ALPHA>
struct State_Info_t : public State_Info<ALPHA > {
    typedef typename ALPHA::Action Action;
    typedef typename ALPHA::State State;
    typedef typename ALPHA::Score Score;
    typedef ALPHA Alpha;
};

template<class ALPHA>
struct State_Info_s : public State_Info<ALPHA > {
    typedef typename ALPHA::Action Action;
    typedef typename ALPHA::State State;
    typedef typename ALPHA::Score Score;
    typedef ALPHA Alpha;
    __gnu_cxx::hash_map< State, std::pair<int, Score>, typename State::HASH> predictors;
};





template <class STATE_INFO>
class Searcher{
public:
    typedef typename STATE_INFO::Action ACTION;
    typedef typename STATE_INFO::State STATE;
    typedef typename STATE_INFO::Score SCORE;
    typedef typename STATE_INFO::Alpha Alpha;

    typedef STATE_INFO State_Info;
    typedef __gnu_cxx::hash_map<STATE, State_Info,typename STATE::HASH> My_Map;

    int beam_width;
    Searcher_Data<Alpha>* data;

    std::vector< My_Map* > sequence;
    My_Map final;

    Searcher(){
    };
    Searcher(Searcher_Data<Alpha>* data,int beam_width){
        this->beam_width=beam_width;
        this->data=data;
    };


    inline void thrink(
            //int step,
            My_Map* map,
            std::vector<std::pair<STATE,Alpha*> >& top_n)
    {
        top_n.clear();
        
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            if ((beam_width==0) || (top_n.size()<this->beam_width)){//if top_n is not full
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
     * beta
     * */
    void cal_betas(){
        int ind=this->sequence.size()-1;
        for(auto iter=final.begin();iter!=final.end();++iter){
            iter->second.betas.push_back(Alpha());
            auto alphas=iter->second.alphas;
            auto beta=iter->second.betas[0];
            for(auto alpha=alphas.begin();alpha!=alphas.end();++alpha){
                (*this->sequence[alpha->ind1])[alpha->state1].betas.push_back(Alpha(
                            beta.score+alpha->inc,
                            alpha->inc,
                            alpha->action,
                            -1,
                            iter->first
                            ));
            };
        };

        My_Map* map;
        while(ind){
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                if(!iter->second.betas.size())continue;
                auto alphas=iter->second.alphas;
                auto beta=iter->second.betas[0];
                for(auto alpha=alphas.begin();alpha!=alphas.end();++alpha){
                    (*this->sequence[alpha->ind1])[alpha->state1].betas.push_back(Alpha(
                                beta.score+alpha->inc,
                                alpha->inc,
                                alpha->action,
                                ind,
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

    /*
     * 线性搜索
     * */
    void call(
            const std::vector<STATE>& init_keys,
            std::vector<Alpha*>& result_alphas
            )
    {
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> next_actions;
        std::vector<int> next_inds;
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
        for(auto it=init_keys.begin();it!=init_keys.end();++it){
            (*this->sequence.back())[(*it)]=State_Info();
            (*this->sequence.back())[(*it)].alphas.push_back(Alpha());
        };
        final.clear();
        //
        My_Map* end_map=&final;
        int step=0;
        while(true){
            if(step>=sequence.size()) break;
            this->thrink(sequence[step],beam);//thrink, get beam
            if(early_stop(step,beam)){
                end_map=sequence[step];
                break;
            };
            //gen_next
            for(int i=0;i<beam.size();i++){
                STATE& last_key=beam[i].first;
                SCORE& last_score=beam[i].second->score;

                this->data->shift(
                        step,
                        last_key,
                        next_actions,
                        next_inds,
                        next_keys,
                        scores);
                
                for(int j=0;j<next_actions.size();j++){
                    int next_ind=next_inds[j];
                    My_Map* this_map;
                    if (next_ind >= 0 ){
                        while(next_ind>=sequence.size())
                            this->sequence.push_back(new My_Map());
                        this_map=this->sequence[next_ind];
                    }else{
                        this_map=&final;
                    }

                    STATE& key=next_keys[j];
                    got=this_map->find(key);
                    if(got==this_map->end()){
                        (*this_map)[key]=State_Info();
                        got=this_map->find(key);
                    };
                    //std::cout<<scores[j]<<"\n";
                    got->second.alphas.push_back(Alpha(
                                last_score+scores[j],
                                scores[j],
                                next_actions[j],
                                step,
                                last_key
                                ));
                };
            };
            step++;
        };

        //make result
        this->thrink(end_map,beam);//thrink, get beam
        sort(beam.begin(),beam.end(),Alpha::state_comp_less);
        
        Alpha* item=&((*end_map)[beam.back().first].alphas[0]);

        result_alphas.clear();
        int ind=item->ind1;
        while(ind>=0){
            result_alphas.push_back(item);
            item=&((*this->sequence[ind])[item->state1].alphas[0]);
            ind=item->ind1;
        };
        std::reverse(result_alphas.begin(),result_alphas.end());
        //cal_betas();
    };

    inline bool early_stop(int& step,std::vector<std::pair<STATE,Alpha*> >& top_n){
        if(!(data->use_early_stop))return false;
        //return false;
        std::vector<STATE> next_states;
        std::vector<Alpha*> last_alphas;

        for(auto iter=top_n.begin();iter!=top_n.end();++iter){
            next_states.push_back(iter->first);
            last_alphas.push_back(iter->second);
        };
        return this->data->early_stop(
                step,
                last_alphas,
                next_states);
    };

    /*
     * 二叉树搜索
     * */
    void operator()(
            const std::vector<STATE>& init_keys,
            const int steps,
            std::vector<Alpha*>& result_alphas
            )
    {
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<STATE> shifted_states;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        std::vector<STATE> reduced_states;
        std::vector<int> next_inds;
        std::vector<int> next_reduce_inds;

        typename My_Map::iterator got;

        
        //clear and init the sequence, release memory
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)
                delete this->sequence[i];
        }
        this->sequence.clear();
        this->sequence.push_back(new My_Map());
        for(auto it=init_keys.begin();it!=init_keys.end();++it){
            (*this->sequence.back())[(*it)]=State_Info();
            (*this->sequence.back())[(*it)].alphas.push_back(Alpha());
        };
        final.clear();
        
        My_Map* end_map=&final;
        int step=0;
        while(true){
            
            
            if(step>=sequence.size()){
                
                break;
            };
            this->thrink(sequence[step],beam);//thrink, get beam
            if(early_stop(step,beam)){
                
                end_map=sequence[step];
                break;
            };
            /*gen next step*/

            for(int i=0;i<beam.size();i++){
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
                SCORE& last_sub_score=beam[i].second->sub_score;

                auto& predictors=(*this->sequence[step])[last_state].predictors;
                
                this->data->shift(
                        step,
                        last_state,
                        shift_actions,
                        next_inds,
                        shifted_states,
                        shift_scores);

                for(int j=0;j<shift_actions.size();j++){
                    int next_ind=next_inds[j];
                    My_Map* next_map;
                    if (next_ind >= 0 ){
                        while(next_ind>=sequence.size())
                            this->sequence.push_back(new My_Map());
                        next_map=this->sequence[next_ind];
                    }else{
                        next_map=&final;
                    }

                    const auto& next_state=shifted_states[j];
                    got=next_map->find(next_state);
                    if(got==next_map->end()){
                        (*next_map)[next_state]=State_Info();
                        got=next_map->find(next_state);
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
                    
                    this->data->reduce(
                            step,
                            last_state,
                            p_step,
                            p_state,
                            reduce_actions,
                            next_reduce_inds,
                            reduced_states,
                            reduce_scores
                            );
                    for(int j=0;j<reduce_actions.size();j++){
                        int next_ind=next_reduce_inds[j];
                        
                        My_Map* next_map;
                        if (next_ind >= 0 ){
                            while(next_ind>=sequence.size())
                                this->sequence.push_back(new My_Map());
                            next_map=this->sequence[next_ind];
                        }else{
                            next_map=&final;
                        }
                        //std::cout<<step<<" "<<steps<<" "<<next_reduce_inds[j]<<"\n";
                        auto& next_state=reduced_states[j];
                        auto& next_action=reduce_actions[j];

                        got=next_map->find(next_state);
                        if(got==next_map->end()){
                            (*next_map)[next_state]=State_Info();
                            got=next_map->find(next_state);
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
        this->thrink(end_map,beam);//thrink, get beam
        sort(beam.begin(),beam.end(),Alpha::state_comp_less);
        
        
        Alpha* item=&((*end_map)[beam.back().first].alphas[0]);
        //Alpha* item=&(*this->sequence[step])[beam.back().first].alphas[0];
        
        //result_alphas.resize(step);
        //set_result(item,0,step,result_alphas);

        result_alphas.clear();
        int ind=item->ind1;
        while(ind>=0){
            
            result_alphas.push_back(item);
            item=&((*this->sequence[ind])[item->state1].alphas[0]);
            ind=item->ind1;
        };
        std::reverse(result_alphas.begin(),result_alphas.end());
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
    void set_result(
            Alpha* alpha,
            int begin,
            int end, 
            std::vector<Alpha*>& result_alphas
            )
    {
        result_alphas[end-1]=alpha;
        while(((begin+1)!=end)&&(alpha->is_shift)){
            
            end--;
            alpha=&(*this->sequence[alpha->ind1])[alpha->state1].alphas[0];
            result_alphas[end-1]=alpha;
        };
        if(begin==end)return;
        if(alpha->is_shift)return;
        int last_ind=alpha->ind1;
        const STATE& last_state=alpha->state1;
        int p_ind=alpha->ind2;
        const STATE& p_state=alpha->state2;
        set_result(&(*this->sequence[p_ind])[p_state].alphas[0],begin,p_ind,result_alphas);
        set_result(&(*this->sequence[last_ind])[last_state].alphas[0],p_ind,end-1,result_alphas);
        alpha++;
    };
};
};//isan
