#ifndef DRAW_PID_H
#define DRAW_PID_H

#include <QWidget>
#include <QMainWindow>
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
#include <QFileDialog>
#include <QPixmap>
#include <QOpenGLWidget>
#include "QCustomPlot.h" // 包含 QCustomPlot 头文件

namespace Ui {
class draw_pid;
}

class draw_pid : public QWidget
{
    Q_OBJECT

public:
    explicit draw_pid(QWidget *parent = nullptr);
    ~draw_pid();

protected:
    void closeEvent(QCloseEvent *event) override; // 重写 closeEvent 方法

private slots:
    void on_onoff_draw_clicked(); // 按钮点击槽函数
    void updatePlot(); // 动态绘图槽函数

private:
    Ui::draw_pid *ui;
    QCustomPlot *draw_widget; // QCustomPlot 对象
    QTimer *timer; //QTimer对象
};
#endif // DRAW_PID_H
