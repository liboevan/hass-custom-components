# Wechat Notify

This plug-in is powered by [wxpy](https://github.com/youfou/wxpy). Please install wxpy and pillow before try this plug-in.

```
pip3 install wxpy
pip3 install Pillow
```

To add Wechat Notify to your installation, place `wechat.py` to `.homeassistant/custom_components/notify/`. DO NOT FORGET to change line 41 (line 42 as below):

```
bot = Bot(cache_path='/root/.homeassistant/wxpy.pkl', console_qr=True)
```

Change the path to yours.

Now add the following to your `configuration.yaml` file:

```
notify:
  - platform: wechat
    name: wechat
```

Then start your hass service, and scan the QR code to sign in your Wechat account.

(No need to resign in if restart the service in a short time)

Seems everything is OK, let test it.

Navigate to `Services` of `Developer Tools`, choose `notify` and `wecaht`. Assume you want to sent a message to friend `Retroposter` and group `ThisIsMyGroup`, input the service data as below:

```
{"target":"['Retroposter', 'ThisIsMyGroup#group#']","message":"test test"}
```

The postfix `#group#` is required for group.

And the very important thing: `The group must be saved to your Wechat Contact`.