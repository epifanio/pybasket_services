import functools
import time
import requests
from bokeh.models import Div, Button, Select
from bokeh.layouts import column, row, Spacer
from bokeh.models.widgets import CheckboxGroup, RadioGroup
from waiting import wait
from infrastructure.request_cache import get_data
from fontawesome.fontawesome_icon import FontAwesomeIcon
from json2html import *
from ast import literal_eval
import os
import xarray as xr

from log_util import setup_log, get_logpath


logger = setup_log('custom_checkbox', logtype='stream')


def get_selection(widget, json_data):
    ts_selected = [i.children[0].children[0].labels[0] for i in widget.children[0].children[2].children if
                   i.children[0].children[0].active]
    tsp_selected = [i.children[0].children[0].labels[0] for i in widget.children[1].children[2].children if
                    i.children[0].children[0].active]
    print(ts_selected, tsp_selected)
    return {i: json_data['data'][i] for i in json_data['data'] if
            json_data['data'][i]['title'] in ts_selected + tsp_selected}


def get_status(transaction_id):
    if get_data(transaction_id)['status']:
        return True
    return False


def set_log_txt(output_log):
    output_log.text = "processing"


def get_table(metadata_dict):
    metadata_table = json2html.convert(json=literal_eval(metadata_dict),
                                       escape=True,
                                       table_attributes="id=\"info-table\" class=\"table table-bordered table-hover\"")
    return metadata_table


def meta_button(metadata_dict, host_layout, content_type='metadata'):
    fake_div = Div(text='', width=50)
    fake_div.visible = False
    if content_type == 'metadata':
        content = get_table(metadata_dict)
        icon_name = "info"
    if content_type == 'plot':
        plot_endpoint = os.environ['PLOT_ENDPOINT']  # 'https://ncplot.epinux.com/test/TS-Plot'
        plot_url = literal_eval(metadata_dict)['resources']['opendap'][0]
        content = f'<iframe src="{plot_endpoint}?url={plot_url}" width="1225" height="725" frameborder=0 scrolling=no></iframe>'
        icon_name = "line-chart"
    host_layout.children[0].text = content

    def show_hide_metadata(event):
        if host_layout.visible:
            host_layout.visible = False
        else:
            fake_div.visible = True
            host_layout.visible = True
            fake_div.visible = False

    metadata_button = Button(icon=FontAwesomeIcon(icon_name=icon_name, size=1.5),
                             label="",
                             height=40,
                             width=50,
                             css_classes=['btn-clear'])
    metadata_button.on_click(show_hide_metadata)
    md = column(metadata_button, fake_div)
    return md


def custom_checkbox(json_data):
    logger.debug(f'received: {json_data}')
    metadata_layout = row(Div(text='host'))
    metadata_layout.visible = False
    plot_layout = row(Div(text='host'))
    plot_layout.visible = False

    ts_dict = {data_id: json_data['data'][data_id] for data_id in
               json_data['data'] if
               json_data['data'][data_id]['feature_type'] == 'timeSeries'}
    tsp_dict = {data_id: json_data['data'][data_id] for data_id in
                json_data['data'] if
                json_data['data'][data_id]['feature_type'] == 'timeSeriesProfile'}

    ts_info_layouts = {data_id: row(Div(text='host'), visible=False) for data_id in ts_dict}
    tsp_info_layouts = {data_id: row(Div(text='host'), visible=False) for data_id in tsp_dict}

    ts_info_btns = {data_id: meta_button(str(ts_dict[data_id]), ts_info_layouts[data_id], 'metadata') for data_id in
                    ts_dict}

    tsp_info_btns = {data_id: meta_button(str(tsp_dict[data_id]), tsp_info_layouts[data_id], 'metadata') for data_id in
                     tsp_dict}

    ts_plot_layouts = {data_id: row(Div(text='host'), visible=False) for data_id in ts_dict}
    tsp_plot_layouts = {data_id: row(Div(text='host'), visible=False) for data_id in tsp_dict}

    ts_plot_btns = {data_id: meta_button(str(ts_dict[data_id]), ts_plot_layouts[data_id], 'plot') for data_id in
                    ts_dict}

    tsp_plot_btns = {data_id: meta_button(str(tsp_dict[data_id]), tsp_plot_layouts[data_id], 'plot') for data_id in
                     tsp_dict}

    ts_checkboxes = column([column(row(CheckboxGroup(labels=[ts_dict[data_id]['title']],
                                                     css_classes=['bk-bs-checkbox']),
                                       ts_info_btns[data_id], ts_plot_btns[data_id]),
                                   column([ts_info_layouts[data_id], ts_plot_layouts[data_id]])) for data_id in
                            ts_dict])

    tsp_checkboxes = column([column(row(CheckboxGroup(labels=[tsp_dict[data_id]['title']],
                                                      css_classes=['bk-bs-checkbox']),
                                        tsp_info_btns[data_id], tsp_plot_btns[data_id]),
                                    column([tsp_info_layouts[data_id], tsp_plot_layouts[data_id]])) for data_id in
                             tsp_dict])

    # tsp_checkboxes = column([column(row(CheckboxGroup(labels=[tsp_dict[data_id]['title']],
    #                                                  css_classes=['bk-bs-checkbox']),
    #                                    tsp_info_btns[data_id], tsp_plot_btns[data_id]),
    #                                column([tsp_info_layouts[data_id], plot_layout])) for data_id in
    #                         tsp_dict])

    if len(ts_checkboxes.children) >= 1:
        ts_label = Div(text='<b>Time Series :</b>', css_classes=['custom_label'])
    else:
        ts_label = Div(text='')
    if len(tsp_checkboxes.children) >= 1:
        tsp_label = Div(text='<b>Time Series Profile :</b>', css_classes=['custom_label'])
    else:
        tsp_label = Div(text='')
    multi_select = column(column(ts_label, Spacer(width=20), ts_checkboxes),
                          column(tsp_label, Spacer(width=20), tsp_checkboxes),
                          Spacer(height=20))

    return multi_select


def export_widget(current_doc, widget, json_data, advanced=False):
    download = Button(icon=FontAwesomeIcon(icon_name="cogs", size=1.5),
                      height=50,
                      width=50,
                      label='')

    fake_div = Div(text='', width=100)
    fake_div.visible = False

    export_button = Button(icon=FontAwesomeIcon(icon_name="download", size=1.5),
                           height=40,
                           width=30,
                           label='')
    output_log_widget = Div(text='', min_width=60)

    def clear_download(widget):
        widget.visible = False

    clean_btn = Button(icon=FontAwesomeIcon(icon_name="times", size=1.2),
                       label="",
                       height=30,
                       width=30,
                       css_classes=['btn-clear'])

    clean_btn.on_click(functools.partial(clear_download,
                                         widget=output_log_widget))

    def callback(attr, old, new):
        if new == 0:
            resampling.visible = False
        else:
            resampling.visible = True

    if advanced:
        export_format = Select(title="Select output data format:",
                               value='csv',
                               options=['csv', 'NetCDF'],
                               css_classes=['custom_select'],
                               width=100)
        # hardcoded variables:
        variables = ['sal', 'temp']
        export_variables = CheckboxGroup(labels=variables,
                                         css_classes=['custom_select'])
        resampling = Select(title="Frequency:",
                            value='--',
                            options=['--', 'H', 'D', 'W', 'M', 'Q', 'Y'],
                            css_classes=['custom_select'], max_width=100)
        resampling.visible = False
        export_resampling = RadioGroup(labels=["Raw", "Resampled"], active=0)
        export_resampling_layout = column(Div(text='<font size = "2" color = "darkslategray" ><b>Frequency:<b></font>'),
                                          export_resampling,
                                          Spacer(height=10), resampling)
        export_resampling.on_change('active', callback)

    def data_download():
        pass

    def show_hide_export(event):
        if export_layout.visible:
            export_layout.visible = False
        else:
            fake_div.visible = True
            export_layout.visible = True
            fake_div.visible = False

    def compress_selection(widget, json_data, output_log_widget):
        selected_data = get_selection(widget, json_data)
        for i in data:
            nc_url = selected_data[i]['resources']['opendap'][0]
            try:
                xr.open_dataset(nc_url, decode_cf=False)
            except RuntimeError:
                logger.debug(f'failed to load resource: {nc_url}')
                del selected_data[i]
                logger.debug(f'removing {nc_url} from selected datasources')
        logger.debug(f'attempt to compress: {selected_data}')
        send_data = {'data': selected_data,
                     'email': json_data['email'],
                     'project': json_data['project']}
        # r = requests.post('http://127.0.0.1:9000/api/compress', json=send_data)
        api_host = os.environ['API_HOST']
        logger.debug(f'using api host: {api_host}')
        # api_host = 'metsis.epinux.com'
        # r = requests.post('http://10.0.0.100:8000/api/compress', json=send_data)
        try: 
            r = requests.post(f'https://{api_host}/api/compress', json=send_data)
            transaction_id = str(r.json()['transaction_id'])
            output_log_widget.visible = True
            wait(lambda: get_status(transaction_id), waiting_for="download to be ready")
            transaction_id_data = transaction_id + "_data"
            transaction_data_url = get_data(transaction_id_data)['download_url']
            output_log_widget.text = str(f'<a href="{transaction_data_url}">Download</a>')
            logger.debug(f'succes in compressing: {send_data}')
        except:
            logger.debug(f'transaction failed sending datya: {send_data}')

    download.on_click(show_hide_export)

    def compress_selection_callback(widget, json_data, output_log_widget):
        output_log_widget.text = str(
            '<marquee behavior="scroll" direction="left"><b>. . . processing . . .</b></marquee>')
        current_doc.add_next_tick_callback(functools.partial(compress_selection,
                                                             widget=widget,
                                                             json_data=json_data,
                                                             output_log_widget=output_log_widget))

    export_button.on_click(functools.partial(compress_selection_callback,
                                             widget=widget,
                                             json_data=json_data,
                                             output_log_widget=output_log_widget))
    if advanced:
        export_layout = row(fake_div, Spacer(width=30),
                            column(Div(text='<font size = "3" color = "darkslategray" ><b>Data Export:<b></font>'),
                                   Spacer(height=10),
                                   Div(
                                       text='<font size = "2" color = "darkslategray" ><b>Select Variables to export:<b></font>'),
                                   export_variables,
                                   Spacer(height=10),
                                   export_format,
                                   Spacer(height=10),
                                   export_resampling_layout,
                                   Div(
                                       text='<font size = "2" color = "darkslategray" ><b>Generate Download link:<b></font>'),
                                   Spacer(height=10),
                                   export_button), sizing_mode='fixed')
    else:
        export_layout = row(fake_div, Spacer(width=30),
                            column(Spacer(height=30),
                                   Div(text='<font size = "3" color = "darkslategray" ><b>Data Export:<b></font>'),
                                   Spacer(height=10),
                                   row(export_button,
                                       Spacer(width=20),
                                       output_log_widget,
                                       Spacer(width=20), min_width=100)), sizing_mode='fixed')  # clean_btn

    export_layout.visible = False

    return column(download, export_layout)
