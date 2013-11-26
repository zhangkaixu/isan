import math
class Base_Features :
    def __init__(self,args={},model=None,paras=None):
        if model == None :
            self.w=paras.add({})
        else :
            self.w=model

    def dump_weights(self):
        return self.w.output_obj()
    
    def add_model(self,model):
        self.w.add_model(model)
        pass

    def set_raw(self,atoms):
        self.atoms=atoms

    def __call__(self,ind1,ind2,ind3,delta=0) :
        strm=lambda x:'x' if x=='' else str(math.floor(math.log((x if x>0 else 0)*2+1)))
        w1,t1,m1,len1=self.atoms[ind1]
        w2,t2,m2,len2=self.atoms[ind2]
        w3,t3,m3,len3=self.atoms[ind3]
        fv=(
            (['m3~'+strm(m3), ] if m3 is not None else []) +
                ([ 'm3m2~'+strm(m3)+'~'+strm(m2), ] if m3 is not None  and m2 is not None else [])+
        [
                'w3~'+w3, 't3~'+t3, 'l3~'+len3, 'w3t3~'+w3+t3, 'l3t3~'+len3+t3,

                'w3w2~'+w3+"~"+w2, 'w3t2~'+w3+t2, 't3w2~'+t3+w2, 't3t2~'+t3+t2,

                'l3w2~'+len3+'~'+w2, 'w3l2~'+w3+'~'+len2, 'l3t2~'+len3+'~'+t2, 't3l2~'+t3+'~'+len2,
                'l3l2~'+len3+'~'+len2,
                
                't3t1~'+t3+'~'+t1, 't3t2t1~'+t3+'~'+t2+'~'+t1,
                'l3l1~'+len3+'~'+len1, 'l3l2l1~'+len3+'~'+len2+'~'+len1,
                ])

        if delta==0 :
            v= float(self.w(fv))
            return v
        else :
            self.w.add_delta(fv,delta*100)
            return 0

