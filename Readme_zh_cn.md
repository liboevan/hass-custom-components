# Home Assistant Custom Components

## 天气传感器 - 和风天气

和风天气提供免费版API，但是需要[注册](www.heweather.com)获取API key. 免费版API每天能调用3000次。

* 本插件只用于中国城市，调用 API `https://free-api.heweather.com/v5/weather?city=yourcity&key=yourkey`。

安装本和风天气插件，首先要把`heweather.py`放到`.homeassistant/custom_compoents/sensor/`目录下。然后在`configuration.yaml` 文件中添加以下配置（示例为全部变量配置，必选项/可选项见示例段落下注释）。

```
sensor:
  - platform: heweather
    name: FRIENDLY_NAME
    api_key: YOUR_API_KEY
    city: CN101180101
    update_interval: '00:05:00'
    forecast: 1,2
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
配置变量:

* `api_key` (必选): 你的API key。

* `name` (可选): 显示在页面的snesor名字前缀。默认为He Weather。

* `city` (可选): 中文城市名, 英文城市名或者城市代码。默认为`configuration.yaml`配置的地址。城市里表见 [这里](https://cdn.heweather.com/china-city-list.txt).

* `update_interval` (可选): 传感器更新时间间隔。默认两分钟。

* `forecast` 数组 (可选): 需要预报的天数，明天为1，后天为2（免费API支支持3天预报）。`monitored_condition`中所有带`daily`前缀的变量都会被改配置影响。

* `lang` (可选): 语言选项。默认中文`zh-cn`。多语言支持见[这里](https://www.heweather.com/documents/i18n)。

* `monitored_conditions` 数组 (必选): 将要在页面显示的传感器，至少选择一项。

    `aqi`: 空气质量指数。更多信息在attributes卡片。

    `summary`: 当前天气状况。更多信息在attributes卡片。

    `daily_astro_sr`: 太阳升起时间。

    `daily_astro_ss`: 太阳落下时间。

    `daily_hum`: 湿度。

    `daily_pcpn`: 降水量。

    `daily_pop`: 降水量可能性。

    `daily_pres`: 大气压强。

    `daily_tmp_max`: 最高温度。

    `daily_tmp_min`: 最低温度。

    `daily_vis`: 可见度。

    `daily_wind_deg`: 风向度数。

    `daily_wind_dir`: 风向。

    `daily_wind_sc`: 风力等级。

    `daily_wind_spd`: 风速。
