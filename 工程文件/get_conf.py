import re

def get_conf(txt):
    txt=re.sub('#.*','',txt)
    txt=re.sub(';.*','',txt)
    txt=re.sub(' ','',txt)
    txt=re.sub('\t','',txt)
    txts=str(txt).split('\n')
    dic={}
    nowdic=''
    for line in txts:
        if len(line)==0:
            continue
        if len(re.findall('\[.*\]',line))!=0:
            nowdic=re.findall('\[.*\]', line)[0][1:-1]
            dic[nowdic]={}
        elif len(re.findall('\w*=\w*',line))!=0:
            res=line.split('=')
            dic[nowdic][res[0]]=res[1]
        else:
            # dic[nowdic][len(dic[nowdic].keys())]=line#支持多个没有等号的
            dic[nowdic]=line#没等号的只取最后一个
    return dic



if __name__=="__main__":
    f=open('test.txt','r',encoding='gbk')
    txt=f.read()
    dic=get_conf(txt)
    print(dic)