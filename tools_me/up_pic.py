import requests
from qiniu import Auth, put_file


# def up_photo(key, file_path, bucket_name):
#     access_key = 'KgHe4AAvPJStXOlhxGB3ds-3ndsUxS-wypBwKAgW'
#     secret_key = '6l1ujW79c4Zwo5XmpznDLTdQLaobW3As3r9fnol1'
#
#     q = Auth(access_key, secret_key)
#
#     token = q.upload_token(bucket_name, key, 3600)
#
#     ret, info = put_file(token, key, file_path)
#
#     return info.status_code, ret.get('key')


def sm_photo(path):
    url = "https://sm.ms/api/v2/upload"

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
