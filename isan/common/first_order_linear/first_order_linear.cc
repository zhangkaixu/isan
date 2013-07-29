#include <Python.h>
#include <cstdio>
#include <iostream>
#include <cstring>
//#include "isan/common/common.hpp"
#include "isan/common/first_order_linear/decoder.h"


#define __MODULE_NAME first_order_linear
#define __INIT_FUNC(a,b) a##b
#define INIT_FUNC(a,b) __INIT_FUNC(a,b)
#define PYINIT PyInit_
#define STR(x) #x

namespace isan{

const size_t MAX_LEN=10000;

/**
 * interface of the decoder
 * */
class Interface{
    //typedef Searcher<State_Info_Type > My_Searcher;
public:
    size_t tagset_size;
    size_t length;
    
    PyObject * py_emission; // call to get the emission score
    PyObject * py_transition; // call to get the transition score

    PyObject * raw;

    Score_Type* emissions;
    Score_Type* transitions;
    Alpha_Beta* alphas;
    Alpha_Beta* betas;
    Tag_Type* tags;
    Score_Type score;

public:

    Interface(size_t tagset_size, // size of the tag set
            PyObject * py_emission, // call to get the emission score
            PyObject * py_transition // call to get the transition score
            ){
        emissions=new Score_Type[MAX_LEN*tagset_size];
        alphas=new Alpha_Beta[MAX_LEN*tagset_size];
        betas=new Alpha_Beta[MAX_LEN*tagset_size];
        transitions=new Score_Type[tagset_size*tagset_size];
        tags=new Tag_Type[MAX_LEN];
        
        Py_INCREF(py_emission);
        Py_INCREF(py_transition);
        this->tagset_size=tagset_size;
        this->py_emission=py_emission;
        this->py_transition=py_transition;
        length=0;

        Py_INCREF(Py_None);
        raw=Py_None;

    };

    void set_tagset_size(size_t new_tagset_size){
        delete emissions;
        delete transitions;
        delete alphas;
        delete betas,
        tagset_size=new_tagset_size;

        emissions=new Score_Type[MAX_LEN*tagset_size];
        std::memset(emissions,0,sizeof(Score_Type)*MAX_LEN*tagset_size);

        alphas=new Alpha_Beta[MAX_LEN*tagset_size];
        std::memset(alphas,0,sizeof(Alpha_Beta)*MAX_LEN*tagset_size);

        betas=new Alpha_Beta[MAX_LEN*tagset_size];
        std::memset(betas,0,sizeof(Alpha_Beta)*MAX_LEN*tagset_size);

        transitions=new Score_Type[tagset_size*tagset_size];
        std::memset(transitions,0,sizeof(Score_Type)*tagset_size*tagset_size);
    };
    
    void set_raw(PyObject * raw){
        Py_DECREF(this->raw);
        Py_INCREF(raw);
        this->raw=raw;
    };

    ~Interface(){
        Py_DECREF(raw);
        Py_DECREF(py_emission);
        Py_DECREF(py_transition);
        delete emissions;
        delete alphas;
        delete betas,
        delete tags;
        delete transitions;
    };
};


inline size_t get_matrix(Interface* interface, PyObject* raw, PyObject* callable, size_t tagset_size, Score_Type*& array){
    PyObject * arglist;
    arglist=PyTuple_Pack(1,raw);
    PyObject * result = PyObject_CallObject(callable, arglist);
    Py_DECREF(arglist);
    long size=PySequence_Size(result);
    PyObject * ch;
    for(int i=0;i<size;i++){
        ch=PyList_GET_ITEM(result,i);

        long new_tag_set=PySequence_Size(ch);
        if(interface->tagset_size!=new_tag_set){
            interface->set_tagset_size(new_tag_set);
        };
        
        for(int j=0;j<tagset_size;j++){
            array[i*tagset_size+j]=(PyFloat_AsDouble(PyList_GET_ITEM(ch,j)));
        };
    };
    Py_DECREF(result);
    return size;
};

inline void update_results(PyObject* raw, PyObject* callable, size_t tagset_size,
        PyObject* result, Score_Type delta, size_t step){
    PyObject * arglist;
    PyObject * py_delta=PyFloat_FromDouble(delta);
    PyObject * py_step=PyLong_FromLong(step);
    arglist=PyTuple_Pack(4,raw,result,py_delta,py_step);
    PyObject * r = PyObject_CallObject(callable, arglist);
    Py_DECREF(py_delta);
    Py_DECREF(py_step);
    Py_DECREF(arglist);
    Py_DECREF(r);
};


static PyObject *
update_weights(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject * py_tags;
    double delta=0;
    long step=0;
    long action;
    PyArg_ParseTuple(arg, "LOdi", &interface,&py_tags,&delta,&step);
    
    update_results(interface->raw, interface->py_emission , interface->tagset_size,
        py_tags, delta, step);
    update_results(interface->raw, interface->py_transition , interface->tagset_size,
        py_tags, delta, step);

    
    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
set_raw(PyObject *self, PyObject *arg)
{
    Interface* interface;
    PyObject *new_raw;
    PyArg_ParseTuple(arg, "LO", &interface,&new_raw);
    interface->set_raw(new_raw);

    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
search(PyObject *self, PyObject *arg)
{

    Interface* interface;
    PyObject *py_init_states;
    PyArg_ParseTuple(arg, "LO", &interface,&py_init_states);



    interface->length=get_matrix(interface,interface->raw,interface->py_emission,
            interface->tagset_size,interface->emissions);
    
    get_matrix(interface,interface->raw,interface->py_transition,
            interface->tagset_size,interface->transitions);

    
    Score_Type score;
    score=dp_decode(
        interface->tagset_size,
        interface->length,
        interface->transitions,
        interface->emissions,
        interface->alphas,
        interface->tags
        );
    interface->score=score;

    // a list of tags

    //std::cout<<score<<"\n";
    
    PyObject * result_list;
    result_list=PyList_New(interface->length);
    for(int i=0;i<interface->length;i++){
        PyObject* ind=PyLong_FromLong(interface->tags[i]);
        PyList_SetItem(result_list,i,ind);

        /*

        for(int j=0;j<interface->tagset_size;j++){
            //std::cout<<interface->alphas[i*interface->tagset_size + j].value<<" ";
            //std::cout<<interface->betas[i*interface->tagset_size + j].value<<" ";
            std::cout<<interface->alphas[i*interface->tagset_size + j].value+
                    interface->betas[i*interface->tagset_size + j].value-
                    interface->emissions[i*interface->tagset_size + j]-
                    score
                    <<" ";
        }
        std::cout<<"\n";*/
        
    };

    
    // put the list into a tuple, then a list
    PyObject * rtn_list=PyList_New(1);
    PyObject * py_move=PyTuple_Pack(3,Py_None,Py_None,result_list);
    PyList_SetItem(rtn_list,0,py_move);
    Py_DECREF(result_list);
    return rtn_list;
};

static PyObject *
cal_margins(PyObject *self, PyObject *arg)
{

    Interface* interface;
    PyArg_ParseTuple(arg, "L", &interface);

    dp_cal_beta(
        interface->tagset_size,
        interface->length,
        interface->transitions,
        interface->emissions,
        interface->betas
        );


    PyObject * result_list;
    result_list=PyList_New(interface->length);

    for(int i=0;i<interface->length;i++){
        PyObject * step_list=PyList_New(interface->tagset_size);

        for(int j=0;j<interface->tagset_size;j++){
            PyObject * item_list=PyList_New(3);
            PyList_SetItem(item_list,0,PyFloat_FromDouble(
                        interface->alphas[i*interface->tagset_size + j].value
                        -interface->emissions[i*interface->tagset_size + j]
                        ));
            PyList_SetItem(item_list,1,PyFloat_FromDouble(
                        interface->emissions[i*interface->tagset_size + j]
                        ));
            PyList_SetItem(item_list,2,PyFloat_FromDouble(
                        interface->betas[i*interface->tagset_size + j].value
                        -interface->emissions[i*interface->tagset_size + j]
                        ));

            PyList_SetItem(step_list,j,item_list);

        }
        PyList_SetItem(result_list,i,step_list);
    };

    PyObject * final_list=PyList_New(2);
    PyList_SetItem(final_list,0,PyFloat_FromDouble(interface->score));
    PyList_SetItem(final_list,1,result_list);
    return final_list;
    
};

static PyObject *
module_new(PyObject *self, PyObject *arg)
{
    PyObject * py_emission; // call to get the emission score
    PyObject * py_transition; // call to get the transition score

    long ts;
    PyArg_ParseTuple(arg, "iOO",
            &ts,
            &py_emission,
            &py_transition);

    Interface* interface=new Interface(
            ts,
            py_emission,
            py_transition);

    return PyLong_FromLong((long)interface);
};

static PyObject *
interface_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};


static PyObject *
do_nothing(PyObject *self, PyObject *arg)
{
    Py_INCREF(Py_None);
    return Py_None;
};





/// to make the interface

/** stuffs about the module def */
static PyMethodDef interfaceMethods[] = {
    {"new",  module_new, METH_VARARGS,""},
    {"delete",  interface_delete, METH_O,""},
    {"set_raw",  set_raw, METH_VARARGS,""},
    {"set_step",  do_nothing, METH_VARARGS,""},
    {"set_penalty",  do_nothing, METH_VARARGS,""},
    {"search",  search, METH_VARARGS,""},
    {"set_action",  do_nothing, METH_VARARGS,""},
    {"update_action",  update_weights, METH_VARARGS,""},
    {"export_weights",  do_nothing, METH_VARARGS,""},
    {"make_dat",  do_nothing, METH_VARARGS,""},
    {"average_weights", do_nothing , METH_VARARGS,""},
    {"un_average_weights", do_nothing , METH_VARARGS,""},
    {"cal_margins",  cal_margins, METH_VARARGS,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

static struct PyModuleDef module_struct = {
   PyModuleDef_HEAD_INIT,
   STR(__MODULE_NAME),   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   interfaceMethods
};

PyMODINIT_FUNC
INIT_FUNC(PYINIT,__MODULE_NAME) (void)
{
    return PyModule_Create(&module_struct);
}

};//end of isan
