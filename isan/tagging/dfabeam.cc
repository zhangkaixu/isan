#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "dfa_beam_searcher.hpp"
#include "cws.hpp"
#include "isan/common/weights.hpp"
/**
 * g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3

 * */

typedef Weights<String<char> ,Score_Type> Default_Weights;

void list_to_fv(PyObject * list, std::vector<String<char> > & fv){
    fv.clear();
    
    long size=PySequence_Size(list);
    char* buffer;
    size_t length;
    for(int i=0;i<size;i++){
        PyObject * bytes=PySequence_GetItem(list,i);
        PyBytes_AsStringAndSize(bytes,&buffer,(Py_ssize_t*)&(length));
        fv.push_back(String<char>(buffer,length));
        Py_DECREF(bytes);
    };
    Py_DECREF(list);
};


class Searcher_Data : public DFA_Beam_Searcher_Data<State_Key,Action_Type,Score_Type> {
public:
    State_Key* pinit_key;
    PyObject *keygen;
    Chinese* raw;
    std::map<Action_Type, Weights<String<char> ,Score_Type>* > actions;
    Searcher_Data(State_Key* pinit_key,PyObject *keygen){
        this->pinit_key=pinit_key;
        this->keygen=keygen;
        raw=NULL;
        this->x=321;
        Py_INCREF(keygen);
    };
    void gen_next(State_Key& key,std::vector<Triple<State_Key,Action_Type,Score_Type> >& nexts){
        
        std::vector<String<char> > fv;
        
        
        PyObject * state=key.pack();
        PyObject *result =PyList_New(0);
        PyObject * arglist=Py_BuildValue("(OO)",state,result);
        
        PyObject * ret= PyObject_CallObject(this->keygen, arglist);
        Py_CLEAR(ret);
        
        //list_to_fv(ret,fv);
        default_feature(*raw,key,fv);
        
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
            
            //(*(this->actions[nexts[i].action]))(fv);
            //std::cout<<(*(this->actions[nexts[i].action])).map->size()<<"\n";
            //std::cout<<this->actions.size()<<"\n";
            //std::cout<<fv[0].length<<"\n";
            nexts[i].score=(*(this->actions[nexts[i].action]))(fv);
            //std::cout<<(size_t)weights<<" "<<(size_t)(this->actions[nexts[i].action])<< "\n";
            //nexts[i].score=PyLong_AsLong(tmp_item);Py_DECREF(tmp_item);
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
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);

    
    tmp=PySequence_GetItem(arg,1);
    std::vector<Action_Type> result=interface->searcher->call(*(interface->init_key),PyLong_AsLong(tmp));
    Py_CLEAR(tmp);

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
    
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    State_Key* init_key = new State_Key(tmp);
    Py_CLEAR(tmp);

    PyObject *callback=PySequence_GetItem(arg,1);

    tmp=PySequence_GetItem(arg,2);
    int beam_width=PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
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
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    PyObject *new_raw=PySequence_GetItem(arg,1);
    long raw_size=PySequence_Size(new_raw);
    if(interface->searcher_data->raw)delete interface->searcher_data->raw;
    interface->searcher_data->raw=new Chinese(raw_size);
    for(int i=0;i<raw_size;i++){
        PyObject *tmp=PySequence_GetItem(new_raw,i);
        interface->searcher_data->raw->pt[i]=(Chinese_Character)*PyUnicode_AS_UNICODE(tmp);

        Py_CLEAR(tmp);
    }
    Py_CLEAR(new_raw);
    Py_INCREF(Py_None);
    
    return Py_None;
};

static PyObject *
set_action(PyObject *self, PyObject *arg)
{
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    tmp=PySequence_GetItem(arg,1);
    Action_Type action=(Action_Type)* PyUnicode_AS_UNICODE(tmp);
    Py_CLEAR(tmp);
    
    tmp=PySequence_GetItem(arg,2);
    Weights<String<char> ,Score_Type>* weights=(Weights<String<char> ,Score_Type>*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    interface->searcher_data->actions[action]=new Weights<String<char> ,Score_Type>();
    Py_INCREF(Py_None);
    return Py_None;
};

static PyObject *
update_action(PyObject *self, PyObject *arg)
{
    PyObject * tmp; 
    tmp=PySequence_GetItem(arg,0);
    Interface* interface=
            (Interface*)PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    tmp=PySequence_GetItem(arg,1);
    State_Key state(tmp);
    Py_CLEAR(tmp);
    tmp=PySequence_GetItem(arg,2);
    Action_Type action=(Action_Type)* PyUnicode_AS_UNICODE(tmp);
    Py_CLEAR(tmp);
    tmp=PySequence_GetItem(arg,3);
    long delta=PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    tmp=PySequence_GetItem(arg,4);
    long step=PyLong_AsLong(tmp);
    Py_CLEAR(tmp);
    
    std::vector<String<char> > fv;
    default_feature(*(interface->searcher_data->raw),state,fv);
    
    
    (*(interface->searcher_data->actions[action])).update(fv,delta,step);
    
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
    {"set_action",  set_action, METH_O,""},
    {"update_action",  update_action, METH_O,""},
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
