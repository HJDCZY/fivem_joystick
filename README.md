# fivem_joystick
这个插件允许您使用您的摇杆（飞行摇杆）来控制您的fivem服务器中的飞机和直升机。

python程序用于识别摇杆输入并将其发送到fivem服务器，python和javascript之间通过websocket通信。

目前，它可以成功识别我的thrustmaster t16000m摇杆的输入，但是您可能需要根据您的摇杆进行一些调整。

它支持4个轴，分别是x，y，z和r，分别绑定在升降舵，副翼，方向舵和油门上，其中R轴前一半是油门，后一半是刹车。

目前这个插件可以控制飞机和直升机，但是由于网络传输，可能会有一些延迟。

准备继续做的开发工作：
- 优化使用，优化界面
- 实现苦力帽的命令绑定

## 如何使用
1. 
首先下载release版本，将release中的joystick文件夹部署在fivem上，即放在resources文件夹下。
然后在server.cfg中添加以下代码：
```
start joystick
```

2. 
在release版本中找到joystick.exe文件，双击运行。
如果你有名为joystick_config.json的文件，请和joystick.exe放在同一目录下，joystick.exe在运行时会自动读取这个文件。

3. 进入fivem服务器，确保插件已经打开。

4. 首先在joystick.py中点击“允许fivem连接”，然后在fivem中输入命令`/joystick`，如果一切正常，你可以在屏幕右侧看到一个条，这是你当前摇杆的r轴（油门）的值。

5. 享受摇杆飞行！
