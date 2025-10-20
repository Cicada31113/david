# mmc1.py
from __future__ import annotations
import os, random, json
from datetime import datetime

class DummySensor:
    LOG_PATH = 'mission_env.log'

    def __init__(self) -> None:
        self.env_values: dict[str, float | None] = {
            'mars_base_internal_temperature': None,
            'mars_base_external_temperature': None,
            'mars_base_internal_humidity': None,
            'mars_base_external_illuminance': None,
            'mars_base_internal_co2': None,
            'mars_base_internal_oxygen': None,
        }

    def set_env(self) -> None:
        self.env_values['mars_base_internal_temperature'] = round(random.uniform(18, 30), 2)
        self.env_values['mars_base_external_temperature'] = round(random.uniform(0, 21), 2)
        self.env_values['mars_base_internal_humidity'] = round(random.uniform(50, 60), 2)
        self.env_values['mars_base_external_illuminance'] = round(random.uniform(500, 715), 2)
        self.env_values['mars_base_internal_co2'] = round(random.uniform(0.02, 0.1), 4)
        self.env_values['mars_base_internal_oxygen'] = round(random.uniform(4, 7), 2)

    def get_env(self, *, log: bool = True) -> dict[str, float | None]:
        if log:
            self._log_env(self.env_values)
        return self.env_values

    def _log_env(self, env: dict[str, float | None]) -> None:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        header = (
            'datetime,'
            'mars_base_internal_temperature,'
            'mars_base_external_temperature,'
            'mars_base_internal_humidity,'
            'mars_base_external_illuminance,'
            'mars_base_internal_co2,'
            'mars_base_internal_oxygen'
        )
        line = (
            f"{ts},"
            f"{env['mars_base_internal_temperature']},"
            f"{env['mars_base_external_temperature']},"
            f"{env['mars_base_internal_humidity']},"
            f"{env['mars_base_external_illuminance']},"
            f"{env['mars_base_internal_co2']},"
            f"{env['mars_base_internal_oxygen']}"
        )
        file_exists = os.path.exists(self.LOG_PATH)
        with open(self.LOG_PATH, 'a', encoding='utf-8') as f:
            if not file_exists:
                f.write(header + '\n')
            f.write(line + '\n')

if __name__ == '__main__':
    ds = DummySensor()
    ds.set_env()
    snapshot = ds.get_env(log=True)
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))
