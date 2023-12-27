
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
APOI = None
import cv2
import copy

def times_to_first_shot(entries):
    ttfs = [e['time_to_first_shot'] for e in entries if e['time_to_first_shot']]
    return ttfs
def entry_histogram(entries, ax=None, ax2=None, team=''):
    fontsize_caption=15
    fontsize_chart=10
    ax = ax or plt.gca()
    ax2 = ax2 or plt.gca()
    colors = [[1.0, 0, 0, 0.7], [0, 1, 0, 0.7], [0, 0, 1.0, 0.7]]
    def func(pct, entries):
        absolute = int(np.round(pct / 100. * np.sum(entries)))
        return "{:d}\n({:.0f}%)".format(absolute, pct)
        #return "{:d}".format(absolute)

    labels = ['','','']#'Passes', 'Dumpins', 'Carries']
    total = float(len(entries))
    lead_to_shot = float(len([e for e in entries if e['time_to_first_shot']]))
    passes = len([e for e in entries if e['entry_type'] == 'pass'])
    passes_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'pass'])
    dumpins = len([e for e in entries if e['entry_type'] == 'dumpin'])
    dumpins_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'dumpin'])
    carries = len([e for e in entries if e['entry_type'] == 'carry'])
    carries_with_shot = len([e for e in entries if e['time_to_first_shot'] and e['entry_type'] == 'carry'])
    total = float(len(entries) - lead_to_shot)
    all_entries = [passes, dumpins, carries]
    captions=[str(passes) + '(' + str(passes_with_shot) + ')',
              str(dumpins) + '(' + str(dumpins_with_shot) + ')',
              str(carries) + '(' + str(carries_with_shot) + ')']
    entries_with_shot = [carries_with_shot, dumpins_with_shot, passes_with_shot]
    entries_no_shot = [carries - carries_with_shot, dumpins - dumpins_with_shot, passes-passes_with_shot]
    #ax.pie(all_entries, labels=labels, autopct=lambda pct: func(pct, all_entries), textprops=dict(color="k", size=10),
    #        shadow=True, startangle=90)

    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    ax.set_title('OZ entries with no shots', fontsize=fontsize_caption)
    ax2.axis('equal')
    ax2.set_title('OZ entries generating shots', fontsize=fontsize_caption)
    ax.pie(entries_no_shot, labels=labels, textprops=dict(color="k", size=fontsize_chart),
            shadow=True, startangle=90, colors=colors, autopct=lambda pct: func(pct, entries_no_shot))
    ax2.pie(entries_with_shot, labels=labels, textprops=dict(color="k", size=fontsize_chart),
            shadow=True, startangle=90, colors=colors, autopct=lambda pct: func(pct, entries_with_shot))

    # return ax, ax2
def oge_time_to_shot(entries, fig=None, ax=None, max_time=30, interval=3):
    # demo()
    # noges_for_types(entries)
    fontsize_table = 10
    fontsize_caption = 10
    fontsize_legend = 10
    if fig is None:
        fig = plt.figure(figsize=(40,25))

    ax = fig.add_gridspec(4, 4)
    ax1 = fig.add_subplot(ax[0:2, 3:])
    ax2 = fig.add_subplot(ax[2:, 3:])

    ax3 = fig.add_subplot(ax[0:,0:3])

    entry_histogram(entries, ax=ax1, ax2=ax2)

    #fig=plt.figure(figsize=(15, 10))
    bin_cnt = int(max_time // interval)
    oges = [e for e in entries if e['time_to_first_shot']]
    oges_dumpins = [e for e in oges if e['entry_type'] == 'dumpin']
    oges_passes = [e for e in oges if e['entry_type'] == 'pass']
    oges_carries = [e for e in oges if e['entry_type'] == 'carry']

    noges = [e for e in entries if not e['time_to_first_shot']]
    noges_dumpins = [e for e in noges if e['entry_type'] == 'dumpin']
    noges_passes = [e for e in noges if e['entry_type'] == 'pass']
    noges_carries = [e for e in noges if e['entry_type'] == 'carry']

    dumpins_ttfs = times_to_first_shot(oges_dumpins)
    passes_ttfs = times_to_first_shot(oges_passes)
    carries_ttfs = times_to_first_shot(oges_carries)
    #plt.bar([i for i in range(0,max_time + interval, interval)], dumpins_ttfs)
    #plt.hist([dumpins_ttfs, passes_ttfs, carries_ttfs], range=(0, bin_cnt*interval), width=10, stacked=True)
    counts_c, bins_c = np.histogram(carries_ttfs, range=(0, max_time), bins=bin_cnt)
    counts_d, bins_d = np.histogram(dumpins_ttfs, range=(0, max_time), bins=bin_cnt)
    counts_p, bins_p = np.histogram(passes_ttfs, range=(0, max_time), bins=bin_cnt)

    high_c = len([e for e in oges_carries if e['time_to_first_shot'] > max_time])
    high_d = len([e for e in oges_dumpins if e['time_to_first_shot'] > max_time])
    high_p = len([e for e in oges_passes if e['time_to_first_shot'] > max_time])


    data = np.array([counts_c, counts_d, counts_p])
    data = np.hstack((data, np.array([[high_c], [high_d], [high_p]])))
    # data = np.hstack((data, np.array([[len(noges_carries)], [len(noges_dumpins)], [len(noges_passes)]])))
    columns = [str(int(bins_c[i])) + ' to ' + str(int(bins_c[i+1])) + ' s' for i in range(0, len(bins_c) - 1)] + \
              ['> ' + str(max_time) + ' s'] #+ ['no shots']
    rows = ['carries', 'dumpins', 'passes']
    # colors = plt.cm.BuPu(np.linspace(0, 0.5, len(rows)))
    colors = [[1.0,0,0,0.7], [0,1,0,0.7], [0,0,1.0,0.7]]
    n_rows = len(data)

    index = np.arange(len(columns)) + 0.3
    bar_width = 0.4

    # Initialize the vertical-offset for the stacked bar chart.
    y_offset = np.zeros(len(columns))
    values = np.arange(0, np.max(data)+10, 10)
    value_increment = 1

    # Plot bars and create text labels for the table
    cell_text = []
    plt.axis = ax3
    for row in range(n_rows):
        plt.bar(index, data[row], bar_width, bottom=y_offset, color=colors[row])
        y_offset = y_offset + data[row]
        cell_text.append(['%d' % x for x in data[row]])

    plt.ylabel(f"Number of entries generating a shot within each time interval", fontsize=fontsize_caption)
    plt.yticks(values * value_increment, ['%d' % val for val in values])
    plt.yticks(fontsize=fontsize_table)
    plt.xticks([])
    # plt.title('Entries Time-To-Shot', fontsize=18, weight='bold')
    # Reverse colors and text labels to display the last value at the top.
    colors = colors[::-1]
    cell_text.reverse()
    rows.reverse()


    the_table = plt.table(cellText=cell_text,
                          rowLabels=rows,
                          rowColours=colors,
                          colLabels=columns,
                          cellLoc='center',
                          loc='bottom',
                          fontsize=fontsize_table)
    the_table.auto_set_font_size(False)
    for (row, col), cell in the_table.get_celld().items():
        cell.set_text_props(fontproperties=FontProperties(weight='bold', size=10))

    plt.legend(['carries','dumpins','passes'], fontsize=fontsize_legend)
    the_table.scale(1,4)
    #fig.show()
    # plt.show()
    ax1 = plt
    return plt


def overlay_bars(values, image=None, colors=None, scale=10, entry_interval=3):
    if not isinstance(values[0], list):
        values = [values]
    if colors is None:
        colors = np.random.randint(0,256, (len(values[0]), 3)).tolist()

    maxvals =[max(value) for value in values]
    max_y = max([sum(triplet) for triplet in zip(values[0], values[1], values[2])])

    title_height = 30
    full_height, full_width = image.shape[0:2]
    height = full_height - title_height
    y_scale = int(height / max_y)
    num_bars = len(values[0])
    bar_width = int(40)
    offset = int(20)
    space = int(10)
    start = int(20)

    scaled_values = [[int(v * y_scale) for v in val] for val in values]
    width = num_bars*(bar_width+space) + offset
    if image is None:
        image = np.zeros((height, width, 3), dtype=np.uint8)
    image = cv2.rectangle(image, (0,0), (full_width, title_height), color=(255,255,255), thickness=-1)

    x_ticks = [start + idx*(bar_width + space) for idx in range(0, num_bars)]
    ctr = 1
    for x in x_ticks:
        x_pos = x + bar_width
        image = cv2.putText(image, f"{ctr * entry_interval}", (x_pos, title_height - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            color=(0,0,0), thickness=2)
        ctr += 1
    offsets = len(scaled_values[0]) * [0]
    for value, color in zip(scaled_values, colors):
        for x,y,o in zip(x_ticks,value, offsets):
            image = cv2.rectangle(image, (x,height - o - y + title_height - 1), (x+bar_width, height - o + title_height - 1), color, -1)
            if y > 0:
                image = cv2.putText(image, f"{int(y/y_scale)}", (x+10, height - o - int(y/2) + title_height - 1), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, (255,255,255), 2, cv2.LINE_AA)
        offsets = [of + val for (of, val) in zip(offsets, value)]



    # offsets = len(values[0]) * [0]
    # for value, color in zip(values, colors):
    #     for x, y, o in zip(x_ticks, value, offsets):
    #
    #         image = cv2.putText(image, f"{y}", (x+20, height - int(o/2)) , cv2.FONT_HERSHEY_SIMPLEX,
    #                             0.3, color, 1, cv2.LINE_AA)
    #     # offsets = [of + 15 for of in offsets]
    #     offsets = [of + val for (of, val) in zip(offsets, value)]


        # image = cv2.rectangle(img, (x,height - y - 1), (x+width, height-1), color=(255,0,0))
    return image


def entry_histogram(entries, duration, max_duration):
    intervals = [(i, i+duration) for i in range(0,max_duration, duration)]
    values = []
    oge_entries = [entry for entry in entries if entry['time_to_first_shot'] is not None]
    for type in ['carry', 'pass', 'dumpin']:
        e_t_val = []
        for interval in intervals:
            e_t = [e for e in oge_entries if (interval[0] <= e['time_to_first_shot'] < interval[1]) and e['entry_type'] == type]
            e_t_val.append(len(e_t))
        values.append(e_t_val)
    non_oge_entries = [entry for entry in entries if entry['time_to_first_shot'] is None or entry['time_to_first_shot'] > max_duration]
    e_t_val = []
    for type in ['carry', 'pass', 'dumpin']:

        e_t = [e for e in non_oge_entries if e['entry_type'] == type]
        e_t_val.append(len(e_t))

    values[0].append(e_t_val[0])
    values[1].append(e_t_val[1])
    values[2].append(e_t_val[2])

    return values

def overlay_entry_points(entry_stats, image):
    scale_row = image.shape[0] / 85
    scale_col = image.shape[1] / 200
    color = (0,255,0)
    entry_stats = copy.deepcopy(entry_stats)
    for entry in entry_stats:
        if entry['entry_type'] == 'carry':
            color = (255,0,0)
        elif entry['entry_type'] == 'pass':
            color = (0,255,0)
        else:
            color = (0,0,255)
        if entry['period'] == 2:
            entry['entry_x'] = 0 - entry['entry_x']
            entry['entry_y'] = 0 - entry['entry_y']
            #color = (0,0,0)
        pt = (int(scale_col * (100 + entry['entry_x'])), int(scale_row * (42 + entry['entry_y'])))

        image = cv2.circle(image, pt, 5, color=color, thickness=-1)
        image = cv2.circle(image, pt, 5, color=(100,200, 121), thickness=1)

    return image