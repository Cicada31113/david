# design_dome.py
import math

def sphere_area(diameter: float, material: str, thickness: float = 1.0) -> tuple[float, float]:
    if not isinstance(diameter, (int, float)) or diameter <= 0:
        raise ValueError
    if not isinstance(thickness, (int, float)) or thickness <= 0:
        raise ValueError
    if not isinstance(material, str):
        raise ValueError

    material = material.strip()
    densities_g_per_cm3 = {'유리': 2.4, '알루미늄': 2.7, '탄소강': 7.85}
    if material not in densities_g_per_cm3:
        raise ValueError

    area_m2 = math.pi * (diameter ** 2)        # π·d^2 (m^2)
    area_cm2 = area_m2 * 10000.0               # m^2 → cm^2
    volume_cm3 = area_cm2 * thickness          # cm^3
    mass_kg = densities_g_per_cm3[material] * volume_cm3 / 1000.0
    mars_weight_kg = mass_kg * 0.38
    return area_m2, mars_weight_kg

def main() -> None:
    try:
        diameter_str = input('지름(m)을 입력하세요:').strip()
        material_kor = input('재질(유리/알루미늄/탄소강)을 입력하세요:').strip()
        thickness_str = input('두께(cm)를 입력하세요(기본값 1):').strip()

        if not diameter_str:
            print('Invalid input.'); return
        try:
            diameter_m = float(diameter_str)
        except Exception:
            print('Invalid input.'); return
        if diameter_m <= 0:
            print('Invalid input.'); return

        if material_kor not in ('유리', '알루미늄', '탄소강'):
            print('Invalid input.'); return

        if thickness_str == '':
            thickness_cm = 1.0
        else:
            try:
                thickness_cm = float(thickness_str)
            except Exception:
                print('Invalid input.'); return
            if thickness_cm <= 0:
                print('Invalid input.'); return

        try:
            area_m2, mars_weight_kg = sphere_area(diameter_m, material_kor, thickness_cm)
        except ValueError:
            print('Invalid input.'); return
        except Exception:
            print('Processing error.'); return

        try:
            print(f'재질 : {material_kor}, 지름 : {diameter_m:g}, 두께 : {thickness_cm:g}, 면적 : {area_m2:.3f}, 무게 : {mars_weight_kg:.3f} kg')
        except Exception:
            print('Processing error.'); return

    except Exception:
        print('Processing error.'); return

if __name__ == '__main__':
    main()
