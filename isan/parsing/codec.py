#!/usr/bin/python3


class Prefix:
    def __init__(self):
        self.content=''
    def __call__(self,arg=''):
        tmp=self.content
        self.content=arg
        return tmp
        

def act_pop(stack):
    if len(stack)>1:
        sub=stack.pop()
        stack[-1].append(sub)

def normalize(tree,tag='s'):
    if type(tree)==str:
        assert(1==2)
    tree[0][1]=tag

    structure=[]
    for sub in tree[1:]:
        if type(sub)==str:
            
            if tree[0][0]=='m' and len(tree[1:])>1:
                structure.append([['f','-fix'],[sub,'f']])
            else:
                structure.append([[tree[0][0],'head'],[sub,tree[0][0]]])
        else:
            t= 'm' if not sub[0][1] else sub[0][1]
            #if t=='m' and tag=='m': t='f'
            structure.append(normalize(sub,t))
    print(tree[0])
    for struct in structure:
        print('  ',struct)
    print("")
    return [tree[0],structure]

def decode(line=None):
    #line='[(少将)称([(中方){[{完全}有(实力)]}{在(((黄岩)岛)[对峙])中}奉陪{到底}])]'
    #line='[{((实际)上)}({(中国)的}((国防)科技)部门){一直}{高度}关注({((博弈)论)的}(军事)应用)]'
    #line='[{曾经}纠结([{是否}让((搜狗)(输入)法)支持((火星)文)])]'
    line='''[[只要]a({[这样]的}大师)[在((我们)旁边)]出现]'''
    stack=[]
    
    prefix=Prefix()
    
    actions={
        '[':lambda stack: stack.append([['v',prefix('')]]),
        ']':lambda stack: act_pop(stack),
        '(':lambda stack: stack.append([['n',prefix('')]]),
        ')':lambda stack: act_pop(stack),
        '{':lambda stack: stack.append([['m',prefix('')]]),
        '}':lambda stack: act_pop(stack),
        '<':lambda stack: stack.append([['c',prefix('')]]),
        '>':lambda stack: act_pop(stack),
        'a':lambda stack: prefix('a'),
    }
    for token in line:
        if token in actions:
            actions[token](stack)
        else:
            if len(stack[-1])<2 or type(stack[-1][-1])!=str:
                stack[-1].append('')
            stack[-1][-1]+=token
    
    stack[0]=normalize(stack[0])
    return stack[0]
if __name__=="__main__":
    tree=decode()
    print(tree)
