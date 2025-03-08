/********************************************************************************
** Form generated from reading UI file 'subdrawdynamic.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_SUBDRAWDYNAMIC_H
#define UI_SUBDRAWDYNAMIC_H

#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QGraphicsView>
#include <QtWidgets/QLabel>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_Form
{
public:
    QGraphicsView *graphicsView;
    QLabel *data_label;

    void setupUi(QWidget *Form)
    {
        if (Form->objectName().isEmpty())
            Form->setObjectName("Form");
        Form->resize(434, 355);
        graphicsView = new QGraphicsView(Form);
        graphicsView->setObjectName("graphicsView");
        graphicsView->setGeometry(QRect(10, 30, 411, 311));
        data_label = new QLabel(Form);
        data_label->setObjectName("data_label");
        data_label->setGeometry(QRect(20, 10, 54, 16));

        retranslateUi(Form);

        QMetaObject::connectSlotsByName(Form);
    } // setupUi

    void retranslateUi(QWidget *Form)
    {
        Form->setWindowTitle(QCoreApplication::translate("Form", "Form", nullptr));
        data_label->setText(QCoreApplication::translate("Form", "\346\225\260\346\215\256", nullptr));
    } // retranslateUi

};

namespace Ui {
    class Form: public Ui_Form {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_SUBDRAWDYNAMIC_H
