#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/searcher.hpp"
#include "isan/common/weights.hpp"
using namespace isan;

class Default_State_Type : public State_Type{
    typedef unsigned short type1;
    typedef Action_Type type2;
    typedef Action_Type type3;
    typedef unsigned short type4;
    typedef unsigned short type5;
    static const size_t offset1=sizeof(type1);
    static const size_t offset2=offset1+sizeof(type2);
    static const size_t offset3=offset2+sizeof(type3);
    static const size_t offset4=offset3+sizeof(type4);
    static const size_t offset5=offset4+sizeof(type5);
public:
    
    inline type1* ind(){
        return (type1*)(pt);
    };
    inline type2* last_action(){
        return (type2*)(pt+offset1);
    };

    inline type3* last_last_action(){
        return (type3*)(pt+offset2);
    };

    inline type4* sep_ind(){
        return (type4*)(pt+offset3);
    };
    inline type5* sep_ind_2(){
        return (type5*)(pt+offset4);
    };
    Default_State_Type(){
        length=offset5;
        pt=new unsigned char[length];
        *ind()=0;
        *last_action()='0';
        *last_last_action()='0';
        *sep_ind()=0;
        *sep_ind_2()=0;
    };
    Default_State_Type(type1 v1,type2 v2,type3 v3,type4 v4,type5 v5){
        length=offset5;
        pt=new unsigned char[length];
        *ind()=v1;
        *last_action()=v2;
        *last_last_action()=v3;
        *sep_ind()=v4;
        *sep_ind_2()=v5;
    };
};

class CWS_Feature_Generator: public General_Feature_Generator{
    std::vector<std::vector<Feature_Vector> > chr_based;
public:
    struct F1{
        unsigned char a;
        Action_Type b;
        Action_Type c;
    };
    struct Three{
        unsigned char a;
        Action_Type c;
        Chinese_Character b;
    };
    struct Four{
        unsigned char a;
        Action_Type d;
        Chinese_Character b;
        Chinese_Character c;
    };
    struct Two{
        char a;
        unsigned short len;
    };
    CWS_Feature_Generator(){
        this->raw=NULL;
    };
    void set_raw(const Chinese* raw){
        this->raw=raw;
        chr_based.clear();
        for(int ind=0;ind<raw->size()+1;ind++){
            chr_based.push_back(std::vector<Feature_Vector>());
            const Chinese_Character& char_mid=ind-1>=0?raw->pt[ind-1]:-1;
            const Chinese_Character& char_right=ind<raw->length?raw->pt[ind]:-1;
            const Chinese_Character& char_left=ind-2>=0?raw->pt[ind-2]:-1;
            const Chinese_Character& char_left2=ind-3>=0?raw->pt[ind-3]:-1;
            const Chinese_Character& char_right2=ind+1<raw->length?raw->pt[ind+1]:-1;
            for(unsigned char left_action='0';left_action<='2';++left_action){
                chr_based.back().push_back(Feature_Vector());
                if(ind>0&&left_action=='0')continue;

                Three f_mid={2,(left_action),(char_mid)};
                Three f_right={3,(left_action),(char_right)};
                Three f_left={4,(left_action),(char_left)};
                Four f_mid_right={5,(left_action),(char_mid),(char_right)};
                Four f_left_mid={6,(left_action),(char_left),(char_mid)};
                Four f_left2_left={7,(left_action),(char_left2),(char_left)};
                Four f_right_right2={8,(left_action),(char_right),(char_right2)};

                Feature_Vector& fv=chr_based.back().back();
                fv.push_back(Feature_String((unsigned char*)&f_mid,sizeof(f_mid)));
                fv.push_back(Feature_String((unsigned char*)&f_right,sizeof(f_right)));
                fv.push_back(Feature_String((unsigned char*)&f_left,sizeof(f_left)));
                fv.push_back(Feature_String((unsigned char*)&f_mid_right,sizeof(f_mid_right)));
                fv.push_back(Feature_String((unsigned char*)&f_left_mid,sizeof(f_left_mid)));
                fv.push_back(Feature_String((unsigned char*)&f_left2_left,sizeof(f_left2_left)));
                fv.push_back(Feature_String((unsigned char*)&f_right_right2,sizeof(f_right_right2)));
            };
        };
        
    };
    ~CWS_Feature_Generator(){
    };
    void operator()(const State_Type& super_state, Feature_Vector& fv){
        Default_State_Type& state=(Default_State_Type&)super_state;
        int ind=*(unsigned short*)state.pt;
        const Action_Type& left_action=*state.last_action();
        const Action_Type& left_left_action=*state.last_last_action();
        unsigned short sep_ind=*state.sep_ind();
        
        const Chinese_Character& char_mid=ind-1>=0?raw->pt[ind-1]:-1;
        const Chinese_Character& char_right=ind<raw->length?raw->pt[ind]:-1;
        const Chinese_Character& char_left=ind-2>=0?raw->pt[ind-2]:-1;
        const Chinese_Character& char_left2=ind-3>=0?raw->pt[ind-3]:-1;
        const Chinese_Character& char_right2=ind+1<raw->length?raw->pt[ind+1]:-1;
        
        const F1 f_trans={1,(left_action),(left_left_action)};
        
        const Two f_wl={9,(unsigned short)(sep_ind+1)};
        
        fv.clear();
        fv.insert(fv.begin(),chr_based[ind][left_action-'0'].begin(),chr_based[ind][left_action-'0'].end());
        
        fv.push_back(Feature_String((unsigned char*)&f_trans,sizeof(f_trans)));
        fv.push_back(Feature_String((unsigned char*)& f_wl,sizeof( f_wl)));
        fv.push_back(Feature_String(1+sizeof(Chinese_Character)*sep_ind));
        fv.back().pt[0]=10;
        for(int i=0;i<sep_ind;i++)
            *(Chinese_Character *) (fv.back().pt+1+i*sizeof(Chinese_Character))= raw->pt[ind-sep_ind+i];

        for(int i=0;i<fv.size();i++){
            register auto f=fv[i];
            for(int j=0;j<f.size();j++){
                if(f[j]==0)f[j]=120;
            };
        };
    };
};


class CWS_State_Generator: public General_State_Generator{
public:
    void operator()(State_Type& super_key, std::vector<Action_Type>& next_actions,
            std::vector< State_Type > & super_states){

        next_actions.resize(2);
        next_actions[0]=11;
        next_actions[1]=22;

        Default_State_Type& key=(Default_State_Type&)super_key;
        int ind=*key.ind()+1;
        int sepind=(*key.sep_ind());
        super_states.clear();
        //s
        super_states.push_back(Default_State_Type(
                    ind,
                    '1',
                    *key.last_action(),
                    1,
                    *key.sep_ind()
                    ));
        //c
        super_states.push_back(Default_State_Type(
                    ind,
                    '2',
                    *key.last_action(),
                    sepind+1,
                    *key.sep_ind_2()
                    ));
    };
};



static PyObject *
task_new(PyObject *self, PyObject *arg)
{

    General_State_Generator * shifted_state_generator;
    General_Feature_Generator * feature_generator;
    State_Type* init_state;

    shifted_state_generator=new CWS_State_Generator();
    feature_generator=new CWS_Feature_Generator();
    init_state = new Default_State_Type();
    //std::cout<<init_state->length<<"\n";
    return PyTuple_Pack(3,
            init_state->pack(),
            PyLong_FromUnsignedLong((size_t)shifted_state_generator),
            PyLong_FromUnsignedLong((size_t)feature_generator)
            );

};




/** stuffs about the module def */
static PyMethodDef cwstaskMethods[] = {
    {"new",  task_new, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cwstaskmodule = {
   PyModuleDef_HEAD_INIT,
   "cwstask",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cwstaskMethods
};

PyMODINIT_FUNC
PyInit_cwstask(void)
{
    return PyModule_Create(&cwstaskmodule);
}
