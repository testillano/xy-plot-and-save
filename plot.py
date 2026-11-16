import argparse
import json
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.widgets import Button, RadioButtons

TIMELINE_HEADER = "Timeline(s)"
UNPAINTED = "-"

# Command-line arguments
parser = argparse.ArgumentParser(description="Plot xy curves (value over time)")
parser.add_argument("--output", type=str, default="example", help="Output file basename to store data: session (<basename>.json, reloadable with '--input') and plain text table (<basename>.txt). Defaults to 'example'")
parser.add_argument("--input", type=str, help="Input file basename to load (<basename>.json, as saved). Its parameters (duration, timeline ticks, values range, y-label and labels) are used, so the corresponding options are ignored")
parser.add_argument("--duration", type=int, default=3600, help="Curve maximum time value in seconds. Defaults to 3600")
parser.add_argument("--timeline-ticks", type=int, default=100, help="Number of ticks in timeline axis. The duration must be a multiple of it. Defaults to 100")
parser.add_argument("--max-value", type=int, default=2000, help="Maximum y-value. Defaults to 2000")
parser.add_argument("--min-value", type=int, default=10, help="Minimum y-value reference which helps to draw zero-value points (lower values are zeroed). Defaults to 10")
parser.add_argument("--value-module", type=int, default=1, help="Value module to restrict y-axis resolution. Defaults to 1")
parser.add_argument("--y-label", type=str, default="Value", help="Y-axis label. For example: 'Rate (cps)'")
parser.add_argument("--labels", type=str, help="Curve labels comma-separated list (no spaces within a label). For example: test-001,test-002")

args = parser.parse_args()


def fail(message):
  print(f"ERROR: {message}")
  sys.exit(1)


def validate_parameters(params):
  """Checks the session parameters (from command line or input file)."""
  if params["duration"] < 1:
    fail("invalid duration. Must be positive number !")
  if params["timelineTicks"] < 1:
    fail("invalid timeline ticks. Must be positive number !")
  if params["duration"] % params["timelineTicks"] != 0:
    fail(f"invalid timeline ticks ({params['timelineTicks']}). The duration ({params['duration']}) must be a multiple of it !")
  if params["maxValue"] < 1:
    fail("invalid max value. Must be positive number !")
  if params["minValue"] < 0 or params["minValue"] > params["maxValue"]:
    fail(f"invalid min value. Must be in the range [0, {params['maxValue']}] !")
  if params["valueModule"] < 1:
    fail("invalid value module. Must be positive number !")


def validate_labels(labels):
  """Labels are columns of the whitespace-separated table: no empty, blank-containing or repeated ones."""
  if not labels:
    fail("no labels provided")
  for label in labels:
    if not label or any(c.isspace() for c in label):
      fail(f"invalid label '{label}'. Must be non-empty and with no spaces !")
    if label == TIMELINE_HEADER:
      fail(f"invalid label '{label}'. It is reserved for the timeline column !")
  if len(set(labels)) != len(labels):
    fail(f"repeated labels in '{','.join(labels)}'")


def load_session(basename):
  """Returns the parameters, labels and values (None for unpainted points) saved by save_files()."""
  path = basename + ".json"
  try:
    with open(path) as f:
      session = json.load(f)
    params = {k: int(session[k]) for k in ("duration", "timelineTicks", "maxValue", "minValue", "valueModule")}
    params["yLabel"] = str(session["yLabel"])
    series = [(str(s["label"]), list(s["values"])) for s in session["series"]]
  except (OSError, ValueError, KeyError, TypeError) as e:
    fail(f"reading input file '{path}' ({e})")

  validate_parameters(params)
  validate_labels([label for label, _ in series])
  points = params["timelineTicks"] + 1
  for label, values in series:
    if len(values) != points:
      fail(f"reading input file '{path}': '{label}' has {len(values)} values, {points} expected")
    if any(v is not None and not isinstance(v, int) for v in values):
      fail(f"reading input file '{path}': '{label}' has non-integer values")
  return params, series


#############
# SESSION   #
#############
if args.input:
  if args.labels:
    print("WARNING: --labels will be ignored as input file basename is processed")
  params, series = load_session(args.input)
else:
  if not args.labels:
    fail("--labels is mandatory when input file is not provided")
  params = {
    "duration": args.duration,
    "timelineTicks": args.timeline_ticks,
    "maxValue": args.max_value,
    "minValue": args.min_value,
    "valueModule": args.value_module,
    "yLabel": args.y_label,
  }
  validate_parameters(params)
  labels = args.labels.split(",")
  validate_labels(labels)
  series = [(label, [None] * (params["timelineTicks"] + 1)) for label in labels]

OUTPUT_FILEBN = args.output
T_MAX = params["duration"]
Y_MAX = params["maxValue"]
T_MIN = params["minValue"]
VALUE_MODULE = params["valueModule"]
DELTA = T_MAX // params["timelineTicks"]  # sample time (secs), exact by validation
times = np.arange(0, T_MAX + DELTA, DELTA)  # timelineTicks + 1 points, last one is the duration

tags = [label for label, _ in series]
y_values = {label: np.array([v or 0 for v in values], dtype=int) for label, values in series}
painted = {label: np.array([v is not None for v in values], dtype=bool) for label, values in series}
current_tag = tags[0]
drawing = False
last_point = None  # (index, value) of the previous point in a drag, to fill the skipped ones


def quantize(y_value):
  """Applies the y-axis restrictions: module resolution, zeroed reference and range."""
  y_value = int(round(y_value / VALUE_MODULE) * VALUE_MODULE)
  if y_value < T_MIN:
    y_value = 0  # zeroed reference
  return max(0, min(y_value, Y_MAX))


def refresh_line(tag):
  mask = painted[tag]
  lines[tag].set_data(times[mask], y_values[tag][mask])


def paint(event):
  """Paints the point nearest to the event, and the ones skipped since the previous point of the drag."""
  global last_point
  if event.xdata is None or event.ydata is None:
    return
  index = int(round(event.xdata / DELTA))
  if not 0 <= index < len(times):
    return
  value = float(event.ydata)

  if last_point is None or last_point[0] == index:
    points = [(index, value)]
  else:
    # Fast drags skip indexes: interpolate linearly from the previous point
    prev_index, prev_value = last_point
    step = 1 if index > prev_index else -1
    span = index - prev_index
    points = [(i, prev_value + (value - prev_value) * (i - prev_index) / span)
              for i in range(prev_index + step, index + step, step)]

  for i, v in points:
    y_values[current_tag][i] = quantize(v)
    painted[current_tag][i] = True
  last_point = (index, value)
  refresh_line(current_tag)
  fig.canvas.draw_idle()


def on_press(event):
  global drawing, last_point
  if event.inaxes == ax:
    drawing = True
    last_point = None
    paint(event)  # a single click paints a point


def on_release(event):
  global drawing, last_point
  drawing = False
  last_point = None


def on_motion(event):
  if drawing and event.inaxes == ax:
    paint(event)


def save_files(event):
  # Session file (reloadable):
  session = dict(params)
  session["series"] = [
    {"label": tag, "values": [int(y_values[tag][i]) if painted[tag][i] else None for i in range(len(times))]}
    for tag in tags
  ]
  with open(OUTPUT_FILEBN + ".json", "w") as f:
    json.dump(session, f, indent=2)
    f.write("\n")

  # Plain text table file (painted times only):
  header = [TIMELINE_HEADER] + tags
  rows = []
  for i in np.flatnonzero(np.any([painted[tag] for tag in tags], axis=0)):
    rows.append([str(times[i])] + [str(y_values[tag][i]) if painted[tag][i] else UNPAINTED for tag in tags])
  widths = [2 + max(len(row[c]) for row in [header] + rows) for c in range(len(header))]

  with open(OUTPUT_FILEBN + ".txt", "w") as f:
    for row in [header] + rows:
      f.write(" ".join(cell.ljust(widths[c]) for c, cell in enumerate(row)).rstrip() + "\n")

  print(f"Saved '{OUTPUT_FILEBN}.json' and '{OUTPUT_FILEBN}.txt' files")


def clear_plot(event):
  for tag in tags:
    y_values[tag][:] = 0
    painted[tag][:] = False
    refresh_line(tag)
  fig.canvas.draw_idle()


def exit_program(event):
  # Closing the figures makes plt.show() return: no SystemExit inside the GUI event loop
  print("Goodbye !")
  plt.close("all")


def change_series(label):
  global current_tag
  current_tag = label
  print(f"Selected '{current_tag}'")


#############
# EXECUTION #
#############
dpi = 100
factor = 0.9
wide_px, height_px = factor * 1280, factor * 960
fig, ax = plt.subplots(figsize=(wide_px / dpi, height_px / dpi), dpi=dpi)  # inches (wide x height)
ax.set_xlim(0, T_MAX)
ax.set_ylim(0, Y_MAX)
ax.set_xlabel("Timeline (s)")
ax.set_ylabel(params["yLabel"])
colors = plt.get_cmap("tab10", len(tags))  # tab10, viridis, etc.
lines = {tag: ax.plot([], [], lw=2, label=tag, color=colors(i), marker="o", linestyle="-")[0] for i, tag in enumerate(tags)}
for tag in tags:
  refresh_line(tag)

plt.subplots_adjust(left=0.2, bottom=0.3)
ax.legend()
ax.grid(True)

fig.canvas.mpl_connect("button_press_event", on_press)
fig.canvas.mpl_connect("button_release_event", on_release)
fig.canvas.mpl_connect("motion_notify_event", on_motion)

ax_button_save = plt.axes([0.60, 0.08, 0.1, 0.075])
ax_button_clear = plt.axes([0.72, 0.08, 0.1, 0.075])
ax_button_exit = plt.axes([0.84, 0.08, 0.1, 0.075])
ax_radio = plt.axes([0.01, 0.05, 0.5, 0.15])

button_save = Button(ax_button_save, "Save")
button_clear = Button(ax_button_clear, "Clean")
button_exit = Button(ax_button_exit, "Exit")
radio = RadioButtons(ax_radio, tags)

button_save.on_clicked(save_files)
button_clear.on_clicked(clear_plot)
button_exit.on_clicked(exit_program)
radio.on_clicked(change_series)

plt.show()
