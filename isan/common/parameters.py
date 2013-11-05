"""

"""

class Parameters :
    def __init__(self,para_class):
        self.para_class=para_class
        self._list=list()
        self._dirty=list()

    def add(self,value):
        if type(value)== dict :
            p=self.para_class.d(value)
            p.init(self)
        else :
            p=value.view(self.para_class.ndarray)
            p.init(self)
        self._list.append(p)
        return p

    def update(self,step=0) :
        for p in self._dirty :
            p._update(step)
        del self._dirty[:]

    def final(self,step):
        for p in self._list :
            if hasattr(p,'final') :
                p.final(step)

    def un_final(self):
        for p in self._list :
            if hasattr(p,'un_final') :
                p.un_final()

