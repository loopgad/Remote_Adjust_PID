#ifndef MAINDRAWDYNAMIC_H
#define MAINDRAWDYNAMIC_H

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
class maindrawdynamic;
}

class maindrawdynamic : public QWidget
{
    Q_OBJECT

public:
    explicit maindrawdynamic(QWidget *parent = nullptr);
    ~maindrawdynamic();

protected:
    void closeEvent(QCloseEvent *event) override; // 重写 closeEvent 方法

private:
    Ui::maindrawdynamic *ui;
};

#endif // MAINDRAWDYNAMIC_H
