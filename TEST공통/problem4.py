# 예외처리 우선순위 잡는게 중요하다

import math

def sphere_area(diameter_cm: float, material: str, thickness_cm: float = 1.0) -> tuple[float, float]:
    # 1) 입력값 검증
    if diameter_cm <= 0 or thickness_cm <= 0:
        raise ValueError
    if material not in ['유리', '알루미늄', '탄소강']:
        raise ValueError

    # 2) 밀도: g/cm³
    densities = {
        '유리': 2.4,
        '알루미늄': 2.7,
        '탄소강': 7.85
    }

    # 3) 면적: 먼저 cm²로 계산 후 m²로 변환 (구 표면적 S = π * d²)
    area_cm2 = math.pi * (diameter_cm ** 2)
    area_m2 = area_cm2 / 10000.0  # cm² → m²

    # 4) 질량: g = (g/cm³) * (cm²) * (cm)
    mass_g = densities[material] * area_cm2 * thickness_cm
    mass_kg = mass_g / 1000.0

    # 5) 화성에서의 무게(kgf로 해석: 지구 중량의 0.38배)
    weight_kgf_mars = mass_kg * 0.38
    # ※ 만약 뉴턴(N)으로 요구되면:
    # weight_N_mars = mass_kg * 0.38 * 9.80665

    # 문제 조건: float 2개 반환 → (면적[m²], 무게[kgf])
    return (area_m2, weight_kgf_mars)

def main():
    try:
        diameter = float(input("구의 지름을 입력하세요 (cm): "))   # strip안써서 실패함
        if diameter <= 0:
            raise ValueError

        material = input("재질을 입력하세요(유리/알루미늄/탄소강): ").strip()
        if material not in ['유리', '알루미늄', '탄소강']:
            raise ValueError

        t_in = input("두께를 입력하세요 (기본값 1.0 cm, 생략 가능): ").strip()
        thickness = float(t_in) if t_in else 1.0
        if thickness <= 0:
            raise ValueError

        area_m2, weight_kgf = sphere_area(diameter, material, thickness)

        # ※ 뉴턴(N)이면 weight_kgf 대신 weight_N 계산 후 단위 N로 출력
        print( f"재질 ⇒ {material}, 지름 ⇒ {diameter:g} cm, 두께 ⇒ {thickness:g} cm, 면적 ⇒ {area_m2:.3f} m²,  무게(화성) ⇒ {weight_kgf:.3f} kgf")

    except ValueError:
        # ★ 자동채점이면 정확 문구로 바꿔라(예: "Invalid input.")
        print("Invalid input.")
    except Exception:
        # ★ 자동채점이면 정확 문구로 바꿔라(예: "Error")
        print("Error")

if __name__ == '__main__':
    main()