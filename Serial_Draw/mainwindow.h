#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QtCharts>
#include <QSerialPort>
#include <QSerialPortInfo>
#include <QMessageBox>
#include <QString>
#include <QDateTime>
#include <QFont>
#include <QMessageBox>
#include <QDebug>
#include <QVBoxLayout>
#include <QByteArray>
#include <QFileDialog> // 需要添加这个头文件以使用文件对话框
#include <QPixmap>
#include "draw_buck.h"
#include "draw_pid.h"
#include "maindrawdynamic.h"

const int BUFFER_SIZE = 1024 * 1024; // 缓冲区大小，例如1MB
extern char circularBuffer[BUFFER_SIZE]; // 环形缓存区
extern int bufferIndex; // 当前缓冲区索引

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();
    friend class draw_buck;
    friend class draw_pid;
    friend class maindrawdynamic;

private slots:
    void on_onoff_COM_clicked();    //按键打开/关闭串口
    void on_refresh_COM_clicked();  //按键刷新串口
    void on_send_data_clicked();    //按键发送
    void on_timed_send_stateChanged(int state); //以下4个函数为定时发送所需
    void startTimedSend();
    void stopTimedSend();
    void sendData();
    void on_empty_tx_clicked();     //清发送区
    void on_empty_rx_clicked();     //清接收区
    void rx_recieve();              //串口接收
    void saveData(); // 添加保存数据的槽函数
    void onCheckboxStateChanged(Qt::CheckState state); //checkbox互斥函数
    void on_draw_buck_stateChanged(int state); //打开draw_buck子窗口(非模态)
    void on_draw_pid_stateChanged(int state); //打开draw_pid子窗口(非模态)
    void on_draw_dynamic_stateChanged(int state); //打开draw_dynamic子窗口(非模态)
    void on_drawBuckWindowDestroyed(); // 槽函数，用于处理窗口销毁
    void on_drawPidWindowDestroyed();
    void on_mainDrawDynamicWindowDestroyed();


private:
    QSerialPort *COM = new QSerialPort();//定义串口指针
    Ui::MainWindow *ui;
    QTimer *timer = new QTimer(this);; // 声明定时器
    void updateBufferSize(); //更新超大环形缓存区
    draw_buck *drawBuckWindow = nullptr; // 用于存储新窗口的指针
    draw_pid *drawPidWindow = nullptr;
    maindrawdynamic *mainDrawDynamicWindow = nullptr;
};
#endif // MAINWINDOW_H
