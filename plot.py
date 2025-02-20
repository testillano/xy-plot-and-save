import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pickle
from matplotlib.widgets import Button, RadioButtons
import argparse
import sys, os

# Command-line arguments
parser = argparse.ArgumentParser(description="Draw launcher rates in time")
parser.add_argument("--output", type=str, default="example", help="Output file basename to store data: plain text (<basename>.txt) and pickle serialization (<basename>.pickle). Defaults to 'example'")
parser.add_argument("--duration", type=int, default=3600, help="Curve maximum time value in seconds. Defaults to 3600")
parser.add_argument("--timeline-ticks", type=str, default=100, help="Number of ticks in timeline axis. Defaults to 100")
parser.add_argument("--max-rate", type=int, default=2000, help="Curve maximum rate value. Defaults to 2000")
parser.add_argument("--min-rate", type=int, default=10, help="Minimum rate reference which helps to draw zero-rate points. Defaults to 10")
parser.add_argument("--rate-module", type=int, default=1, help="Rate module to restrict y-axis resolution. Defaults to 1")
parser.add_argument("--labels", type=str, help="Curve labels space-separated list. For example: script-001,script-002")
parser.add_argument("--input", type=str, help="Input file basename to load (.txt and .pickle files are required). Restriction: must have same original timeline ticks")

args = parser.parse_args()

# Parameters
T_MAX = args.duration
Y_MAX = args.max_rate
T_MIN = args.min_rate
rate_module = args.rate_module
if rate_module < 1:
  print ("ERROR: invalid '--rate-module'. Must be positive number !")
  sys.exit(1)

OUTPUT_FILEBN = args.output
INPUT_FILEBN = args.input
COL_SIZE = 20
timeline_ticks = int(args.timeline_ticks)
if timeline_ticks < 1:
  print ("ERROR: invalid '--timeline-ticks'. Must be positive number !")
  sys.exit(1)

DELTA = int(T_MAX/timeline_ticks)  # sample time (secs)
times = np.arange(0, T_MAX + DELTA, DELTA)

tags = []
current_tag = None
colors = None
y_values = {}
painted = {}
drawing = False

def debug():
  print(f"times array: {times}")
  for k, v in painted.items(): print(f"painted dictionary:  {k}: {v}")
  for k, v in y_values.items(): print(f"y_values dictionary: {k}: {v}")

def on_press(event):
  global drawing
  if event.inaxes == ax:
    drawing = True
    #update_curve(event)

def on_release(event):
  global drawing
  drawing = False

def on_motion(event):
  if drawing and event.inaxes == ax:
    update_curve(event)

def update_curve(event):
  if event.xdata is not None and event.ydata is not None:
    y_value = event.ydata

    # Restrictions:
    y_value = round(y_value/rate_module) * rate_module
    if y_value < T_MIN: y_value = 0 # zeroed reference

    index = int(event.xdata // DELTA)
    if 0 <= index < len(times):
      y_values[current_tag][index] = min(int(y_value), Y_MAX)
      painted[current_tag][index] = True
      visible_x = times[painted[current_tag]]
      visible_y = y_values[current_tag][painted[current_tag]]
      lines[current_tag].set_data(visible_x, visible_y)
    fig.canvas.draw()

def generate_list(event):

  #debug()

  # Store corresponding pickle file
  with open(OUTPUT_FILEBN + '.pickle', 'wb') as f:
    pickle.dump(fig, f)

  all_times = sorted(set(times[np.any(list(painted.values()), axis=0)]))
  header = ["Timeline(s)"] + tags
  output_data = []

  for t in all_times:
    row = [str(t)]
    for tag in tags:
      index = np.where(times == t)[0][0] # time index is serie
      if painted[tag][index]:
        row.append(str(y_values[tag][index]))
      else:
        row.append("-")
    output_data.append(" ".join(row))

  with open(OUTPUT_FILEBN + '.txt', "w") as f:
    for data in header:
      f.write(data.ljust(COL_SIZE))
    f.write("\n")
    for data in output_data:
      for w in data.split():
        f.write(w.ljust(COL_SIZE))
      f.write("\n")

  print(f"Saved '{OUTPUT_FILEBN}' .txt and .pickle' files")

def clear_plot(event):
  for tag in y_values:
    y_values[tag][:] = 0
    painted[tag][:] = False
    lines[tag].set_data([], [])
  fig.canvas.draw()

def exit_program(event):
  print("Goodbye !")
  sys.exit(0)

def change_series(label):
  global current_tag
  current_tag = label
  print(f"Selected '{current_tag}'")

#############
# EXECUTION #
#############
# Create figure:
fig, ax = None, None
lines = {}

if INPUT_FILEBN: # from previous data:

  if args.labels:
    print("WARNING: --labels will be ignored as input file basename is processed")

  try:
    # PICKLE FILE
    with open(INPUT_FILEBN + '.pickle', 'rb') as f:
      fig = pickle.load(f)
      ax = fig.get_axes()[0]
      lines = {line.get_label(): line for line in ax.lines}
      legend = ax.get_legend()
      tags = [label.get_text() for label in legend.get_texts()]
      current_tag = tags[0]

    # DATA FILE
    df = pd.read_csv(INPUT_FILEBN + '.txt', sep=r'\s+', engine='python')  # Usamos sep='\s+' para manejar múltiples espacios

    # Extract times:
    #times = df.iloc[:, 0].to_numpy()  # first column as numpy array

    # Read tags from file:
    tags = list(df.columns[1:])

    # Initialize dictionaries:
    y_values = {}
    painted = {}

    for tag in tags:
      y_values[tag] = np.full(timeline_ticks + 1, 0) # initialize
      painted[tag] = np.zeros(timeline_ticks + 1, dtype=bool) # initialize

      for i, row in df.iterrows():
        timeline_value = row['Timeline(s)']
        tag_value = row[tag]

        if tag_value != '-': # has value
          index = np.where(times == timeline_value)[0][0] # time index is serie
          y_values[tag][index] = int(tag_value)
          painted[tag][index] = True

        index = index + 1

  except Exception as e:
    print (f"ERROR: reading input files (.txt and/or .pickle) for basename '{INPUT_FILEBN}'  ({e})")
    sys.exit(1)

else:
  if not args.labels:
    print("ERROR: --labels are mandatory when input file is not provided")
    sys.exit(1)

  tags = args.labels.split(",")
  current_tag = tags[0]
  colors = plt.get_cmap("tab10", len(tags)) # tab10, viridis, etc.
  y_values = {tag: np.zeros_like(times, dtype=int) for tag in tags}
  painted = {tag: np.zeros_like(times, dtype=bool) for tag in tags} # to select painted points

  fig, ax = plt.subplots(figsize=(10, 10*Y_MAX/timeline_ticks)) #  inches (wide x height)
  ax.set_xlim(0, T_MAX)
  ax.set_ylim(0, Y_MAX)
  ax.set_xlabel("Timeline (s)")
  ax.set_ylabel("Rate (scripts/s)")
  lines = {tag: ax.plot([], [], lw=2, label=tag, color=colors(i), marker="o", linestyle='-')[0] for i, tag in enumerate(tags)}

#debug()
plt.subplots_adjust(left=0.2, bottom=0.3)
ax.legend()
plt.grid(True)

fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("motion_notify_event", on_motion)

ax_button_generate = plt.axes([0.55, 0.05, 0.1, 0.075])
ax_button_clear = plt.axes([0.67, 0.05, 0.1, 0.075])
ax_button_exit = plt.axes([0.79, 0.05, 0.1, 0.075])
ax_radio = plt.axes([0.01, 0.3, 0.1, 0.3])

button_generate = Button(ax_button_generate, "Save")
button_clear = Button(ax_button_clear, "Clean")
button_exit = Button(ax_button_exit, "Exit")
radio = RadioButtons(ax_radio, tags)

button_generate.on_clicked(generate_list)
button_clear.on_clicked(clear_plot)
button_exit.on_clicked(exit_program)
radio.on_clicked(change_series)

plt.show()

