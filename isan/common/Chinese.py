#!/usr/bin/python3
"""
知识点：
    》unicode编码中，汉字的大体范围为：“一”-“鿋”
    》半角转全角，只需要内码加上65248,全角空格为12288
    
"""

#汉字集合
chinese_characters=set(chr(i) for i in range(ord('一'),ord('鿋')+1))
#阿拉伯数字集合
number_characters=set(chr(x) for x in range(ord('０'),ord('９')+1))
#拉丁字母
latin_characters=set(chr(x) for x in range(ord('ａ'),ord('ｚ')+1))
latin_characters.update(chr(x) for x in range(ord('Ａ'),ord('Ｚ')+1))

#内容字符，汉字、阿拉伯数字、拉丁字母的集合
content_characters=set()
content_characters.update(chinese_characters)
content_characters.update(number_characters)
content_characters.update(latin_characters)

#句末符号
full_stops=set('。？！')

def test():
    print("测试")

def to_full(text,ignore=set()):
    """
    半角转全角的程序
        空格变成全角
        大于空格的直接加上偏移量
        否则不变
    """
    
    return ''.join(chr(12288) if x==32 else chr(x+65248) if x<128 and x>32 and x not in ignore else chr(x)
            for x in map(ord,text))

def seg_sentence(text):
    """
    切分句子
    """
    cache=[]
    sentences=[]
    has_non=False
    for c in text:
        cache.append(c)
        if c in full_stops and has_non:
            cache=''.join(cache)
            
            cache=cache.strip()
            if cache:
                sentences.append(cache)
            cache=[]
            has_non=False
            
        elif c in content_characters:
            has_non=True
    if cache:
        if not sentences:sentences.append('')
        sentences[-1]+=''.join(cache)
    return sentences
            
def seg_by_punctuations(text):
    pass
if __name__=="__main__":
    
    print(seg_sentence(to_full('。“hello world？！wo23。”')))
