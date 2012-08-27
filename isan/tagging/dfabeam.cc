#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "dfa_beam_searcher.hpp"
#include "cws.hpp"
/**
 * g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3

 * */








class Searcher_Data : public DFA_Beam_Searcher_Data<State_Key,Action_Type,Score_Type> {
public:
    State_Key* pinit_key;
    PyObject *keygen;
    Chinese* raw;
    Searcher_Data(State_Key* pinit_key,PyObject *keygen){
        this->pinit_key=pinit_key;
        this->keygen=keygen;
        raw=NULL;
        this->x=321;
        Py_INCREF(keygen);
    };
    void gen_next(State_Key& key,std::vector<Triple<State_Key,Action_Type,Score_Type> >& nexts){
        
        std::vector<String<char> > fv;
        default_feature(*raw,key, fv);
        
        PyObject * state=key.pack();
        PyObject *result =PyList_New(0);
        PyObject * arglist=Py_BuildValue("(OO)",state,result);
        
        PyObject_CallObject(this->keygen, arglist);
        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        
        
        key.pack_decref(state);Py_CLEAR(arglist);
        
        
        
        while(nexts.size()>size){
            nexts.pop_back();
        };
        while(nexts.size()<size){
            nexts.push_back(Triple<State_Key,Action_Type,Score_Type>());
        };


        for(int i=0;i<size;i++){
            PyObject * tri=PySequence_GetItem(result,i);
            PyObject * tmp_item=PySequence_GetItem(tri,0);
            nexts[i].key=State_Key(tmp_item);Py_DECREF(tmp_item);
            tmp_item=PySequence_GetItem(tri,1);
            nexts[i].action=*PyUnicode_AS_UNICODE(tmp_item);Py_DECREF(tmp_item);
            tmp_item=PySequence_GetItem(tri,2);
            nexts[i].score=PyLong_AsLong(tmp_item);Py_DECREF(tmp_item);
            Py_DECREF(tri);
        };
        
        PySequence_DelSlice(result,0,size);
        
        Py_DECREF(result);
    };
    
    ~Searcher_Data(){
        Py_DECREF(keygen);
        if(raw)delete raw;
    };
};



class Interface{
public:
    State_Key *init_key;
    PyObject *callback;
    Searcher_Data* searcher_data;
    DFA_Beam_Searcher<State_Key,Action_Type,Score_Type>* searcher;
    Chinese* raw;
    
    Interface(State_Key *init_key,PyObject *callback,int beam_width){
        raw=NULL;
        searcher_data=new Searcher_Data(init_key,callback);
        this->init_key=init_key;
        searcher=new DFA_Beam_Searcher<State_Key,Action_Type,Score_Type>(searcher_data,beam_width);
    };
};





static PyObject *
search(PyObject *self, PyObject *arg)
{
    
    Interface* interface=
            (Interface*)PyLong_AsLong(PySequence_GetItem(arg,0));

    
    std::vector<Action_Type> result=interface->searcher->call(*(interface->init_key),PyLong_AsLong(PySequence_GetItem(arg,1)));
    

    PyObject * list=PyList_New(result.size());
    
    for(int i=0;i<result.size();i++){
        unsigned int la=result[i];
        PyList_SetItem(list,i,PyUnicode_FromUnicode(&la,1));
    }
    return list;
};


static PyObject *
searcher_new(PyObject *self, PyObject *arg)
{
    
    State_Key* init_key = new State_Key(PySequence_GetItem(arg,0));
    PyObject *callback=PySequence_GetItem(arg,1);
    int beam_width=PyLong_AsLong(PySequence_GetItem(arg,2));
    Interface* interface=new Interface(init_key,callback,beam_width);
    
    
    return PyLong_FromLong((long)interface);
};

static PyObject *
searcher_delete(PyObject *self, PyObject *arg){
    delete (Interface*)PyLong_AsLong(arg);
    Py_INCREF(Py_None);
    return Py_None;
};


static PyObject *
set_raw(PyObject *self, PyObject *arg)
{
    Interface* interface=
            (Interface*)PyLong_AsLong(PySequence_GetItem(arg,0));
    PyObject *new_raw=PySequence_GetItem(arg,1);
    long raw_size=PySequence_Size(new_raw);
    if(interface->searcher_data->raw)delete interface->searcher_data->raw;
    interface->searcher_data->raw=new Chinese(raw_size);
    for(int i=0;i<raw_size;i++){
        interface->searcher_data->raw->pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(PySequence_GetItem(new_raw,i));
    }
    Py_INCREF(Py_None);
    
    return Py_None;
};

/** stuffs about the module def */
static PyMethodDef dfabeamMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    //{"add",  spam_add, METH_O,""},
    {"search",  search, METH_O,""},
    {"new",  searcher_new, METH_O,""},
    {"delete",  searcher_delete, METH_O,""},
    {"set_raw",  set_raw, METH_O,""},
    //{"test_map",  test_map, METH_O,""},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};
static struct PyModuleDef dfabeammodule = {
   PyModuleDef_HEAD_INIT,
   "dfabeam",   /* name of module */
   NULL, /* module documentation, may be NULL */
   -1,       /* size of per-interpreter state of the module,
                or -1 if the module keeps state in global variables. */
   dfabeamMethods
};

PyMODINIT_FUNC
PyInit_dfabeam(void)
{
    return PyModule_Create(&dfabeammodule);
}
