# Wechat Notify

这个插件基于[wxpy](https://github.com/youfou/wxpy). 请先安装Python包wxpy和pillow，命令如下：

```
pip3 install wxpy
pip3 install Pillow
```

然后将`wechat.py` 放置到 `.homeassistant/custom_components/notify/`目录下. 别忘记改第41行代码（下面是第41行）：

```
bot = Bot(cache_path='/root/.homeassistant/wxpy.pkl', console_qr=True)
```

把路径改成你的HASS运行目录。

接下来把下面配置添加到 `configuration.yaml`：

```
notify:
  - platform: wechat
    name: wechat
```

然后启动你的hass服务，并扫二维码登录微信（短时间内重启不需要重新登录）。

安装和配置完成，接下来测试以下。
在`Developer Tools`打开`Services`，选择`notify`和`wecaht`。假设你要发消息给朋友`Retroposter`和群聊`ThisIsMyGroup`，在service data中输入以下数据：

```
{"target":"['Retroposter', 'ThisIsMyGroup#group#']","message":"test test"}
```

群聊名后必须加后缀`#group#`，否则会被理解为朋友名字。

非常重要：`群聊必须保存到微信通讯录，才能发送成功`.