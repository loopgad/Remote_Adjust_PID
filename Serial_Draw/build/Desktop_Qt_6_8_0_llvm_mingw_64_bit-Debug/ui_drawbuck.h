/********************************************************************************
** Form generated from reading UI file 'drawbuck.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DRAWBUCK_H
#define UI_DRAWBUCK_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QDoubleSpinBox>
#include <QtWidgets/QGraphicsView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Form
{
public:
    QCheckBox *show_temp;
    QCheckBox *show_input;
    QGraphicsView *buck_view;
    QPushButton *refresh_window;
    QPushButton *onoff_draw;
    QCheckBox *show_output;
    QDoubleSpinBox *set_target;
    QPushButton *switch_mode;
    QLabel *label;

    void setupUi(QWidget *Form)
    {
        if (Form->objectName().isEmpty())
            Form->setObjectName("Form");
        Form->resize(595, 383);
        show_temp = new QCheckBox(Form);
        show_temp->setObjectName("show_temp");
        show_temp->setGeometry(QRect(490, 30, 79, 20));
        show_input = new QCheckBox(Form);
        show_input->setObjectName("show_input");
        show_input->setGeometry(QRect(490, 60, 79, 20));
        buck_view = new QGraphicsView(Form);
        buck_view->setObjectName("buck_view");
        buck_view->setGeometry(QRect(10, 10, 461, 361));
        refresh_window = new QPushButton(Form);
        refresh_window->setObjectName("refresh_window");
        refresh_window->setGeometry(QRect(490, 140, 75, 24));
        onoff_draw = new QPushButton(Form);
        onoff_draw->setObjectName("onoff_draw");
        onoff_draw->setGeometry(QRect(490, 180, 75, 24));
        show_output = new QCheckBox(Form);
        show_output->setObjectName("show_output");
        show_output->setGeometry(QRect(490, 90, 79, 20));
        set_target = new QDoubleSpinBox(Form);
        set_target->setObjectName("set_target");
        set_target->setGeometry(QRect(500, 250, 62, 22));
        switch_mode = new QPushButton(Form);
        switch_mode->setObjectName("switch_mode");
        switch_mode->setGeometry(QRect(490, 220, 75, 24));
        label = new QLabel(Form);
        label->setObjectName("label");
        label->setGeometry(QRect(570, 250, 16, 16));

        retranslateUi(Form);

        QMetaObject::connectSlotsByName(Form);
    } // setupUi

    void retranslateUi(QWidget *Form)
    {
        Form->setWindowTitle(QCoreApplication::translate("Form", "Form", nullptr));
        show_temp->setText(QCoreApplication::translate("Form", "\346\230\276\347\244\272\346\270\251\345\272\246", nullptr));
        show_input->setText(QCoreApplication::translate("Form", "\346\230\276\347\244\272\350\276\223\345\205\245", nullptr));
        refresh_window->setText(QCoreApplication::translate("Form", "\345\210\267\346\226\260\347\273\230\345\233\276", nullptr));
        onoff_draw->setText(QCoreApplication::translate("Form", "\345\274\200\345\247\213\347\273\230\345\233\276", nullptr));
        show_output->setText(QCoreApplication::translate("Form", "\346\230\276\347\244\272\350\276\223\345\207\272", nullptr));
        switch_mode->setText(QCoreApplication::translate("Form", "\347\224\265\345\216\213\346\250\241\345\274\217", nullptr));
        label->setText(QCoreApplication::translate("Form", "A", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Form: public Ui_Form {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DRAWBUCK_H
