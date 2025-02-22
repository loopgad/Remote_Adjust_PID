#include "maindrawdynamic.h"
#include "ui_maindrawdynamic.h"
#include "mainwindow.h" // 包含 MainWindow 的头文件

maindrawdynamic::maindrawdynamic(QWidget *parent)
    : QWidget(parent)
    , ui(new Ui::maindrawdynamic)
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

}

maindrawdynamic::~maindrawdynamic()
{
    delete ui;
}

void maindrawdynamic::closeEvent(QCloseEvent *event) {
    // 在关闭窗口时执行的操作
    MainWindow *mainWindow = static_cast<MainWindow*>(parentWidget()); // 获取父窗口（MainWindow）的指针
    if (mainWindow) {
        mainWindow->on_draw_dynamic_stateChanged(Qt::Unchecked); // 调用 MainWindow 中的槽函数来恢复复选框
    }
    QWidget::closeEvent(event); // 调用基类的 closeEvent 方法来完成关闭操作
}
