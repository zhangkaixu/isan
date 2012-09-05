#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "isan/common/common.hpp"
#include "isan/common/weights.hpp"
#include "isan/parsing/push_down.hpp"

namespace isan{

typedef Smart_String<Chinese_Character> Chinese;
typedef Smart_String<char> Feature_String;
typedef std::vector<Feature_String> Feature_Vector;
class State_Type: public Smart_String<char>{
public:
    PyObject* pack(){
        return PyBytes_FromStringAndSize(pt,length);
    };
    State_Type(){
    };
    State_Type(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        int rtn=PyBytes_AsStringAndSize(py_key,&buffer,&len);
        length=(size_t)len;
        pt=new char[length];
        memcpy(pt,buffer,length*sizeof(char));        
    };
};

/**
 * */

typedef Feature_Generator<Chinese,State_Type,Feature_Vector> Parser_Feature_Generator;
typedef State_Generator<Chinese,State_Type,Action_Type> CWS_State_Generator;


class Python_Feature_Generator: public Parser_Feature_Generator{
public:
    PyObject * callback;
    Python_Feature_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Feature_Generator(){
        Py_DECREF(callback);
    };
    void operator()(State_Type& state, Feature_Vector& fv){
        PyObject * pkey=state.pack();
        PyObject * arglist=Py_BuildValue("(O)",pkey);
        
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);
        
        Py_DECREF(pkey);
        Py_DECREF(arglist);
        
        fv.clear();
        char* buffer;
        size_t length;
        long size=PySequence_Size(pfv);
        PyObject * pf;
        for(int i=0;i<size;i++){
            pf=PySequence_GetItem(pfv,i);
            PyBytes_AsStringAndSize(pf,&buffer,(Py_ssize_t*)&(length));
            fv.push_back(Feature_String(buffer,length));
            Py_DECREF(pf);
        };
        Py_DECREF(pfv);
    };
};








typedef Push_Down<Action_Type,State_Type,Score_Type> Python_Push_Down;
class Python_Push_Down_Data : public Push_Down_Data<Action_Type,State_Type,Score_Type>{
public:
    PyObject* shift_callback;
    PyObject* reduce_callback;
    Python_Push_Down_Data(PyObject* shift_callback,PyObject* reduce_callback){
        this->shift_callback=shift_callback;
        this->reduce_callback=reduce_callback;
        Py_INCREF(shift_callback);
        Py_INCREF(reduce_callback);
    };
    ~Python_Push_Down_Data(){
        Py_DECREF(shift_callback);
        Py_DECREF(reduce_callback);
    };

    void shift(
            State_Type& state, 
            std::vector<Action_Type>& next_actions,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
        PyObject * py_state=state.pack();
        PyObject * arglist=Py_BuildValue("(O)",py_state);
        PyObject * result= PyObject_CallObject(this->shift_callback, arglist);
        Py_CLEAR(py_state);Py_CLEAR(arglist);


        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        next_actions.resize(2);
        next_states.clear();
        for(int i=0;i<size;i++){
            tri=PySequence_GetItem(result,i);
            
            tmp_item=PySequence_GetItem(tri,0);
            next_actions[i]=(PyLong_AsLong(tmp_item));
            Py_DECREF(tmp_item);

            tmp_item=PySequence_GetItem(tri,1);
            next_states.push_back(State_Type(tmp_item));
            Py_DECREF(tmp_item);
            
            Py_DECREF(tri);
        };
        Py_DECREF(result);
    };
    void reduce(
            State_Type& state, 
            State_Type& predictor,
            std::vector<Action_Type>& actions,
            std::vector<State_Type>& next_states,
            std::vector<Score_Type>& scores
            ){
    };
};




class Interface{
public:
    State_Type init_state;
    int beam_width;
    Python_Push_Down_Data * data;
    Python_Push_Down * push_down;
    
    
    Interface(State_Type init_state,int beam_width,
            PyObject * py_shift_callback,
            PyObject * py_reduce_callback
            ){
        this->init_state=init_state;
        this->beam_width=beam_width;
        this->data=new Python_Push_Down_Data(py_shift_callback,py_reduce_callback);
        this->push_down=new Python_Push_Down(this->data,beam_width);

    };
    void set_raw(){
    }
    ~Interface(){
        delete this->data;
        delete this->push_down;
    };
};




static PyObject *
pushdown_new(PyObject *self, PyObject *arg)
{
    PyObject * py_init_stat;
    PyObject * py_shift_callback;
    PyObject * py_reduce_callback;
    PyObject * py_feature_cb;
    int beam_width;
    PyArg_ParseTuple(arg, "iOOOO", &beam_width,&py_init_stat,
            &py_shift_callback,&py_reduce_callback,
            &py_feature_cb);
    State_Type* init_key = NULL;
    init_key = new State_Type(py_init_stat);
    
    Interface* interface=new Interface(*init_key,beam_width,
            py_shift_callback,py_reduce_callback);
    delete init_key;
    return PyLong_FromLong((long)interface);
};

static PyObject *
pushdown_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
search(PyObject *self, PyObject *arg)
{

    Interface* interface;
    unsigned long steps;
    PyArg_ParseTuple(arg, "LL", &interface,&steps);

    std::vector<Action_Type> result;
    (*interface->push_down)(interface->init_state,steps,result);

    //PyObject * list=PyList_New(result.size());
    
    //return list;
    Py_INCREF(Py_None);
    return Py_None;
};



/** stuffs about the module def */
static PyMethodDef pushdownMethods[] = {
    {"new",  pushdown_new, METH_VARARGS,""},
    {"delete",  pushdown_delete, METH_O,""},
    {"search",  search, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef pushdownmodule = {
   PyModuleDef_HEAD_INIT,
   "dfabeam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   pushdownMethods
};

PyMODINIT_FUNC
PyInit_pushdown(void)
{
    return PyModule_Create(&pushdownmodule);
}


};//end of isan
