#pragma once
#include <ext/hash_map>
#include <map>
#include <algorithm>
#include <iostream>
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
            const std::vector<ALPHA*>& pred_alphas,
            std::vector<ACTION>& actions,
            std::vector<int>& next_inds,
            std::vector<STATE>& next_states,
            std::vector<int>& reduce_pred_alphas,
            std::vector<SCORE>& scores
            )=0;
};


template<class ACTION,class STATE,class SCORE>
struct Alpha{
    typedef ACTION Action;
    typedef STATE State;
    typedef SCORE Score;
    SCORE score;// score now
    SCORE inc;// score of last action
    ACTION action;//last action
    int ind1;//index of last state
    STATE state1;//last state
#ifdef REDUCE
    bool is_shift;
    SCORE sub_score;
    STATE state2;
    Alpha* p_alpha;
    int ind2;
#endif
    Alpha(){
        this->ind1=-1;
        this->score=0;
    };
    Alpha(SCORE s,SCORE i, ACTION act,int last_ind, STATE last_stat)
        {
        this->score=(s);
        this->inc=(i);
        this->action=(act);
        this->state1=(last_stat);
        this->ind1=(last_ind);
#ifdef REDUCE
        this->is_shift=true;
        this->sub_score=0;
#endif
    };
#ifdef REDUCE
    Alpha(SCORE s,SCORE sub_s,SCORE i,bool is_sh, ACTION act,
            int last_ind, STATE last_stat,
            Alpha* p_alpha
            )
        {
        this->score=(s);
        this->sub_score=(sub_s);
        this->inc=(i);
        this->action=(act);
        this->state1=(last_stat);
        this->is_shift=(is_sh);
        this->ind1=(last_ind);
        this->ind2=p_alpha->ind1;
        this->state2=p_alpha->state1;
        this->p_alpha=(p_alpha);
    };
#endif
    inline bool operator > (const Alpha& right){
        if( this->score > right.score) return true;
        if( this->score < right.score) return false;
#ifdef REDUCE
        if( this->sub_score > right.sub_score) return true;
        if( this->sub_score < right.sub_score) return false;
#endif
        return false;
    };
    static class CompareFoo{
    public:
        inline bool operator()(const std::pair<STATE,Alpha*>& first, const std::pair<STATE,Alpha*>& second) const{
            return (*first.second) > *(second.second);
        }
    } state_comp_greater;

    static class CompareFoo2{
    public:
        inline bool operator()(const std::pair<STATE,Alpha*>& first, const std::pair<STATE,Alpha*>& second) const{
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
    Alpha* best_alpha;
    std::vector<Alpha> alphas;
    std::vector<Alpha> betas;
#ifdef REDUCE
    __gnu_cxx::hash_map< STATE, Alpha, typename STATE::HASH> predictors;
#endif
    inline void max_top_beta(){
        if(betas.size()==0){
            return;
        }
        int max_ind=0;
        for(int ind=1;ind<betas.size();ind++)
            if (betas[max_ind].score < betas[ind].score)
                max_ind=ind;
        if(max_ind)
            std::swap(betas[max_ind],betas[0]);
    };
    inline void max_top(){
        if(alphas.size()==0){
            std::cout<<"zero alphas!!!\n";
            return;
        }
        int max_ind=0;
        for(int ind=1;ind<alphas.size();ind++)
            if (alphas[ind]>alphas[max_ind])
                max_ind=ind;
        best_alpha=&alphas[max_ind];
    };
};



template <class STATE_INFO>
class Searcher{
public:
    typedef typename STATE_INFO::ACTION ACTION;
    typedef typename STATE_INFO::STATE STATE;
    typedef typename STATE_INFO::SCORE SCORE;
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
            My_Map* map,
            std::vector<std::pair<STATE,Alpha*> >& top_n,
            int beam_width)
    {
        top_n.clear();
        
        typename My_Map::iterator it;
        for (it=map->begin() ; it != map->end(); ++it ){
            it->second.max_top();
            if ((beam_width==0) || (top_n.size()<beam_width)){//if top_n is not full
                top_n.push_back(std::pair<STATE,Alpha*>((*it).first,(*it).second.best_alpha));
                if(top_n.size()==beam_width){//full, make this a (min)heap
                    make_heap(top_n.begin(),top_n.end(),Alpha::state_comp_greater);
                }
            }else{
                if(top_n.front().second->score<(*it).second.best_alpha->score){//greater than the top of the heap
                    pop_heap(top_n.begin(),top_n.end(),Alpha::state_comp_greater);
                    top_n.pop_back();
                    top_n.push_back(std::pair<STATE,Alpha*>((*it).first,(*it).second.best_alpha));
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
                    scores.push_back(iter->second.best_alpha->score+iter->second.betas[0].score);
                };
            };
        };
        My_Map* map=&final;
        for(auto iter=map->begin();iter!=map->end();++iter){
            if(iter->second.alphas.size() && iter->second.betas.size()){
                states.push_back(iter->first);
                scores.push_back(iter->second.best_alpha->score+iter->second.betas[0].score);
            };
        };
    };

    /*
     * beta
     * */
    void cal_betas(){
        
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
        int ind=this->sequence.size()-1;
        while(ind){
            map=(this->sequence[ind]);
            for(auto iter=map->begin();iter!=map->end();++iter){
                iter->second.max_top_beta();
            };
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
            std::vector<Alpha*>& result_alphas
            )
    {
        std::vector<std::pair<STATE,Alpha*> > beam;
        std::vector<ACTION> shift_actions;
        std::vector<SCORE> shift_scores;
        std::vector<STATE> shifted_states;
        std::vector<int> next_inds;
#ifdef REDUCE
        std::vector<Alpha*> pred_alphas;
        std::vector<int> reduce_pred_alphas;
        std::vector<ACTION> reduce_actions;
        std::vector<SCORE> reduce_scores;
        std::vector<STATE> reduced_states;
        std::vector<int> next_reduce_inds;
#endif

        typename My_Map::iterator got;

        
        //clear and init the sequence, release memory
        if(this->sequence.size()){
            for(int i=0;i<this->sequence.size();i++)delete this->sequence[i];
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
            this->thrink(sequence[step],beam,this->beam_width);//thrink, get beam
            if(early_stop(step,beam)){
                end_map=sequence[step];
                break;
            };
            /*gen next step*/
            for(int i=0;i<beam.size();i++){
                STATE& last_state=beam[i].first;
                SCORE& last_score=beam[i].second->score;
#ifdef REDUCE
                SCORE& last_sub_score=beam[i].second->sub_score;
                auto& predictors=(*this->sequence[step])[last_state].predictors;
#endif
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
                    got->second.alphas.push_back(Alpha(
                                last_score+shift_scores[j],//prefix score
                                shift_scores[j],//delta score
                                shift_actions[j],//shift action
                                step,
                                last_state
                                ));
#ifdef REDUCE
                    got->second.predictors[last_state]=(got->second.alphas.back());
#endif
                };
#ifdef REDUCE

                pred_alphas.clear();
                for(auto p=predictors.begin();p!=predictors.end();++p){
                    pred_alphas.push_back(&(p->second));
                };
                this->data->reduce(
                        step,//步骤
                        last_state,//状态
                        pred_alphas,//上一个步骤和状态
                        reduce_actions,//动作
                        next_reduce_inds,//下一个步骤
                        reduced_states,//下一个状态
                        reduce_pred_alphas,
                        reduce_scores//分数
                        );
                
                for(int j=0;j<reduce_actions.size();j++){
                    auto& pred_alpha=*pred_alphas[reduce_pred_alphas[j]];

                    auto& p_state_info=(*this->sequence[pred_alpha.ind1])[pred_alpha.state1];
                    auto& p_score=p_state_info.best_alpha->score;
                    auto& p_sub_score=p_state_info.best_alpha->sub_score;

                    int next_ind=next_reduce_inds[j];
                    
                    My_Map* next_map;
                    if (next_ind >= 0 ){
                        while(next_ind>=sequence.size())
                            this->sequence.push_back(new My_Map());
                        next_map=this->sequence[next_ind];
                    }else{
                        next_map=&final;
                    }
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
                        next_state_info.predictors[it->first]=it->second;
                    };
                    next_state_info.alphas.push_back(Alpha(
                                p_score+last_sub_score+reduce_scores[j]+pred_alpha.inc,
                                p_sub_score+last_sub_score+reduce_scores[j]+pred_alpha.inc,
                                reduce_scores[j],
                                false,
                                next_action,
                                step,
                                last_state,
                                &pred_alpha
                                ));
                };
#endif
            };
            step++;
        };
        //make result
        this->thrink(end_map,beam,this->beam_width);//thrink, get beam
        sort(beam.begin(),beam.end(),Alpha::state_comp_less);
        
        Alpha* item=((*end_map)[beam.back().first].best_alpha);
        //std::cout<<item->score<<"\n";
        

        result_alphas.clear();
        make_result(item,0,result_alphas);
        std::reverse(result_alphas.begin(),result_alphas.end());
    };


    void make_result(
            Alpha* item,
            int begin_step,
            std::vector<Alpha*>& result_alphas){
        //std::cout<<"start make "<<begin_step<<"\n";
        result_alphas.push_back(item);
#ifdef REDUCE
        if(item->is_shift){//shift
#endif
            //std::cout<<begin_step<<" shift "<<item->ind1<<"\n";
            if( item->ind1 > begin_step){
                make_result(
                        (*this->sequence[item->ind1])[item->state1].best_alpha,
                        begin_step,
                        result_alphas);
            };
#ifdef REDUCE
        }else{//reduce
            //std::cout<<begin_step<<" reduce "<<item->ind2<<" "<<item->ind1<<"\n";
            if( item->ind1>=0 && item->ind1 > item->ind2){
                make_result(
                        (*this->sequence[item->ind1])[item->state1].best_alpha,
                        item->ind2,
                        result_alphas);
            };
            result_alphas.pop_back();
            result_alphas.push_back(item->p_alpha);
            if( item->ind2 > begin_step){
                make_result(
                        (*this->sequence[item->ind2])[item->state2].best_alpha,
                        begin_step,
                        result_alphas);
            };
        };
#endif
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
};
};//isan
