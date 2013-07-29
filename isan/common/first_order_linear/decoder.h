#pragma once
namespace isan{

typedef double Score_Type; 
typedef size_t Tag_Type; 

//a structure for alphas and betas
struct Alpha_Beta{
    Score_Type value;
    Tag_Type tag_id;
};

/** The DP algorithm(s) for path labeling */
inline Score_Type dp_decode(
        const size_t tagset_size,
        const size_t node_size,
        const Score_Type* transitions,
        const Score_Type* emissions,
        Alpha_Beta* alphas,
        Tag_Type* tags
        ){

    Tag_Type max_tag_id;
    Score_Type max_value;
    // scores of the first item
    for(Tag_Type j=0;j<tagset_size;j++){ alphas[j].value=emissions[j]; };

    for(size_t i=1;i<node_size;i++){
        for(Tag_Type j=0;j<tagset_size;j++){ // j-th in i

            max_tag_id=0;
            max_value=alphas[(i-1)*tagset_size].value+transitions[j];
            for(Tag_Type k=1;k<tagset_size;k++){// k-th in i-1
                Score_Type value=alphas[(i-1)*tagset_size+k].value+transitions[k*tagset_size+j];
                if(value > max_value){
                    max_value=value;
                    max_tag_id=k;
                }
            };
            
            alphas[i*tagset_size+j].value=emissions[i*tagset_size+j]+max_value;
            alphas[i*tagset_size+j].tag_id=max_tag_id;
            
        };
    };

    max_tag_id=0;
    max_value=alphas[(node_size-1)*tagset_size].value;
    for(Tag_Type k=1;k<tagset_size;k++){// k-th in i-1
        Score_Type value=alphas[(node_size-1)*tagset_size+k].value;
        if(value > max_value){
            max_value=value;
            max_tag_id=k;
        }
    };

    size_t node_id=node_size-1;
    size_t tag_id=max_tag_id;
    tags[node_id]=tag_id;
    while (node_id>0) {
        tag_id=alphas[(node_id)*tagset_size+tag_id].tag_id;
        node_id--;
        tags[node_id]=tag_id;
        
    };
    return max_value;
};



/** cal beta */
inline void dp_cal_beta(
        const size_t tagset_size,
        const size_t node_size,
        const Score_Type* transitions,
        const Score_Type* emissions,
        Alpha_Beta* betas
        ){

    Tag_Type max_tag_id;
    Score_Type max_value;
    // scores of the first item
    for(Tag_Type j=0;j<tagset_size;j++){ 
        betas[j+(node_size-1)*tagset_size].value=emissions[j+(node_size-1)*tagset_size]; 
    };

    for(int i=node_size-2;i>=0;--i){
        for(Tag_Type j=0;j<tagset_size;j++){ // j-th in i

            //find max
            max_tag_id=0;
            max_value=betas[(i+1)*tagset_size].value+transitions[j*tagset_size];
            for(Tag_Type k=1;k<tagset_size;k++){// k-th in i+1
                Score_Type value=betas[(i+1)*tagset_size+k].value+transitions[j*tagset_size+k];
                if(value > max_value){
                    max_value=value;
                    max_tag_id=k;
                }
            };
            
            betas[i*tagset_size+j].value=emissions[i*tagset_size+j]+max_value;
            betas[i*tagset_size+j].tag_id=max_tag_id;
            
        };
    };
};


}//end of namespace
