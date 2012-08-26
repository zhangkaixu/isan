#include <Python.h>
#include <iostream>
#include <vector>
#include <map>
#include "dfa_beam_searcher.cc"
/**
 * g++ dfabeam.cc -I /usr/include/python3.2mu -shared -o dfabeam.so -fPIC -O3

 * */



typedef char Action_Type;
typedef int Score_Type;
struct State_Key{
    short ind;
    Action_Type last_action;
    Action_Type last_last_action;
    short sep_ind;
    State_Key(){
        this->ind=0;this->last_action=0;
        this->last_last_action=0;this->sep_ind=0;
    };
    State_Key(PyObject* py_key){
        this->ind=PyLong_AsLong(PySequence_GetItem(py_key,0));
        this->last_action=*PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,1));
        this->last_last_action=*PyUnicode_AS_UNICODE(PySequence_GetItem(py_key,2));
        this->sep_ind=PyLong_AsLong(PySequence_GetItem(py_key,3));
    
    
    };
    bool operator<(const State_Key& next)const{
        if (this->ind < next.ind) return 1;
        if (this->ind > next.ind) return 0;
        if (this->last_action < next.last_action) return 1;
        if (this->last_action > next.last_action) return 0;
        if (this->last_last_action < next.last_last_action) return 1;
        if (this->last_last_action > next.last_last_action) return 0;
        if (this->sep_ind < next.sep_ind) return 1;
        if (this->sep_ind > next.sep_ind) return 0;
        return 0;
    };
    PyObject* pack(){
        unsigned int la=this->last_action;
        unsigned int lla=this->last_last_action;
        return PyTuple_Pack(4,
                PyLong_FromLong(this->ind),
                //PyUnicode_FromUnicode((unsigned int*)&(this->last_action),1),
                //PyUnicode_FromUnicode((unsigned int*)&(this->last_last_action),1),
                PyUnicode_FromUnicode(&la,1),
                PyUnicode_FromUnicode(&lla,1),
                PyLong_FromLong(this->sep_ind)
        );
    }
};



class Searcher_Data : public DFA_Beam_Searcher_Data<State_Key,Action_Type,Score_Type> {
public:
    State_Key* pinit_key;
    PyObject *keygen;
    
    Searcher_Data(State_Key* pinit_key,PyObject *keygen){
        this->pinit_key=pinit_key;
        this->keygen=keygen;
        this->x=321;
        Py_INCREF(keygen);
    };
    void gen_next(State_Key& key,std::vector<Triple<State_Key,Action_Type,Score_Type> >& nexts){
        PyObject *result = PyObject_CallObject(this->keygen, Py_BuildValue("(O)",key.pack()));
        long size=PySequence_Size(result);
        while(nexts.size()>size){
            nexts.pop_back();
        };
        while(nexts.size()<size){
            nexts.push_back(Triple<State_Key,Action_Type,Score_Type>());
        };
        for(int i=0;i<size;i++){
            PyObject * tri=PySequence_GetItem(result,i);
            nexts[i].key=State_Key(PySequence_GetItem(tri,0));
            nexts[i].action=*PyUnicode_AS_UNICODE(PySequence_GetItem(tri,1));
            nexts[i].score=PyLong_AsLong(PySequence_GetItem(tri,2));
        };
    };
    
    ~Searcher_Data(){
        Py_DECREF(keygen);
    };
};


State_Key *init_key;
PyObject *callback;
Searcher_Data* searcher_data;
DFA_Beam_Searcher<State_Key,Action_Type,Score_Type>* searcher;

static PyObject *
set_init(PyObject *self, PyObject *arg)
{
    init_key = new State_Key(PySequence_GetItem(arg,0));
    callback=PySequence_GetItem(arg,1);
    //std::cout<<init_key->ind<<" "<<init_key->last_action<<"\n";
    
    searcher_data=new Searcher_Data(init_key,callback);
    searcher=new DFA_Beam_Searcher<State_Key,Action_Type,Score_Type>(searcher_data,8);
    
    Py_INCREF(Py_None);
    return Py_None;
};



static PyObject *
search(PyObject *self, PyObject *py_step)
{
    
    //searcher_data->gen_next(*init_key);
    std::vector<Action_Type> result=searcher->call(*init_key,PyLong_AsLong(py_step));
    
    PyObject * list=PyList_New(result.size());
    
    for(int i=0;i<result.size();i++){
        unsigned int la=result[i];
        PyList_SetItem(list,i,PyUnicode_FromUnicode(&la,1));
    }
    return list;
    
    Py_INCREF(Py_None);
    return Py_None;
};



/** stuffs about the module def */
static PyMethodDef dfabeamMethods[] = {
    //{"system",  spam_system, METH_VARARGS,"Execute a shell command."},
    //{"add",  spam_add, METH_O,""},
    {"set_init",  set_init, METH_O,""},
    {"search",  search, METH_O,""},
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
