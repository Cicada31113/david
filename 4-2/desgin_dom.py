import zipfile
import os


zip_dir = os.path.dirname(os.path.realpath(__file__))
zip_path = os.path.join(zip_dir, 'mars_base.zip') #경로지정 목적

with zipfile.ZipFile(zip_path, 'r') as zips:      # ZIP파일 열거얌
    zips.extractall(zip_dir)                  # extractall() : 압축해제
    print('압축해제 완료했지렁')

# from pathlib import Path
# folder_path = Path(zip_path).parent  이런식으로 폴더위치 지정해도됨
print(os.getcwd()) # -> 지금 작업디렉토리 확인하고 넘어가야함. 그래야 아래 csv 파일 열 수 있음.
print ('---------------------------위로 일단 파일 압축해제함-------------------------------')
print('\n')

def MBILCSV():
    with open ('Mars_Base_Inventory_List.csv', 'r', encoding='utf-8') as f:
        out1 = []
        header = f.readline().strip().split(',')
        print(', '.join(header))
        if not header:
            return header, out1
        
        for line in f:
            line = line.strip()
            parts = line.split(',')
            out1.append(parts)

            if len(parts) != 5:
                print('잘못된 것 같은데?')
                continue
    return header, out1

header, out1 = MBILCSV() 
for out1s in out1:
    print(', '.join(out1s))

print('-----------위로 csv파일 읽음-------------------------------')
print('\n')

print('------------FI 기준으로 내림차순 정렬할거임------------------')
out2 = sorted(out1, key=lambda x: float(x[4]), reverse=True)
for out2s in out2:
    print(', '.join(out2s))
print('---------------------------------------------------------')
print('\n')

print('----------------FI 기준 0.7이상인 항목만 출력----------------')
out3 = [x for x in out2 if float(x[4]) >= 0.7]
for out3s in out3:
    print(', '.join(out3s))

import csv
def write_FI07(header, out3):      #함수가 호출될때 입력값이 header와 out3라는 말
    with open('Mars_Base_Inventory_danger.csv', 'w', encoding='utf-8', newline='') as f:
        k = csv.writer(f)
        k.writerow(header)
        for out3s in out3:
            k.writerow(out3s)
    print('Mars_Base_Inventory_danger.csv 파일 생성 완료')
print('----------------------문제1번완료------------------------------')


def main():
    write_FI07(header, out3)

if __name__ == "__main__":
    main()