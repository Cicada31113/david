import zipfile
import os
import csv
import pickle # 이진 저장을 위한 라이브러리 추가
import numpy as np
import math

#---------------------------------------------------------------------------------------
# 경로/압축
#---------------------------------------------------------------------------------------
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


#---------------------------------------------------------------------------------------
# 문제 1. 인벤토리 csv/이진 처리
#---------------------------------------------------------------------------------------


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
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in data:
                row[-1] = f"{float(row[-1]): .3f}"      # 인화성 지수(마지막 열) 소수점 3자리 고정
                writer.writerow(row)            
        print(f'{filename} 파일 저장 완료되었습니다')
    except OSError as e:
        print(f'파일 저장 오류: {e}')


def write_binary(data, filename):
    try:
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        print(f'{filename} 이진 파일 저장했다오')
    except OSError as e:
        print(f'이진 파일 저장 오류: {e}')

def read_binary(filename):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except OSError as e:
        print(f'이진 파일 읽기 오류: {e}')
        return []   # 이거 추가됨



#---------------------------------------------------------------------------------------
# 문제 2. 돔 표면적/무게 계산
#---------------------------------------------------------------------------------------

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
    """
    입력: diamter(m), material(glass/aluminum/carbon_steel), thickness(cm)
    전역 all_set에 요약 저장
    """
    try:
        # 표면적 
        R = float(input("diameter(m: meter): ").strip())
        if R <= 0 :
            raise ValueError(" 음수는 계산 불가능 ")
        r = R / 2.0
        surface_area = 3 * math.pi * (r ** 2)

        # 재질
        material = input("무슨 재질인데? 영어로 (glass, aluminum, carbon_steel): ").strip().lower()
        if material not in density_dict:
            raise ValueError("조건에 없는 재질임")
        density_g_cm3 = density_dict[material]

        # 두께
        raw = input("두께(cm, 기본=1): ").strip()
        thickness_cm = float(raw) if raw else 1.0
        if thickness_cm <= 0:
            raise ValueError("두께는 양수만")
        
        # 단위변환/계산
        # 질량(mass) = 부피 x 밀도 -> 단위:kg
        # 무게(weight) = 질량 x 중력가속도 -> 단위: 뉴턴(N)

        thickness_m = thickness_cm / 100.0
        density_kg_m3 = density_g_cm3 * 1000.0
        volume_m3 = surface_area * thickness_m
        mass_kg = volume_m3 * density_kg_m3
        weight_on_mars_N = mass_kg * 9.80665 * 0.38
        weight_mars_kg_equiv = mass_kg * MARS_G  # 응?

        # 출력
        print(f"면적(m^2): {surface_area:.3f}")
        print(f"무게(kg): {mass_kg:.3f}")
        print(f"화성에서의 무게(N): {weight_on_mars_N:.3f}")

        # 전역상태 저장 (성공시에만)
        all_set.update({
            'material': material,
            'diameter': R,
            'thickness': thickness_cm,
            'surface_area': round(surface_area, 3),
            'weight_mars_kg': round(weight_mars_kg_equiv, 3),
        })

        print('\n')

    except ValueError as e :   # 추가된건데 확인요망
        print("입력오류", e)
        return None, None, None       
    
        
#---------------------------------------------------------------------------------------
# 문제 3. 부품 데이터 통합 분석 (NumPy)
#---------------------------------------------------------------------------------------

def parts_analysis():
    try:
        def load(fname):
            return np.genfromtxt(
                fname, 
                delimiter=",",
                names=True, 
                dtype=None,         #혼합타입 자동
                encoding="utf-8"
            )
        
        a1 = load("mars_base_main_parts-001.csv")
        a2 = load("mars_base_main_parts-002.csv")
        a3 = load("mars_base_main_parts-003.csv")

        col1, col2 = a1.dtype.names

        names_all = np.concatenate([a1[col1], a2[col1], a3[col1]])
        vals_all = np.concatenate([a1[col2], a2[col2], a3[col2]]).astype(float)

        uniq, inv = np.unique(names_all, return_inverse=True)
        sums = np.bincount(inv, weights=vals_all, minlength=len(uniq))
        counts = np.bincount(inv, minlength=len(uniq))
        means = sums / counts
        
        # 평균 50 미만 필터링
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

    except Exception as e:
        print("에러:", e)

    try:
        parts2 = np.genfromtxt(
            "parts_to_work_on.csv",
            delimiter=",",
            skip_header=1,
            dtype=str,
            encoding='utf-8'
        )

        if parts2.size == 0:
            print("parts_to_work_on.csv 에 유효데이터 없어서 parts3 못만듦")
        else:
            if parts2.ndim == 1:
                parts2 = parts2.reshape(1, -1)

            np.savetxt("parts2.csv", parts2, delimiter=",", fmt="%s", encoding="utf-8")
            print("parts2.csv 저장완")

            parts3 = parts2.T
            np.savetxt("parts3.csv", parts3, delimiter=",", fmt="%s")
            print("parts3.csv 저장완")
            print(parts3)

    except Exception as e:
        print("에러:", e)


#---------------------------------------------------------------------------------------
# 메인
#---------------------------------------------------------------------------------------

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
