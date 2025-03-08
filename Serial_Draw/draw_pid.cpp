#include "draw_pid.h"
#include "ui_draw_pid.h"
#include "mainwindow.h"
#include <QSplineSeries>  // 引入 QSplineSeries 来实现平滑曲线
#include <QValueAxis>     // 使用 QValueAxis 来替代 axisX 和 axisY
#include <QTimer>


draw_pid::draw_pid(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::draw_pid)
    ,timer(new QTimer(this)) // 创建 QTimer 对象
{
    ui->setupUi(this);

    // 设置字体
    QFont font("Arial", 10);
    this->setFont(font);

    // 设置样式表
    this->setStyleSheet(
        "QMainWindow { background-color: #f0f0f0; }"
        "QPushButton {"
        "    background-color: #007bff; "
        "    color: white; "
        "    border: none; "
        "    border-radius: 5px; "
        "    padding: 10px; "
        "    font-weight: bold; "
        "} "
        "QPushButton:hover { background-color: #0056b3; } "
        "QComboBox {"
        "    background-color: white; "
        "    border: 1px solid #ccc; "
        "    border-radius: 5px; "
        "    padding: 5px; "
        "    font-size: 10pt; "
        "} "
        "QTextEdit, QTextBrowser {"
        "    border: 1px solid #ccc; "
        "    border-radius: 5px; "
        "    padding: 5px; "
        "    font-size: 10pt; "
        "} "
        "QLabel {"
        "    font-size: 10pt; "
        "} "
        );

    // // 创建 QCustomPlot 对象

    //ui->draw_widget->setGeometry(QRect(50, 50, 500, 400)); // 设置绘图区域大小
    ui->draw_widget->xAxis->setLabel("X Axis");
    ui->draw_widget->yAxis->setLabel("Y Axis");
    ui->draw_widget->xAxis->setRange(0, 400); // 设置X轴范围
    ui->draw_widget->yAxis->setRange(-100, 100); // 设置Y轴范围
    ui->draw_widget->addGraph(); // 添加一个绘图
    ui->draw_widget->graph(0)->setPen(QPen(Qt::blue)); // 设置绘图颜色
    ui->draw_widget->setOpenGl(true);
    // connect(ui->onoff_draw, SIGNAL(clicked()), this, SLOT(on_onoff_draw_clicked())); //连接点击信号到更新绘图区
    // 设置 QTimer，定时触发 updatePlot 函数，以达到至少100帧/秒的刷新率
    timer->setInterval(10); // 10毫秒触发一次，即100帧/秒
    connect(timer, &QTimer::timeout, this, &draw_pid::updatePlot);
    timer->stop(); // 关闭定时器
}

draw_pid::~draw_pid()
{
    delete ui->draw_widget;
    delete ui;
}

void draw_pid::on_onoff_draw_clicked()
{
    // 按钮点击时启动或停止定时器
    if (timer->isActive()) {
        ui->onoff_draw->setText("开始绘图");
        timer->stop();
    } else {
        timer->start();
        ui->onoff_draw->setText("停止绘图");
    }
}

void draw_pid::updatePlot()
{
    static int key = 0; // 用于生成数据的静态变量
    double value = 50 * qSin(key / 10.0) * qCos(key / 10.0); // 示例数据

    // 将新的数据点添加到图表中
    ui->draw_widget->graph(0)->addData(key, value);

    // 如果数据量超过 400 个，移除最早的数据点
    if (ui->draw_widget->graph(0)->data()->size() > 400) {
        ui->draw_widget->graph(0)->data()->removeBefore(key - 400);
    }

    // 更新数据点索引
    key++;

    // 设置x轴的可视范围，始终显示最新的 400 个数据点
    int visibleRangeStart = key - 400;
    int visibleRangeEnd = key + 50;  // 这里 +50 是为了让新数据点在可视范围的右侧有一点空隙

    // 更新x轴的显示范围
    ui->draw_widget->xAxis->setRange(key, key, Qt::AlignLeft);

    // 重绘图表
    ui->draw_widget->replot();
}




void draw_pid::closeEvent(QCloseEvent *event)
{
    // 在关闭窗口时执行的操作
    MainWindow *mainWindow = static_cast<MainWindow*>(parentWidget()); // 获取父窗口（MainWindow）的指针
    if (mainWindow) {
        mainWindow->on_draw_pid_stateChanged(Qt::Unchecked); // 调用 MainWindow 中的槽函数来恢复复选框
    }
    QWidget::closeEvent(event); // 调用基类的 closeEvent 方法来完成关闭操作
}
