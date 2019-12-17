import requests
import json
import datetime
import logging
import operator
import time
from apps.bento_create_card.public import change_today
from tools_me.other_tools import xianzai_time, login_required, check_float, make_name, finance_required, sum_code
from tools_me.parameter import RET, MSG, TRANS_STATUS, TRANS_TYPE, DO_TYPE
# from tools_me.RSA_NAME.helen import QuanQiuFu
from tools_me.remain import get_card_remain
from . import user_blueprint
from flask import render_template, request, jsonify, session, g, url_for, redirect
from tools_me.mysql_tools import SqlData
from apps.bento_create_card.main_create_card import main_createcard, CreateCard, get_bento_data
from apps.bento_create_card.sqldata_native import SqlDataNative
from apps.bento_create_card.sqldata import BentoCard
from apps.bento_create_card.sqldata import session as Sql_Session
from apps.bento_create_card.main_transactionrecord import main_alias_datas, TransactionRecord
from apps.bento_create_card.main_recharge import main_transaction_data, RechargeCard
from flask.views import MethodView
from . import study_blueprint
logging.basicConfig(level=logging.INFO, format='%(asctime)s :: %(levelname)s :: %(message)s', filename="error.log")


class FlaskStudy(MethodView):
    def get(self):
        return render_template("study_html/flask/index.html")

class CeleryStudy(MethodView):
    def get(self):
        return render_template("study_html/celery/index.html")

study_blueprint.add_url_rule("/flask/", view_func=FlaskStudy.as_view("flaskstudy"))
study_blueprint.add_url_rule("/celery/", view_func=FlaskStudy.as_view("celerystudy"))
