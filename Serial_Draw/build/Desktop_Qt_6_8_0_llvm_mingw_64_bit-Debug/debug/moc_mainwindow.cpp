/****************************************************************************
** Meta object code from reading C++ file 'mainwindow.h'
**
** Created by: The Qt Meta Object Compiler version 68 (Qt 6.8.0)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../../../mainwindow.h"
#include <QtGui/qtextcursor.h>
#include <QtGui/qscreen.h>
#include <QtCharts/qlineseries.h>
#include <QtCharts/qabstractbarseries.h>
#include <QtCharts/qvbarmodelmapper.h>
#include <QtCharts/qboxplotseries.h>
#include <QtCharts/qcandlestickseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qpieseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qboxplotseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qpieseries.h>
#include <QtCharts/qpieseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qxyseries.h>
#include <QtCharts/qxyseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qboxplotseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qpieseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCharts/qxyseries.h>
#include <QtCore/qabstractitemmodel.h>
#include <QtCore/qmetatype.h>

#include <QtCore/qtmochelpers.h>

#include <memory>


#include <QtCore/qxptype_traits.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'mainwindow.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 68
#error "This file was generated using the moc from 6.8.0. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

#ifndef Q_CONSTINIT
#define Q_CONSTINIT
#endif

QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
QT_WARNING_DISABLE_GCC("-Wuseless-cast")
namespace {

#ifdef QT_MOC_HAS_STRINGDATA
struct qt_meta_stringdata_CLASSMainWindowENDCLASS_t {};
constexpr auto qt_meta_stringdata_CLASSMainWindowENDCLASS = QtMocHelpers::stringData(
    "MainWindow",
    "on_onoff_COM_clicked",
    "",
    "on_refresh_COM_clicked",
    "on_send_data_clicked",
    "on_timed_send_stateChanged",
    "state",
    "startTimedSend",
    "stopTimedSend",
    "sendData",
    "on_empty_tx_clicked",
    "on_empty_rx_clicked",
    "rx_recieve",
    "saveData",
    "onCheckboxStateChanged",
    "Qt::CheckState",
    "on_draw_buck_stateChanged",
    "on_draw_pid_stateChanged",
    "on_draw_dynamic_stateChanged",
    "on_drawBuckWindowDestroyed",
    "on_drawPidWindowDestroyed",
    "on_mainDrawDynamicWindowDestroyed"
);
#else  // !QT_MOC_HAS_STRINGDATA
#error "qtmochelpers.h not found or too old."
#endif // !QT_MOC_HAS_STRINGDATA
} // unnamed namespace

Q_CONSTINIT static const uint qt_meta_data_CLASSMainWindowENDCLASS[] = {

 // content:
      12,       // revision
       0,       // classname
       0,    0, // classinfo
      18,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       0,       // signalCount

 // slots: name, argc, parameters, tag, flags, initial metatype offsets
       1,    0,  122,    2, 0x08,    1 /* Private */,
       3,    0,  123,    2, 0x08,    2 /* Private */,
       4,    0,  124,    2, 0x08,    3 /* Private */,
       5,    1,  125,    2, 0x08,    4 /* Private */,
       7,    0,  128,    2, 0x08,    6 /* Private */,
       8,    0,  129,    2, 0x08,    7 /* Private */,
       9,    0,  130,    2, 0x08,    8 /* Private */,
      10,    0,  131,    2, 0x08,    9 /* Private */,
      11,    0,  132,    2, 0x08,   10 /* Private */,
      12,    0,  133,    2, 0x08,   11 /* Private */,
      13,    0,  134,    2, 0x08,   12 /* Private */,
      14,    1,  135,    2, 0x08,   13 /* Private */,
      16,    1,  138,    2, 0x08,   15 /* Private */,
      17,    1,  141,    2, 0x08,   17 /* Private */,
      18,    1,  144,    2, 0x08,   19 /* Private */,
      19,    0,  147,    2, 0x08,   21 /* Private */,
      20,    0,  148,    2, 0x08,   22 /* Private */,
      21,    0,  149,    2, 0x08,   23 /* Private */,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::Int,    6,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, 0x80000000 | 15,    6,
    QMetaType::Void, QMetaType::Int,    6,
    QMetaType::Void, QMetaType::Int,    6,
    QMetaType::Void, QMetaType::Int,    6,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,

       0        // eod
};

Q_CONSTINIT const QMetaObject MainWindow::staticMetaObject = { {
    QMetaObject::SuperData::link<QMainWindow::staticMetaObject>(),
    qt_meta_stringdata_CLASSMainWindowENDCLASS.offsetsAndSizes,
    qt_meta_data_CLASSMainWindowENDCLASS,
    qt_static_metacall,
    nullptr,
    qt_incomplete_metaTypeArray<qt_meta_stringdata_CLASSMainWindowENDCLASS_t,
        // Q_OBJECT / Q_GADGET
        QtPrivate::TypeAndForceComplete<MainWindow, std::true_type>,
        // method 'on_onoff_COM_clicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_refresh_COM_clicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_send_data_clicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_timed_send_stateChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<int, std::false_type>,
        // method 'startTimedSend'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'stopTimedSend'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'sendData'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_empty_tx_clicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_empty_rx_clicked'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'rx_recieve'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'saveData'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'onCheckboxStateChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<Qt::CheckState, std::false_type>,
        // method 'on_draw_buck_stateChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<int, std::false_type>,
        // method 'on_draw_pid_stateChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<int, std::false_type>,
        // method 'on_draw_dynamic_stateChanged'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        QtPrivate::TypeAndForceComplete<int, std::false_type>,
        // method 'on_drawBuckWindowDestroyed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_drawPidWindowDestroyed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>,
        // method 'on_mainDrawDynamicWindowDestroyed'
        QtPrivate::TypeAndForceComplete<void, std::false_type>
    >,
    nullptr
} };

void MainWindow::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        auto *_t = static_cast<MainWindow *>(_o);
        (void)_t;
        switch (_id) {
        case 0: _t->on_onoff_COM_clicked(); break;
        case 1: _t->on_refresh_COM_clicked(); break;
        case 2: _t->on_send_data_clicked(); break;
        case 3: _t->on_timed_send_stateChanged((*reinterpret_cast< std::add_pointer_t<int>>(_a[1]))); break;
        case 4: _t->startTimedSend(); break;
        case 5: _t->stopTimedSend(); break;
        case 6: _t->sendData(); break;
        case 7: _t->on_empty_tx_clicked(); break;
        case 8: _t->on_empty_rx_clicked(); break;
        case 9: _t->rx_recieve(); break;
        case 10: _t->saveData(); break;
        case 11: _t->onCheckboxStateChanged((*reinterpret_cast< std::add_pointer_t<Qt::CheckState>>(_a[1]))); break;
        case 12: _t->on_draw_buck_stateChanged((*reinterpret_cast< std::add_pointer_t<int>>(_a[1]))); break;
        case 13: _t->on_draw_pid_stateChanged((*reinterpret_cast< std::add_pointer_t<int>>(_a[1]))); break;
        case 14: _t->on_draw_dynamic_stateChanged((*reinterpret_cast< std::add_pointer_t<int>>(_a[1]))); break;
        case 15: _t->on_drawBuckWindowDestroyed(); break;
        case 16: _t->on_drawPidWindowDestroyed(); break;
        case 17: _t->on_mainDrawDynamicWindowDestroyed(); break;
        default: ;
        }
    }
}

const QMetaObject *MainWindow::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *MainWindow::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_CLASSMainWindowENDCLASS.stringdata0))
        return static_cast<void*>(this);
    return QMainWindow::qt_metacast(_clname);
}

int MainWindow::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QMainWindow::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 18)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 18;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 18)
            *reinterpret_cast<QMetaType *>(_a[0]) = QMetaType();
        _id -= 18;
    }
    return _id;
}
QT_WARNING_POP
