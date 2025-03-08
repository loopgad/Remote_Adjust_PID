/********************************************************************************
** Form generated from reading UI file 'mainwindow.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINWINDOW_H
#define UI_MAINWINDOW_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QLabel>
#include <QtWidgets/QMainWindow>
#include <QtWidgets/QMenuBar>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QStatusBar>
#include <QtWidgets/QTextBrowser>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_MainWindow
{
public:
    QWidget *centralwidget;
    QPushButton *onoff_COM;
    QPushButton *refresh_COM;
    QPushButton *check_onoff;
    QTextEdit *textEdit;
    QComboBox *available_COM;
    QComboBox *set_BUAD;
    QCheckBox *draw_pid;
    QCheckBox *draw_buck;
    QCheckBox *enter_send;
    QTextBrowser *textBrowser;
    QCheckBox *timed_send;
    QCheckBox *add_crlf;
    QCheckBox *draw_dynamic;
    QTextEdit *time_edit;
    QLabel *label;
    QPushButton *send_data;
    QPushButton *empty_rx;
    QPushButton *empty_tx;
    QLabel *buffer_size;
    QPushButton *save_data;
    QLabel *time_image;
    QLabel *dynamic_label;
    QLabel *buck_label;
    QLabel *pid_label;
    QCheckBox *hex_send;
    QMenuBar *menubar;
    QStatusBar *statusbar;

    void setupUi(QMainWindow *MainWindow)
    {
        if (MainWindow->objectName().isEmpty())
            MainWindow->setObjectName("MainWindow");
        MainWindow->resize(800, 600);
        centralwidget = new QWidget(MainWindow);
        centralwidget->setObjectName("centralwidget");
        onoff_COM = new QPushButton(centralwidget);
        onoff_COM->setObjectName("onoff_COM");
        onoff_COM->setGeometry(QRect(690, 140, 91, 31));
        refresh_COM = new QPushButton(centralwidget);
        refresh_COM->setObjectName("refresh_COM");
        refresh_COM->setGeometry(QRect(690, 93, 91, 31));
        check_onoff = new QPushButton(centralwidget);
        check_onoff->setObjectName("check_onoff");
        check_onoff->setGeometry(QRect(660, 140, 20, 20));
        QSizePolicy sizePolicy(QSizePolicy::Policy::Fixed, QSizePolicy::Policy::Fixed);
        sizePolicy.setHorizontalStretch(0);
        sizePolicy.setVerticalStretch(0);
        sizePolicy.setHeightForWidth(check_onoff->sizePolicy().hasHeightForWidth());
        check_onoff->setSizePolicy(sizePolicy);
        textEdit = new QTextEdit(centralwidget);
        textEdit->setObjectName("textEdit");
        textEdit->setGeometry(QRect(20, 420, 521, 141));
        textEdit->setMinimumSize(QSize(250, 60));
        textEdit->setMaximumSize(QSize(2400, 900));
        available_COM = new QComboBox(centralwidget);
        available_COM->setObjectName("available_COM");
        available_COM->setGeometry(QRect(670, 20, 111, 22));
        sizePolicy.setHeightForWidth(available_COM->sizePolicy().hasHeightForWidth());
        available_COM->setSizePolicy(sizePolicy);
        set_BUAD = new QComboBox(centralwidget);
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->addItem(QString());
        set_BUAD->setObjectName("set_BUAD");
        set_BUAD->setGeometry(QRect(670, 60, 111, 22));
        sizePolicy.setHeightForWidth(set_BUAD->sizePolicy().hasHeightForWidth());
        set_BUAD->setSizePolicy(sizePolicy);
        draw_pid = new QCheckBox(centralwidget);
        draw_pid->setObjectName("draw_pid");
        draw_pid->setGeometry(QRect(660, 210, 111, 20));
        sizePolicy.setHeightForWidth(draw_pid->sizePolicy().hasHeightForWidth());
        draw_pid->setSizePolicy(sizePolicy);
        draw_buck = new QCheckBox(centralwidget);
        draw_buck->setObjectName("draw_buck");
        draw_buck->setGeometry(QRect(660, 240, 111, 20));
        sizePolicy.setHeightForWidth(draw_buck->sizePolicy().hasHeightForWidth());
        draw_buck->setSizePolicy(sizePolicy);
        enter_send = new QCheckBox(centralwidget);
        enter_send->setObjectName("enter_send");
        enter_send->setGeometry(QRect(690, 450, 79, 20));
        textBrowser = new QTextBrowser(centralwidget);
        textBrowser->setObjectName("textBrowser");
        textBrowser->setGeometry(QRect(20, 20, 601, 371));
        textBrowser->setMinimumSize(QSize(300, 180));
        textBrowser->setMaximumSize(QSize(2800, 2100));
        timed_send = new QCheckBox(centralwidget);
        timed_send->setObjectName("timed_send");
        timed_send->setGeometry(QRect(580, 420, 79, 20));
        add_crlf = new QCheckBox(centralwidget);
        add_crlf->setObjectName("add_crlf");
        add_crlf->setGeometry(QRect(580, 450, 79, 20));
        draw_dynamic = new QCheckBox(centralwidget);
        draw_dynamic->setObjectName("draw_dynamic");
        draw_dynamic->setGeometry(QRect(660, 270, 131, 20));
        sizePolicy.setHeightForWidth(draw_dynamic->sizePolicy().hasHeightForWidth());
        draw_dynamic->setSizePolicy(sizePolicy);
        time_edit = new QTextEdit(centralwidget);
        time_edit->setObjectName("time_edit");
        time_edit->setGeometry(QRect(660, 410, 101, 31));
        label = new QLabel(centralwidget);
        label->setObjectName("label");
        label->setGeometry(QRect(770, 420, 21, 20));
        send_data = new QPushButton(centralwidget);
        send_data->setObjectName("send_data");
        send_data->setGeometry(QRect(580, 490, 91, 61));
        empty_rx = new QPushButton(centralwidget);
        empty_rx->setObjectName("empty_rx");
        empty_rx->setGeometry(QRect(690, 490, 71, 31));
        empty_tx = new QPushButton(centralwidget);
        empty_tx->setObjectName("empty_tx");
        empty_tx->setGeometry(QRect(690, 520, 71, 31));
        buffer_size = new QLabel(centralwidget);
        buffer_size->setObjectName("buffer_size");
        buffer_size->setGeometry(QRect(660, 360, 131, 20));
        save_data = new QPushButton(centralwidget);
        save_data->setObjectName("save_data");
        save_data->setGeometry(QRect(690, 313, 75, 41));
        time_image = new QLabel(centralwidget);
        time_image->setObjectName("time_image");
        time_image->setGeometry(QRect(620, 400, 20, 20));
        dynamic_label = new QLabel(centralwidget);
        dynamic_label->setObjectName("dynamic_label");
        dynamic_label->setGeometry(QRect(620, 260, 31, 31));
        buck_label = new QLabel(centralwidget);
        buck_label->setObjectName("buck_label");
        buck_label->setGeometry(QRect(620, 230, 31, 31));
        pid_label = new QLabel(centralwidget);
        pid_label->setObjectName("pid_label");
        pid_label->setGeometry(QRect(620, 200, 31, 31));
        hex_send = new QCheckBox(centralwidget);
        hex_send->setObjectName("hex_send");
        hex_send->setGeometry(QRect(580, 470, 79, 20));
        MainWindow->setCentralWidget(centralwidget);
        menubar = new QMenuBar(MainWindow);
        menubar->setObjectName("menubar");
        menubar->setGeometry(QRect(0, 0, 800, 22));
        MainWindow->setMenuBar(menubar);
        statusbar = new QStatusBar(MainWindow);
        statusbar->setObjectName("statusbar");
        MainWindow->setStatusBar(statusbar);

        retranslateUi(MainWindow);

        QMetaObject::connectSlotsByName(MainWindow);
    } // setupUi

    void retranslateUi(QMainWindow *MainWindow)
    {
        MainWindow->setWindowTitle(QCoreApplication::translate("MainWindow", "MainWindow", nullptr));
        onoff_COM->setText(QCoreApplication::translate("MainWindow", "\346\211\223\345\274\200\344\270\262\345\217\243", nullptr));
        refresh_COM->setText(QCoreApplication::translate("MainWindow", "\345\210\267\346\226\260COM", nullptr));
        check_onoff->setText(QString());
        set_BUAD->setItemText(0, QCoreApplication::translate("MainWindow", "9600", nullptr));
        set_BUAD->setItemText(1, QCoreApplication::translate("MainWindow", "115200", nullptr));
        set_BUAD->setItemText(2, QCoreApplication::translate("MainWindow", "230400", nullptr));
        set_BUAD->setItemText(3, QCoreApplication::translate("MainWindow", "460800", nullptr));
        set_BUAD->setItemText(4, QCoreApplication::translate("MainWindow", "921600", nullptr));
        set_BUAD->setItemText(5, QCoreApplication::translate("MainWindow", "1382400", nullptr));
        set_BUAD->setItemText(6, QCoreApplication::translate("MainWindow", "4000000", nullptr));

        draw_pid->setText(QCoreApplication::translate("MainWindow", "pid\350\260\203\350\257\225", nullptr));
        draw_buck->setText(QCoreApplication::translate("MainWindow", "buck\350\260\203\350\257\225", nullptr));
        enter_send->setText(QCoreApplication::translate("MainWindow", "\345\233\236\350\275\246\345\217\221\351\200\201", nullptr));
        timed_send->setText(QCoreApplication::translate("MainWindow", "\345\256\232\346\227\266\345\217\221\351\200\201", nullptr));
        add_crlf->setText(QCoreApplication::translate("MainWindow", "\346\267\273\345\212\240\\r\\n", nullptr));
        draw_dynamic->setText(QCoreApplication::translate("MainWindow", "\345\212\250\346\200\201\347\273\230\345\210\266(\346\225\260\346\215\256\347\233\264\345\207\272)", nullptr));
        label->setText(QCoreApplication::translate("MainWindow", "ms", nullptr));
        send_data->setText(QCoreApplication::translate("MainWindow", "\345\217\221\351\200\201\346\225\260\346\215\256", nullptr));
        empty_rx->setText(QCoreApplication::translate("MainWindow", "\346\270\205\346\216\245\346\224\266\345\214\272", nullptr));
        empty_tx->setText(QCoreApplication::translate("MainWindow", "\346\270\205\345\217\221\351\200\201\345\214\272", nullptr));
        buffer_size->setText(QCoreApplication::translate("MainWindow", "\345\275\223\345\211\215\347\274\223\345\255\230\357\274\232", nullptr));
        save_data->setText(QCoreApplication::translate("MainWindow", "\344\277\235\345\255\230\346\225\260\346\215\256", nullptr));
        time_image->setText(QString());
        dynamic_label->setText(QCoreApplication::translate("MainWindow", "3", nullptr));
        buck_label->setText(QCoreApplication::translate("MainWindow", "3", nullptr));
        pid_label->setText(QCoreApplication::translate("MainWindow", "3", nullptr));
        hex_send->setText(QCoreApplication::translate("MainWindow", "hex\345\217\221\351\200\201", nullptr));
    } // retranslateUi

};

namespace Ui {
    class MainWindow: public Ui_MainWindow {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINWINDOW_H
