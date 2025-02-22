#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "QSerialPort"
#include "QSerialPortInfo"
#include "QFont"
#include "QMessageBox"
#include "QDebug"
#include "QDateTime"
#include "QChart"
#include "QTimer"

int bufferIndex = 0;
char circularBuffer[BUFFER_SIZE] = {0};

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    // 设置字体
    QFont font("Arial", 10);
    this->setFont(font);

    // 设置样式表
    this->setStyleSheet(
        "QMainWindow { "
        "background-color: transparent; " // 设置背景透明
        "background-image: url(:/image/qt_picture/background.jpg); " // 使用你的图片路径
        "background-position: center; " // 背景图片居中显示
        "background-repeat: no-repeat; " // 不重复显示背景图片
        "} "
        "QPushButton {"
        "    background-color: #007bff;"
        "    color: white;"
        "    border: none;"
        "    border-radius: 5px;"
        "    padding: 10px;"
        "    font-weight: bold;"
        "}"
        "QPushButton:hover { background-color: #0056b3; }"
        "QComboBox {"
        "    background-color: white;"
        "    border: 1px solid #ccc;"
        "    border-radius: 5px;"
        "    padding: 5px;"
        "    font-size: 10pt;"
        "}"
        "QTextEdit, QTextBrowser {"
        "    border: 1px solid #ccc;"
        "    border-radius: 5px;"
        "    padding: 5px;"
        "    font-size: 10pt;"
        "}"
        "QLabel {"
        "    font-size: 10pt;"
        "}"
        );

    on_refresh_COM_clicked(); // 打开时刷新一次串口
    ui->check_onoff->setStyleSheet("background-color:white"); // 设置串口开启指示灯初始化为白色
    QPixmap pixmap1(":/image/qt_picture/ArcticonsPidLitacka.png"); // 加载pid图片
    ui->pid_label->setPixmap(pixmap1.scaled(ui->pid_label->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation)); // 缩放图片以适应 QLabel
    ui->pid_label->setAlignment(Qt::AlignCenter); // 设置QLabel居中对齐
    QPixmap pixmap2(":/image/qt_picture/HugeiconsPowerService.png"); // 加载buck图片
    ui->buck_label->setPixmap(pixmap2.scaled(ui->buck_label->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation)); // 缩放图片以适应 QLabel
    ui->buck_label->setAlignment(Qt::AlignCenter); // 设置QLabel居中对齐
    QPixmap pixmap3(":/image/qt_picture/ArcticonsOscilloscope.png"); // 加载动态绘图图片
    ui->dynamic_label->setPixmap(pixmap3.scaled(ui->dynamic_label->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation)); // 缩放图片以适应 QLabel
    ui->dynamic_label->setAlignment(Qt::AlignCenter); // 设置QLabel居中对齐

    // 信号与槽的连接
    connect(COM, SIGNAL(readyRead()), this, SLOT(rx_recieve())); // 接收回调函数
    connect(timer, &QTimer::timeout, this, &MainWindow::sendData); // 连接定时器的超时信号到发送函数
    connect(ui->timed_send, SIGNAL(stateChanged(int)), this, SLOT(on_timed_send_stateChanged(int))); // 连接状态变化信号
    connect(ui->save_data, &QPushButton::clicked, this, &MainWindow::saveData); // 连接保存数据的操作
    connect(ui->draw_pid, &QCheckBox::checkStateChanged, this, &MainWindow::onCheckboxStateChanged);//三个checkbox互斥操作
    connect(ui->draw_dynamic, &QCheckBox::checkStateChanged, this, &MainWindow::onCheckboxStateChanged);
    connect(ui->draw_buck, &QCheckBox::checkStateChanged, this, &MainWindow::onCheckboxStateChanged);
    connect(ui->draw_buck, &QCheckBox::checkStateChanged, this, &MainWindow::on_draw_buck_stateChanged); // 连接 QCheckBox的checkStateChanged信号到槽函数
    connect(ui->draw_pid, &QCheckBox::checkStateChanged, this, &::MainWindow::on_draw_pid_stateChanged);
    connect(ui->draw_dynamic, &QCheckBox::checkStateChanged, this, &MainWindow::on_draw_dynamic_stateChanged);
    // 设置控件的大小策略
    foreach (QWidget *widget, this->findChildren<QWidget*>()) {
        widget->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Preferred);
    }
}

MainWindow::~MainWindow()
{
    delete ui;
    if (drawBuckWindow) {
        delete drawBuckWindow;
    }
}

void MainWindow::on_onoff_COM_clicked()
{
    // 初始化串口
    QSerialPort::BaudRate baudRate;
    QSerialPort::DataBits dataBits;
    QSerialPort::StopBits stopBits;
    QSerialPort::Parity checkBits;
    // 默认停止位，数据位和奇偶校验
    stopBits = QSerialPort::OneStop;
    dataBits = QSerialPort::Data8;
    checkBits = QSerialPort::NoParity;
    // 根据选择设置波特率
    if (ui->set_BUAD->currentText() == "9600") {
        baudRate = QSerialPort::Baud9600;
    } else if (ui->set_BUAD->currentText() == "115200") {
        baudRate = QSerialPort::Baud115200;
    } else if (ui->set_BUAD->currentText() == "230400") {
        baudRate = QSerialPort::Baud230400;
    } else if (ui->set_BUAD->currentText() == "460800") {
        baudRate = QSerialPort::Baud460800;
    } else if (ui->set_BUAD->currentText() == "921600") {
        baudRate = QSerialPort::Baud921600;
    } else if (ui->set_BUAD->currentText() == "1382400") {
        baudRate = QSerialPort::Baud1382400;
    } else if (ui->set_BUAD->currentText() == "4000000") {
        baudRate = QSerialPort::Baud4000000;
    }else {
        baudRate = QSerialPort::Baud115200; // 默认值
    }
    // 设置串口参数
    COM->setBaudRate(baudRate);
    COM->setDataBits(dataBits);
    COM->setStopBits(stopBits);
    COM->setParity(checkBits);
    // 设置串口名称
    COM->setPortName(ui->available_COM->currentText());
    // 检查串口是否已经打开
    if (COM->isOpen()) {
        COM->close();
        ui->check_onoff->setStyleSheet("background-color:white");
        ui->onoff_COM->setText("打开串口");
    } else {
        if (COM->open(QIODevice::ReadWrite)) {
            ui->check_onoff->setStyleSheet("background-color:red");
            ui->onoff_COM->setText("关闭串口");
        } else {
            qDebug() << "Failed to open COM port:" << COM->errorString();
            QMessageBox::critical(this, "错误提示", "指定端口被占用或无可用端口");
            ui->onoff_COM->setStyleSheet("background-color:gray");
            ui->onoff_COM->setText("打开串口");
        }
    }
}

void MainWindow::on_refresh_COM_clicked()
{
    bool hasAvailablePorts = false; // 标记是否有可用的串口
    ui->available_COM->clear(); // 清空下拉列表
    // 遍历所有可用的串口
    foreach (const QSerialPortInfo &info, QSerialPortInfo::availablePorts()) {
        ui->available_COM->addItem(info.portName());
        hasAvailablePorts = true; // 有可用串口
    }

    // 如果没有可用串口，则添加“无”
    if (!hasAvailablePorts) {
        ui->available_COM->addItem(tr("无"));
    }

}

void MainWindow::on_send_data_clicked() {
    QByteArray data;
    // 判断是否勾选了 hex_send 控件
    if (ui->hex_send->isChecked()) {
        // 如果勾选了，进行十六进制转换
        QString hexString = ui->textEdit->toPlainText().toUpper(); // 将输入转换为大写
        data = QByteArray::fromHex(hexString.toUtf8()); // 将十六进制字符串转换为字节数组
    } else {
        // 如果没有勾选，直接获取文本框中的数据
        data = ui->textEdit->toPlainText().toLatin1();
    }

    // 判断是否需要自动添加回车换行
    if (ui->add_crlf->checkState()) {
        COM->write(data); // 写入数据
        COM->write("\r\n"); // 添加回车换行
        ui->textBrowser->insertPlainText("\r\n" + QDateTime::currentDateTime().toString("MM-dd HH:mm:ss:zzz") +
                                         tr(" - send:") + "\t" + tr(ui->textEdit->toPlainText().toLatin1())
                                         + "\\r\\n"); // 发送数据回显
    } else {
        COM->write(data); // 发送数据
        ui->textBrowser->insertPlainText("\r\n" + QDateTime::currentDateTime().toString("MM-dd HH:mm:ss:zzz") +
                                         tr(" - send:") + "\t" + tr(ui->textEdit->toPlainText().toLatin1())); // 发送数据回显
    }
}

void MainWindow::on_empty_tx_clicked() {
    ui->textEdit->clear(); // 清除发送区
}

void MainWindow::on_empty_rx_clicked() {
    ui->textBrowser->clear(); // 清除接收区
}

void MainWindow::rx_recieve() {
        QByteArray buf; // 接收缓冲区
        buf = COM->readAll(); // 数据存储

        QString str;
        if (!buf.isEmpty()) { // 不为空打印接收数据
            // 将接收到的数据存储到环形缓存区
            for (char byte : buf) {
                circularBuffer[bufferIndex] = byte; // 存储字节
                bufferIndex = (bufferIndex + 1) % BUFFER_SIZE; // 更新环形索引
            }

            str = tr(buf); // 转换
            ui->textBrowser->insertPlainText("\r\n" + QDateTime::currentDateTime().toString("MM-dd HH:mm:ss:zzz")
                                             + tr(" - receive:") + "\t" + str);
            ui->textBrowser->moveCursor(QTextCursor::End); // 光标移动
        }
        updateBufferSize(); //回显中更新超大环形缓冲区
}

void MainWindow::saveData() {
    QString filePath = QFileDialog::getSaveFileName(this, "保存文件", "", "Text Files (*.txt);;All Files (*)");
    if (filePath.isEmpty()) {
        return; // 用户取消了保存
    }

    QFile file(filePath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        QMessageBox::warning(this, "错误", "无法打开文件以进行写入");
        return;
    }

    // 将环形缓存区的内容写入文件
    for (int i = 0; i < BUFFER_SIZE; ++i) {
        if (circularBuffer[i] != '\0') { // 只写入有效字节
            file.write(QByteArray(1, circularBuffer[i])); // 将char转换为QByteArray
        }
    }

    file.close(); // 关闭文件
    QMessageBox::information(this, "成功", "数据已成功保存到文件中");
}


void MainWindow::updateBufferSize() {
    int bytesInBuffer = (bufferIndex < BUFFER_SIZE) ? bufferIndex : BUFFER_SIZE; // 计算当前缓冲区中的字节数
    ui->buffer_size->setText(QString("Buffer Size: %1 bytes").arg(bytesInBuffer)); // 更新 QLabel
}

void MainWindow::on_timed_send_stateChanged(int state) {
    if (state == Qt::Checked) {
        startTimedSend(); // 启动定时发送
    } else {
        stopTimedSend(); // 停止定时发送
        QPixmap pixmap(":/image/qt_picture/TablerClockCancel.png"); // 加载停止时的图片
        ui->time_image->setPixmap(pixmap.scaled(ui->time_image->size(), Qt::KeepAspectRatio, Qt::SmoothTransformation)); // 缩放图片以适应 QLabel
    }
}

void MainWindow::startTimedSend() {
    bool ok;
    int interval = ui->time_edit->toPlainText().toInt(&ok); // 获取 interval 值
    if (!ok || interval < 1 || interval > 5000) {
        QMessageBox::warning(this, "错误", "请输入有效的时间间隔（1到5000毫秒）");
        ui->timed_send->setChecked(false); // 取消勾选
        return;
    }
    timer->start(interval); // 启动定时器
}

void MainWindow::stopTimedSend() {
    timer->stop(); // 停止定时器
}

void MainWindow::sendData() {
    QByteArray data;
    // 判断是否勾选了 hex_send 控件
    if (ui->hex_send->isChecked()) {
        // 如果勾选了，进行十六进制转换
        QString hexString = ui->textEdit->toPlainText().toUpper(); // 将输入转换为大写
        data = QByteArray::fromHex(hexString.toUtf8()); // 将十六进制字符串转换为字节数组
    } else {
        // 如果没有勾选，直接获取文本框中的数据
        data = ui->textEdit->toPlainText().toLatin1();
    }
   // 判断是否需要自动添加回车换行
    if (ui->add_crlf->checkState()) {
        COM->write(data); // 写入数据
        COM->write("\r\n"); // 添加回车换行
        ui->textBrowser->insertPlainText("\r\n" + QDateTime::currentDateTime().toString("MM-dd HH:mm:ss:zzz") +
                                         tr(" - send:") + "\t" + tr(ui->textEdit->toPlainText().toLatin1())
                                         + "\\r\\n"); // 发送数据回显
    } else {
        COM->write(data); // 发送数据
        ui->textBrowser->insertPlainText("\r\n" + QDateTime::currentDateTime().toString("MM-dd HH:mm:ss:zzz") +
                                         tr(" - send:") + "\t" + tr(ui->textEdit->toPlainText().toLatin1())); // 发送数据回显
    }
}

void MainWindow::onCheckboxStateChanged(Qt::CheckState state) {
    QCheckBox* senderCheckbox = qobject_cast<QCheckBox*>(sender()); // 获取发送信号的复选框

    if (state == Qt::Checked) {
        // 如果当前复选框被选中，则禁用其他复选框并改变颜色
        if (senderCheckbox == ui->draw_pid) {
            ui->draw_dynamic->setEnabled(false);
            ui->draw_buck->setEnabled(false);
            ui->draw_dynamic->setStyleSheet("background-color: lightgray;");
            ui->draw_buck->setStyleSheet("background-color: lightgray;");
        } else if (senderCheckbox == ui->draw_dynamic) {
            ui->draw_pid->setEnabled(false);
            ui->draw_buck->setEnabled(false);
            ui->draw_pid->setStyleSheet("background-color: lightgray;");
            ui->draw_buck->setStyleSheet("background-color: lightgray;");
        } else if (senderCheckbox == ui->draw_buck) {
            ui->draw_pid->setEnabled(false);
            ui->draw_dynamic->setEnabled(false);
            ui->draw_pid->setStyleSheet("background-color: lightgray;");
            ui->draw_dynamic->setStyleSheet("background-color: lightgray;");
        }
    } else {
        // 如果当前复选框被取消选中，检查其他复选框状态
        if (!ui->draw_pid->isChecked() && !ui->draw_dynamic->isChecked() && !ui->draw_buck->isChecked()) {
            // 所有复选框都未选中，重置所有复选框为可用状态
            ui->draw_dynamic->setEnabled(true);
            ui->draw_pid->setEnabled(true);
            ui->draw_buck->setEnabled(true);
            ui->draw_dynamic->setStyleSheet(""); // 重置样式
            ui->draw_pid->setStyleSheet(""); // 重置样式
            ui->draw_buck->setStyleSheet(""); // 重置样式
        } else {
            // 否则，保持选中的复选框禁用状态
            if (ui->draw_pid->isChecked()) {
                ui->draw_dynamic->setEnabled(false);
                ui->draw_buck->setEnabled(false);
                ui->draw_dynamic->setStyleSheet("background-color: lightgray;");
                ui->draw_buck->setStyleSheet("background-color: lightgray;");
            } else if (ui->draw_dynamic->isChecked()) {
                ui->draw_pid->setEnabled(false);
                ui->draw_buck->setEnabled(false);
                ui->draw_pid->setStyleSheet("background-color: lightgray;");
                ui->draw_buck->setStyleSheet("background-color: lightgray;");
            } else if (ui->draw_buck->isChecked()) {
                ui->draw_pid->setEnabled(false);
                ui->draw_dynamic->setEnabled(false);
                ui->draw_pid->setStyleSheet("background-color: lightgray;");
                ui->draw_dynamic->setStyleSheet("background-color: lightgray;");
            }
        }
    }
}

void MainWindow::on_draw_buck_stateChanged(int state) {
    if (state == Qt::Checked) {
        // 如果 draw_buck 被选中，打开新窗口
        if (!drawBuckWindow) {
            drawBuckWindow = new draw_buck(nullptr); // 创建新窗口实例，没有父窗口
            drawBuckWindow->setAttribute(Qt::WA_DeleteOnClose); // 设置窗口关闭时自动删除
            connect(drawBuckWindow, &QObject::destroyed, this, &MainWindow::on_drawBuckWindowDestroyed); // 连接 destroyed 信号
            drawBuckWindow->show(); // 显示新窗口
        } else {
            drawBuckWindow->show(); // 如果窗口已存在，仅显示
        }
    } else {
        // 如果 draw_buck 未被选中，隐藏新窗口
        if (drawBuckWindow) {
            drawBuckWindow->hide(); // 隐藏新窗口
        }
    }
}

void MainWindow::on_draw_pid_stateChanged(int state) {
    if (state == Qt::Checked) {
        // 如果 draw_pid 被选中，打开新窗口
        if (!drawPidWindow) {
            drawPidWindow = new draw_pid(nullptr); // 创建新窗口实例
            drawPidWindow->setAttribute(Qt::WA_DeleteOnClose); // 设置窗口关闭时自动删除
            connect(drawPidWindow, &QObject::destroyed, this, &MainWindow::on_drawPidWindowDestroyed); // 连接 destroyed 信号
            drawPidWindow->show(); // 显示新窗口
        }
    } else {
        // 如果 draw_pid 未被选中，隐藏新窗口
        if (drawPidWindow) {
            drawPidWindow->hide(); // 隐藏新窗口
        }
    }
}

void MainWindow::on_draw_dynamic_stateChanged(int state) {
    if (state == Qt::Checked) {
        // 如果 draw_dynamic 被选中，打开新窗口
        if (!mainDrawDynamicWindow) {
            mainDrawDynamicWindow = new maindrawdynamic(nullptr); // 创建新窗口实例
            mainDrawDynamicWindow->setAttribute(Qt::WA_DeleteOnClose); // 设置窗口关闭时自动删除
            connect(mainDrawDynamicWindow, &QObject::destroyed, this, &MainWindow::on_mainDrawDynamicWindowDestroyed); // 连接 destroyed 信号
            mainDrawDynamicWindow->show(); // 显示新窗口
        }
    } else {
        // 如果 draw_dynamic 未被选中，隐藏新窗口
        if (mainDrawDynamicWindow) {
            mainDrawDynamicWindow->hide(); // 隐藏新窗口
        }
    }
}


void MainWindow::on_drawBuckWindowDestroyed() {
    drawBuckWindow = nullptr; // 窗口销毁时，将指针设置为 nullptr
    /************恢复复选框************/
    ui->draw_buck->setChecked(false); // 将复选框设置为未选择状态
    ui->draw_dynamic->setEnabled(true);
    ui->draw_pid->setEnabled(true);
    ui->draw_dynamic->setStyleSheet(""); // 重置样式
    ui->draw_pid->setStyleSheet(""); // 重置样式
}

void MainWindow::on_drawPidWindowDestroyed() {
    drawPidWindow = nullptr; // 窗口销毁时，将指针设置为 nullptr
    /************恢复复选框************/
    ui->draw_pid->setChecked(false); // 将复选框设置为未选择状态
    ui->draw_dynamic->setEnabled(true);
    ui->draw_buck->setEnabled(true);
    ui->draw_dynamic->setStyleSheet(""); // 重置样式
    ui->draw_buck->setStyleSheet(""); // 重置样式
}

void MainWindow::on_mainDrawDynamicWindowDestroyed() {
    mainDrawDynamicWindow = nullptr; // 窗口销毁时，将指针设置为 nullptr
    /************恢复复选框************/
    ui->draw_dynamic->setChecked(false); // 将复选框设置为未选择状态
    ui->draw_buck->setEnabled(true);
    ui->draw_pid->setEnabled(true);
    ui->draw_buck->setStyleSheet(""); // 重置样式
    ui->draw_pid->setStyleSheet(""); // 重置样式
}

