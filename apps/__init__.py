from flask import Blueprint


upload_blueprint = Blueprint('upload', __name__, url_prefix='/upload', template_folder='../templates')


user_blueprint = Blueprint('user', __name__, url_prefix='/user', template_folder='../templates')


middle_blueprint = Blueprint('middle', __name__, url_prefix='/middle',  template_folder='../templates')


admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin',  template_folder='../templates')

pay_blueprint = Blueprint('pay', __name__, url_prefix='/pay',  template_folder='../templates')

bentodata_blueprint = Blueprint('bentodata', __name__, url_prefix='/475440', template_folder='../template')

verify_pay_blueprint = Blueprint('verify_pay', __name__, url_prefix='/verify_pay', template_folder='../templates')

finance_blueprint = Blueprint('finance', __name__, url_prefix='/finance', template_folder='../template')

study_blueprint = Blueprint('study', __name__, url_prefix='/study', template_folder='../template')


index_blueprint = Blueprint('/', __name__, url_prefix='/', template_folder='../template')

# from . import upload, user,  middle, admin, index
