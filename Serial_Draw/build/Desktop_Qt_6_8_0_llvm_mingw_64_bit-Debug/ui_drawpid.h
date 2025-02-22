/********************************************************************************
** Form generated from reading UI file 'drawpid.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DRAWPID_H
#define UI_DRAWPID_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QDoubleSpinBox>
#include <QtWidgets/QGraphicsView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QSlider>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Form
{
public:
    QSlider *kp_slider;
    QSlider *ki_slider;
    QSlider *kd_slider;
    QLabel *kp_text;
    QLabel *ki_text;
    QLabel *kd_text;
    QDoubleSpinBox *kp_set;
    QDoubleSpinBox *ki_set;
    QDoubleSpinBox *kd_set;
    QGraphicsView *pid_view;
    QDoubleSpinBox *window_wide;
    QPushButton *draw_pid;
    QLabel *label;

    void setupUi(QWidget *Form)
    {
        if (Form->objectName().isEmpty())
            Form->setObjectName("Form");
        kp_slider = new QSlider(Form);
        kp_slider->setObjectName("kp_slider");
        kp_slider->setGeometry(QRect(70, 300, 160, 16));
        kp_slider->setOrientation(Qt::Orientation::Horizontal);
        ki_slider = new QSlider(Form);
        ki_slider->setObjectName("ki_slider");
        ki_slider->setGeometry(QRect(70, 330, 160, 16));
        ki_slider->setOrientation(Qt::Orientation::Horizontal);
        kd_slider = new QSlider(Form);
        kd_slider->setObjectName("kd_slider");
        kd_slider->setGeometry(QRect(70, 360, 160, 16));
        kd_slider->setOrientation(Qt::Orientation::Horizontal);
        kp_text = new QLabel(Form);
        kp_text->setObjectName("kp_text");
        kp_text->setGeometry(QRect(10, 300, 54, 16));
        ki_text = new QLabel(Form);
        ki_text->setObjectName("ki_text");
        ki_text->setGeometry(QRect(10, 330, 54, 16));
        kd_text = new QLabel(Form);
        kd_text->setObjectName("kd_text");
        kd_text->setGeometry(QRect(10, 360, 41, 21));
        kp_set = new QDoubleSpinBox(Form);
        kp_set->setObjectName("kp_set");
        kp_set->setGeometry(QRect(250, 300, 62, 22));
        ki_set = new QDoubleSpinBox(Form);
        ki_set->setObjectName("ki_set");
        ki_set->setGeometry(QRect(250, 330, 61, 21));
        kd_set = new QDoubleSpinBox(Form);
        kd_set->setObjectName("kd_set");
        kd_set->setGeometry(QRect(250, 360, 61, 21));
        pid_view = new QGraphicsView(Form);
        pid_view->setObjectName("pid_view");
        pid_view->setGeometry(QRect(10, 10, 441, 281));
        window_wide = new QDoubleSpinBox(Form);
        window_wide->setObjectName("window_wide");
        window_wide->setGeometry(QRect(350, 330, 71, 22));
        draw_pid = new QPushButton(Form);
        draw_pid->setObjectName("draw_pid");
        draw_pid->setGeometry(QRect(350, 300, 75, 24));
        label = new QLabel(Form);
        label->setObjectName("label");
        label->setGeometry(QRect(350, 360, 71, 16));

        retranslateUi(Form);

        QMetaObject::connectSlotsByName(Form);
    } // setupUi

    void retranslateUi(QWidget *Form)
    {
        Form->setWindowTitle(QCoreApplication::translate("Form", "Form", nullptr));
        kp_text->setText(QCoreApplication::translate("Form", "kp:", nullptr));
        ki_text->setText(QCoreApplication::translate("Form", "ki:", nullptr));
        kd_text->setText(QCoreApplication::translate("Form", "kd:", nullptr));
        draw_pid->setText(QCoreApplication::translate("Form", "\345\274\200\345\247\213\347\273\230\345\210\266", nullptr));
        label->setText(QCoreApplication::translate("Form", "\347\252\227\345\217\243\345\256\275\345\272\246(s)", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Form: public Ui_Form {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DRAWPID_H
