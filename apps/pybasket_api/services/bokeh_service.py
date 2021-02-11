from bokeh.embed import server_document


def get_dashboard_script(data):
    dashboard = server_document(f'http://10.0.0.100:7000/pybasket_ui', arguments={'data': data})
    return dashboard
