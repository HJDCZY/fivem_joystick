let socket = null;
const SERVER_PORT = 11556;
let isConnecting = false;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

console.log('Joystick script loaded');

function initUDPConnection() {
    if (isConnecting) return;
    isConnecting = true;
    
    try {
        console.log(`Connecting to ws://127.0.0.1:${SERVER_PORT}`);
        socket = new WebSocket(`ws://127.0.0.1:${SERVER_PORT}`);
        
        socket.onopen = () => {
            console.log('WebSocket连接已建立');
            isConnecting = false;
            reconnectAttempts = 0;
            socket.send('connect');
        };
        socket.onmessage = (event) => {
            try {
                // 检查是否是命令数据
                if (event.data.startsWith('cmd:')) {
                    const command = event.data.substring(4);
                    fetch(`https://joystick/executeCommand`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ command })
                    }).catch(err => {
                        console.error('发送命令错误:', err);
                    });
                    return;
                }

                // 处理常规摇杆数据
                const values = event.data.split(',').map(v => parseFloat(v));
                if (values.length === 4) {
                    // 只更新滑块位置
                    document.getElementById('rAxisSlider').value = values[3];
                    
                    const joystickData = {
                        axes: values
                    };
                    
                    fetch(`https://joystick/joystickUpdate`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(joystickData)
                    }).catch(err => {
                        console.error('发送摇杆数据错误:', err);
                    });
                }
            } catch (error) {
                console.error('数据解析错误:', error, '原始数据:', event.data);
            }
        };

        socket.onerror = (error) => {
            console.error('WebSocket错误:', error);
            isConnecting = false;
        };

        socket.onclose = (event) => {
            console.log(`WebSocket连接关闭 (code: ${event.code}, reason: ${event.reason})`);
            isConnecting = false;
            
            if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                reconnectAttempts++;
                console.log(`尝试重连 (${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS})`);
                setTimeout(initUDPConnection, 5000);
            } else {
                console.error('达到最大重连次数，停止重连');
            }
        };
    } catch (error) {
        console.error('连接初始化错误:', error);
        isConnecting = false;
    }
}

// 页面加载完成后初始化连接
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始连接');
    initUDPConnection();
});

// 页面关闭前清理
window.addEventListener('beforeunload', () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log('关闭WebSocket连接');
        socket.close(1000, '页面关闭');
    }
});

// 添加滑块事件监听
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，开始连接');
    initUDPConnection();

    // 添加R轴滑块值变化监听器
    const rSlider = document.getElementById('rAxisSlider');
    rSlider.addEventListener('input', (e) => {
        document.getElementById('rAxisValue').textContent = `R轴值: ${e.target.value}`;
    });
});