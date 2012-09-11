
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
