/********************************************************************************
** Form generated from reading UI file 'draw_buck.ui'
**
** Created by: Qt User Interface Compiler version 6.8.0
**
** WARNING! All changes made in this file will be lost when recompiling UI file!
********************************************************************************/

#ifndef UI_DRAW_BUCK_H
#define UI_DRAW_BUCK_H

#include <QtCharts/QChartView>
#include <QtCore/QVariant>
#include <QtWidgets/QApplication>
#include <QtWidgets/QCheckBox>
#include <QtWidgets/QComboBox>
#include <QtWidgets/QLabel>
#include <QtWidgets/QPushButton>
#include <QtWidgets/QTextBrowser>
#include <QtWidgets/QWidget>

QT_BEGIN_NAMESPACE

class Ui_draw_buck
{
public:
    QChartView *graphicsView;
    QPushButton *onoff_draw;
    QPushButton *clean_window;
    QComboBox *comboBox;
    QPushButton *save_data;
    QLabel *label;
    QLabel *label_2;
    QTextBrowser *textBrowser;
    QCheckBox *show_temp;

    void setupUi(QWidget *draw_buck)
    {
        if (draw_buck->objectName().isEmpty())
            draw_buck->setObjectName("draw_buck");
        draw_buck->resize(640, 480);
        graphicsView = new QChartView(draw_buck);
        graphicsView->setObjectName("graphicsView");
        graphicsView->setGeometry(QRect(10, 10, 501, 401));
        onoff_draw = new QPushButton(draw_buck);
        onoff_draw->setObjectName("onoff_draw");
        onoff_draw->setGeometry(QRect(540, 353, 81, 31));
        clean_window = new QPushButton(draw_buck);
        clean_window->setObjectName("clean_window");
        clean_window->setGeometry(QRect(540, 310, 81, 31));
        comboBox = new QComboBox(draw_buck);
        comboBox->addItem(QString());
        comboBox->addItem(QString());
        comboBox->addItem(QString());
        comboBox->setObjectName("comboBox");
        comboBox->setGeometry(QRect(520, 20, 111, 22));
        QFont font;
        font.setPointSize(7);
        comboBox->setFont(font);
        save_data = new QPushButton(draw_buck);
        save_data->setObjectName("save_data");
        save_data->setGeometry(QRect(420, 420, 81, 41));
        label = new QLabel(draw_buck);
        label->setObjectName("label");
        label->setGeometry(QRect(360, 440, 54, 16));
        label_2 = new QLabel(draw_buck);
        label_2->setObjectName("label_2");
        label_2->setGeometry(QRect(520, 160, 91, 20));
        textBrowser = new QTextBrowser(draw_buck);
        textBrowser->setObjectName("textBrowser");
        textBrowser->setGeometry(QRect(520, 180, 111, 31));
        show_temp = new QCheckBox(draw_buck);
        show_temp->setObjectName("show_temp");
        show_temp->setGeometry(QRect(540, 280, 79, 20));

        retranslateUi(draw_buck);

        QMetaObject::connectSlotsByName(draw_buck);
    } // setupUi

    void retranslateUi(QWidget *draw_buck)
    {
        draw_buck->setWindowTitle(QCoreApplication::translate("draw_buck", "Form", nullptr));
        onoff_draw->setText(QCoreApplication::translate("draw_buck", "\345\274\200\345\247\213\347\273\230\345\233\276", nullptr));
        clean_window->setText(QCoreApplication::translate("draw_buck", "\346\270\205\351\231\244\347\252\227\345\217\243", nullptr));
        comboBox->setItemText(0, QCoreApplication::translate("draw_buck", "V_Mode(voltage)", nullptr));
        comboBox->setItemText(1, QCoreApplication::translate("draw_buck", "V_Mode(peak currrent)", nullptr));
        comboBox->setItemText(2, QCoreApplication::translate("draw_buck", "I_Mode", nullptr));

        save_data->setText(QCoreApplication::translate("draw_buck", "\344\277\235\345\255\230\346\225\260\346\215\256", nullptr));
        label->setText(QCoreApplication::translate("draw_buck", "TextLabel", nullptr));
        label_2->setText(QCoreApplication::translate("draw_buck", "\347\233\256\346\240\207\347\224\265\345\216\213\357\274\232V", nullptr));
        show_temp->setText(QCoreApplication::translate("draw_buck", "\346\270\251\345\272\246\346\230\276\347\244\272", nullptr));
    } // retranslateUi

};

namespace Ui {
    class draw_buck: public Ui_draw_buck {};
} // namespace Ui

QT_END_NAMESPACE

#endif // UI_DRAW_BUCK_H
