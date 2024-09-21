#include <stdio.h>
#include <string.h>
#include "stm32f4xx_hal.h"

// 宏定义
#define TX_BUFFER_SIZE 10
#define RX_BUFFER_SIZE 100
#define PID_ARRAY_SIZE 4

// 变量定义
float pid[PID_ARRAY_SIZE];
char rx_buffer[1];  // 接收缓冲区，单字节接收
uint8_t data_buffer[RX_BUFFER_SIZE];  // 存储有效数据
int data_index = 0;

// 函数定义
void ProcessReceivedData(uint8_t *data, int length);

// 以USART2为例
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    static int flag = 0; // 判断是否开始读取数据

    if (huart->Instance == USART2) {
        if (rx_buffer[0] == '\\') {
            flag = 1; // 开始读取数据
            data_index = 0; // 初始化索引
            memset(data_buffer, 0, RX_BUFFER_SIZE); // 清空数据缓冲区
        } 
        else if (rx_buffer[0] == '\n') {
            if (data_index > 0) { // 只有在有数据时才处理
                ProcessReceivedData(data_buffer, data_index);
            }
            flag = 0; // 结束读取数据
            data_index = 0; // 重置索引
        } 
        else {
            if (flag == 1 && data_index < RX_BUFFER_SIZE - 1) {
                data_buffer[data_index++] = rx_buffer[0]; // 存储普通字符
            }
        }
        // 继续接收下一个字符
        HAL_UART_Receive_IT(huart, rx_buffer, 1);
    }
}

void ProcessReceivedData(uint8_t *data, int length) {
    char *token;
    int index = 0;

    token = strtok((char*)data, "\t");
    while (token != NULL && index < PID_ARRAY_SIZE) {
        pid[index++] = atof(token);  // 将字符串转换为浮点数
        token = strtok(NULL, "\t");
    }
}

void UART_SendFloat(float value) {
    char buffer[TX_BUFFER_SIZE];  // 缓冲区，用于存放字符串
    snprintf(buffer, TX_BUFFER_SIZE, "%.2f", value);  // 转换为字符串，保留两位小数
    HAL_UART_Transmit(&huart2, (uint8_t*)buffer, strlen(buffer), HAL_MAX_DELAY);  // 发送字符串
}
