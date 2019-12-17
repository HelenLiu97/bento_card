import requests


def sm_photo(path):
    url = "https://sm.ms/api/v2/upload?inajax=1"

    file = open(path, 'rb')

    smfile = {'smfile': file}

    header = {'Authorization': "y5Ddvk7l0eca8eyDJO70zyk6FdujIv3k"}

    results = requests.post(url, headers=header, files=smfile)

    dict_info = results.json()

    data = dict_info.get('data')

    code = dict_info.get('code')

    if code == 'exception':
        return 'F'
    elif code != 'success':
        return False
    else:
        url = data.get('url')
        return url

