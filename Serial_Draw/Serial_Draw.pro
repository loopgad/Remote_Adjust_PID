QT       += core gui serialport charts printsupport

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++17

QT_CHARTS_USE_NAMESPACE

# You can make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

SOURCES += \
    draw_buck.cpp \
    draw_pid.cpp \
    main.cpp \
    maindrawdynamic.cpp \
    mainwindow.cpp \
    qcustomplot.cpp


HEADERS += \
    draw_buck.h \
    draw_pid.h \
    maindrawdynamic.h \
    mainwindow.h \
    qcustomplot.h

FORMS += \
    draw_buck.ui \
    draw_pid.ui \
    maindrawdynamic.ui \
    mainwindow.ui

# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

RESOURCES += \
    resource.qrc
