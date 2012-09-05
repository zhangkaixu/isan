#pragma once
#include "isan/common/common.hpp"


namespace isan{

class Default_State_Type: public State_Type{
public:
    
    inline short* ind2(){
        return (short*)(pt);
    };
    inline Action_Type* last_action2(){
        return (Action_Type*)(pt+sizeof(short));
    };

    inline Action_Type* last_last_action2(){
        return (Action_Type*)(pt+sizeof(short)+sizeof(Action_Type));
    };

    inline short* sep_ind2(){
        return (short*)(pt+sizeof(short)+sizeof(Action_Type)+sizeof(Action_Type));
    };
    
    
    Default_State_Type(){
        length=sizeof(short)+sizeof(Action_Type)+sizeof(Action_Type)+sizeof(short);
        pt=new char[length];
        *ind2()=0;
        *last_action2()='0';
        *last_last_action2()='0';
        *sep_ind2()=0;
    };
};




class Default_Feature_Generator: public General_Feature_Generator{
public:
    struct Three{
        char a;
        Chinese_Character b;
        Action_Type c;
    };
    struct Four{
        char a;
        Chinese_Character b;
        Chinese_Character c;
        Action_Type d;
    };
    Default_Feature_Generator(){
        this->raw=NULL;
    };
    void operator()(const State_Type& super_state, Feature_Vector& fv){
        Default_State_Type& state=(Default_State_Type&)super_state;
        int ind=*(short*)state.pt;
        Action_Type left_action=*state.last_action2();
        Action_Type left_left_action=*state.last_last_action2();
        long sep_ind=*state.sep_ind2();
        
        Chinese_Character char_mid=ind-1>=0?raw->pt[ind-1]:-1;
        Chinese_Character char_right=ind<raw->length?raw->pt[ind]:-1;
        Chinese_Character char_left=ind-2>=0?raw->pt[ind-2]:-1;
        Chinese_Character char_left2=ind-3>=0?raw->pt[ind-3]:-1;
        Chinese_Character char_right2=ind+1<raw->length?raw->pt[ind+1]:-1;
        
        Three f_trans={0,(left_action),(left_left_action)};
        Three f_mid={1,(char_mid),(left_action)};
        Three f_right={2,(char_right),(left_action)};
        Three f_left={3,(char_left),(left_action)};
        
        Four f_mid_right={4,(char_mid),(char_right),(left_action)};
        Four f_left_mid={5,(char_left),(char_mid),(left_action)};
        Four f_left2_left={6,(char_left2),(char_left),(left_action)};
        Four f_right_right2={7,(char_right),(char_right2),(left_action)};
        
        fv.clear();
        fv.push_back(Feature_String((char*)&f_trans,sizeof(f_trans)));
        fv.push_back(Feature_String((char*)&f_mid,sizeof(f_mid)));
        fv.push_back(Feature_String((char*)&f_right,sizeof(f_right)));
        fv.push_back(Feature_String((char*)&f_left,sizeof(f_left)));
        
        fv.push_back(Feature_String((char*)&f_mid_right,sizeof(f_mid_right)));
        fv.push_back(Feature_String((char*)&f_left_mid,sizeof(f_left_mid)));
        fv.push_back(Feature_String((char*)&f_left2_left,sizeof(f_left2_left)));
        fv.push_back(Feature_String((char*)&f_right_right2,sizeof(f_right_right2)));
        
        fv.push_back(Feature_String(1+sizeof(Chinese_Character)*sep_ind));
        fv.back().pt[0]=8;
        for(int i=0;i<sep_ind;i++)
            *(Chinese_Character *) (fv.back().pt+1+i*sizeof(Chinese_Character))= raw->pt[ind-sep_ind+i];
    };
};


class Default_State_Generator: public General_State_Generator{
public:

    Default_State_Generator(){
        
    }
    
    void operator()(State_Type& super_key, std::vector<Action_Type>& next_actions,
            std::vector< State_Type > & super_states){
        Default_State_Type& key=(Default_State_Type&)super_key;
        std::vector<Default_State_Type > & next_states=
                (std::vector<Default_State_Type> &)super_states;
        
        next_actions.clear();
        next_actions.resize(2);
        next_states.clear();
        next_states.resize(2);
        next_actions[0]=11;
        (*next_states[0].ind2())=(*key.ind2())+1;
        *next_states[0].last_action2()=11;
        *next_states[0].last_last_action2()=*key.last_action2();
        *next_states[0].sep_ind2()=1;
        
        

        next_actions[1]=22;
        *next_states.back().ind2()=(*key.ind2())+1;
        *next_states.back().last_action2()=22;
        *next_states.back().last_last_action2()=*key.last_action2();
        *next_states.back().sep_ind2()=*key.sep_ind2()+1;
    };
};


};//isan
