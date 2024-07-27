import pandas as pd
import numpy as np
import cv2
import uuid
from utils.tools import *
import db_tools
from utils import read_write, graphics
from shapely.geometry import Polygon, Point
import entries
import geometry
import tkinter as tk
from tkinter import filedialog, constants, END
import tkinter
import copy
from PIL import Image, ImageTk
import pass_length
import json


class HockeyGuiHandler(object):

    def rgb_color(self, rgb):
        return '#%02x%02x%02x' % rgb
    def mouse_wheel_up(self, event):
        # logging.debug('mousewheel up at position [%d , %d]', event.x, event.y)
        self.scale_up_image(event)

    def mouse_wheel_down(self, event):
        # logging.debug('mousewheel down at position [%d , %d]', event.x, event.y)
        self.scale_down_image(event)

    def control_left(self, event):
        # logging.debug('Left mouse button clicked at [%d , %d]', event.x, event.y)
        self.add_vertex_to_selected_box(event)

    def control_right(self, event):
        pass

    def shift_left(self, event):
        # logging.debug('shift left')
        self.add_to_multi_selection(event)

    def key_release_event(self, event):
        # logging.debug('Keypressed: %s', event.keysym)
        if event.keysym == 'Delete':
            self.delete(event)

    def middle_click(self, event):
        # logging.debug('Middle mouse clicked at coordinates [%d , %d]', event.x, event.y)
        # for i in range(1,1000):
        #     self.navigate_to_frame(i)
        #     self._update_image()

        self.deselect(event)

    def middle_release(self, event):
        # logging.debug('Middle mouse released at coordinates [%d , %d]', event.x, event.y)
        pass

    def mouse_move(self, event):
        # logging.debug('Mouse moved to [%d , %d]', event.x, event.y)
        self.move_object(event)

    def transform_canvas2image(self, x, y):
        x_image = (x + self.canvas.canvasx(0) - self.image_position[0]) / self.scale
        y_image = (y + self.canvas.canvasy(0) - self.image_position[1]) / self.scale
        return x_image, y_image

    def left_double_click(self, event):
        # logging.debug('Left mouse doubleclicked at coordinates [%d , %d]', event.x, event.y)
        pass

    def right_click(self, event):
        # logging.debug('Right mousebutton clicked at coordinates [%d , %d]', event.x, event.y)
        self.grab_object(event)

    def right_release(self, event):
        # logging.debug('Right mousebutton released at coordinates [%d , %d]', event.x, event.y)
        self.right_down = False
        self.background_is_grabbed = False

    def left_release(self, event):
        # logging.debug('Left mousebutton released at coordinates [%d , %d]', event.x, event.y)
        self.set_left_mouse_released(event)

    def left_click(self, event):
        # logging.debug('Left mousebutton clicked at coordinates [%d , %d]', event.x, event.y)
        self.add_new_box(event)

    def deselect(self, event):
        if not self.current_box is None:
            self.current_box = None
            self.current_id = None
            self._update_image()

    def scale_up_image(self, event):
        org_scale = self.scale
        if self.clean_image is not None:
            if self.scale * self.SCALING_FACTOR * max(self.clean_image.shape[0:2]) <= 1920:
                self.scale = self.scale / self.SCALING_FACTOR
        print('scale_up ', self.scale)
        self.update_controls()
        self._update_image()

    def scale_down_image(self, event):
        # Make sure rescaled image is at least one pixel
        org_scale = self.scale
        if self.clean_image is not None:
            if self.scale * self.SCALING_FACTOR * min(self.clean_image.shape[0:2]) > 1:
                self.scale = self.scale * self.SCALING_FACTOR
        print('scale down', self.scale)
        self.update_controls()
        self._update_image()

    def add_vertex_to_selected_box(self, event):
        # Add a new vertex to the selected box. The vertex will be located
        # at the closest point on the shape boundary.
        if not self.current_box is None:
            self.unsaved_changes = True
            x_image, y_image = self.transform_canvas2image(event.x, event.y)
            new_vertex_coords = self.current_box.closest_point(x_image, y_image)
            preceeding_vertex = self.current_box.segment(new_vertex_coords.x, new_vertex_coords.y)
            self.current_box.add_vertex(preceeding_vertex, new_vertex_coords.x, new_vertex_coords.y)
            self.update_controls()
            self._update_image()

    def key_release_event(self, event):
        if event.keysym == 'Delete':
            self.delete(event)

    def delete(self, event):
        if not self.selected_vertex is None:
            self.unsaved_changes = True
            self.current_box.remove_vertex(self.selected_vertex)
            self.selected_vertex = None
        elif not self.current_box is None:
            self.unsaved_changes = True
            idx = self.boxes.index(self.current_box)
            self.boxes.pop(idx)
            self.categories.pop(idx)
            self.ids.pop(idx)
            self.current_box = None


        self._update_image()

    def delete_box_from_rules(self, box):
        for key in self.restriction_rules.keys():
            if box in self.restriction_rules[key]:
                self.restriction_rules[key].pop(self.restriction_rules[key].index(box))
        for key in self.exclusion_rules.keys():
            if box in self.exclusion_rules[key]:
                self.exclusion_rules[key].pop(self.exclusion_rules[key].index(box))

    def move_object(self, event):
        x_image, y_image = self.transform_canvas2image(event.x, event.y)
        if self.left_down:
            self.unsaved_changes = True
            self.current_box.update_vertex(self.selected_vertex,
                                           x_image - self.vertex_offset[0],
                                           y_image - self.vertex_offset[1])
            self._update_image()

        elif self.right_down and self.background_is_grabbed:
            if self.enforce_scale.get() == 0:
                delta = [event.x - self.anchor_point_canvas[0],
                         event.y - self.anchor_point_canvas[1]]
                self.anchor_point_canvas = (event.x, event.y)
                self.image_position = (self.image_position[0] + delta[0],
                                       self.image_position[1] + delta[1])
            else:
                delta = [event.x - self.anchor_point_canvas[0],
                         event.y - self.anchor_point_canvas[1]]
                self.clean_image = np.roll(self.clean_image, delta[0], axis=1)
                self.clean_image = np.roll(self.clean_image, delta[1], axis=0)
                self.anchor_point_canvas = (event.x, event.y)
                self._update_image()
            self._update_image()

        elif self.right_down and not self.current_box is None:
            self.unsaved_changes = True
            self.current_box.update_position(x_image - self.anchor_point[0], y_image - self.anchor_point[1])
            self.anchor_point = (x_image, y_image)
            self._update_image()

    def grab_object(self, event):
        x_image, y_image = self.transform_canvas2image(event.x, event.y)
        self.right_down = True
        self.selected_vertex = None
        self.anchor_point = (x_image, y_image)
        self.anchor_point_canvas = (event.x, event.y)

        for box in self.boxes:
            if box.contains_point(x_image, y_image):
                self.current_box = box
                self._update_image()
                self.update_controls()
                return
        self.background_is_grabbed = True

    def add_to_multi_selection(self, event):
        x_image, y_image = self.transform_canvas2image(event.x, event.y)
        for box in self.boxes:
            if box.contains_point(x_image, y_image):
                if box not in self.multi_selection_box:
                    self.multi_selection_box.append(box)
                else:
                    self.multi_selection_box.pop(self.multi_selection_box.index(box))
                self._update_image()
                self.update_controls()

    def set_left_mouse_released(self, event):
        self.left_down = False

    def team_selected_updated(self):
        self.c1.configure(text=self.team_1_name.get())
        self.c2.configure(text=self.team_2_name.get())
        self.update_controls()
        self._update_image()
    def add_new_box(self, event):
        self.unsaved_changes = True
        x_image, y_image = self.transform_canvas2image(event.x, event.y)
        if self.current_box is None:
            self.boxes.append(geometry.Boundingbox(x_image, y_image))
            self.categories.append(self.current_category.get())
            self.ids.append(str(uuid.uuid4()))
            self.current_box = self.boxes[-1]
        else:
            self.left_down = True
            self.selected_vertex = self.current_box.closest_vertex(x_image, y_image)
            vertex_coords = self.current_box.get_vertecies()[self.selected_vertex]
            self.vertex_offset = (x_image - vertex_coords[0], y_image - vertex_coords[1])
        self._update_image()


    def update_controls(self):

        if not self.current_box is None:
            idx = self.boxes.index(self.current_box)
            color = self.rgb_color(tuple(self.classes_colors[self.categories[idx]]['overlay_color']))
            self.current_category.set(self.categories[idx])
            self.var_current_id.set(self.ids[idx][:8])
        else:
            color = self.rgb_color(tuple(self.classes_colors[self.current_category.get()]['overlay_color']))
        #if self.video_player.num_frames > 0:
        self.players_t1_listbox.delete(0, END)
        self.players_t2_listbox.delete(0, END)
        for (idx, team) in enumerate(self.teams):
            for player in self.players[team]:
                player_string = f"{int(player['playerJersey'])} {player['playerFirstName']} {player['playerLastName']}"
                if idx == 0:
                    self.players_t1_listbox.insert(END, player_string)
                else:
                  self.players_t2_listbox.insert(END, player_string)




    def _update_image(self):
        print(self.scale)
        image = copy.copy(self.clean_image)

        image = cv2.resize(image, (np.uint32(self.scale * image.shape[1]),
                                   np.uint32(self.scale * image.shape[0])), interpolation=cv2.INTER_CUBIC)

        graphics_img = copy.copy(self.clean_graphics_image)
        overlay = np.zeros(image.shape, dtype=np.uint8)

        if self.selected_team.get() == 1:
            entry_statistics = self.entry_statistics['team_1']
        elif self.selected_team.get() == 2:
            entry_statistics = self.entry_statistics['team_2']


        #Fulhack
        entry_statistics = self.entry_statistics

        if True: #isinstance(self.entry_statistics['team_1'], list) and len(self.entry_statistics) > 0:
            self.entry_histogram = graphics.entry_histogram(entry_statistics, self.entry_interval, 60)
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            graphics_img = graphics.overlay_bars(self.entry_histogram,  image=graphics_img, colors=colors,
                                                 scale=self.scale, entry_interval=self.entry_interval)
            image = graphics.overlay_entry_points(entry_statistics, image)

        for box, category in zip(self.boxes, self.categories):
            if category in self.classes_colors.keys():
                c = self.classes_colors[category]['overlay_color']
            else:
                c = (128, 128, 128)
            overlay = box.overlay_box_scaled(overlay, color=c, scale=self.scale)
        if not self.current_box is None:
            overlay = self.current_box.overlay_box_scaled(overlay, color=(0, 255, 255), scale=self.scale,
                                                          draw_vertecies=True,
                                                          selected_vertex=self.selected_vertex)


        image = cv2.addWeighted(image, 0.7, overlay, 0.3, gamma=0.0)

        self.image = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.graphics_image = ImageTk.PhotoImage(image=Image.fromarray(graphics_img))
        if not self.image_item is None:
            self.canvas.delete(self.image_item)
        self.image_item = self.canvas.create_image(self.image_position[0],
                                                   self.image_position[1],
                                                   anchor=tkinter.NW, image=self.image)
        self.graphics_item = self.stat_canvas.create_image(self.image_position[0],
                                                    self.image_position[1],
                                                    anchor=tkinter.NW, image=self.graphics_image)

    def slider_frame_action(self, value):
        self.entry_interval = int(value)
        self._update_image()
        print(value)

    def open_gamefile(self):
        save_to_folder = 'static/images'
        # options = QFileDialog.Options()
        # options |= QFileDialog.ReadOnly
        file_name = "/home/veronica/hockeystats/NHL/2022-23/gamefiles/92424_playsequence-20230413-NHL-VGKvsSEA-20222023-21312.csv"
        # file_name = "/home/veronica/hockeystats/IIHF/2022-23/gamefiles/106656_playsequence-20230528-IIHF World Championship-GERvsCAN-20222023-106656.csv"
        # file_name, _ = QFileDialog.getOpenFileName(self, "Open Gamefile", "", "All Files (*)", options=options)
        if file_name:
            self.gamefile_file_path = file_name
            df = pd.read_csv(self.gamefile_file_path)
            self.teams = extract_teams(df)
            self.players = extract_all_players(df)
            self.current_gamefile_df = df
            events = read_write.load_events(df)
            e2 = db_tools.get_events_from_game(3637)
            oz_entries = entries.get_oz_rallies(events)
            entry_times = entries.time_entry_to_shots(oz_entries[list(oz_entries.keys())[0]])
            # entry_times, team_names = entries.generate_entry_statistics(df=df)
            # self.canvas.figure.clear()
            # oge_time_to_shot(entry_times[0], fig=self.canvas.figure)
            self.entry_statistics = [e['rally_stat'] for e in entry_times]
            self._update_image()
            # cv2.imshow('apa', img)
            # cv2.waitKey(0)
            # self.barchart()
            # self.main()
            # oge_time_to_shot(entry_stat, fig=self.canvas.figure)

            # self.canvas.draw()
            # print('apa')
            # print(plt.get_fignums())
            # plt.show()
            # plt.show()
            self.update_controls()

    def extract_teams_from_league(self):
        print('extract_teams_from_league')




    def statistics_1(self):
        #games = db_tools.run_select_query("select id from game where date<'2023-11-11'")
        query = f"select id from game where date > '2023-09-01' and date < '2024-07-01' and league_id = 2"
        games = db_tools.run_select_query(query)
        games = [g[0] for g in games]
        for g in games[100:200]:
            print(g)
            events = db_tools.get_events_from_game(g)
            teams = db_tools.extract_teams(events)
            #a = db_tools.run_select_query(f"select * from team where id={int(teams[0])}")
            total_t1, average_pass_length_t1 = pass_length.pass_analysis(df=events, team=teams[0])
            total_t2, average_pass_length_t2 = pass_length.pass_analysis(df=events, team=teams[1])
            goals = db_tools.goals_in_game(g)
            keys = goals.keys()
            t1_goals = goals[list(keys)[0]]
            t2_goals = goals[list(keys)[1]]
            print(f"Total passes team 1: {int(total_t1 / average_pass_length_t1)} Total passlength: {total_t1} Average passlength: {average_pass_length_t1} Goals: {t1_goals}")
            print(f"Total passes team 2: {int(total_t2 / average_pass_length_t2)} Total passlength: {total_t2} Average passlength: {average_pass_length_t2} Goals: {t2_goals}")

    def statistics_2(self):
        # db_tools.verify_events(game_id=837)
        db_tools.store_events('/home/veronica/hockeystats/SHL/2022-23/gamefiles/84804_playsequence-20230223-SHL-SAIKvsTIK-20222023-16316.csv')
        print('some statistics')

    def statistics_3(self):
        df = pd.read_csv('/home/veronica/hockeystats/kaggle/goals.csv')
        #self.goal_order(df)
        #self.find_comebacks()
        self.lead_wins()
        # goals=df.loc[df['event'] == 'Goal']
        # goals=goals.loc[goals['periodType'] == 'REGULAR']
        # games=list(goals['game_id'].unique())
        #
        # print('some statistics')

    def goal_order(self, df):

        games = list(df['game_id'].unique())
        goals = df.loc[df['event'] == 'Goal']
        goals=goals.loc[goals['periodType'] == 'REGULAR']
        #games=list(goals['game_id'].unique())
        ctr=0
        game_goal_orders = []
        for game in games:
            print(ctr,' / ', len(games))
            game_goals = goals.loc[goals['game_id'] == game]
            goals_order = list(zip(list(game_goals['goals_home']), list(game_goals['goals_away'])))
            game_goal_orders.append(goals_order)
            ctr += 1

        file = open('goal_orders.json', 'w')
        json.dump(game_goal_orders, file, indent=4)
        file.close()

    def lead_wins(self):
        with open('goal_orders.json', "r") as f:
            games = json.load(f)
        leads = [0] * 20
        wins = [0] * 20
        comebacks = [0] * 20
        for game in games:

            diff = [0] + [a[0] - a[1] for a in game]
            t1 = max(diff)
            t2 = abs(min(diff))
            for i in range(0,t1+1):
                leads[i] += 1
                if diff[-1] > 0:
                    wins[i] += 1
                else:
                    comebacks[i] += 1
            for i in range(0, t2+1):
                leads[i] += 1
                if diff[-1] < 0:
                    wins[i] += 1
                else:
                    comebacks[i] += 1
        for i in range(0, 20):
            print('Leads by ', i, ' goal(s):', leads[i], ' ', wins[i], comebacks[i])


    def find_comebacks(self):
        with open('goal_orders.json', "r") as f:
            games = json.load(f)

        comebacks = []
        max_diffs = []
        for g in games:
            comeback, max_diff = self.max_comeback(g)
            comebacks.append(comeback)
            max_diffs.append(max_diff)
        print(str(len(comebacks)) + ' games')
        num_leads = []
        num_comebacks = []
        for d in range(0,21):
            num_comebacks.append(len([c for c in comebacks if c == d]))
            num_leads.append(len([c for c in max_diffs if c == d]))

        for i in range(0,21):
            print(num_leads[i], ' ', num_comebacks[i])

        # print(len([c for c in comebacks if c == 0]))
        # print(len([c for c in comebacks if c == 1]))
        # print(len([c for c in comebacks if c == 2]))
        # print(len([c for c in comebacks if c == 3]))
        # print(len([c for c in comebacks if c == 4]))
        # print(len([c for c in comebacks if c == 5]))
        # print(len([c for c in comebacks if c == 6]))
        # print(len([c for c in comebacks if c == 7]))
        # print(len([c for c in comebacks if c == 8]))
        # print(len([c for c in comebacks if c == 9]))
        # print(len([c for c in comebacks if c == 10]))
        # print('Max diffs')
        # print(len([c for c in max_diffs if c == 0]))
        # print(len([c for c in max_diffs if c == 1]))
        # print(len([c for c in max_diffs if c == 2]))
        # print(len([c for c in max_diffs if c == 3]))
        # print(len([c for c in max_diffs if c == 4]))
        # print(len([c for c in max_diffs if c == 5]))
        # print(len([c for c in max_diffs if c == 6]))
        # print(len([c for c in max_diffs if c == 7]))
        # print(len([c for c in max_diffs if c == 8]))
        # print(len([c for c in max_diffs if c == 9]))
        # print(len([c for c in max_diffs if c == 10]))


    def max_comeback(self, game):
        diff = [0] + [a[0] - a[1] for a in game]
        if diff[-1] > 0:
            winner = 0
        elif diff[-1] < 0:
            winner = 1
        else:
            winner = 2
        max_diff = max(diff)
        min_diff = min(diff)
        if winner == 2:
            res = max(max_diff, abs(min_diff))
        elif winner == 0:
            res = abs(min_diff)
        else:
            res = max_diff
        return res, max(abs(d) for d in diff)