import functools
import time
import requests
from bokeh.models import Div, Button, Select, Dropdown
from bokeh.layouts import column, row, Spacer
from bokeh.models.widgets import CheckboxGroup, RadioGroup
from waiting import wait
from infrastructure.request_cache import get_data
from fontawesome.fontawesome_icon import FontAwesomeIcon
from json2html import *
from ast import literal_eval
import os
import xarray as xr
import yaml
from ipywidgets import Box, VBox, Layout, Label
from ipywidgets_bokeh import IPyWidget
from ipywidgets import widgets


from log_util import setup_log, get_logpath

logger = setup_log("custom_checkbox", logtype="stream")

selected_notebooks = []


def get_selection(widget, json_data, nb_config):
    ts_selected = [
        i.children[0].children[0].labels[0]
        for i in widget.children[0].children[2].children
        if i.children[0].children[0].active
    ]
    p_selected = [
        i.children[0].children[0].labels[0]
        for i in widget.children[1].children[2].children
        if i.children[0].children[0].active
    ]
    tsp_selected = [
        i.children[0].children[0].labels[0]
        for i in widget.children[2].children[2].children
        if i.children[0].children[0].active
    ]
    na_selected = [
        i.children[0].children[0].labels[0]
        for i in widget.children[3].children[2].children
        if i.children[0].children[0].active
    ]
    # Notebooks Multi-selection
    # nb_selected = [i.children[0].children[0].labels[0] for i in widget.children[4].children[2].children if
    #                i.children[0].children[0].active]
    # NB single selection
    # nb_selected = widget.children[4].children[2].children[0].children[0].value
    # print("SELECTED NOTEBOOK:", nb_selected)
    # nb_selected = []
    # print(ts_selected, p_selected, tsp_selected, na_selected, nb_selected)
    if json_data['notebook'] == True:
        nb_dict = {i["name"]: i for i in nb_config["notebooks"]}
        # nb_selected_dict = {i: nb_dict[i] for i in nb_dict if i in nb_selected}
        nb_selected_dict = {
            widget.children[4]
            .children[2]
            .children[0]
            .children[0]
            .value: nb_dict[widget.children[4].children[2].children[0].children[0].value]
        }
        print(nb_selected_dict)
    else:
        nb_selected_dict = {}
    data_selected_dict = {
        i: json_data["data"][i]
        for i in json_data["data"]
        if json_data["data"][i]["title"]
        in ts_selected + p_selected + tsp_selected + na_selected
    }

    print(json_data)
    return {"data": data_selected_dict, "notebooks": nb_selected_dict}


def get_status(transaction_id, redishost, password):
    if get_data(
        transaction_id=transaction_id,
        redishost=os.environ["REDIS_HOST"],
        password=password,
    )["status"]:
        return True
    return False


def set_log_txt(output_log):
    output_log.text = "processing"


def get_table(metadata_dict):
    metadata_table = json2html.convert(
        json=literal_eval(metadata_dict),
        escape=True,
        table_attributes='id="info-table" class="table table-bordered table-hover"',
    )
    return metadata_table


def nb_info(attr, old, new, metadata_dict, host_layout):
    fake_div = Div(text="", width=50)
    fake_div.visible = False
    content = json2html.convert(
        json=metadata_dict[new],
        escape=True,
        table_attributes='id="info-table" class="table table-bordered table-hover"',
    )
    icon_name = "info"
    host_layout.children[0].text = content
    print(content)


def meta_button(metadata_dict, host_layout, content_type="metadata"):
    fake_div = Div(text="", width=50)
    fake_div.visible = False
    if content_type == "metadata":
        content = get_table(metadata_dict)
        icon_name = "info"
    if content_type == "plot":
        plot_endpoint = os.environ[
            "PLOT_ENDPOINT"
        ]  # 'https://ncplot.epinux.com/test/TS-Plot'
        plot_url = literal_eval(metadata_dict)["resources"]["opendap"][0]
        content = f'<iframe src="{plot_endpoint}?url={plot_url}" width="1225" height="725" frameborder=0 scrolling=no></iframe>'
        icon_name = "line-chart"
    if content_type == "NA":
        if "OGC:WMS" in literal_eval(metadata_dict)["resources"]:
            wms_endpoint = os.environ[
                "WMS_ENDPOINT"
            ]  # 'https://bokeh.metsis-api.met.no/GISPY'
            wms_url = literal_eval(metadata_dict)["resources"]["OGC:WMS"][0]
            content = f'<iframe src="{wms_endpoint}?url={wms_url}" width="1225" height="725" frameborder=0 scrolling=no></iframe>'
        else:
            content = "Plotting routine not implemented for this featureType"
        icon_name = "line-chart"

    host_layout.children[0].text = content

    def show_hide_metadata(event):
        if host_layout.visible:
            host_layout.visible = False
        else:
            fake_div.visible = True
            host_layout.visible = True
            fake_div.visible = False

    metadata_button = Button(
        icon=FontAwesomeIcon(icon_name=icon_name, size=1.5),
        label="",
        height=40,
        width=50,
        css_classes=["btn-clear"],
    )
    metadata_button.on_click(show_hide_metadata)
    md = column(metadata_button, fake_div)
    return md


def custom_checkbox(json_data, nb_config_file):
    logger.debug(f"received: {json_data}")
    metadata_layout = row(Div(text="host"))
    metadata_layout.visible = False
    plot_layout = row(Div(text="host"))
    plot_layout.visible = False

    # timeSereies
    ts_dict = {
        data_id: json_data["data"][data_id]
        for data_id in json_data["data"]
        if json_data["data"][data_id]["feature_type"] == "timeSeries"
    }
    ts_info_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in ts_dict
    }
    ts_info_btns = {
        data_id: meta_button(
            str(ts_dict[data_id]), ts_info_layouts[data_id], "metadata"
        )
        for data_id in ts_dict
    }
    ts_plot_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in ts_dict
    }
    ts_plot_btns = {
        data_id: meta_button(str(ts_dict[data_id]), ts_plot_layouts[data_id], "plot")
        for data_id in ts_dict
    }
    ts_checkboxes = column(
        [
            column(
                column(
                    CheckboxGroup(
                        labels=[ts_dict[data_id]["title"]],
                        css_classes=["bk-bs-checkbox"],
                    ),
                    row([Spacer(width=20), ts_info_btns[data_id],
                    ts_plot_btns[data_id]]),
                ),
                column([ts_info_layouts[data_id], ts_plot_layouts[data_id]]),
            )
            for data_id in ts_dict
        ]
    )
    ####
    # profile
    p_dict = {
        data_id: json_data["data"][data_id]
        for data_id in json_data["data"]
        if json_data["data"][data_id]["feature_type"] == "profile"
    }
    p_info_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in p_dict
    }
    p_info_btns = {
        data_id: meta_button(str(p_dict[data_id]), p_info_layouts[data_id], "metadata")
        for data_id in p_dict
    }
    p_plot_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in p_dict
    }
    p_plot_btns = {
        data_id: meta_button(str(p_dict[data_id]), p_plot_layouts[data_id], "plot")
        for data_id in p_dict
    }
    p_checkboxes = column(
        [
            column(
                column(
                    CheckboxGroup(
                        labels=[p_dict[data_id]["title"]],
                        css_classes=["bk-bs-checkbox"],
                    ),
                    row([Spacer(width=20), p_info_btns[data_id],
                    p_plot_btns[data_id]]),
                ),
                column([p_info_layouts[data_id], p_plot_layouts[data_id]]),
            )
            for data_id in p_dict
        ]
    )
    ####
    # timeSeriesProfile
    tsp_dict = {
        data_id: json_data["data"][data_id]
        for data_id in json_data["data"]
        if json_data["data"][data_id]["feature_type"] == "timeSeriesProfile"
    }
    tsp_info_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in tsp_dict
    }
    tsp_info_btns = {
        data_id: meta_button(
            str(tsp_dict[data_id]), tsp_info_layouts[data_id], "metadata"
        )
        for data_id in tsp_dict
    }
    tsp_plot_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in tsp_dict
    }
    tsp_plot_btns = {
        data_id: meta_button(str(tsp_dict[data_id]), tsp_plot_layouts[data_id], "plot")
        for data_id in tsp_dict
    }
    tsp_checkboxes = column(
        [
            column(
                column(
                    CheckboxGroup(
                        labels=[tsp_dict[data_id]["title"]],
                        css_classes=["bk-bs-checkbox"],
                    ),
                    row([Spacer(width=20),tsp_info_btns[data_id],
                    tsp_plot_btns[data_id]]),
                ),
                column([tsp_info_layouts[data_id], tsp_plot_layouts[data_id]]),
            )
            for data_id in tsp_dict
        ]
    )
    ####
    # NA
    na_dict = {
        data_id: json_data["data"][data_id]
        for data_id in json_data["data"]
        if json_data["data"][data_id]["feature_type"] == "NA"
    }
    na_info_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in na_dict
    }
    na_info_btns = {
        data_id: meta_button(
            str(na_dict[data_id]), na_info_layouts[data_id], "metadata"
        )
        for data_id in na_dict
    }
    na_plot_layouts = {
        data_id: row(Div(text="host"), visible=False) for data_id in na_dict
    }
    na_plot_btns = {
        data_id: meta_button(str(na_dict[data_id]), na_plot_layouts[data_id], "NA")
        for data_id in na_dict
    }
    na_checkboxes = column(
        [
            column(
                column(
                    CheckboxGroup(
                        labels=[na_dict[data_id]["title"]],
                        css_classes=["bk-bs-checkbox"],
                    ),
                    row([Spacer(width=20),na_info_btns[data_id],
                    na_plot_btns[data_id]]),
                ),
                column([na_info_layouts[data_id], na_plot_layouts[data_id]]),
            )
            for data_id in na_dict
        ]
    )

    # WMS
    ######
    if len(ts_checkboxes.children) >= 1:
        ts_label = Div(text="<b>Time Series :</b>", css_classes=["custom_label"])
    else:
        ts_label = Div(text="")
    if len(p_checkboxes.children) >= 1:
        p_label = Div(text="<b>Profile :</b>", css_classes=["custom_label"])
    else:
        p_label = Div(text="")
    if len(tsp_checkboxes.children) >= 1:
        tsp_label = Div(
            text="<b>Time Series Profile :</b>", css_classes=["custom_label"]
        )
    else:
        tsp_label = Div(text="")
    if len(na_checkboxes.children) >= 1:
        na_label = Div(text="<b>Others :</b>", css_classes=["custom_label"])
    else:
        na_label = Div(text="")
    # NOTEBOOKS - multi-selection
    if json_data['notebook'] == True:
        parsed_yaml = parse_notebook_config(nb_config_file)
        print(parsed_yaml)
        if parsed_yaml is not None:
            nb_label = Div(text="<b>Notebooks :</b>", css_classes=["custom_label"])
            nb_dict = {i["name"]: i for i in parsed_yaml["notebooks"]}
            # nb_info_layouts = {
            #    nb_id: row(Div(text="host"), visible=False) for nb_id in nb_dict
            # }

            # nb_info_btns = {
            #    nb_id: meta_button(str(nb_dict[nb_id]), nb_info_layouts[nb_id], "metadata")
            #    for nb_id in nb_dict
            # }

            # nb_checkboxes = column(
            #    [
            #        column(
            #            row(
            #                CheckboxGroup(
            #                    labels=[nb_dict[nb_id]["name"]],
            #                    css_classes=["bk-bs-checkbox"],
            #                ),
            #                nb_info_btns[nb_id],
            #            ),
            #            column([nb_info_layouts[nb_id]]),
            #        )
            #        for nb_id in nb_dict
            #    ]
            # )
            #
            # nb_radio = row(column(RadioGroup(labels=[nb_id for nb_id in nb_dict], active=0, height_policy='max')), column([nb_info_btns[i] for i in nb_info_btns]))

            nb_sel = Select(
                title="",
                value=[nb_id for nb_id in nb_dict][0],
                options=[nb_id for nb_id in nb_dict],
                css_classes=["custom_select"],
                width=100,
            )

            content = json2html.convert(
                json=nb_dict[nb_sel.value],
                escape=True,
                table_attributes='id="info-table" class="table table-bordered table-hover"',
            )
            nb_info_layout = row(Div(text=content), visible=True)
            nb_sel.on_change(
                "value",
                functools.partial(
                    nb_info, metadata_dict=nb_dict, host_layout=nb_info_layout
                ),
            )
            # nb_sel.on_change("selected", nb_info(nb_dict, nb_info_layout, content_type='metadata'))
            nb_selector = row(column(nb_sel), nb_info_layout)

            #
        else:
            # nb_checkboxes = column(Spacer(width=20), Spacer(width=20), Spacer(width=20))
            nb_selector = column(Spacer(width=20), Spacer(width=20), Spacer(width=20))
            nb_label = Spacer(width=20)
    else:
        # nb_checkboxes = column(Spacer(width=20), Spacer(width=20), Spacer(width=20))
        nb_selector = column(Spacer(width=20), Spacer(width=20), Spacer(width=20))
        nb_label = Spacer(width=20)

    ##
    multi_select = column(
        column(ts_label, Spacer(width=20), ts_checkboxes),
        column(p_label, Spacer(width=20), p_checkboxes),
        column(tsp_label, Spacer(width=20), tsp_checkboxes),
        column(na_label, Spacer(width=20), na_checkboxes),
        # column(nb_label, Spacer(width=20), nb_checkboxes),
        column(nb_label, Spacer(width=20), nb_selector),
        Spacer(height=20),
    )

    return multi_select


def parse_notebook_config(nb_config_file):
    with open(nb_config_file, "r") as stream:
        parsed_yaml = yaml.safe_load(stream)
    return parsed_yaml


def gen_SelectMultiple(use_case_dict):
    print(use_case_dict)
    w = widgets.SelectMultiple(
        options=list(use_case_dict["notebooks"].keys()),
        value=[],
        # rows=10,
        description=use_case_dict["name"],
        disabled=False,
        description_tooltip=use_case_dict["name"],
    )
    return w


def export_widget(current_doc, widget, json_data, nb_config_file, advanced=False):
    nb_config = parse_notebook_config(nb_config_file)
    download = Button(
        icon=FontAwesomeIcon(icon_name="cogs", size=1.5), height=50, width=50, label=""
    )

    fake_div = Div(text="", width=100)
    fake_div.visible = False

    export_button = Button(
        icon=FontAwesomeIcon(icon_name="download", size=1.5),
        height=40,
        width=30,
        label="",
    )
    output_log_widget = Div(text="", min_width=60)

    def clear_download(widget):
        widget.visible = False

    clean_btn = Button(
        icon=FontAwesomeIcon(icon_name="times", size=1.2),
        label="",
        height=30,
        width=30,
        css_classes=["btn-clear"],
    )

    clean_btn.on_click(functools.partial(clear_download, widget=output_log_widget))

    def callback(attr, old, new):
        if new == 0:
            resampling.visible = False
        else:
            resampling.visible = True

    if advanced:
        export_format = Select(
            title="Select output data format:",
            value="csv",
            options=["csv", "NetCDF"],
            css_classes=["custom_select"],
            width=100,
        )
        # hardcoded variables:
        variables = ["sal", "temp"]
        export_variables = CheckboxGroup(
            labels=variables, css_classes=["custom_select"]
        )
        resampling = Select(
            title="Frequency:",
            value="--",
            options=["--", "H", "D", "W", "M", "Q", "Y"],
            css_classes=["custom_select"],
            max_width=100,
        )
        resampling.visible = False
        export_resampling = RadioGroup(labels=["Raw", "Resampled"], active=0)
        export_resampling_layout = column(
            Div(
                text='<font size = "2" color = "darkslategray" ><b>Frequency:<b></font>'
            ),
            export_resampling,
            Spacer(height=10),
            resampling,
        )
        export_resampling.on_change("active", callback)

    def data_download():
        pass

    def show_hide_export(event):
        if export_layout.visible:
            export_layout.visible = False
        else:
            fake_div.visible = True
            export_layout.visible = True
            fake_div.visible = False

    def generate_spec(widget, json_data, nb_config_file, output_log_widget):
        nb_config = parse_notebook_config(nb_config_file)
        selected_options = get_selection(widget, json_data, nb_config)
        selected_data = selected_options["data"]
        selected_notebooks = selected_options["notebooks"]
        send_data = {
            "data": selected_data,
            "email": json_data["email"],
            "project": json_data["project"],
            "notebooks": selected_notebooks,
        }
        api_host = os.environ["API_HOST"]
        logger.debug(f"using api host: {api_host}")

        output_log_widget.visible = True
        output_log_widget.text = str(
            f"{selected_data} - {output_type_radio_group.active}"
        )

    # def generate_ipynb(widget, json_data, output_log_widget):
    #    selected_data = get_selection(widget, json_data)

    #    output_log_widget.visible = True
    #    output_log_widget.text = str(f'{selected_data} - {output_type_radio_group.active}')

    def compress_selection(widget, json_data, nb_config_file, output_log_widget):
        nb_config = parse_notebook_config(nb_config_file)
        # selected_data = get_selection(widget, json_data, nb_config)
        selected_options = get_selection(widget, json_data, nb_config)
        selected_data = selected_options["data"]
        selected_notebooks = selected_options["notebooks"]
        for i in selected_data.copy():
            if "opendap" in selected_data[i]["resources"]:
                nc_url = selected_data[i]["resources"]["opendap"][0]
                try:
                    xr.open_dataset(nc_url, decode_cf=False)
                except RuntimeError:
                    logger.debug(f"failed to load (invalid) resource: {nc_url}")
                    del selected_data[i]
                    logger.debug(f"removing {nc_url} from selected datasources")
                except OSError:
                    logger.debug(f"failed to load (missing) resource: {nc_url}")
                    del selected_data[i]
                    logger.debug(f"removing {nc_url} from selected datasources")
        logger.debug(f"attempt to compress: {selected_options}")
        send_data = {
            "data": selected_data,
            "notebooks": selected_notebooks,
            "email": json_data["email"],
            "project": json_data["project"],
        }

        # r = requests.post('http://127.0.0.1:9000/api/compress', json=send_data)
        api_host = os.environ["API_HOST"]
        logger.debug(f"using api host: {api_host}")
        # api_host = 'metsis.epinux.com'
        # r = requests.post('http://10.0.0.100:8000/api/compress', json=send_data)
        if output_type_radio_group.active == 0:
            api_call = "getspec"
        if output_type_radio_group.active == 1:
            api_call = "compress"
        if output_type_radio_group.active == 2:
            api_call = "getspec2"
        try:
            print(send_data, "api_call:", api_call)
            r = requests.post(f"https://{api_host}/api/{api_call}", json=send_data)
            transaction_id = str(r.json()["transaction_id"])
            output_log_widget.visible = True
            wait(
                lambda: get_status(
                    transaction_id=transaction_id,
                    redishost=os.environ["REDIS_HOST"],
                    password=os.environ["REDIS_PASSWORD"],
                ),
                waiting_for="download to be ready",
            )
            transaction_id_data = transaction_id + "_data"
            transaction_data_url = get_data(
                transaction_id=transaction_id_data,
                redishost=os.environ["REDIS_HOST"],
                password=os.environ["REDIS_PASSWORD"],
            )["download_url"]
            output_log_widget.text = str(
                f'<a href="{transaction_data_url}">Download</a>'
            )
            logger.debug(f"succes in compressing: {send_data}")
        except:
            logger.debug(f"transaction failed sending data: {send_data}")

    download.on_click(show_hide_export)

    def export_selection_callback(widget, json_data, nb_config_file, output_log_widget):
        # if output_type_radio_group.active == 0:
        #    output_log_widget.text = str(
        #        f'<marquee behavior="scroll" direction="left"><b>. . . processing . . .</b></marquee>')
        #    current_doc.add_next_tick_callback(functools.partial(generate_spec,
        #                                                        widget=widget,
        #                                                        json_data=json_data,
        #                                                        output_log_widget=output_log_widget))
        # if output_type_radio_group.active == 1:
        #    output_log_widget.text = str(
        #        f'<marquee behavior="scroll" direction="left"><b>. . . processing . . .</b></marquee>')
        #    current_doc.add_next_tick_callback(functools.partial(generate_ipynb,
        #                                                        widget=widget,
        #                                                        json_data=json_data,
        #                                                        output_log_widget=output_log_widget))
        # if output_type_radio_group.active == 1:
        output_log_widget.text = str(
            f'<marquee behavior="scroll" direction="left"><b>. . .  processing . . .</b></marquee>'
        )
        current_doc.add_next_tick_callback(
            functools.partial(
                compress_selection,
                widget=widget,
                json_data=json_data,
                nb_config_file=nb_config_file,
                output_log_widget=output_log_widget,
            )
        )

    export_button.on_click(
        functools.partial(
            export_selection_callback,
            widget=widget,
            json_data=json_data,
            nb_config_file=nb_config_file,
            output_log_widget=output_log_widget,
        )
    )

    def output_type_handler(new):
        print("Selected output type " + str(new) + " selected.")

    output_type_radio_group = RadioGroup(
        labels=[
            "data object [Yaml spec file]",
            "zip including data object and data file",
        ],
        active=0,
    )  #  "ipynb",
    output_type_radio_group.on_click(output_type_handler)

    if advanced:
        export_layout = row(
            fake_div,
            Spacer(width=30),
            column(
                Div(
                    text='<font size = "3" color = "darkslategray" ><b>Data Export:<b></font>'
                ),
                Spacer(height=10),
                Div(
                    text='<font size = "2" color = "darkslategray" ><b>Select Variables to export:<b></font>'
                ),
                export_variables,
                Spacer(height=10),
                export_format,
                Spacer(height=10),
                export_resampling_layout,
                Div(
                    text='<font size = "2" color = "darkslategray" ><b>Generate Download link:<b></font>'
                ),
                Spacer(height=10),
                export_button,
            ),
            sizing_mode="fixed",
        )
    else:
        export_layout = row(
            fake_div,
            Spacer(width=30),
            column(
                Spacer(height=30),
                row(
                    Div(
                        text='<font size = "3" color = "darkslategray" ><b>Data Export:<b></font>'
                    ),
                    output_type_radio_group,
                ),
                Spacer(height=10),
                row(
                    export_button,
                    Spacer(width=20),
                    output_log_widget,
                    Spacer(width=20),
                    min_width=100,
                ),
            ),
            sizing_mode="fixed",
        )  # clean_btn

    export_layout.visible = False

    return column(
        column(
            Div(
                text='<font size = "4" color = "darkslategray" ><b>Processing Toolbox <b></font>'
            ),
            download,
        ),
        export_layout,
    )
