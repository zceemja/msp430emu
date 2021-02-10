#include "py_interface.h"


PyObject *pyOnSerial;
PyObject *pyOnConsole;
PyObject *pyOnControl;

static PyObject *method_start(PyObject *self, PyObject *args) {
    char *firmware_file;
    if(!PyArg_ParseTuple(args, "s", &firmware_file)) {
        return NULL;
    }
    Py_BEGIN_ALLOW_THREADS
    start_emu(firmware_file);
    Py_END_ALLOW_THREADS
    return Py_None;
}

static PyObject *method_cmd(PyObject *self, PyObject *args) {
    char *cmd;
    int len;
    if(!PyArg_ParseTuple(args, "s#", &cmd, &len)) {
        return NULL;
    }
    cmd_emu(cmd, len);
    return Py_None;
}

static PyObject *method_get_regs(PyObject *self, PyObject *args) {
    uint8_t reg_type;

    if(!PyArg_ParseTuple(args, "B", &reg_type)) {
        return NULL;
    }
    switch(reg_type) {
    case GET_REG_P1:
        return get_port1_regs();
    }
    return Py_None;
}

static PyObject *method_set_regs(PyObject *self, PyObject *args) {
    uint8_t reg_type, reg_value;
    if(!PyArg_ParseTuple(args, "BB", &reg_type, &reg_value)) {
        return NULL;
    }
    set_reg(reg_type, reg_value);
    return Py_None;
}

static PyObject *method_stop(PyObject *self, PyObject *args) {
    stop_emu();
//    Py_XDECREF(pyOnSerial);
//    Py_XDECREF(pyOnConsole);
//    Py_XDECREF(pyOnControl);
    return Py_None;
}

static PyObject *method_reset(PyObject *self, PyObject *args) {
    reset_emu();
    return Py_None;
}

static PyObject *method_play(PyObject *self, PyObject *args) {
    play_emu();
    return Py_None;
}

static PyObject *method_pause(PyObject *self, PyObject *args) {
    pause_emu();
    return Py_None;
}

static PyObject *method_on_serial(PyObject *self, PyObject *args) {
    if(!PyArg_ParseTuple(args, "O", &pyOnSerial)) {
        PyErr_SetString(PyExc_ValueError, "Invalid argument, must be single object");
        pyOnSerial = NULL;
        return NULL;
    }
    if(!PyCallable_Check(pyOnSerial)) {
        PyErr_SetString(PyExc_ValueError, "Argument object is not callable");
        pyOnSerial = NULL;
        return NULL;
    }
    Py_INCREF(pyOnSerial);
    return Py_None;
}

static PyObject *method_on_console(PyObject *self, PyObject *args) {
    if(!PyArg_ParseTuple(args, "O", &pyOnConsole)) {
        PyErr_SetString(PyExc_ValueError, "Invalid argument, must be single object");
        pyOnControl = NULL;
        return NULL;
    }
    if(!PyCallable_Check(pyOnConsole)) {
        PyErr_SetString(PyExc_ValueError, "Argument object is not callable");
        pyOnConsole = NULL;
        return NULL;
    }
    Py_INCREF(pyOnConsole);
    PyObject *tuple = PyTuple_New(1);
    PyObject *pyBuf = PyUnicode_FromString("Console established..\n");
    PyTuple_SetItem(tuple, 0, pyBuf);
    PyObject_Call(pyOnConsole, tuple, NULL);
    return Py_None;
}

static PyObject *method_on_control(PyObject *self, PyObject *args) {
    if(!PyArg_ParseTuple(args, "O", &pyOnControl)) {
        PyErr_SetString(PyExc_ValueError, "Invalid argument, must be single object");
        pyOnSerial = NULL;
        return NULL;
    }
    if(!PyCallable_Check(pyOnControl)) {
        PyErr_SetString(PyExc_ValueError, "Argument object is not callable");
        pyOnSerial = NULL;
        return NULL;
    }
    Py_INCREF(pyOnControl);
    return Py_None;
}


static PyMethodDef RunMethods[] = {
    {"init", method_start, METH_VARARGS, "Initialise msp430 emulator"},
    {"cmd", method_cmd, METH_VARARGS, "Send command to msp430 emulator"},
    {"stop", method_stop, METH_NOARGS, "Stop msp430 emulator"},
    {"play", method_play, METH_NOARGS, "Start running msp430 emulator"},
    {"pause", method_pause, METH_NOARGS, "Pause running msp430 emulator"},
    {"reset", method_reset, METH_NOARGS, "Reset msp430 emulator"},
    {"on_serial", method_on_serial, METH_VARARGS, "Set emulator callback for serial"},
    {"on_console", method_on_console, METH_VARARGS, "Set emulator callback for console"},
    {"on_control", method_on_control, METH_VARARGS, "Set emulator callback for control"},
    {"get_regs", method_get_regs, METH_VARARGS, "Get emulator registers"},
    {"set_regs", method_set_regs, METH_VARARGS, "Set emulator registers"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef msp430module = {
    PyModuleDef_HEAD_INIT,
    "_msp430emu",
    "Python interface for msp430 emulator",
    -1,
    RunMethods
};

PyMODINIT_FUNC PyInit__msp430emu(void) {
    return PyModule_Create(&msp430module);
}


void print_serial(Emulator *emu, char *buf) {
    if(pyOnSerial == NULL) return;

    // set thread state
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *tuple = PyTuple_New(1);
    PyObject *pyBuf = PyUnicode_FromString(buf);
    PyTuple_SetItem(tuple, 0, pyBuf);
    PyObject_Call(pyOnSerial, tuple, NULL);

//    Py_DECREF(pyBuf);
//    Py_DECREF(tuple);
    // resolve thread state
    PyGILState_Release(gstate);
}


void print_console (Emulator *emu, const char *buf) {
    if(pyOnConsole == NULL) {
        puts(buf);
        return;
    }

    // set thread state
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *tuple = PyTuple_New(1);
    PyObject *pyBuf = PyUnicode_FromString(buf);
    PyTuple_SetItem(tuple, 0, pyBuf);
    PyObject_Call(pyOnConsole, tuple, NULL);

//    Py_DECREF(pyBuf);
//    Py_DECREF(tuple);

    // resolve thread state
    PyGILState_Release(gstate);
}

void send_control (Emulator *emu, uint8_t opcode, void *data, size_t size) {
    if(pyOnControl == NULL) return;

    // set thread state
    PyGILState_STATE gstate;
    gstate = PyGILState_Ensure();

    PyObject *tuple = PyTuple_New(2);
    PyObject *pyOpcode = PyLong_FromLong(opcode);
    PyTuple_SetItem(tuple, 0, pyOpcode);
    PyObject *pyData = PyBytes_FromStringAndSize(data, size);
    PyTuple_SetItem(tuple, 1, pyData);
    PyObject_Call(pyOnControl, tuple, NULL);

//    Py_DECREF(pyOpcode);
//    Py_DECREF(pyData);
//    Py_DECREF(tuple);

    // resolve thread state
    PyGILState_Release(gstate);
}
