# Solar Optimizer - konfigurace

## Global settings (Settings → Integrations → Solar Optimizer)

| Pole                        | Hodnota                                    |
|-----------------------------|--------------------------------------------|
| Refresh period              | `300` s                                    |
| Net consumption             | `sensor.shelly_pro3em_total_active_power`  |
| PV production               | `sensor.growatt_solar_solar_total_power`   |
| Import kWh cost             | `input_number.energy_buy_price`            |
| Export kWh cost             | `input_number.energy_sell_price`           |
| Sell tax %                  | `input_number.energy_sell_tax_percent`     |
| Battery SOC                 | `sensor.growatt_battery_battery_soc`       |
| Battery net power           | `sensor.growatt_battery_net_power_so`      |

> Battery net power: kladné = discharge, záporné = charge (template sensor invertující growatt battery_power)

---

## Zařízení

### Bojler (GBO-Aku SSR)

| Pole                      | Hodnota                        |
|---------------------------|--------------------------------|
| name                      | Bojler                         |
| entity_id                 | `switch.gbo_boiler_enable`     |
| device_power              | `2000` W (průměr při regulaci) |
| duration_min              | `30`                           |
| duration_stop_min         | `15`                           |
| check_usable_template     | `{{ True }}`                   |
| battery_soc_threshold     | `40`                           |
| max_on_time_per_day_min   | `240`                          |
| min_on_time_per_day_min   | `60`                           |
| offpeak_time              | `22:00`                        |
| Priorita                  | High                           |

> GBO interně reguluje SSR plynule — SO jen otevírá/zavírá okno.
> device_power uprav podle reálné spotřeby z historie.

---

### Bazén (Shelly)

| Pole                      | Hodnota                                                          |
|---------------------------|------------------------------------------------------------------|
| name                      | Bazen                                                            |
| entity_id                 | `switch.shelly_pool_pump` ← doplnit skutečné entity ID          |
| device_power              | `450` W                                                          |
| duration_min              | `60`                                                             |
| duration_stop_min         | `30`                                                             |
| check_usable_template     | `{{ not is_state('binary_sensor.gbo_k1_pool_pump', 'on') }}`   |
| battery_soc_threshold     | `30`                                                             |
| min_on_time_per_day_min   | `180`                                                            |
| offpeak_time              | `22:00`                                                          |
| Priorita                  | Medium                                                           |

> check_usable_template zabraňuje souběhu Shelly a GBO K1 na stejném kabelu.

---

### Myčka

| Pole                      | Hodnota                                        |
|---------------------------|------------------------------------------------|
| name                      | Mycka                                          |
| entity_id                 | `switch.mycka`                                 |
| device_power              | `1200` W                                       |
| duration_min              | `90`                                           |
| duration_stop_min         | `90`                                           |
| check_usable_template     | `{{ is_state('switch.mycka', 'on') }}`         |
| battery_soc_threshold     | `50`                                           |
| Priorita                  | Low                                            |

> duration_stop_min = 90 zabraňuje přerušení myčky během cyklu.
> check_usable_template = SO ji zapne jen když ji uživatel ručně spustil.
