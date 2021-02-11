from bokeh.plotting import curdoc
from bokeh.models import Spacer
from bokeh.layouts import row, column
from custom_bk_widgets import custom_checkbox, export_widget
import json

import sys

sys.path.append("fontawesome")
from pathlib import Path
import os

curdoc_element = curdoc()

args = curdoc_element.session_context.request.arguments

if not Path(os.environ['TSPLOT_DOWNLOAD']).exists():
    Path(os.environ['TSPLOT_DOWNLOAD']).mkdir(parents=True, exist_ok=True)

input_data = json.loads(args.get('data')[0].decode())


checkboxes = custom_checkbox(input_data)
doc = curdoc()
export_layout = export_widget(doc, checkboxes, input_data)

curdoc_element.add_root(column(column(checkboxes,
                                      column(Spacer(width=10, height=10, sizing_mode='fixed'),
                                             export_layout)),
                               Spacer(height=10, sizing_mode='scale_width'),
                               row(Spacer(height=10, sizing_mode='fixed')),
                               sizing_mode='scale_width'))
