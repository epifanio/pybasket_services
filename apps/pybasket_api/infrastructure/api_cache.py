import datetime
from typing import Optional, Tuple
import redis
import json




def get_data(transaction_id, redishost='redismod'):
    r = redis.StrictRedis(host=redishost)
    reply = json.loads(r.execute_command('JSON.GET', transaction_id))
    return reply


def set_data(transaction_id, data, redishost='redismod'):
    r = redis.StrictRedis(host=redishost)
    r.execute_command('JSON.SET', transaction_id, '.', json.dumps(data))
    return transaction_id


def __create_key():
    pass


def __clean_out_of_date():
    pass

