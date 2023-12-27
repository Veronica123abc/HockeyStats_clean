from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GL import *
import sys
from math import *
import ctypes
import logging

import numpy as np
import OpenGL.GL as gl
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QOpenGLWindow


logger = logging.getLogger(__name__)


vertex_code = '''
attribute vec2 position;
void main()
{
  gl_Position = vec4(position, 0.0, 1.0);
}
'''


fragment_code = '''
void main()
{
  gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
}
'''


class MinimalGLWidget(QOpenGLWindow):
    def initializeGL(self):

        program = gl.glCreateProgram()
        vertex = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        fragment = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        #
        # # Set shaders source
        gl.glShaderSource(vertex, vertex_code)
        gl.glShaderSource(fragment, fragment_code)
        #
        # # Compile shaders
        gl.glCompileShader(vertex)
        if not gl.glGetShaderiv(vertex, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(vertex).decode()
            logger.error("Vertex shader compilation error: %s", error)

        gl.glCompileShader(fragment)
        if not gl.glGetShaderiv(fragment, gl.GL_COMPILE_STATUS):
            error = gl.glGetShaderInfoLog(fragment).decode()
            print(error)
            raise RuntimeError("Fragment shader compilation error")

        # gl.glAttachShader(program, vertex)
        # gl.glAttachShader(program, fragment)
        # gl.glLinkProgram(program)
        #
        # if not gl.glGetProgramiv(program, gl.GL_LINK_STATUS):
        #     print(gl.glGetProgramInfoLog(program))
        #     raise RuntimeError('Linking error')
        #
        # gl.glDetachShader(program, vertex)
        # gl.glDetachShader(program, fragment)
        #
        # gl.glUseProgram(program)
        #
        # # Build data
        # data = np.zeros((4, 2), dtype=np.float32)
        # # Request a buffer slot from GPU
        # buffer = gl.glGenBuffers(1)
        #
        # # Make this buffer the default one
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
        #
        # stride = data.strides[0]
        #
        # offset = ctypes.c_void_p(0)
        # loc = gl.glGetAttribLocation(program, "position")
        # gl.glEnableVertexAttribArray(loc)
        # gl.glBindBuffer(gl.GL_ARRAY_BUFFER, buffer)
        # gl.glVertexAttribPointer(loc, 2, gl.GL_FLOAT, False, stride, offset)
        #
        # # Assign CPU data
        # data[...] = [(-1, +1), (+1, -1), (-1, -1), (+1, -1)]
        #
        # # Upload CPU data to GPU buffer
        # gl.glBufferData(
        #     gl.GL_ARRAY_BUFFER, data.nbytes, data, gl.GL_DYNAMIC_DRAW)

    def paintGL(self):

        posx, posy = 0, 0
        sides = 32
        radius = 1
        glBegin(GL_POLYGON)
        for i in range(100):
            cosine = radius * cos(i * 2 * pi / sides) + posx
            sine = radius * sin(i * 2 * pi / sides) + posy
            glVertex2f(cosine, sine)
        # gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        # gl.glDrawArrays(gl.GL_TRIANGLE_STRIP, 0, 4)


if __name__ == '__main__':
    app = QApplication([])
    widget = MinimalGLWidget()
    widget.show()
    app.exec_()

# from PyQt5 import QtCore, QtGui, QtWidgets
#
# from PyQt5.QtWidgets import *
# from PyQt5.QtGui import *
# from PyQt5.QtCore import *
# from PyQt5.uic import *
#
# from OpenGL.GL import *
# from OpenGL.GLUT import *
# from OpenGL.GLU import *
#
# class Ui_MainWindow(object):
#     def setupUi(self, MainWindow):
#         MainWindow.setObjectName("MainWindow")
#         MainWindow.resize(800, 600)
#         self.centralwidget = QtWidgets.QWidget(MainWindow)
#         self.centralwidget.setObjectName("centralwidget")
#         self.openGLWidget = QtWidgets.QOpenGLWidget(self.centralwidget)
#         self.openGLWidget.setGeometry(QtCore.QRect(110, 50, 591, 451))
#         self.openGLWidget.setObjectName("openGLWidget")
#         MainWindow.setCentralWidget(self.centralwidget)
#         self.statusbar = QtWidgets.QStatusBar(MainWindow)
#         self.statusbar.setObjectName("statusbar")
#         MainWindow.setStatusBar(self.statusbar)
#
#         self.retranslateUi(MainWindow)
#         QtCore.QMetaObject.connectSlotsByName(MainWindow)
#
#     def retranslateUi(self, MainWindow):
#         _translate = QtCore.QCoreApplication.translate
#         MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
#
#         self.openGLWidget.initializeGL()
#         self.openGLWidget.resizeGL(651,551)
#         self.openGLWidget.paintGL = self.paintGL
#
#         timer = QTimer(self.centralwidget)
#         timer.timeout.connect(self.openGLWidget.update)
#         timer.start(1000)
#
#     def paintGL(self):
#         glClear(GL_COLOR_BUFFER_BIT)
#         glColor3f(1,0,0);
#         glBegin(GL_TRIANGLES);
#         glVertex3f(-0.5,-0.5,0);
#         glVertex3f(0.5,-0.5,0);
#         glVertex3f(0.0,0.5,0);
#         glEnd()
#
#         gluPerspective(45, 651/551, 0.1, 50.0)
#         glTranslatef(0.0,0.0, -5)
#
# if __name__ == "__main__":
#     import sys
#     app = QtWidgets.QApplication(sys.argv)
#     MainWindow = QtWidgets.QMainWindow()
#     ui = Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec_())



# name = 'ball_glut'

# def main():
#     glutInit(sys.argv)
#     glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
#     glutInitWindowSize(400,400)
#     glutCreateWindow(name)
#
#     glClearColor(0.,0.,0.,1.)
#     glShadeModel(GL_SMOOTH)
#     glEnable(GL_CULL_FACE)
#     glEnable(GL_DEPTH_TEST)
#     glEnable(GL_LIGHTING)
#     lightZeroPosition = [10.,4.,10.,1.]
#     lightZeroColor = [0.8,1.0,0.8,1.0] #green tinged
#     glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
#     glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)
#     glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
#     glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.05)
#     glEnable(GL_LIGHT0)
#     glutDisplayFunc(display)
#     glMatrixMode(GL_PROJECTION)
#     gluPerspective(40.,1.,1.,40.)
#     glMatrixMode(GL_MODELVIEW)
#     gluLookAt(0,0,10,
#               0,0,0,
#               0,1,0)
#     glPushMatrix()
#     glutMainLoop()
#     return
#
# def display():
#     glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
#     glPushMatrix()
#     color = [1.0,0.,0.,1.]
#     glMaterialfv(GL_FRONT,GL_DIFFUSE,color)
#     glutSolidSphere(2,20,20)
#     glPopMatrix()
#     glutSwapBuffers()
#     return
#
#
# if __name__ == '__main__':
#     main()
