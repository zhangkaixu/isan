#!/usr/bin/python3
def decode(raw,gen):
    spans={}
    for i,c in enumerate(raw):
        d=gen.unary(raw,i)
        spans[(i,i+1)]=d
    for l in range(2,len(raw)+1):
        for i in range(0,len(raw)-l+1):
            j=i+l
            kv=[]
            for k in range(i+1,j):
                kv+=list(gen.binary(raw,i,k,j,spans[(i,k)],spans[(k,j)]).items())
            kv=sorted(kv)
            spans[(i,j)]=dict(kv)
    #print(spans[(0,len(raw))])
    results=sorted(list(spans[(0,len(raw))].items()),key=lambda x:x[1][0],reverse=True)
    #print(results[0])
    return results
class Gen:
    """
    默认的
    key 是head的下标，和整个短语目前的标签
    value[0]是整个短语目前的分数（这个是默认的，不能更改）
    value[1]是span
    value[2]是key
    value[3]是head所在子树下标
    value[4]是一个数组，指向各个子树
    """
    
    def unary(self,raw,i):
        return {(i,'x'):[0,(i,i+1),(i,'x'),-1,[]]}
    def binary(self,raw,i,k,j,left,right):
        m=dict()
        for lk,lv in left.items():
            for rk,rv in right.items():
                if lv[3]==-1:
                    m[lk]=[0,(i,j),lk,2
                else:
                    m[lk]=[0,(i,j),lk,lv[3],lv[4]+[rv]]

        return m
if __name__=="__main__":
    gen=Gen()
    results=decode('什么情况',gen)
    print(results[-1])
