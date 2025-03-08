/********************************************************************************
** Form generated from reading UI file 'draw_pid.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DRAW_PID_H
#define UI_DRAW_PID_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSlider>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QWidget>
#include <qcustomplot.h>

QT_BEGIN_NAMESPACE

class Ui_draw_pid
{
public:
    QPushButton *onoff_draw;
    QPushButton *clean_window;
    QSlider *horizontalSlider;
    QSlider *horizontalSlider_2;
    QSlider *horizontalSlider_3;
    QLabel *label;
    QLabel *label_2;
    QLabel *label_3;
    QLabel *kp_label;
    QLabel *ki_label;
    QLabel *kd_label;
    QTextEdit *kp_textEdit;
    QTextEdit *ki_textEdit;
    QTextEdit *kd_textEdit;
    QCustomPlot *draw_widget;

    void setupUi(QWidget *draw_pid)
    {
        if (draw_pid->objectName().isEmpty())
            draw_pid->setObjectName("draw_pid");
        draw_pid->resize(640, 480);
        onoff_draw = new QPushButton(draw_pid);
        onoff_draw->setObjectName("onoff_draw");
        onoff_draw->setGeometry(QRect(540, 403, 81, 31));
        clean_window = new QPushButton(draw_pid);
        clean_window->setObjectName("clean_window");
        clean_window->setGeometry(QRect(540, 443, 81, 31));
        horizontalSlider = new QSlider(draw_pid);
        horizontalSlider->setObjectName("horizontalSlider");
        horizontalSlider->setGeometry(QRect(30, 410, 160, 16));
        horizontalSlider->setOrientation(Qt::Orientation::Horizontal);
        horizontalSlider_2 = new QSlider(draw_pid);
        horizontalSlider_2->setObjectName("horizontalSlider_2");
        horizontalSlider_2->setGeometry(QRect(30, 430, 160, 16));
        horizontalSlider_2->setOrientation(Qt::Orientation::Horizontal);
        horizontalSlider_3 = new QSlider(draw_pid);
        horizontalSlider_3->setObjectName("horizontalSlider_3");
        horizontalSlider_3->setGeometry(QRect(30, 450, 160, 16));
        horizontalSlider_3->setOrientation(Qt::Orientation::Horizontal);
        label = new QLabel(draw_pid);
        label->setObjectName("label");
        label->setGeometry(QRect(10, 410, 16, 16));
        label_2 = new QLabel(draw_pid);
        label_2->setObjectName("label_2");
        label_2->setGeometry(QRect(10, 430, 16, 16));
        label_3 = new QLabel(draw_pid);
        label_3->setObjectName("label_3");
        label_3->setGeometry(QRect(10, 450, 16, 16));
        kp_label = new QLabel(draw_pid);
        kp_label->setObjectName("kp_label");
        kp_label->setGeometry(QRect(260, 410, 54, 16));
        ki_label = new QLabel(draw_pid);
        ki_label->setObjectName("ki_label");
        ki_label->setGeometry(QRect(260, 430, 54, 16));
        kd_label = new QLabel(draw_pid);
        kd_label->setObjectName("kd_label");
        kd_label->setGeometry(QRect(260, 450, 54, 16));
        kp_textEdit = new QTextEdit(draw_pid);
        kp_textEdit->setObjectName("kp_textEdit");
        kp_textEdit->setGeometry(QRect(200, 410, 51, 21));
        ki_textEdit = new QTextEdit(draw_pid);
        ki_textEdit->setObjectName("ki_textEdit");
        ki_textEdit->setGeometry(QRect(200, 430, 51, 21));
        kd_textEdit = new QTextEdit(draw_pid);
        kd_textEdit->setObjectName("kd_textEdit");
        kd_textEdit->setGeometry(QRect(200, 450, 51, 21));
        draw_widget = new QCustomPlot(draw_pid);
        draw_widget->setObjectName("draw_widget");
        draw_widget->setGeometry(QRect(10, 10, 621, 381));

        retranslateUi(draw_pid);

        QMetaObject::connectSlotsByName(draw_pid);
    } // setupUi

    void retranslateUi(QWidget *draw_pid)
    {
        draw_pid->setWindowTitle(QCoreApplication::translate("draw_pid", "Form", nullptr));
        onoff_draw->setText(QCoreApplication::translate("draw_pid", "\345\274\200\345\247\213\347\273\230\345\210\266", nullptr));
        clean_window->setText(QCoreApplication::translate("draw_pid", "\346\270\205\351\231\244\347\252\227\345\217\243", nullptr));
        label->setText(QCoreApplication::translate("draw_pid", "kp", nullptr));
        label_2->setText(QCoreApplication::translate("draw_pid", "ki", nullptr));
        label_3->setText(QCoreApplication::translate("draw_pid", "kd", nullptr));
        kp_label->setText(QCoreApplication::translate("draw_pid", "num", nullptr));
        ki_label->setText(QCoreApplication::translate("draw_pid", "num", nullptr));
        kd_label->setText(QCoreApplication::translate("draw_pid", "num", nullptr));
    } // retranslateUi

};

namespace Ui {
    class draw_pid: public Ui_draw_pid {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DRAW_PID_H
