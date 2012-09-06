#pragma once
#include <vector>
#include <map>

namespace isan{

typedef unsigned short Chinese_Character;
typedef int Score_Type;


template<class ITEM>
class Smart_String{
public:
    ITEM* pt;
    size_t length;
    size_t* _ref_count;
    Smart_String(){
        pt=NULL;
        length=0;
        _ref_count=new size_t[1];
        *_ref_count=1;
    };
    Smart_String(ITEM* buffer, size_t length){
        _ref_count=new size_t[1];
        *_ref_count=1;
        pt=new ITEM[length];
        this->length=length;
        memcpy(pt,buffer,length*sizeof(ITEM));
    };
    Smart_String(size_t length){
        _ref_count=new size_t[1];
        *_ref_count=1;
        pt=new ITEM[length];
        this->length=length;
    };
    Smart_String(const Smart_String& other){
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
    void operator=(const Smart_String& other){
        (*_ref_count)--;
        if(!*_ref_count){
            delete[] _ref_count;
            if(pt)delete[] pt;
        }
        pt=other.pt;
        length=other.length;
        _ref_count=other._ref_count;
        (*_ref_count)++;
    };
    ~Smart_String(){
        (*_ref_count)--;
        if(!*_ref_count){
            delete[] _ref_count;
            if(pt)delete[] pt;
        }
    };

    inline bool operator==(const Smart_String &next) const{
        if(length!=next.length)
            return false;
        if(pt==next.pt)return true;
        for(int i=0;i<length;i++){
            if(pt[i]!=next.pt[i])return false;
        }
        return true;
    };
    inline bool operator<(const Smart_String& next)const{
        if(length<next.length)return 1;
        if(length>next.length)return 0;
        for(int i=0;i<length;i++){
            if(pt[i]<next.pt[i])return 1;
            if(pt[i]>next.pt[i])return 0;
        }
        return 0;
    };
    class HASH{
    public:
        inline size_t operator()(const Smart_String& cx) const{
            size_t value=0;
            for(int i=0;i<cx.length;i++){
                value+=cx.pt[i]<<((i%8)*8);
            }
            return value;
        }
    };
};

typedef unsigned char Action_Type;

template <class RAW, class STATE, class FEATURE_VECTOR>
class Feature_Generator{
public:
    RAW* raw;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(const STATE& key, FEATURE_VECTOR& fv)=0;
};

template <class RAW, class STATE, class ACTION>
class State_Generator{
public:
    RAW* raw;
    STATE init_state;
    void set_raw(RAW* raw){
        this->raw=raw;
    };
    virtual void operator()(STATE& key, std::vector<ACTION>&,std::vector<STATE > & nexts)=0;

};

typedef Smart_String<Chinese_Character> Chinese;
typedef Smart_String<char> Feature_String;
typedef std::vector<Feature_String> Feature_Vector;

class State_Type: public Smart_String<char>{
public:
    PyObject* pack() const{
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

typedef Feature_Generator<Chinese,State_Type,Feature_Vector> General_Feature_Generator;
typedef State_Generator<Chinese,State_Type,Action_Type> General_State_Generator;
class Python_Feature_Generator: public General_Feature_Generator{
public:
    PyObject * callback;
    Python_Feature_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_Feature_Generator(){
        Py_DECREF(callback);
    };
    void operator()(const State_Type& state, Feature_Vector& fv){
        PyObject * pkey=state.pack();
        PyObject * arglist=PyTuple_Pack(1,pkey);
        PyObject * pfv= PyObject_CallObject(this->callback, arglist);
        Py_DECREF(pkey);
        Py_DECREF(arglist);
        
        fv.clear();
        char* buffer;
        size_t length;
        long size=PySequence_Size(pfv);
        for(int i=0;i<size;i++){
            PyBytes_AsStringAndSize(PyList_GET_ITEM(pfv,i),&buffer,(Py_ssize_t*)&(length));
            fv.push_back(Feature_String(buffer,length));
        };
        Py_DECREF(pfv);
    };
};


class Python_State_Generator: public General_State_Generator{
public:
    PyObject * callback;
    Python_State_Generator(PyObject * callback){
        Py_INCREF(callback);
        this->callback=callback;
    };
    ~Python_State_Generator(){
        Py_DECREF(callback);
    };
    void operator()(State_Type& key, std::vector<Action_Type>&next_actions,std::vector<State_Type> & next_states){
        PyObject * state=key.pack();
        PyObject * arglist=Py_BuildValue("(O)",state);
        PyObject * result= PyObject_CallObject(this->callback, arglist);
        Py_CLEAR(state);Py_CLEAR(arglist);
        
        long size=PySequence_Size(result);
        PyObject * tri;
        PyObject * tmp_item;
        next_actions.resize(size);
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
};




};//end of isan
