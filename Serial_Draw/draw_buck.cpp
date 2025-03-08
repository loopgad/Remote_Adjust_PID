#include "draw_buck.h"
#include "ui_draw_buck.h"
#include "mainwindow.h" // 包含 MainWindow 的头文件


draw_buck::draw_buck(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::draw_buck)
{
    ui->setupUi(this);
    // 设置字体
    QFont font("Arial", 10);
    this->setFont(font);

    // 设置样式表
    this->setStyleSheet(
        "QMainWindow { background-color: #f0f0f0; }"
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

    //OpenGL加速
    ui->graphicsView->setRenderHint(QPainter::Antialiasing);
    ui->graphicsView->setViewport(new QOpenGLWidget());
    // 初始化定时器和其他成员变量
    dataTimer = new QTimer(this); // 创建定时器
    isDrawing = false;

    connect(dataTimer, &QTimer::timeout, this, &draw_buck::readData); // 绘图信号回调
    connect(ui->onoff_draw, &QPushButton::clicked, this, &draw_buck::on_onoff_draw_clicked);
    connect(ui->clean_window, &QPushButton::clicked, this, &draw_buck::on_clean_window_clicked);

}

draw_buck::~draw_buck()
{
    delete ui;
}

void draw_buck::on_onoff_draw_clicked() {
    if (isDrawing) {
        // 停止绘制
        dataTimer->stop(); // 停止定时器
        ui->onoff_draw->setText("开始绘制");
        // 这里添加其他停止绘制所需的代码
        // 例如，清除绘图区域，停止数据读取等
        isDrawing = false;
    } else {
        // 开始绘制
        dataTimer->start(1000); // 每1000毫秒读取一次数据
        ui->onoff_draw->setText("停止绘制");
        // 这里添加开始绘制所需的代码
        isDrawing = true;
    }
}

void draw_buck::readData() {
    if (!isDrawing) return; // 如果不是绘制状态，则不执行任何操作

    MainWindow *mainWindow = static_cast<MainWindow*>(parentWidget()); // 获取父窗口（MainWindow）的指针
    if (!mainWindow) {
        QMessageBox::warning(this, tr("错误"), tr("无法获取主窗口指针"));
        return;
    }

    QByteArray data = mainWindow->COM->readAll();
    if (data.isEmpty()) {
        QMessageBox::warning(this, tr("错误"), tr("没有可读取的数据"));
        return;
    }

    QStringList dataList = QString(data).split("\r\n", Qt::SkipEmptyParts);
    if (dataList.isEmpty()) {
        QMessageBox::warning(this, tr("错误"), tr("数据列表为空"));
        return;
    }

    // 处理数据并绘图
    foreach (const QString &line, dataList) {
        if (line.isEmpty()) {
            continue; // 跳过空行
        }

        QStringList dataPoints = line.split(",", Qt::SkipEmptyParts);
        if (dataPoints.isEmpty()) {
            QMessageBox::warning(this, tr("错误"), tr("数据点列表为空"));
            return;
        }

        QDateTime timestamp = QDateTime::fromString(dataPoints[0], "yyyyMMdd-hhmmss");
        if (!timestamp.isValid()) {
            QMessageBox::warning(this, tr("错误"), tr("时间戳格式不正确"));
            return;
        }

        for (int i = 1; i < dataPoints.size(); ++i) {
            bool ok;
            double value = dataPoints[i].toDouble(&ok);
            if (!ok) {
                QMessageBox::warning(this, tr("错误"), tr("数据格式不正确"));
                return;
            }
            addDataToPoints(timestamp.toMSecsSinceEpoch(), value, i - 1);
        }
    }
}
void draw_buck::addDataToPoints(qint64 time, double value, int seriesIndex) {
    QChart *chart = ui->graphicsView->chart();
    QLineSeries *series = static_cast<QLineSeries*>(chart->series().at(seriesIndex));
    if (!series) {
        series = new QLineSeries(this);
        chart->addSeries(series);
        // 设置系列名称，可以根据 seriesIndex 来命名
        series->setName(QString("Series %1").arg(seriesIndex + 1));
    }
    series->append(time, value);

    // 刷新图表视图
    ui->graphicsView->update();

    // 自动滚动到最新的数据点
    QList<QAbstractAxis *> axesX = chart->axes(Qt::Horizontal);
    QList<QAbstractAxis *> axesY = chart->axes(Qt::Vertical);
    if (!axesX.isEmpty() && !axesY.isEmpty()) {
        QValueAxis *axisX = static_cast<QValueAxis*>(axesX.first());
        QValueAxis *axisY = static_cast<QValueAxis*>(axesY.first());
        axisX->setRange(axisX->min(), time + 10000); // 假设右侧留10000毫秒空间
        axisY->setRange(axisY->min(), value + 10); // 假设上方留10单位空间
    }
}

void draw_buck::on_clean_window_clicked() {
    ui->graphicsView->chart()->removeAllSeries(); //清空窗口
}


void draw_buck::closeEvent(QCloseEvent *event) {
    // 在关闭窗口时执行的操作
    MainWindow *mainWindow = static_cast<MainWindow*>(parentWidget()); // 获取父窗口（MainWindow）的指针
    if (mainWindow) {
        mainWindow->on_draw_buck_stateChanged(Qt::Unchecked); // 调用 MainWindow 中的槽函数来恢复复选框
    }
    QWidget::closeEvent(event); // 调用基类的 closeEvent 方法来完成关闭操作
}
