#ifndef DRAW_BUCK_H
#define DRAW_BUCK_H

#include <QWidget>
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
#include <QOpenGLWidget>

namespace Ui {
class draw_buck;
}

class draw_buck : public QWidget
{
    Q_OBJECT

public:
    explicit draw_buck(QWidget *parent = nullptr);
    ~draw_buck();
private slots:
    void on_onoff_draw_clicked(); // 开始绘图
    void on_clean_window_clicked(); // 清除窗口
    void addDataToPoints(qint64 time, double value, int seriesIndex); //绘图时间轴
    void readData(); // 用于读取数据的槽函数

private:
    Ui::draw_buck *ui;
    QTimer *dataTimer; // 用于定时读取数据的定时器
    bool isDrawing;    // 跟踪绘制状态

protected:
    void closeEvent(QCloseEvent *event) override; // 重写 closeEvent 方法
};

#endif // DRAW_BUCK_H
