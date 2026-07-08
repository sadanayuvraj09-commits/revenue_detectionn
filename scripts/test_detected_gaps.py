import time
import requests

start = time.time()
try:
    r = requests.get('http://127.0.0.1:8001/detected_gaps', timeout=60)
    elapsed = time.time() - start
    print('status', r.status_code)
    print('elapsed_sec', round(elapsed, 3))
    try:
        j = r.json()
        print('keys', list(j.keys()))
        if 'detected_gaps' in j:
            print('count', len(j.get('detected_gaps') or []))
    except Exception as e:
        print('json_error', e)
except Exception as e:
    print('error', e)
