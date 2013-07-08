#include<cstdlib>
#include<vector>
#include<cstdio>
#include<iostream>
#include<fstream>
#include<string>
#include<unistd.h>
#include"dat.h"

using namespace dat;


void showhelp(){
    printf("双数组TRIE树构建器\n\t作者：张开旭\n");
    printf("    get words and make DAT\n");
    printf("-f filename\n    use filename instead of stdin\n");
    printf("-s\n    save base array and check array Seperately\n");
    printf("-P\n    申明没有一个词是另一个词的前缀，将编号存在base，而不是base指向的节点\n");
    
}
int main(int argc,char **argv){
    int c;
    int is_old_style=false;
    char* lexicon_filename=NULL;
    int no_prefix=0;
    char separator=0;
    while ( (c = getopt(argc, argv, "f:shPi")) != -1) {
        switch (c) {
            case 'i':// the index is 
                separator=' ';
                break;
            case 's'://seperated two arrays
                is_old_style=true;
                break;
            case 'P'://prefix free
                no_prefix=true;
                break;
            case 'f' : //specify the file
                lexicon_filename = optarg;
                break;            
            case 'h' :
            case '?' : 
            default : 
                showhelp();
                return 1;
        }
    }
    char* dat_filename=argv[optind];
    
    //输入文件名
    FILE* inputFile=stdin;
    std::istream* is=&std::cin;
    std::cout<<"begin\n";
    std::string str;
    if(lexicon_filename){
        std::cout<<"file\n";
        is=new std::ifstream(lexicon_filename,std::ifstream::in);
    }
   
    
    DATMaker dm;
    fprintf(stderr,"Double Array Trie Builder, author ZHANG, Kaixu\n");
    std::vector<DATMaker::KeyValue> lexicon;
    lexicon.push_back(DATMaker::KeyValue());
    int end_character=0;
    
    //load wordlist
    int id=0;

    void* rtn;
    do{
        rtn=std::getline(*is,str);
        if(str.length()==0)continue;
        if(separator){//to find a score as value instread of id
            int sep_ind=str.rfind(separator);
            //thulac::string_to_raw(str.substr(0,sep_ind),lexicon.back().key);
            //std::cout<<lexicon.back().key<<"\n";
            lexicon.back().value=atoi(str.substr(sep_ind+1).c_str());
        }else{
            //thulac::string_to_raw(str,lexicon.back().key);
            lexicon.back().value=id;
        }

        //init a new element
        lexicon.push_back(DATMaker::KeyValue());
        lexicon.back().key.clear();
        id+=1;
    }while(rtn);
        
    

    /*do{
        end_character=thulac::get_raw(lexicon.back().key,inputFile,32);//space is allowed
        if((int)lexicon.back().key.size()>0){
            if(separator){//to find a score as value instread of id
                int sep_ind=lexicon.back().key.rfind(separator);
                std::cout<<sep_ind<<"\n";
                lexicon.back().value=id;
            }else{
                lexicon.back().value=id;
            }

            //init a new element
            lexicon.push_back(DATMaker::KeyValue());
            lexicon.back().key.clear();
            id+=1;
        }
        if(end_character==-1)break;
    }while(1);*/
    if(lexicon_filename){
        fclose(inputFile);
    }
    lexicon.pop_back();
    
        

    
    
    fprintf(stderr,"%d words are loaded\n",(int)lexicon.size());
    dm.make_dat(lexicon,no_prefix);
    dm.shrink();
    fprintf(stderr,"size of DAT %d\n",(int)dm.dat_size);
    
    //save it
    if(is_old_style)
        dm.save_as_old_type(dat_filename);
    else
        dm.save_as(dat_filename);
    if(is!=&std::cin)delete is;
};


