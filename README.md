# Remote_Adjust_PID
Remote_Adjust_PID with sparklink,uart and python realize

## 内容功能
用python实现上位机端的参数调整与发送，并通过接受反馈进行可视化参数调整
可通过控制算法的不同适当改动发送的参数类型，并在下位机串口接收回调中自行实现相关解包


注：星闪模块使用BearPI的Hi3863，相关历程可于
"https://www.bearpi.cn/core_board/bearpi/pico/h3863/software/SLE%E4%B8%B2%E5%8F%A3%E9%80%8F%E4%BC%A0%E6%B5%8B%E8%AF%95.html"
处查看，按照相关步骤配置星闪通信

## 使用步骤
1. 克隆项目：
   ```bash
   git clone https://github.com/loopgad/Remote_Adjust_PID.git
   ```
2. 安装依赖：
   ```bash
   pip install PyQt5 pyserial matplotlib
   ```
3. 连接好上位机与下位机的星闪模块并查看连接的串口端口
4. 在程序中修改对应的端口与波特率

把设备全部Reset，在上位机启动程序


## 版本描述
- **版本 1.0.0** - 2024.9.21
  - 初版，基本实现pid调节功能；test用于测试滑块调节功能
- **版本 1.1.0** - 2024.9.23
  - python的图线绘制速度效果一般，尝试用matlab appdesigner重写

## 贡献
欢迎贡献！

## 许可证
该项目采用 [MIT 许可证](LICENSE)。


