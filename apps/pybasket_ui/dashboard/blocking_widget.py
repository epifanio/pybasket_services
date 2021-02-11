from time import sleep
import functools
from bokeh.layouts import column, row
from bokeh.models import Button, Div


def blocker(curdoc, something):
    d = Div(text="""<iframe src="https://ncplot.epinux.com/test/TS-Plot?url=https://hyrax.epinux.com/opendap/local_data/ctdiaoos_gi2007_2009.nc"></iframe>""", width=300, height=300)

    b = Button(label='blocking task')

    def work(t='end'):
        sleep(2)
        d.text = t

    def cb(something):
        d.text = f"... processing ... {something}"
        curdoc.add_next_tick_callback(functools.partial(work, something))

    b.on_click(functools.partial(cb, something))
    return row(b, d)
