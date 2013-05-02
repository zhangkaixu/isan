#pragma once
#include <string>
#include <iostream>
template<class ITEM>
class Smart_String{
public:
    typedef size_t SIZE_T;
    ITEM* pt;
    SIZE_T length;
    SIZE_T* _ref_count;
    Smart_String(){
        pt=NULL;
        length=0;
        _ref_count=new SIZE_T();
        *_ref_count=1;
    };
    Smart_String(ITEM* buffer, SIZE_T length){
        _ref_count=new SIZE_T();
        *_ref_count=1;
        pt=new ITEM[length];
        this->length=length;
        memcpy(pt,buffer,length*sizeof(ITEM));
    };
    Smart_String(SIZE_T length){
        _ref_count=new SIZE_T();
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
    inline void operator=(const Smart_String& other){
        (*_ref_count)--;
        if(!*_ref_count){
            delete _ref_count;
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
            delete _ref_count;
            if(pt)delete[] pt;
        }
    };

    inline bool operator==(const Smart_String&next) const{
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
    inline const size_t& size() const{
        return length;
    };

    class HASH{
    public:
        inline SIZE_T operator()(const Smart_String& cx) const{
            SIZE_T value=0;
            for(int i=0;i<cx.length;i++){
                value+=cx.pt[i]<<((i%8)*8);
            }
            return value;
        }
    };
};


class Smart_Chars{
public:
    typedef unsigned char Char;
private:
public:
    std::string str;
    PyObject* pack() const{
        return PyBytes_FromStringAndSize((char*)str.data(),str.length());
    };
    Smart_Chars(){
    };
    Smart_Chars(const Smart_Chars& other){
        str=other.str;
    };
    Smart_Chars(PyObject* py_key){
        char* buffer;
        Py_ssize_t len;
        PyBytes_AsStringAndSize(py_key,&buffer,&len);
        str=std::string(buffer,len);
    };
    Smart_Chars(Char* buffer, size_t length){
        str=std::string((char*)buffer,length);
    };
    Smart_Chars(const Smart_Chars& other,int length){
        str=std::string(other.str.data(),length);
    };
    inline void operator=(const Smart_Chars& other){
        str=other.str;
    };
    void make_positive(){
        for(int i=0;i<str.length();i++){
            if(str[i]==0){
                std::cout<<"zero\n";
            };
        };
    };
    inline const Char operator[](const int i) const{
        return (Char)str[i];
    };
    inline const size_t size() const{
        return str.length();
    };
    class HASH{
    public:
        inline size_t operator()(const Smart_Chars& cx) const{
            size_t value=0;
            for(int i=0;i<cx.str.length();i++){
                value+=(Char)cx.str[i]<<((i%8)*8);
                //value=131*value+cx.str[i];
            }
            return value;
            return value & 0x7FFFFFFF;
        }
    };
    inline bool operator==(const Smart_Chars&next) const{
        return this->str==next.str;
    };
    inline bool operator<(const Smart_Chars& next)const{
        if(this->str.length()<next.str.length())return 1;
        if(this->str.length()>next.str.length())return 0;
        for(int i=0;i<this->str.length();i++){
            if((Char)this->str[i]<(Char)next.str[i])return 1;
            if((Char)this->str[i]>(Char)next.str[i])return 0;
        }
        return 0;
    };
};
