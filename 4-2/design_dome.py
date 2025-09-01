import zipfile
import os
import csv
import pickle # 이진 저장을 위한 라이브러리 추가
import numpy as np

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


def write_binary(data, filename):
    with open(filename, 'wb') as f:
        pickle.dump(data, f)
    print(f'{filename} 이진 파일 저장했다오')

def read_binary(filename):
    with open(filename, 'rb') as f:
        return pickle.load(f)




# 문제 2

import math

# 전역상태 저장
all_set = {
    'material': None,
    'diameter': None,
    'thickness': None,
    'area_m2': None,
    'weight_mars_kg': None,
}

density_dict = {
    'glass': 2.4,
    'aluminum': 2.7,
    'carbon_steel': 7.85,
}

MARS_G = 0.38 # 지구 중력의 0.38ㅂ0

def sphere_area():
    try:
        # 표면적 
        R = float(input("diameter(m: meter): ").strip())
        if R <= 0 :
            raise ValueError(" 음수는 계산 불가능 ")
        r = R / 2
        surface_area = 3 * math.pi * (r ** 2)

        # 재질
        material = input("무슨 재질인데? 영어로 (glass, aluminum, carbon_steel): ").strip().lower()
        if material not in density_dict:
            raise ValueError("조건에 없는 재질임")
        density = density_dict[material]

        # 밀도 단위 변환: g/cm -> kg/m
        density_kg_m3 = density_dict[material] * 1000


        # 두께
        thickness_in = input("두께(cm, 기본=1): ").strip()
        thickness_cm = float(thickness_in) if thickness_in else 1.0
        if thickness_cm <= 0:
            raise ValueError("두께는 양수여야함")
        thickness_m = thickness_cm / 100.0

        face_outer = surface_area * thickness_m
        mass_kg = face_outer * density_kg_m3
        weight_mars_kg = mass_kg * MARS_G

        all_set.update({
            'material': material,
            'diamter': R,
            'thickness': thickness_cm,
            'surface_area': round(surface_area, 3),
            'weight_mars_kg': round(weight_mars_kg, 3),
        })

        print('\n')
        print('---------------------결과값--------------------')
        print(f'surface_area: {surface_area: .3f} m**2')
        print(f'mass: {mass_kg: .3f} kg')
        print(f'weight on Mars(~kgf): {weight_mars_kg: .3f} kg')
        print(f'재질 -> {material}, 지름 -> {R: .3f}, 두께 -> {thickness_cm: .3f}, 면적 -> {surface_area: .3f} m^2, 무게 -> {weight_mars_kg: .3f} kg')

    except ValueError as e :
        print("입력오류", e)
        


def parts_analysis():
    try:
        def load(fname):
            return np.genfromtxt(
                fname, 
                delimiter=",",
                names=True, 
                dtype=None, 
                encoding="utf-8"
            )
        a1 = load("mars_base_main_parts-001.csv")
        a2 = load("mars_base_main_parts-002.csv")
        a3 = load("mars_base_main_parts-003.csv")

        col1, col2 = a1.dtype.names

        names_all = np.concatenate([a1[col1], a2[col1], a3[col1]])
        vals_all = np.concatenate([a1[col2], a2[col2], a3[col2]])

        uniq, inv = np.unique(names_all, return_inverse=True)
        sums = np.bincount(inv, weights=vals_all, minlength=len(uniq))
        counts = np.bincount(inv, minlength=len(uniq))
        means = sums / counts
        
        mask = means < 50
        work_names = uniq[mask]
        work_means = means[mask]

        with open("parts_to_work_on.csv", "w", encoding="utf-8", newline="") as f:
            if work_names.size == 0:
                f.write("part,mean_strength\n")
            else:
                out = np.column_stack([work_names, np.round(work_means, 2).astype(str)])
                np.savetxt(
                    f, out, delimiter=",", fmt="%s",
                    header="part,mean_stength", comments=""
                )
        print("parts_to_work_on.csv 저장완")

        if work_names.size == 0:
            print("전치 행렬:\n []")
        else:
            print("전치 행렬:\n", [list(work_names), list(np.round(work_means, 2))])

    except Exception as e:
        print("에러:", e)



def main():
    #1 압축해제
    unzip_file(zip_dir, zip_path)
    print('현재 작업 디렉토리 확인:', os.getcwd())
    print('----------------------------------')

    #2 CSV 읽기
    header, out1 = read_csv('Mars_Base_Inventory_List.csv')
    for row in out1:
        print(', '.join(row))
    print('----------------------------------')

    #3 위험도 0.7 이상인것만 추출
    out2 = sorted(out1, key=lambda x: float(x[4]), reverse=True)
    for row in out2:
        print(', '.join(row))
    print('----------------------------------')

    #4 위험도 0.7 이상인것만 추출
    out3 = [row for row in out2 if float(row[4]) >=0.7]
    for row in out3:
        print(', '.join(row))
    print('----------------------------------')

    #5 CSV 쓰기
    write_csv(header, out3, 'Mars_Base_Inventory_danger.csv')


    #6 이진 파일 쓰기
    write_binary(out2, 'Mars_Base_Inventory_List.bin')

    #7 이진 파일 읽기
    loaded = read_binary('Mars_Base_Inventory_List.bin')
    print("이진 파일 읽어왔어요:")
    for row in loaded:
        print(', '.join(row))
    print('----------------------------------------------------')
    

    # 반구체 표면적과 무게 계산
    sphere_area()

    print('\n')
    #Mars 부품데이터 통합 분석(Numpy 활용)
    parts_analysis()

if __name__ == '__main__':
    main()
