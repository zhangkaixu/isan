#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/searcher.hpp"
#include "isan/common/weights.hpp"
#include "isan/common/decoder.hpp"
namespace isan{
typedef General_Interface<State_Info_t> Interface;
};
#include "isan/common/python_interface.hpp"
using namespace isan;

class Default_State_Type: public State_Type{
    typedef unsigned short type1;
    typedef Action_Type type2;
    typedef Action_Type type3;
    typedef unsigned short type4;
    static const size_t offset1=sizeof(type1);
    static const size_t offset2=offset1+sizeof(type2);
    static const size_t offset3=offset2+sizeof(type3);
    static const size_t offset4=offset3+sizeof(type4);
public:
    
    inline type1* ind2(){
        return (type1*)(pt);
    };
    inline type2* last_action2(){
        return (type2*)(pt+offset1);
    };

    inline type3* last_last_action2(){
        return (type3*)(pt+offset2);
    };

    inline type4* sep_ind2(){
        return (type4*)(pt+offset3);
    };
    Default_State_Type(){
        length=offset4;
        pt=new char[length];
        *ind2()=0;
        *last_action2()='0';
        *last_last_action2()='0';
        *sep_ind2()=0;
    };
    Default_State_Type(type1 v1,type2 v2,type3 v3,type4 v4){
        length=offset4;
        pt=new char[length];
        *ind2()=v1;
        *last_action2()=v2;
        *last_last_action2()=v3;
        *sep_ind2()=v4;
    };
};

class CWS_Feature_Generator: public General_Feature_Generator{
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
    CWS_Feature_Generator(){
        this->raw=NULL;
    };
    void operator()(const State_Type& super_state, Feature_Vector& fv){
        Default_State_Type& state=(Default_State_Type&)super_state;
        int ind=*(unsigned short*)state.pt;
        const Action_Type& left_action=*state.last_action2();
        const Action_Type& left_left_action=*state.last_last_action2();
        long sep_ind=*state.sep_ind2();
        
        const Chinese_Character& char_mid=ind-1>=0?raw->pt[ind-1]:-1;
        const Chinese_Character& char_right=ind<raw->length?raw->pt[ind]:-1;
        const Chinese_Character& char_left=ind-2>=0?raw->pt[ind-2]:-1;
        const Chinese_Character& char_left2=ind-3>=0?raw->pt[ind-3]:-1;
        const Chinese_Character& char_right2=ind+1<raw->length?raw->pt[ind+1]:-1;
        
        const Three f_trans={0,(left_action),(left_left_action)};
        const Three f_mid={1,(char_mid),(left_action)};
        const Three f_right={2,(char_right),(left_action)};
        const Three f_left={3,(char_left),(left_action)};
        
        const Four f_mid_right={4,(char_mid),(char_right),(left_action)};
        const Four f_left_mid={5,(char_left),(char_mid),(left_action)};
        const Four f_left2_left={6,(char_left2),(char_left),(left_action)};
        const Four f_right_right2={7,(char_right),(char_right2),(left_action)};
        
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


class CWS_State_Generator: public General_State_Generator{
public:
    
    void operator()(State_Type& super_key, std::vector<Action_Type>& next_actions,
            std::vector< State_Type > & super_states){

        next_actions.resize(2);
        next_actions[0]=11;
        next_actions[1]=22;

        Default_State_Type& key=(Default_State_Type&)super_key;
        int ind=*key.ind2()+1;
        int sepind=(*key.sep_ind2());
        super_states.clear();
        super_states.push_back(Default_State_Type(
                    ind,
                    's',
                    *key.last_action2(),
                    1
                    ));
        super_states.push_back(Default_State_Type(
                    ind,
                    'c',
                    *key.last_action2(),
                    sepind+1
                    ));
    };
};

static PyObject *
search(PyObject *self, PyObject *arg)
{

    Interface* interface;
    unsigned long steps;
    PyArg_ParseTuple(arg, "LL", &interface,&steps);
    
    std::vector<Action_Type> result;
    interface->push_down->call(interface->init_state,steps,result);

    PyObject * list=PyList_New(result.size());
    
    for(int i=0;i<result.size();i++){
        PyList_SetItem(list,i,PyLong_FromLong(result[i]));
    }
    //std::cout<<"searchend\n";
    return list;
};


static PyObject *
searcher_new(PyObject *self, PyObject *arg)
{
    PyObject * py_init_stat;
    PyObject * py_state_cb;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOO", &beam_width,&py_init_stat,&py_state_cb,&py_feature_cb);

    General_State_Generator * shifted_state_generator;
    General_Feature_Generator * feature_generator;
    shifted_state_generator=new CWS_State_Generator();
    feature_generator=new CWS_Feature_Generator();

    State_Type* init_state = NULL;
    
    init_state = new Default_State_Type();
    Interface* interface=new Interface(*init_state,beam_width, 
            shifted_state_generator,
            feature_generator);
    delete init_state;
    
    return PyLong_FromLong((long)interface);
};




static PyObject *
my_set_raw(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject *new_raw;
    PyArg_ParseTuple(arg, "LO", &interface,&new_raw);
    long raw_size=PySequence_Size(new_raw);
    
    Chinese raw(raw_size);
    for(int i=0;i<raw_size;i++){
        PyObject *tmp=PySequence_GetItem(new_raw,i);
        raw.pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(tmp);
        Py_DECREF(tmp);
    }
    interface->set_raw(raw);
    interface->feature_generator->raw=interface->raw;
    Py_INCREF(Py_None);
    
    return Py_None;
};



/** stuffs about the module def */
static PyMethodDef cwssearcherMethods[] = {
    {"new",  searcher_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"set_raw",  my_set_raw, METH_VARARGS,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  set_weights, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"export_weights",  export_weights, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef cwssearchermodule = {
   PyModuleDef_HEAD_INIT,
   "seggersearcher",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   cwssearcherMethods
};

PyMODINIT_FUNC
PyInit_cwssearcher(void)
{
    return PyModule_Create(&cwssearchermodule);
}
