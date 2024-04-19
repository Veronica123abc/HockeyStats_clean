import os
import os
import tkinter as tk
from tkinter import *
import tkinter
import json
import itertools
import cv2
from PIL import Image,ImageTk
import numpy as np

import hockey_gui_handler
import copy


class HockeyGui(hockey_gui_handler.HockeyGuiHandler):
    def load_config(self, filepath='app_default.json'):
        with open(filepath, "r") as content:
            configs = json.load(content)
            for key in configs:
                if hasattr(self, key):
                    setattr(self, key, configs[key])

    def scale_clean_image_to_canvas(self):
        w = float(self.canvas['width'])
        h = float(self.canvas['heigh'])
        ratio = min(w / self.clean_image.shape[1], h / self.clean_image.shape[0])
        self.clean_image = cv2.resize(self.clean_image, (int(ratio * self.clean_image.shape[1]),
                                                         int(ratio * self.clean_image.shape[0])),
                                      interpolation=cv2.INTER_CUBIC)


    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.teams = []
        self.players = []
        self.current_gamefile_df = None
        self.default_image_canvas_height = 0
        self.default_image_canvas_width = 0
        self.default_statistics_canvas_height = 0
        self.default_statistics_canvas_width = 0
        self.root = Tk()
        self.root.geometry("1400x1000")
        self.image_item = None
        self.clean_image = None
        self.image_position = (0,0)
        self.entry_statistics = {'team_1': 'None', 'team_2': 'None'}
        self.entry_interval = 1
        self.menubar = Menu(self.root)
        self.filemenu = Menu(self.menubar)
        self.filemenu.add_command(label="Select gamefile", command=self.open_gamefile)
        self.scrape = Menu(self.menubar)
        self.scrape.add_command(label="extract teams from league", command=self.extract_teams_from_league)
        self.statistics = Menu(self.menubar)
        self.statistics.add_command(label="some statistics ...", command=self.statistics_1)
        self.statistics.add_command(label="some statistics ...", command=self.statistics_2)
        self.statistics.add_command(label="some statistics ...", command=self.statistics_3)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.menubar.add_cascade(label="Scraping", menu=self.scrape)
        self.menubar.add_cascade(label="Statistics", menu=self.statistics)
        self.root.config(menu=self.menubar)

        self.image = []
        self.scale = 1
        self.stored_scales =[]
        self.enforce_scale = tk.IntVar()

        self.classes_colors = {'region': {'name': 'default', 'overlay_color': (128, 128, 128)}}
        self.track_colors = [[0, 0, 255], [25, 200, 25]]


        self.selected_team = tk.IntVar()
        self.team_1_name = tk.StringVar()
        self.team_2_name = tk.StringVar()
        self.var_current_frame = tk.StringVar()
        self.var_current_frame.set(0)
        self.var_current_id = tk.StringVar()
        self.var_current_id.set('None')
        self.var_stored_id = tk.StringVar()
        self.var_stored_id.set('None')
        self.stored_id = None
        self.image_size  = (0,0)
        self.rink_width = 85 # North American defaults to 85 feet
        self.rink_length = 200 # North-amerikan rinks defaults to 200 feet

        self.background_is_grabbed = False
        self.current_box = None
        self.boxes = []
        self.categories = []
        self.ids = []
        self.current_category = tk.StringVar()
        self.current_category.set('default')

        self.selected_box = None
        self.multi_selection_box = []
        self.current_id = None
        self.vertex_offset = (0,0)
        self.selected_vertex = None
        self.anchor_point = (0,0)
        self.image_position = (0,0)
        self.scale_delta = 0.1 # Dynamically changed to make downscaling slower as the image becomes very small
        self.SCALE_DELTA_MAX = 0.1 # The highest allowed change in scale
        self.SCALING_FACTOR = 0.9
        self.default_clean_file = "/home/veronica/repos/HockeyStats/static/images/rink.jpg"
        self.clean_image_changed = False
        self.filename = 'regions.json'
        self.left_down = False
        self.middle_down = False
        self.right_down = False
        self.button_down_coords = (0,0)
        self.left_frame = Frame(self.root)
        self.left_frame.grid(row=0,column=0)
        self.default_checkpoint = None
        self.default_model_config = None
        self.current_directory = None
        self.load_config()

        # Create a canvas
        self.right_frame = Frame(self.root)
        self.canvas_frame = Frame(self.root)
        self.statistics_frame = Frame(self.root)
        self.navigation_frame = Frame(self.root)
        self.entries_frame = Frame(self.root)
        self.canvas = Canvas(self.canvas_frame,
                             width=self.default_image_canvas_width,
                             height=self.default_image_canvas_height)
        self.stat_canvas = Canvas(self.statistics_frame,
                             width=self.default_statistics_canvas_width,
                             height=self.default_statistics_canvas_height)
        scrollbar_t1 = Scrollbar(self.right_frame, orient="vertical")
        scrollbar_t1.grid(row=1, column=1,sticky="NS")
        self.team_1_label = Label(self.right_frame, textvariable=self.team_1_name,  font=('Helvetica', 18))
        self.team_2_label = Label(self.right_frame, textvariable=self.team_2_name, font=('Helvetica', 18))
        self.players_t1_listbox = Listbox(self.right_frame, width=35, height=22, yscrollcommand = scrollbar_t1.set,
                                    exportselection=0,
                                    relief=SUNKEN,
                                    bg='gray')
        scrollbar_t2 = Scrollbar(self.right_frame, orient="vertical")
        scrollbar_t2.grid(row=3, column=1,sticky="NS")
        self.players_t2_listbox = Listbox(self.right_frame, width=35, height=22, yscrollcommand = scrollbar_t2.set,
                                    exportselection=0,
                                    relief=SUNKEN,
                                    bg='gray')

        self.team_1_label.grid(row=0, column=0, sticky="N")
        self.team_2_label.grid(row=2, column=0, sticky="N")

        self.c1 = tk.Radiobutton(self.canvas_frame, text=self.team_1_name.get(), variable=self.selected_team, value=1,
                                 command= self.team_selected_updated, font=('Helvetica', 18))
        self.c2 = tk.Radiobutton(self.canvas_frame, text=self.team_2_name.get(), variable=self.selected_team, value=2,
                                 command = self.team_selected_updated, font=('Helvetica', 18))
        self.c1.grid(row=1, column=0, sticky="W")
        self.c2.grid(row=2, column=0, sticky="W")
        self.players_t1_listbox.grid(row=1, column=0, sticky="N")
        self.players_t2_listbox.grid(row=3, column=0, sticky="N")
        self.canvas_frame.grid(row=0, column=0, sticky="N")
        self.canvas.grid(row=0, column=0, sticky="N")
        self.statistics_frame.grid(row=1, column=0, sticky="N")
        self.stat_canvas.grid(row=0, column=0, sticky="N")
        self.right_frame.grid(row=0, column=1, rowspan=2, sticky="N")
        self.clean_image = cv2.imread("static/images/rink.jpg")
        self.clean_image = cv2.cvtColor(self.clean_image, cv2.COLOR_BGR2RGB)
        self.clean_graphics_image = np.zeros((self.default_statistics_canvas_height,
                                              self.default_statistics_canvas_width, 3), dtype=np.uint8)
        self.scale_clean_image_to_canvas()
        image = copy.copy(self.clean_image)
        image2 = copy.copy(self.clean_graphics_image)
        self.graphics_image = ImageTk.PhotoImage(image=Image.fromarray(image2))
        self.image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.image_item = self.canvas.create_image(0, 0, anchor=NW, image=self.image)
        self.graphics_item = self.stat_canvas.create_image(0, 0, anchor=NW, image=self.graphics_image)
        self.navigation_frame.grid(row=2, column=0, sticky="W")
        self.entries_frame.grid(row=2, column=0)#, sticky="S")
        self.entries_slider = Scale(self.entries_frame, orient="horizontal",
                                 from_=0, to=10, length=self.default_statistics_canvas_width, command=self.slider_frame_action)
        self.entries_slider.grid(row=2, column=0)#, sticky="S")
        # Load an image in the script

        self.entries_slider.set(25)
        self.canvas.bind('<Button-1>', self.left_click)
        self.canvas.bind('<Button-2>', self.middle_click)
        self.canvas.bind('<Button-3>', self.right_click)
        self.canvas.bind('<ButtonRelease-1>', self.left_release)
        self.canvas.bind('<ButtonRelease-2>', self.middle_release)
        self.canvas.bind('<ButtonRelease-3>', self.right_release)
        self.canvas.bind('<Motion>', self.mouse_move)
        self.canvas.bind('<Double-Button-1>', self.left_double_click)
        self.canvas.bind_all('<KeyRelease>', self.key_release_event)
        self.canvas.bind('<Control-Button-1>', self.control_left)
        self.canvas.bind('<Control-Button-3>', self.control_right)
        self.canvas.bind('<Shift-Button-1>', self.shift_left)
        self.canvas.bind("<Button-4>", self.mouse_wheel_up)
        self.canvas.bind("<Button-5>", self.mouse_wheel_down)

        self.root.mainloop()



a = HockeyGui()
import matplotlib.pyplot as plt


# # Data for a three-dimensional line
# zline = np.linspace(0, 15, 1000)
# xline = np.sin(zline)
# yline = np.cos(zline)
# ax.plot3D(xline, yline, zline, 'gray')

# Data for three-dimensional scattered points
# z = np.random.randint(0,4,(100))
# #zdata = 10+15 * np.random.randint(0,2,(100)).astype(float)
# colors = np.array(['red', 'blue','green', 'yellow'])
# vocabulary = z.tolist()
# zdata = 255 * z
# xdata = np.random.randn(100)
# ydata = np.random.randn(100)
# ax = plt.axes(projection='3d')
# ax.scatter3D(xdata, ydata, zdata, c=colors[z], s=50)
#
#
# ax.set_facecolor('black')
# plt.grid(False)
# plt.axis('off')
# plt.show()