import pygame
import tkinter as tk
from tkinter import ttk
import threading
import time
import asyncio
import websockets
import keyboard  # 新增导入

class JoystickGUI:
    def __init__(self):
        self.running = True
        # 创建新的事件循环，并确保它在主线程中运行
        self.loop = asyncio.new_event_loop()
        self.loop_thread = None
        self.ws = None
        
        self.root = tk.Tk()
        self.root.title("摇杆监视器")
        self.root.geometry("600x800")

        # 添加按键绑定相关变量
        self.waiting_for_keyboard = False
        self.waiting_for_joystick = False
        self.temp_keyboard_key = None
        self.key_bindings = {}  # {joystick_button: keyboard_key}
        self.keyboard_state = {}  # 记录键盘按键状态
        self.command_bindings = {}  # {joystick_button: command}
        self.waiting_for_command = False
        self.temp_command = None
        

        # 创建滑块
        self.sliders = []
        self.labels = []
        self.reverse_buttons = []  # 新增反向按钮列表
        self.axis_reversed = [False] * 4  # 记录每个轴的反向状态
        axis_names = ["X轴", "Y轴", "Z轴", "R轴"]


        
        for i, name in enumerate(axis_names):
            label = ttk.Label(self.root, text=name)
            label.grid(row=i, column=0, padx=5, pady=5)
            
            slider = ttk.Scale(
                self.root,
                from_=-1.0,
                to=1.0,
                orient="horizontal",
                length=200
            )
            slider.grid(row=i, column=1, padx=5, pady=5)
            slider.set(0)
            
            value_label = ttk.Label(self.root, text="0.00")
            value_label.grid(row=i, column=2, padx=5, pady=5)
            
            # 添加反向按钮
            reverse_button = ttk.Button(
                self.root,
                text="反向",
                command=lambda x=i: self.toggle_reverse(x)
            )
            reverse_button.grid(row=i, column=3, padx=5, pady=5)
            
            self.sliders.append(slider)
            self.labels.append(value_label)
            self.reverse_buttons.append(reverse_button)
                # 添加按钮框架
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.grid(row=7, column=0, columnspan=3, pady=10)
        
        # 创建连接按钮
        self.connect_button = ttk.Button(
            self.button_frame, 
            text="允许fivem连接",
            command=self.connect_to_fivem
        )
        self.connect_button.grid(row=0, column=0, padx=10)
        
        # 创建退出按钮
        self.exit_button = ttk.Button(
            self.button_frame, 
            text="退出",
            command=self.quit_application
        )
        self.exit_button.grid(row=0, column=1, padx=10)


        # 按钮状态标签
        self.button_label = ttk.Label(self.root, text="没有按钮被按下")
        self.button_label.grid(row=4, column=0, columnspan=3, pady=10)

         # 添加HAT状态显示
        self.hat_frame = ttk.LabelFrame(self.root, text="苦力帽状态")
        self.hat_frame.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky="nsew")
        
        # 创建方向指示标签
        self.hat_label = ttk.Label(self.hat_frame, text="当前方向: 中央")
        self.hat_label.grid(row=0, column=0, padx=5, pady=5)

        # 创建方向显示画布
        self.hat_canvas = tk.Canvas(self.hat_frame, width=100, height=100)
        self.hat_canvas.grid(row=1, column=0, padx=5, pady=5)
        self._draw_hat_indicator((0, 0))  # 初始化为中央位置

        # 在button_frame中添加ZR翻转按钮
        self.zr_swap_button = ttk.Button(
            self.button_frame,
            text="ZR翻转: 关闭",
            command=self.toggle_zr_swap
        )
        self.zr_swap_button.grid(row=0, column=2, padx=10)
        
        # 添加ZR交换状态标志
        self.zr_swapped = False

        # 用于停止线程的标志
        self.running = True

        # 在button_frame之前添加按键绑定框架
        self.binding_frame = ttk.LabelFrame(self.root, text="按键绑定")
        self.binding_frame.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        self.binding_label = ttk.Label(self.binding_frame, text="未进行按键绑定")
        self.binding_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.binding_button = ttk.Button(
            self.binding_frame,
            text="绑定新按键",
            command=self.start_key_binding
        )
        self.binding_button.grid(row=0, column=1, padx=5, pady=5)

        # 在binding_frame中添加命令绑定区域
        self.command_binding_frame = ttk.LabelFrame(self.root, text="命令绑定")
        self.command_binding_frame.grid(row=7, column=0, columnspan=4, padx=5, pady=5, sticky="nsew")
        
        self.command_label = ttk.Label(self.command_binding_frame, text="未绑定命令")
        self.command_label.grid(row=0, column=0, padx=5, pady=5)
        
        self.command_entry = ttk.Entry(self.command_binding_frame)
        self.command_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.command_bind_button = ttk.Button(
            self.command_binding_frame,
            text="绑定命令",
            command=self.start_command_binding
        )
        self.command_bind_button.grid(row=0, column=2, padx=5, pady=5)

        # 调整其他元素的行号
        self.button_frame.grid(row=8, column=0, columnspan=3, pady=10)

    def update_values(self, values):
        for i, value in enumerate(values):
            if i < len(self.sliders):
                self.sliders[i].set(value)
                self.labels[i].config(text=f"{value:.2f}")

    def update_buttons(self, buttons):
        """更新按钮状态，并处理按键绑定"""
        # 先处理键盘按键的释放
        for button_num in self.keyboard_state:
            if str(button_num) not in buttons and self.keyboard_state[button_num]:
                key = self.key_bindings[button_num]
                keyboard.release(key)
                self.keyboard_state[button_num] = False

        # 处理命令绑定
        if self.waiting_for_command and len(buttons) == 1:
            button_num = int(buttons[0])
            self.command_bindings[button_num] = self.temp_command
            self.command_label.config(text=f"命令绑定完成: 按键 {button_num} -> {self.temp_command}")
            self.waiting_for_command = False
            self.temp_command = None
            self.command_bind_button.config(state="normal")
            return

        if buttons:
            self.button_label.config(text=f"按下的按钮: {', '.join(buttons)}")
            
            # 处理按键绑定
            if self.waiting_for_joystick and len(buttons) == 1:
                self.complete_binding(buttons[0])
                return
            
            # 模拟按下绑定的键盘按键
            for button in buttons:
                button_num = int(button)
                if button_num in self.key_bindings:
                    key = self.key_bindings[button_num]
                    if not self.keyboard_state.get(button_num, False):
                        keyboard.press(key)
                        self.keyboard_state[button_num] = True

                # 发送绑定的命令
                if button_num in self.command_bindings:
                    command = self.command_bindings[button_num]
                    # 发送命令到WebSocket客户端
                    if self.ws:
                        data = f"cmd:{command}"
                        asyncio.run_coroutine_threadsafe(self.ws.send(data), self.loop)
        else:
            self.button_label.config(text="没有按钮被按下")

    def _draw_hat_indicator(self, hat_value):
        """绘制HAT方向指示器"""
        self.hat_canvas.delete("all")
        
        # 绘制背景十字
        self.hat_canvas.create_line(50, 10, 50, 90, fill="gray")  # 垂直线
        self.hat_canvas.create_line(10, 50, 90, 50, fill="gray")  # 水平线
        
        # 根据HAT值确定位置
        x, y = hat_value
        center_x = 50 + (x * 20)  # 20像素的移动范围
        center_y = 50 - (y * 20)  # 20像素的移动范围
        
        # 绘制当前位置指示器
        self.hat_canvas.create_oval(center_x-5, center_y-5, 
                                  center_x+5, center_y+5, 
                                  fill="red")

    def update_hat(self, hat_value):
        """更新HAT显示"""
        x, y = hat_value
        # 更新文字显示
        directions = []
        # 修改这两行，交换上下的判断条件
        if y > 0: directions.append("上")
        if y < 0: directions.append("下")
        # 保持左右不变
        if x < 0: directions.append("左")
        if x > 0: directions.append("右")
        
        direction_text = "中央" if not directions else "、".join(directions)
        self.hat_label.config(text=f"当前方向: {direction_text}")
        
        # 更新图形显示
        self._draw_hat_indicator(hat_value)

    def display(self , message):
        # 将“检测到摇杆”等消息显示在GUI上
        label = ttk.Label(self.root, text=message)
        label.grid(row=10, column=0, columnspan=3, pady=10)



    def connect_to_fivem(self):
        """连接到FiveM的处理函数"""
        try:
            # 创建新线程运行事件循环
            self.loop_thread = threading.Thread(target=self._run_event_loop)
            self.loop_thread.daemon = True
            self.loop_thread.start()
            
            # 等待事件循环启动
            time.sleep(0.1)
            
            # 使用run_coroutine_threadsafe启动WebSocket服务器
            async def start_server():
                self.ws_server = await websockets.serve(
                    lambda ws: self._handle_websocket(ws),  # 使用 lambda 移除 path 参数
                    '127.0.0.1', 
                    11556
                )
            
            future = asyncio.run_coroutine_threadsafe(
                start_server(), 
                self.loop
            )
            future.result()  # 等待服务器启动
            
            # 更新按钮状态
            self.connect_button.config(text="等待连接", state="disabled")
            # self.display("WebSocket服务器已启动,等待客户端连接...")
                
        except Exception as e:
            print(f"启动失败: {str(e)}")

    
    async def _handle_websocket(self, websocket):
        """处理WebSocket连接"""
        try:
            self.ws = websocket
            # 更新连接状态显示
            self.root.after(0, lambda: (
                self.connect_button.config(text="已连接", state="disabled"),
                # self.display("客户端已连接")
            ))
            print("客户端已连接")
            
            # 等待接收连接消息
            message = await websocket.recv()
            print(f"收到消息: {message}")
            
            if message == 'connect':
                print("开始发送数据")
                # 启动数据发送线程
                self.send_thread = threading.Thread(target=self._send_joystick_data)
                self.send_thread.daemon = True  
                self.send_thread.start()
                
            while self.running:
                await asyncio.sleep(0.1)
                
        except websockets.exceptions.ConnectionClosed as e:
            print(f"连接关闭原因: {e}")
            # 更新断开连接状态显示
            self.root.after(0, lambda: (
                self.connect_button.config(text="允许fivem连接", state="normal"),
                # self.display("客户端断开连接")
            ))
        except Exception as e:
            print(f"连接错误详情: {str(e)}")
            # 更新错误状态显示
            self.root.after(0, lambda: (
                self.connect_button.config(text="允许fivem连接", state="normal"),
                self.display(f"连接错误: {str(e)}")
            ))
        finally:
            self.ws = None
    
    def toggle_reverse(self, axis_index):
        """切换指定轴的反向状态"""
        self.axis_reversed[axis_index] = not self.axis_reversed[axis_index]
        button_text = "正向" if not self.axis_reversed[axis_index] else "反向"
        self.reverse_buttons[axis_index].config(text=button_text)

    def update_values(self, values):
        """更新轴的值，考虑反向状态和ZR交换"""
        # 如果启用了ZR交换，交换Z轴和R轴的值
        if self.zr_swapped and len(values) >= 4:
            values[2], values[3] = values[3], values[2]
            
        for i, value in enumerate(values):
            if i < len(self.sliders):
                actual_value = -value if self.axis_reversed[i] else value
                self.sliders[i].set(actual_value)
                self.labels[i].config(text=f"{actual_value:.2f}")

    def toggle_zr_swap(self):
        """切换Z轴和R轴的交换状态"""
        self.zr_swapped = not self.zr_swapped
        button_text = "ZR翻转: 开启" if self.zr_swapped else "ZR翻转: 关闭"
        self.zr_swap_button.config(text=button_text)



    def _send_joystick_data(self):
        """发送摇杆数据时考虑反向设置和ZR交换"""
        while self.running and self.ws:
            try:
                values = []
                for i, slider in enumerate(self.sliders):
                    # 获取滑块值并应用反向设置
                    value = slider.get()
                    # value = -value if self.axis_reversed[i] else value
                    values.append(value)
                
                # 如果启用了ZR交换，在发送前交换Z轴和R轴的值
                # if self.zr_swapped and len(values) >= 4:
                #     values[2], values[3] = values[3], values[2]
                
                # 将数据格式化为字符串
                data = ','.join(f"{v:.3f}" for v in values)
                asyncio.run_coroutine_threadsafe(self.ws.send(data), self.loop)
                time.sleep(1/60)
                
            except Exception as e:
                print(f"发送数据错误: {str(e)}")
                break

    def _run_event_loop(self):
        """在新线程中运行事件循环"""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def quit_application(self):
        """退出应用程序"""
        self.running = False
        
        # 关闭WebSocket连接
        if self.ws:
            asyncio.run_coroutine_threadsafe(
                self.ws.close(), 
                self.loop
            )
        
        # 停止事件循环
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            if self.loop_thread:
                self.loop_thread.join(timeout=1.0)
            self.loop.close()
        
        # 退出程序
        self.root.quit()
        
    def start_key_binding(self):
        """开始按键绑定过程"""
        self.waiting_for_keyboard = True
        self.binding_label.config(text="请按下要绑定的键盘按键...")
        self.binding_button.config(state="disabled")
        
        # 绑定键盘事件
        self.root.bind('<Key>', self.on_keyboard_press)
        
    def on_keyboard_press(self, event):
        """处理键盘按键事件"""
        if self.waiting_for_keyboard:
            self.temp_keyboard_key = event.keysym
            self.waiting_for_keyboard = False
            self.waiting_for_joystick = True
            self.binding_label.config(text=f"已记录键盘按键: {event.keysym}\n请按下要绑定的摇杆按键...")
            self.root.unbind('<Key>')
            
    def complete_binding(self, joystick_button):
        """完成按键绑定"""
        if self.waiting_for_joystick and self.temp_keyboard_key:
            try:
                # 尝试验证按键是否可用
                keyboard.parse_hotkey(self.temp_keyboard_key)
                
                # 如果验证通过，完成绑定
                self.key_bindings[int(joystick_button)] = self.temp_keyboard_key
                self.binding_label.config(
                    text=f"绑定完成: 摇杆按键 {joystick_button} -> 键盘按键 {self.temp_keyboard_key}"
                )
            except ValueError as e:
                # 按键无效，取消本次绑定
                self.binding_label.config(
                    text=f"绑定失败: 无效的键盘按键 {self.temp_keyboard_key}"
                )
            finally:
                self.waiting_for_joystick = False
                self.temp_keyboard_key = None
                self.binding_button.config(state="normal")

    def start_command_binding(self):
        """开始命令绑定过程"""
        command = self.command_entry.get()
        if not command:
            return
            
        self.waiting_for_command = True
        self.temp_command = command
        self.command_label.config(text="请按下要绑定的摇杆按键...")
        self.command_bind_button.config(state="disabled")
            
def joystick_thread(gui):
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("没有检测到摇杆设备")
        return

    joystick = pygame.joystick.Joystick(0)
    joystick.init()

    gui.display("检测到摇杆设备: " + joystick.get_name() +"\n" + "按键数: " + str(joystick.get_numbuttons()) + "\n" + "轴数: " + str(joystick.get_numaxes()) + "\n" + "苦力帽数: " + str(joystick.get_numhats()))

    try:
        while gui.running:
            pygame.event.pump()

            # 读取HAT状态
            if joystick.get_numhats() > 0:
                hat_value = joystick.get_hat(0)  # 获取第一个HAT的值
                gui.root.after(0, gui.update_hat, hat_value)

            
            # 读取轴的值
            axes_values = []
            for i in range(min(4, joystick.get_numaxes())):
                axis = joystick.get_axis(i)
                axes_values.append(axis)

            # 读取按钮状态
            pressed_buttons = []
            for i in range(joystick.get_numbuttons()):
                if joystick.get_button(i):
                    pressed_buttons.append(str(i))
            

            # 更新GUI
            gui.root.after(0, gui.update_values, axes_values)
            gui.root.after(0, gui.update_buttons, pressed_buttons)
            
            time.sleep(0.1)

    finally:
        pygame.quit()

if __name__ == "__main__":
    gui = JoystickGUI()
    
    # 创建并启动摇杆监听线程
    thread = threading.Thread(target=joystick_thread, args=(gui,))
    thread.daemon = True
    thread.start()
    print("摇杆监视器已启动")
    
    try:
        gui.root.mainloop()
    finally:
        gui.running = False
        # 安全检查 loop_thread 是否存在和是否已初始化
        if hasattr(gui, 'loop_thread') and gui.loop_thread is not None:
            gui.loop_thread.join(timeout=1.0)
        if thread is not None:
            thread.join(timeout=1.0)