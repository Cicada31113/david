import zipfile
import string
import itertools
import random
import time
import optparse

# 중간 종료를 위한 변수
en_exit=0
# keyword list + add character max number
addcharmax=3

#--------------------
# zip 파일 패스워드 풀기 
#(패스워드는 리스트 파일에서 가져옴)
#--------------------
def unzip_file(zipfilename,dictionary):
    global en_exit
    t0=time.time()
    password = None
    zip_file = zipfile.ZipFile(zipfilename)

    #Tries at first a dictionary attack 
    print("--------------------------")
    print("1. Find password in keyword list")
    print("--------------------------")
    with open(dictionary, 'r') as f:
        for line in f.readlines():
            password_string = line.strip('\n')
            try:
                password = bytes(password_string, 'utf-8')
                zip_file.extractall(pwd=password)
                t1=time.time()
                total = t1 - t0
                print('Password found : %s' %password_string)
                print('Time spent : %f seconds' %total)
                en_exit=1

            except:
                continue
            
            if(en_exit==1):
                break
    f.close

#--------------------
# keyword list + any character
#--------------------
def unzip_file2(zipfilename,dictionary):
    global en_exit
    
    if (en_exit==0):
        t0=time.time()
        password = None
        zip_file = zipfile.ZipFile(zipfilename)
        
        global addcharmax #Maximum length to test
        alphabet = string.ascii_letters + string.digits + string.punctuation 
        
        print(" => There is no compressed password in the keyword list.")
        print("--------------------------")
        print("2. Find Password with 'Keyword + Broad forcing'")
        print("--------------------------")
        #If the password hasn't been found yet, the function switches to bruteforce
        with open(dictionary, 'r') as f:
            for line in f.readlines():
                password_string = line.strip('\n')
                #print("==========================")
                print("keyword list: " + password_string)
                #print("==========================")
                #crack2_option(zip_file, password_string)
                for i in range(1,addcharmax):
                    #print('Testing length = %i' % i)
                    for j in itertools.product(alphabet, repeat=i):
                        try:
                            password_bf="{0}{1}".format(password_string, ''.join(j))
                            #print(password_bf)
                            password = bytes(password_bf, 'utf-8')
                            zip_file.extractall(pwd=password)
                            t1=time.time()
                            total = t1 - t0
                            print("==========================")
                            print('Password found : %s' %password_bf)
                            print('Time spent : %f seconds' %total)
                            print("==========================")
                            en_exit=1
                        except:
                            continue
                            
                        if(en_exit==1):
                            break
                    if(en_exit==1):
                        break
                if(en_exit==1):
                    break
        f.close

if __name__ == "__main__":
    # ex). python test.py -f Test.zip -d dictionary.txt
    parser = optparse.OptionParser(usage="사용법: python zip_bruteforce.py " + "-f 'zip 파일명' -d '비밀번호 키 모음 파일'") 
    
    parser.add_option("-f", dest="zname", type="string", help="Specify Zip File")
    parser.add_option("-d", dest="dname", type="string", help="Specify Dictionary Name")
    # 튜플 형의 변수에 parse_args() 메서드를 호출하면 options, args 분리 저장
    (options, args) = parser.parse_args() 

    if (options.zname == None) | (options.dname == None) :
        print(parser.usage)
        exit(0)
    else:
        zip_filename = options.zname
        pass_filename = options.dname
        print("--------------------------")
        print("input filename:{0}, password file: {1}".format(zip_filename, pass_filename))
        print("--------------------------")
    #crack('test.zip','dictionary.txt')
    unzip_file(zip_filename, pass_filename)
    unzip_file2(zip_filename, pass_filename)