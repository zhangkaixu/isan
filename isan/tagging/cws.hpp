#pragma once
#include "isan/common/common.hpp"

typedef String<Chinese_Character> Chinese;
typedef String<char> Feature_String;
typedef std::vector<Feature_String> Feature_Vector;



struct State_Key: public String<char>{
    short* ind;
    Action_Type* last_action;
    Action_Type* last_last_action;
    short* sep_ind;
    State_Key(){
        length=sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action)+sizeof(*sep_ind);
        
        pt=new char[length];
        ind=(short*)pt;
        last_action=(Action_Type*)(pt+sizeof(*ind));
        last_last_action=(Action_Type*)(pt+sizeof(*ind)+sizeof(*last_action));
        sep_ind=(short*)(pt+sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action));
        *ind=0;
        *last_action='|';
        *last_last_action='|';
        *sep_ind=0;
    };
    State_Key(const State_Key& other){
        //std::cout<<length<<" a\n";
        length=sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action)+sizeof(*sep_ind);
        pt=new char[length];
        ind=(short*)pt;
        last_action=(Action_Type*)(pt+sizeof(*ind));
        last_last_action=(Action_Type*)(pt+sizeof(*ind)+sizeof(*last_action));
        sep_ind=(short*)(pt+sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action));
        *ind=*other.ind;
        *last_action=*other.last_action;
        *last_last_action=*other.last_last_action;
        *sep_ind=*other.sep_ind;
        //std::cout<<"b\n";
    };
    void operator=(const State_Key& other){
        *ind=*other.ind;
        *last_action=*other.last_action;
        *last_last_action=*other.last_last_action;
        *sep_ind=*other.sep_ind;
    };
    ~State_Key(){
    };
    State_Key(PyObject* py_key){
        length=sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action)+sizeof(*sep_ind);
        pt=new char[length];
        ind=(short*)pt;
        last_action=(Action_Type*)(pt+sizeof(*ind));
        last_last_action=(Action_Type*)(pt+sizeof(*ind)+sizeof(*last_action));
        sep_ind=(short*)(pt+sizeof(*ind)+sizeof(*last_action)+sizeof(*last_last_action));
        PyObject* tmp;
        tmp=PySequence_GetItem(py_key,0);
        *this->ind=PyLong_AsLong(tmp);Py_DECREF(tmp);
        tmp=PySequence_GetItem(py_key,1);
        *this->last_action=*PyUnicode_AS_UNICODE(tmp);Py_DECREF(tmp);
        tmp=PySequence_GetItem(py_key,2);
        *this->last_last_action=*PyUnicode_AS_UNICODE(tmp);Py_DECREF(tmp);
        tmp=PySequence_GetItem(py_key,3);
        *this->sep_ind=PyLong_AsLong(tmp);Py_DECREF(tmp);
    
    
    };
    PyObject* pack(){
        unsigned int la=*this->last_action;
        unsigned int lla=*this->last_last_action;
        return PyTuple_Pack(4,
                PyLong_FromLong(*this->ind),
                PyUnicode_FromUnicode(&la,1),
                PyUnicode_FromUnicode(&lla,1),
                PyLong_FromLong(*this->sep_ind)
        );
    };
    
    void pack_decref(PyObject* pack){
        Py_CLEAR(pack);
    };
    
};


typedef Feature_Generator<Chinese,State_Key,Feature_Vector> CWS_Feature_Generator;
typedef State_Generator<Chinese,State_Key,Action_Type> CWS_State_Generator;


class Default_Feature_Generator: public CWS_Feature_Generator{
public:
    struct Three{
        char a;
        Chinese_Character b;
        char c;
    };
    struct Four{
        char a;
        Chinese_Character b;
        Chinese_Character c;
        char d;
    };
    Default_Feature_Generator(){
        this->raw=NULL;
    };
    void operator()(State_Key& state, Feature_Vector& fv){
        int ind=*state.ind;
        Action_Type left_action=*state.last_action;
        Action_Type left_left_action=*state.last_last_action;
        long sep_ind=*state.sep_ind;
        
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
        fv.push_back(String<char>((char*)&f_trans,sizeof(f_trans)));
        fv.push_back(String<char>((char*)&f_mid,sizeof(f_mid)));
        fv.push_back(String<char>((char*)&f_right,sizeof(f_right)));
        fv.push_back(String<char>((char*)&f_left,sizeof(f_left)));
        
        fv.push_back(String<char>((char*)&f_mid_right,sizeof(f_mid_right)));
        fv.push_back(String<char>((char*)&f_left_mid,sizeof(f_left_mid)));
        fv.push_back(String<char>((char*)&f_left2_left,sizeof(f_left2_left)));
        fv.push_back(String<char>((char*)&f_right_right2,sizeof(f_right_right2)));
        
        fv.push_back(String<char>(1+sizeof(Chinese_Character)*sep_ind));
        fv.back().pt[0]=8;
        for(int i=0;i<sep_ind;i++)
            *(Chinese_Character *) (fv.back().pt+1+i*sizeof(Chinese_Character))= raw->pt[ind-sep_ind+i];
    };
};


class Default_State_Generator: public CWS_State_Generator{
public:

    Default_State_Generator(){
        
    }
    
    void operator()(State_Key& key, std::vector<std::pair<Action_Type, State_Key> > & nexts){
        nexts.clear();
        nexts.push_back(std::pair<Action_Type, State_Key>());
        nexts.back().first='s';
        *nexts.back().second.ind=*key.ind+1;
        *nexts.back().second.last_action='s';
        *nexts.back().second.last_last_action=*key.last_action;
        *nexts.back().second.sep_ind=1;
        
        
        nexts.push_back(std::pair<Action_Type, State_Key>());
        nexts.back().first='c';
        *nexts.back().second.ind=*key.ind+1;
        *nexts.back().second.last_action='c';
        *nexts.back().second.last_last_action=*key.last_action;
        *nexts.back().second.sep_ind=*key.sep_ind+1;
        
    };
};
