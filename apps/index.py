from . import index_blueprint
from flask import redirect


@index_blueprint.route('/')
def index():
    return redirect('/user/')

