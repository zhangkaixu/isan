#!/usr/bin/python3
class Path_Finding :
    """
    finding path in a DAG
    """
    class codec :
        @staticmethod
        def decode(line):
            """
            编码、解码
            从一行文本中，得到输入（raw）和输出（y）
            """
            if not line: return []
            seq=[word.split('_') for word in line.split()]

            
            print(seq)
            raw=''
            return {'raw':raw,
                    'y':seq,
                    'Y_a' : None,
                    'Y_b' : None,
                    }
        @staticmethod
        def encode(y):
            return ' '.join(y)
    pass
if __name__ == '__main__':
    pf=Path_Finding()
    for line in open('../lattice/test.lat') :
        line=line.strip()
        pf.codec.decode(line)

