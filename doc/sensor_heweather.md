# Weather Sensor - He Weather

You need an API key which is free but requires [registration](https://www.heweather.com). You can make up to 3000 calls per day for free.

* This plugin invokes the API `https://free-api.heweather.com/v5/weather?city=yourcity&key=yourkey` for Chinese cities only.

To add HeWeather to your installation, place `heweather.py` to `.homeassistant/custom_compoents/sensor/` and add the following (full-configuration example) to your `configuration.yaml` file:

```
sensor:
  - platform: heweather
    name: FRIENDLY_NAME
    api_key: YOUR_API_KEY
    city: CN101180101
    update_interval: '00:05:00'
    forecast: 1
    lang: en
    monitored_conditions:
      - aqi
      - summary
      - daily_astro_sr
      - daily_astro_ss
      - daily_summary_day
      - daily_summary_night
      - daily_hum
      - daily_pcpn
      - daily_pop
      - daily_pres
      - daily_tmp_max
      - daily_tmp_min
      - daily_vis
      - daily_wind_deg
      - daily_wind_dir
      - daily_wind_sc
      - daily_wind_spd

```
Configuration variables:

* `api_key` (Required): Your API key.

* `name` (Optional): Additional name for the sensors. Default to platform name.

* `city` (Optional): City Chinese name, English name or code. Default to the configured location in `configuration.yaml`. See the city list [Here](https://cdn.heweather.com/china-city-list.txt).

* `update_interval` (Optional): Minimum time interval between updates. Default is 2 minutes.

* `forecast` array (Optional): List of days in the 3 day forecast you would like to receive data on, starting with tomorrow as day 1. Any `monitored_condition` which a daily forecast by HeWeather will generate a sensor. The sensor wll tagged with `_tomorrow` or `after_tomorrow`.

* `lang` (Optional): Which language you would the result to be. Default to `zh-cn`. See more[here](https://www.heweather.com/documents/i18n).

* `monitored_conditions` array (Required): Conditions to display in the frontend.

    `aqi`: Air quality index. Detailed information in attributes.

    `summary`: Currently weather summary. Detailed information in attributes.

    `daily_astro_sr`: Sun raise time.

    `daily_astro_ss`: Sun set time.

    `daily_hum`: The relative humidity.

    `daily_pcpn`: The average expected intensity of precipitation occurring.

    `daily_pop`: A value between 0 and 1 which is representing the probability of precipitation.

    `daily_pres`: The sea-level air pressure in millibars.

    `daily_tmp_max`: Day’s expected high temperature.

    `daily_tmp_min`: Day’s expected low temperature.

    `daily_vis`: The average visibility.

    `daily_wind_deg`: Where the wind is coming from in degrees, with true north at 0° and progressing clockwise.

    `daily_wind_dir`: The wind direction.

    `daily_wind_sc`: The wind scale.

    `daily_wind_spd`: The wind speed.
