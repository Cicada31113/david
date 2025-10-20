import math

def sphere_area(diameter: float, material: str, thickness: float = 1.0) -> tuple[float, float]:

    if not isinstance(diameter, (int, float)) or diameter <= 0:
        raise ValueError('Invalid diameter')
    if material not in ['유리', '알루미늄', '탄소강']:
        raise ValueError('Invalid material')
    if not isinstance(thickness, (int, float)) or thickness <= 0:
        raise ValueError('Invalid thickness')


    densities = {
        '유리': 2.4,
        '알루미늄': 2.7,
        '탄소강': 7.85,
    }


    area_m2 = math.pi * (diameter ** 2)


    density_g_cm3 = densities[material]
    area_cm2 = area_m2 * 10000        # m² -> cm² 변환
    volume_cm3 = area_cm2 * thickness   # 부피(cm³) 계산
    mass_g = density_g_cm3 * volume_cm3 # 질량(g) 계산
    mass_kg = mass_g / 1000           # g -> kg 변환
    mars_weight_kg = mass_kg * 0.38   # 화성 무게(kg) 환산

    return (area_m2, mars_weight_kg)

def main():

    try:
        diameter_str = input('지름(m)을 입력하세요: ').strip()
        if not diameter_str: 
            raise ValueError
        diameter = float(diameter_str)
        if diameter <= 0: 
            raise ValueError


        material = input('재질(유리/알루미늄/탄소강)을 입력하세요: ').strip()
        if material not in ['유리', '알루미늄', '탄소강']:
            raise ValueError


        thickness_str = input('두께(cm)를 입력하세요(기본값 1): ').strip()
        if not thickness_str:
            thickness = 1.0
        else:
            thickness = float(thickness_str)
            if thickness <= 0:
                raise ValueError


        area, weight = sphere_area(diameter, material, thickness)


        print(f'재질: {material}, 지름: {diameter:g}, 두께: {thickness:g}, 면적: {area:.3f}, 무게: {weight:.3f} kg')

    except ValueError:

        print('Invalid input.')
    except Exception:

        print('Processing error.')


if __name__ == '__main__':
    main()