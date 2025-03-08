/********************************************************************************
** Form generated from reading UI file 'maindrawdynamic.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_MAINDRAWDYNAMIC_H
#define UI_MAINDRAWDYNAMIC_H

#include <QtCharts/QChartView>
#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_maindrawdynamic
{
public:
    QChartView *graphicsView;
    QCheckBox *show_windows;
    QPushButton *onoff_draw;
    QPushButton *clean_window;

    void setupUi(QWidget *maindrawdynamic)
    {
        if (maindrawdynamic->objectName().isEmpty())
            maindrawdynamic->setObjectName("maindrawdynamic");
        maindrawdynamic->resize(640, 480);
        graphicsView = new QChartView(maindrawdynamic);
        graphicsView->setObjectName("graphicsView");
        graphicsView->setGeometry(QRect(10, 10, 621, 391));
        show_windows = new QCheckBox(maindrawdynamic);
        show_windows->setObjectName("show_windows");
        show_windows->setGeometry(QRect(50, 410, 79, 20));
        onoff_draw = new QPushButton(maindrawdynamic);
        onoff_draw->setObjectName("onoff_draw");
        onoff_draw->setGeometry(QRect(530, 403, 81, 31));
        clean_window = new QPushButton(maindrawdynamic);
        clean_window->setObjectName("clean_window");
        clean_window->setGeometry(QRect(530, 443, 81, 31));

        retranslateUi(maindrawdynamic);

        QMetaObject::connectSlotsByName(maindrawdynamic);
    } // setupUi

    void retranslateUi(QWidget *maindrawdynamic)
    {
        maindrawdynamic->setWindowTitle(QCoreApplication::translate("maindrawdynamic", "Form", nullptr));
        show_windows->setText(QCoreApplication::translate("maindrawdynamic", "\345\244\232\347\252\227\346\230\276\347\244\272", nullptr));
        onoff_draw->setText(QCoreApplication::translate("maindrawdynamic", "PushButton", nullptr));
        clean_window->setText(QCoreApplication::translate("maindrawdynamic", "PushButton", nullptr));
    } // retranslateUi

};

namespace Ui {
    class maindrawdynamic: public Ui_maindrawdynamic {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_MAINDRAWDYNAMIC_H
