from celery import Celery
from celery.utils.log import get_task_logger

import re
import uuid
import base64
import time
import zipfile
from itsdangerous import TimestampSigner
from itsdangerous import BadSignature, SignatureExpired

from pathlib import Path
import os

import smtplib
import mimetypes
import email
import email.mime.application
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from jinja2 import Environment, FileSystemLoader
import datetime as dt
import xarray as xr

from infrastructure.api_cache import set_data
import os
import yaml

import json

# from jsonschema import validate
from starlette.templating import Jinja2Templates
from jsonschema import ValidationError, validate

templates = Jinja2Templates(directory="./templates")


rabbit_host = os.environ["RABBIT_HOST"]
api_host = os.environ["API_HOST"]
download_dir = os.environ["DOWNLOAD_DIR"]
# celery_app = Celery('tasks', broker='pyamqp://guest@10.0.0.100:5672//')
celery_app = Celery("tasks", broker=rabbit_host)

logger = get_task_logger(__name__)


def validate_object(generated_yaml):
    with open('info_object_schema.json') as f:
        information_object_schema = json.loads(f.read())

        # Load the information object.
        with open(generated_yaml) as f:
            information_object = yaml.load(f, Loader=yaml.FullLoader)

            # Validate the information object.
            validate(instance=information_object, schema=information_object_schema)

            print('If there are no exceptions then the info objected was validated!')
            return True


@celery_app.task
def generate_information_object(data, transaction_id, download_token):
    # take the selected data including selected notebooks
    # and store everything following the teplate file available at
    #
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    unique = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    filename = str(unique) + ".yaml"
    outfile = Path(download_dir, str(filename))
    s = TimestampSigner("secret-key")
    download_token = s.sign(filename).decode()
    with open(outfile, "w+") as yaml_file:
        yaml.dump(data, yaml_file, allow_unicode=True)

    env = Environment(loader=FileSystemLoader("""/app/templates"""))
    template = env.get_template("download/mail_download.html")
    url = f"https://{api_host}/api/download/{download_token}"
    output = template.render(data=data, date=dt.datetime.now().isoformat(), url=url)
    data["download_url"] = url
    transaction_id_data = transaction_id + "_data"
    set_data(
        transaction_id=transaction_id_data,
        data=data,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    time.sleep(1)
    status = {"status": True}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost=os.environ["REDIS_HOST"],
        password=os.environ["REDIS_PASSWORD"],
    )
    print(url, transaction_id, data)
    pass


@celery_app.task
def generate_spec2(data, transaction_id, download_token):
    # here I generete the download token from the post API, this way i can reuse the same token as download id
    # rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    # unique = re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)
    filename = str(transaction_id) + ".yaml"
    outfile = Path(download_dir, str(filename))
    # s = TimestampSigner('secret-key')
    # download_token = s.sign(transaction_id).decode()
    with open(outfile, "w+") as yaml_file:
        yaml.dump(data, yaml_file, allow_unicode=True)

    env = Environment(loader=FileSystemLoader("""/app/templates"""))
    template = env.get_template("download/mail_download.html")
    url = f"https://{api_host}/api/download/{download_token}"
    output = template.render(data=data, date=dt.datetime.now().isoformat(), url=url)
    data["download_url"] = url
    transaction_id_data = transaction_id + "_data"
    set_data(
        transaction_id=transaction_id_data,
        data=data,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    time.sleep(1)
    status = {"status": True}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    print(url, transaction_id, data)


@celery_app.task
def generate_spec(data, notebooks, transaction_id):
    print(data)
    data = {"data": data, "notebooks": notebooks}
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    unique = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    filename = str(unique) + ".yaml"
    outfile = Path(download_dir, str(filename))
    s = TimestampSigner("secret-key")
    download_token = s.sign(filename).decode()
    datasets = [
        {
            "id": i,
            "title": data["data"][i]["title"],
            "resource": data["data"][i]["resources"][
                list(data["data"][i]["resources"].keys())[0]
            ][0],
            "type": list(data["data"][i]["resources"].keys())[0],
        }
        for i in data["data"]
    ]
    notebooks = [
        {
            "resource": data["notebooks"][i]["resource"],
            "type": "jupyter",
            "dependencies": [],
        }
        for i in data["notebooks"]
    ]
    print(data['notebooks'])
    notebooks = [{'name': i, 
            'resource': data['notebooks'][i]['resource'],
             'dependencies': [{'name':j['name'],
                               # library dependencies are hardcoded to an emty array 
                               # can be extended if really needed
                               'dependencies':[], 
                               'resource': j['resource'],
                               'version': j['version']} for j in data['notebooks'][i]['dependencies']]} for i in data['notebooks']]
    
    # context is hardocoded here
    # need to generate a uuid
    # dependencies for the dependencies are set to be empty
    context = {'type':'VRE config', 
           'id': str(uuid.uuid4())}
    environment = {'provider':'PTEP', 
               'processor':'JupyterHub'}
    templates = Jinja2Templates(directory="/app/templates")
    #ff = templates.get_template("config/obj_tmpl.yaml").render(
    #    {"request": "request", "datasets": datasets, "notebooks": notebooks}
    #)

    ff = templates.get_template("config/ptep_obj_tmpl.yaml").render({"request": 'request', 
                                                            "datasets": datasets, 
                                                            "notebooks": notebooks,
                                                            "context": context,
                                                            "environment": environment})


    print(ff)
    try:
        with open('/app/config/info_object_schema.json') as f:
            information_object_schema = json.loads(f.read())
            validate(instance=ff, schema=information_object_schema)
    except ValidationError:
        print('generated yaml not valid')

    with open(outfile, "w+") as yaml_file:
        ##yaml.dump(data, yaml_file, allow_unicode=True)
        yaml_file.write(ff)

    env = Environment(loader=FileSystemLoader("""/app/templates"""))
    template = env.get_template("download/mail_download.html")
    url = f"https://{api_host}/api/download/{download_token}"
    output = template.render(data=data, date=dt.datetime.now().isoformat(), url=url)
    data["download_url"] = url
    transaction_id_data = transaction_id + "_data"
    set_data(
        transaction_id=transaction_id_data,
        data=data,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    time.sleep(1)
    status = {"status": True}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    print(url, transaction_id, data)


# try:
#    Path(os.environ['DOWNLOAD_DIR']).mkdir(parents=True, exist_ok=True)
# except KeyError:
#    pass


@celery_app.task
def fake_compress(data, email_to, transaction_id):
    # print(data, email_to)
    # for i in data:
    #    print('key:', i)
    #    print('opendap_url:', data[i]['resources']['opendap'][0])
    # print('to be sent to:', email_to)
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    unique = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    filename = str(unique) + ".zip"
    outfile = Path(download_dir, str(filename))
    s = TimestampSigner("secret-key")
    download_token = s.sign(filename).decode()
    zip_file = zipfile.ZipFile(outfile, "a")
    yaml_filename = str(unique) + ".yaml"
    yaml_outfile = Path(download_dir, str(yaml_filename))
    with open(yaml_outfile, "w+") as yaml_file:
        yaml.dump(data, yaml_file, allow_unicode=True)
    zip_file.write(yaml_outfile, os.path.basename(yaml_outfile))
    for i in data:
        nc_url = data[i]["resources"]["opendap"][0]
        logger.info(f"processing {i} in {filename}")
        try:
            with xr.open_dataset(nc_url, decode_cf=False) as ds:
                try:
                    nc_name = nc_url.split("/")[-1]
                    ds.to_netcdf(nc_name)
                except:
                    logger.debug(f"failed processing {i}")
                try:
                    zip_file.write(nc_name, os.path.basename(nc_name))
                except:
                    logger.debug(f"failed processing {i}")
            logger.info(f"Compressing {i} in {filename}")
        except FileNotFoundError:
            print(f"resource {nc_url} is not a valid opendap resource")
    zip_file.close()
    env = Environment(loader=FileSystemLoader("""/app/templates"""))
    template = env.get_template("download/mail_download.html")
    url = f"https://{api_host}/api/download/{download_token}"
    output = template.render(data=data, date=dt.datetime.now().isoformat(), url=url)
    data["download_url"] = url
    transaction_id_data = transaction_id + "_data"
    set_data(
        transaction_id=transaction_id_data,
        data=data,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    time.sleep(1)
    status = {"status": True}
    set_data(
        transaction_id=transaction_id,
        data=status,
        redishost="redis",
        password=os.environ["REDIS_PASSWORD"],
    )
    print(url, transaction_id, data)


@celery_app.task
def compress(data, email_to):
    rv = base64.b64encode(uuid.uuid4().bytes).decode("utf-8")
    unique = re.sub(
        r"[\=\+\/]", lambda m: {"+": "-", "/": "_", "=": ""}[m.group(0)], rv
    )
    filename = str(unique) + ".zip"
    outfile = Path("download", str(filename))
    s = TimestampSigner("secret-key")
    download_token = s.sign(filename).decode()
    zip_file = zipfile.ZipFile(outfile, "a")
    for i in data:
        with xr.open_dataset(i, decode_cf=False) as ds:
            nc_name = i.split("/")[-1]
            ds.to_netcdf(nc_name)
            zip_file.write(nc_name, os.path.basename(nc_name))
        logger.info(f"Compressing {i} in {filename}")
    zip_file.close()
    for i in data:
        nc_name = i.split("/")[-1]
        os.remove(nc_name)
    logger.info(f"download_token is {download_token} ")
    # logger.info(f"{send_mail('nothing')}")
    #
    env = Environment(loader=FileSystemLoader("""templates/download"""))
    template = env.get_template("mail_download.html")
    output = template.render(
        data=data,
        date=dt.datetime.now().isoformat(),
        url=f"https://pybasket.epinux.com/download/{download_token}",
    )
    # logger.info(f"HTML contains: {output} ")
    sendMail(
        subject="METSIS Download",
        msgfrom="massimodisasha@gmail.com",
        msgto=email_to,
        text="",
        html=output,
        inlineimage=None,
        pdfattachment=None,
        msgtype="html",
        smtp="smtp.gmail.com",
        smtp_port=587,
        username="",
        password="eqofmorupowquzjv",
    )
    for i in data:
        logger.info(f"data contains: {i} ")
    return download_token


def sendMail(
    subject="",
    msgfrom="",
    msgto="",
    text="",
    html="",
    inlineimage=None,
    pdfattachment=None,
    msgtype="html",
    smtp="",
    username="",
    smtp_port="",
    password="",
):
    msg = MIMEMultipart()
    msg["Subject"] = f"{subject}"
    msg["From"] = msgfrom
    # msg as plain text
    if msgtype == "plain":
        part = MIMEText(text, "plain")
        msg.attach(part)
    # msg as html
    if msgtype == "html":
        part = MIMEText(html, "html")
        msg.attach(part)

    # Inline image attachment
    if inlineimage:
        for i in inlineimage:
            if os.path.exists(i):
                ctype, encoding = mimetypes.guess_type(i)
                ctype = "application/octet-stream"
                maintype, subtype = ctype.split("/", 1)
                fp = open(i, "rb")
                part = MIMEImage(fp.read(), _subtype=subtype)
                part.add_header("Content-Disposition", "attachment", filename=i)
                fp.close()
                msg.attach(part)

    # PDF attachment
    if pdfattachment:
        for i in pdfattachment:
            if os.path.exists(i):
                fp = open(i, "rb")
                att = email.mime.application.MIMEApplication(fp.read(), _subtype="pdf")
                fp.close()
                att.add_header("Content-Disposition", "attachment", filename=i)
                msg.attach(att)

    s = smtplib.SMTP(smtp, smtp_port)
    s.starttls()  # enable security
    s.login(msgfrom, password)  # login with mail_id and password
    # s.login(username, password)
    s.sendmail(msgfrom, msgto, msg.as_string())
    s.quit()
