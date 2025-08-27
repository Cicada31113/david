import zipfile
import os
import csv

zip_dir = os.path.dirname(os.path.realpath(__file__))
zip_path = os.path.join(zip_dir, 'mars_base.zip') 

def unzip_file(zip_dir, zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zips:      # ZIP파일 열거얌
            zips.extractall(zip_dir)                  # extractall() : 압축해제
            print('압축해제 완료했지렁')
    
    except FileNotFoundError:
        print('파일이 없는데 ?')
    except zipfile.BadZipFile:
        print('zip파일이 좀 이상한가봐 ?')

# from pathlib import Path
# folder_path = Path(zip_path).parent  이런식으로 폴더위치 지정해도됨
print(os.getcwd()) # -> 지금 작업디렉토리 확인하고 넘어가야함. 그래야 아래 csv 파일 열 수 있음.
print ('---------------------------위로 일단 파일 압축해제함-------------------------------')
print('\n')

def read_csv(filename):
    out1 = []
    try:
        with open (filename, 'r', encoding='utf-8') as f:
            header = f.readline().strip().split(',')
            print('HEADER:',', '.join(header))
            if not header:
                return header, out1
            
            for line in f:
                parts = line.strip().split(',')
                if len(parts) != 5:
                    print('잘못된 것 같은데?')
                    continue
                out1.append(parts)
        return header, out1
    
    except FileNotFoundError:
        print('파일이 없는데 ?')
        return [], []          # header, out1 값 내놓는게 이 함수니까 문제발생시 빈리스트값 보여주자는거
    except Exception as e:
        print('뭔가 문제가 있는 것 같은데?', e)
        return [], []


def write_csv(header, data, filename):
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        for row in data:
            writer.writerow(row)
    print(f'{filename} 파일 저장 완료되었습니다')

def main():
    unzip_file(zip_dir, zip_path)
    print('현재 작업 디렉토리 확인:', os.getcwd())
    print('----------------------------------')

    header, out1 = read_csv('Mars_Base_Inventory_List.csv')
    for row in out1:
        print(', '.join(row))
    print('----------------------------------')

    out2 = sorted(out1, key=lambda x: float(x[4]), reverse=True)
    for row in out2:
        print(', '.join(row))
    print('----------------------------------')

    out3 = [row for row in out2 if float(row[4]) >=0.7]
    for row in out3:
        print(', '.join(row))
    print('----------------------------------')

    write_csv(header, out3, 'Mars_Base_Inventory_danger.csv')

if __name__ == '__main__':
    main()
