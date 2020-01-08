import logging
from datetime import timedelta
from flask import Flask
from flask_cache import Cache
from tools_me.parameter import DIR_PATH

app = Flask(__name__)
# 使用缓存,缓存大量查出来的信息
# cache = Cache(app, config={'CACHE_TYPE': 'simple'})
cache = Cache(app, config={'CACHE_TYPE': 'redis',
                           'CACHE_REDIS_HOST': '127.0.0.1',
                           'CACHE_REDIS_PORT': 6379,
                           'CACHE_REDIS_DB': '',
                           'CACHE_REDIS_PASSWORD': ''}, with_jinja2_ext=False)

app.config['SECRET_KEY'] = 'Gute9878934'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=60*60*12)

app.app_context().push()
# CSRFProtect(app)


LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(pathname)s %(message)s "  # 配置输出日志格式
DATE_FORMAT = '%Y-%m-%d  %H:%M:%S %a '  # 配置输出时间的格式，注意月份和天数不要搞乱了
logging.basicConfig(level=logging.ERROR,
                    format=LOG_FORMAT,
                    datefmt=DATE_FORMAT,
                    filename=DIR_PATH.LOG_PATH  # 有了filename参数就不会直接输出显示到控制台，而是直接写入文件
                    )

# 注册路由,以url_prefix区分功能(蓝图)

from apps.upload import upload_blueprint

app.register_blueprint(upload_blueprint)

from apps.user import user_blueprint

app.register_blueprint(user_blueprint)

from apps.middle import middle_blueprint

app.register_blueprint(middle_blueprint)

from apps.admin import admin_blueprint

app.register_blueprint(admin_blueprint)

from apps.pay import pay_blueprint

app.register_blueprint(pay_blueprint)

from apps.verify_pay import verify_pay_blueprint

app.register_blueprint(verify_pay_blueprint)

from apps.bentodata import bentodata_blueprint
app.register_blueprint(bentodata_blueprint)

from apps.finance import finance_blueprint
app.register_blueprint(finance_blueprint)


from apps.index import index_blueprint
app.register_blueprint(index_blueprint)


'''
if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/bento.log', maxBytes=10240,backupCount=10)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('bento startup')
'''
