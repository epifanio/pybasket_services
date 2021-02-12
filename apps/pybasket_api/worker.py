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

rabbit_host = os.environ['RABBIT_HOST']
api_host = os.environ['API_HOST']
download_dir = os.environ['DOWNLOAD_DIR']
# celery_app = Celery('tasks', broker='pyamqp://guest@10.0.0.100:5672//')
celery_app = Celery('tasks', broker=rabbit_host)

logger = get_task_logger(__name__)


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
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    unique = re.sub(r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)
    filename = str(unique) + '.zip'
    outfile = Path(download_dir, str(filename))
    s = TimestampSigner('secret-key')
    download_token = s.sign(filename).decode()
    zip_file = zipfile.ZipFile(outfile, 'a')
    for i in data:
        nc_url = data[i]['resources']['opendap'][0]
        try:
            with xr.open_dataset(nc_url, decode_cf=False) as ds:
                nc_name = nc_url.split('/')[-1]
                ds.to_netcdf(nc_name)
                zip_file.write(nc_name, os.path.basename(nc_name))
            logger.info(f"Compressing {i} in {filename}")
        except FileNotFoundError:
            print(f'resource {nc_url} is not a valid opendap resource')
    zip_file.close()
    env = Environment(loader=FileSystemLoader("""/app/templates"""))
    template = env.get_template('download/mail_download.html')
    url = f'https://{api_host}/api/download/{download_token}'
    output = template.render(data=data,
                             date=dt.datetime.now().isoformat(),
                             url=url)
    data['download_url'] = url
    transaction_id_data = transaction_id + "_data"
    set_data(transaction_id_data, data)
    time.sleep(1)
    status = {"status": True}
    set_data(transaction_id, status)
    print(url, transaction_id, data)


@celery_app.task
def compress(data, email_to):
    rv = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
    unique = re.sub(
        r'[\=\+\/]', lambda m: {'+': '-', '/': '_', '=': ''}[m.group(0)], rv)
    filename = str(unique) + '.zip'
    outfile = Path('download', str(filename))
    s = TimestampSigner('secret-key')
    download_token = s.sign(filename).decode()
    zip_file = zipfile.ZipFile(outfile, 'a')
    for i in data:
        with xr.open_dataset(i, decode_cf=False) as ds:
            nc_name = i.split('/')[-1]
            ds.to_netcdf(nc_name)
            zip_file.write(nc_name, os.path.basename(nc_name))
        logger.info(f"Compressing {i} in {filename}")
    zip_file.close()
    for i in data:
        nc_name = i.split('/')[-1]
        os.remove(nc_name)
    logger.info(f"download_token is {download_token} ")
    # logger.info(f"{send_mail('nothing')}")
    #
    env = Environment(loader=FileSystemLoader("""templates/download"""))
    template = env.get_template('mail_download.html')
    output = template.render(data=data,
                             date=dt.datetime.now().isoformat(),
                             url=f'https://pybasket.epinux.com/download/{download_token}')
    # logger.info(f"HTML contains: {output} ")
    sendMail(subject='METSIS Download',
             msgfrom='massimodisasha@gmail.com',
             msgto=email_to,
             text='',
             html=output,
             inlineimage=None,
             pdfattachment=None,
             msgtype='html',
             smtp='smtp.gmail.com',
             smtp_port=587,
             username='',
             password='eqofmorupowquzjv')
    for i in data:
        logger.info(f"data contains: {i} ")
    return download_token


def sendMail(subject='',
             msgfrom='',
             msgto='',
             text='',
             html='',
             inlineimage=None,
             pdfattachment=None,
             msgtype='html',
             smtp='',
             username='',
             smtp_port='',
             password=''):
    msg = MIMEMultipart()
    msg['Subject'] = f'{subject}'
    msg['From'] = msgfrom
    # msg as plain text
    if msgtype == 'plain':
        part = MIMEText(text, 'plain')
        msg.attach(part)
    # msg as html
    if msgtype == 'html':
        part = MIMEText(html, 'html')
        msg.attach(part)

    # Inline image attachment
    if inlineimage:
        for i in inlineimage:
            if os.path.exists(i):
                ctype, encoding = mimetypes.guess_type(i)
                ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                fp = open(i, 'rb')
                part = MIMEImage(fp.read(), _subtype=subtype)
                part.add_header('Content-Disposition', 'attachment', filename=i)
                fp.close()
                msg.attach(part)

    # PDF attachment
    if pdfattachment:
        for i in pdfattachment:
            if os.path.exists(i):
                fp = open(i, 'rb')
                att = email.mime.application.MIMEApplication(fp.read(), _subtype="pdf")
                fp.close()
                att.add_header('Content-Disposition', 'attachment', filename=i)
                msg.attach(att)

    s = smtplib.SMTP(smtp, smtp_port)
    s.starttls()  # enable security
    s.login(msgfrom, password)  # login with mail_id and password
    # s.login(username, password)
    s.sendmail(msgfrom, msgto, msg.as_string())
    s.quit()
