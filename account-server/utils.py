import json
import random
import hashlib
from datetime import datetime
from Crypto.Random import get_random_bytes

random.seed()

def generate_random_str(n):
    assert n % 2 == 0
    return get_random_bytes(n // 2).hex()
    # return ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(n))

def hashmd5(v):        
    if type(v) == str:
        v = v.encode()
    m = hashlib.md5()
    m.update(v)
    return m.hexdigest().lower()

def datetime_from_json_date_str(x):
    return datetime.strptime(x, '%Y-%m-%dT%H:%M:%S.%fZ')

def date_to_str(d):
    return datetime.strftime(d, '%d/%m/%y %H:%M:%S')

def str_to_date(s):
    return datetime.strptime(s, '%d/%m/%y %H:%M:%S')

if __name__ == "__main__":
    json_date_str = '2012-05-29T19:30:03.283Z'
    print(datetime.datetime.strptime(json_date_str, '%Y-%m-%dT%H:%M:%S.%fZ'))
