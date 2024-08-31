

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys

name = 'ball_glut'
import sys
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np
import time
import cv2
import pandas as pd
#import mysql.connector
#import mysql
import pandas as pd
import numpy as  np
import os
from difflib import SequenceMatcher
import db_tools
import entries
import entries_from_db
import store_players
from sportlogiq import extract_game_info_from_schedule_html
import sportlogiq
import scraping
import feature_engineering
import db_tools
import uuid
import logging
import matplotlib.pyplot as plt
from matplotlib.figure import  Figure
from utils.graphics import oge_time_to_shot
from utils import read_write
class EntryStats(object):
    def __init__(self):
        super().__init__()

        self.entries=None
        self.intervals = []
class VideoApp(QMainWindow): #QWidget):
    def __init__(self):
        super().__init__()

        # Initialize video file path
        self.video_path = ""
        self.game_file_path = ""

        widget = QWidget(self)
        self.setCentralWidget(widget)

        # Create a QLabel to display video
        self.video_label = QLabel(self)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Create a QPushButton for opening a video file
        self.open_video_btn = QPushButton("Open Video File", self)
        self.open_video_btn.clicked.connect(self.open_video_file)

        # Create a QPushButton for opening a second file
        self.open_gamefile_btn = QPushButton("Open Second File", self)
        self.open_gamefile_btn.clicked.connect(self.open_gamefile)

        self.opengl_btn = QPushButton("Opengl", self)
        self.opengl_btn.clicked.connect(self.sphere)

        # Create a QVBoxLayout to arrange widgets
        layout = QVBoxLayout(self)
        layout.addWidget(self.video_label)
        layout.addWidget(self.open_video_btn)
        layout.addWidget(self.open_gamefile_btn)
        layout.addWidget(self.opengl_btn)


        #self.entry_fig = Figure(figsize=(10,10), dpi=100) #plt.figure(figsize=(250, 200))
        self.entry_fig = plt.figure(figsize=(10, 10), dpi=100)  # plt.figure(figsize=(250, 200))
        self.canvas = FigureCanvas(self.entry_fig) #figsize=(250, 200)))
        self.toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        widget.setLayout(layout)

        # Initialize QTimer for video frame update
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)

    def open_video_file(self):
        # im = cv2.imread('/home/veronica/Pictures/a.jpg')
        # cv2.imshow('apa', im)
        # cv2.waitKey(0)
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Video File", "", "Video Files (*.mp4 *.avi);;All Files (*)", options=options)
        if file_name:
            self.video_path = file_name
            self.cap = cv2.VideoCapture(self.video_path)
            self.update_frame()
            #self.timer.start(30)  # Start timer to update video frames

    def open_gamefile(self):
        save_to_folder = 'static/images'
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_name = "/home/veronica/hockeystats/IIHF/2022-23/gamefiles/106656_playsequence-20230528-IIHF World Championship-GERvsCAN-20222023-106656.csv"
        #file_name, _ = QFileDialog.getOpenFileName(self, "Open Gamefile", "", "All Files (*)", options=options)
        if file_name:
            self.gamefile_file_path = file_name
            df = pd.read_csv(self.gamefile_file_path)
            print(df.head())
            events = read_write.load_events(df)
            oz_entries = entries.get_oz_rallies(events)
            entry_times = entries.time_entry_to_shots(oz_entries[list(oz_entries.keys())[0]])
            #entry_times, team_names = entries.generate_entry_statistics(df=df)
            self.canvas.figure.clear()
            #oge_time_to_shot(entry_times[0], fig=self.canvas.figure)
            entry_stat = [e['rally_stat'] for e in entry_times]
            #self.barchart()
            self.main()
            #oge_time_to_shot(entry_stat, fig=self.canvas.figure)

            self.canvas.draw()
            print('apa')
            # print(plt.get_fignums())
            #plt.show()
            # plt.show()

    def barchart(self):
        # create list for y-axis
        y1 = [5, 5, 7, 10, 3, 8, 9, 1, 6, 2]

        # create horizontal list i.e x-axis
        x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        # create pyqt5graph bar graph item
        # with width = 0.6
        # with bar colors = green
        window = pg.plot()
        window.setGeometry(100, 100, 600, 500)

        # title for the plot window
        title = "GeeksforGeeks PyQtGraph"

        # setting window title to plot window
        window.setWindowTitle(title)
        bargraph = pg.BarGraphItem(x=x, height=y1, width=0.6, brush='g')
        window.addItem(bargraph)
    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            height, width, channel = frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
            self.video_label.setPixmap(QPixmap.fromImage(q_img))

    def closeEvent(self, event):
        if hasattr(self, 'cap'):
            self.cap.release()
        event.accept()


    def sphere(self):
        glutInit() #sys.argv)
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
        glutInitWindowSize(400,400)
        glutCreateWindow(name)

        glClearColor(0.,0.,0.,1.)
        glShadeModel(GL_SMOOTH)
        glEnable(GL_CULL_FACE)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        lightZeroPosition = [10.,4.,10.,1.]
        lightZeroColor = [0.8,1.0,0.8,1.0] #green tinged
        glLightfv(GL_LIGHT0, GL_POSITION, lightZeroPosition)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, lightZeroColor)
        glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
        glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.05)
        glEnable(GL_LIGHT0)
        glutDisplayFunc(self.display)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(40.,1.,1.,40.)
        glMatrixMode(GL_MODELVIEW)
        gluLookAt(0,0,10,
                  0,0,0,
                  0,1,0)
        glPushMatrix()
        glutMainLoop()
        return

    def display(self):
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glPushMatrix()
        color = [1.0,0.,0.,1.]
        glMaterialfv(GL_FRONT,GL_DIFFUSE,color)
        glutSolidSphere(2,20,20)
        glPopMatrix()
        glutSwapBuffers()
        return

if __name__ == '__main__':
    glutInit()
    app = QApplication(sys.argv)
    main_win = VideoApp()
    main_win.show()
    sys.exit(app.exec_())