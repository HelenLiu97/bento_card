import datetime
import logging
import xlrd
from tools_me.other_tools import save_file, excel_to_data, sum_code, login_required, transferContent
from . import upload_blueprint
from flask import render_template, jsonify, request, send_file, g
from tools_me.mysql_tools import SqlData
from tools_me.parameter import RET, MSG, ACCOUNT_DIR, TASK_DIR, DW_TASK, DW_ACCOUNT, SMT_TASK


@upload_blueprint.route('/up_acc', methods=['GET'])
@login_required
def up_acc():
    return render_template('account/up_account.html')


@upload_blueprint.route('/up_ta', methods=['GET'])
@login_required
def up_ta():
    return render_template('task/up_task.html')


@upload_blueprint.route('/account_excel', methods=['GET'])
@login_required
def download_account():
    response = send_file(DW_ACCOUNT)
    return response


@upload_blueprint.route('/task_excel', methods=['GET'])
def download_task():
    response = send_file(DW_TASK)
    return response


@upload_blueprint.route('/smt_excel', methods=['GET'])
def download_smt():
    response = send_file(SMT_TASK)
    return response


@upload_blueprint.route('/up_account', methods=['POST'])
@login_required
def up_account():
    file = request.files.get('file')
    filename = file.filename
    file_path = save_file(file, filename, ACCOUNT_DIR)
    # file_path ='G:\\order_flask\\static\\excel_account\\20190725\\20190725155935.xls'
    results = {'code': RET.OK, 'data': MSG.OK}
    user_id = g.user_id
    if 'static' in file_path:
        method = 'r'
        data = xlrd.open_workbook(file_path, encoding_override='utf-8')
        table = data.sheets()[0]
        nrows = table.nrows  # 行数
        ncols = table.ncols  # 列数
        row_list = list()
        if method == 'r':
            row_list = [table.row_values(i) for i in range(0, nrows)]  # 所有行的数据
        elif method == 'c':
            col_list = [table.col_values(i) for i in range(0, ncols)]  # 所有列的数据
        index = 1
        err_list = list()
        for i in row_list[1:]:
            index += 1
            if not all([i[0], i[1], i[7], i[8]]):
                err_list.append(str(index))

        if len(err_list) != 0:
            results['code'] = RET.SERVERERROR
            m = ""
            for i in err_list:
                m = m + i + ','
            results['msg'] = "第" + m + "行缺少必填参数!"
            return jsonify(results)
        in_account_list = list()
        for one in row_list[1:]:
            account = one[0]
            in_account = SqlData().search_account_count(account, user_id)
            if in_account:
                in_account_list.append(account)
            else:
                password = one[1]
                email = one[2]
                email_pw = one[3]
                if one[4]:
                    pay_money = float(one[4])
                else:
                    pay_money = 0
                if not one[5]:
                    reg_time = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                else:
                    reg_time = excel_to_data(int(one[5]))
                label = one[6]
                terrace = one[7].strip().upper()
                country = one[8]
                member_state = one[9]
                name = transferContent(one[10])
                phone = one[11]
                coun = one[12]
                province = one[13]
                city = transferContent(one[14])
                zip_num = one[15]
                address = transferContent(one[16])
                card_num = one[17]
                if not one[18]:
                    sizeof = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                else:
                    sizeof = excel_to_data(int(one[18]))
                security_code = one[19]
                SqlData().insert_account_detail(user_id, account, password, email, email_pw, pay_money, reg_time, label, terrace,
                                                country, member_state, name, phone, coun, province, city, zip_num,
                                                address, card_num, sizeof, security_code)
        if in_account_list:
            in_account_str = str(in_account_list)
            s = "以下账号未导入系统,因为账号名已存在: " + in_account_str
            results['data'] = s
            return jsonify(results)
        else:
            return jsonify(results)


@upload_blueprint.route('/up_task', methods=['POST'])
@login_required
def up_task():
    file = request.files.get('file')
    filename = file.filename
    file_path = save_file(file, filename, TASK_DIR)
    results = {'code': RET.OK, 'data': MSG.OK}
    user_id = g.user_id
    if 'static' in file_path:
        method = 'r'
        data = xlrd.open_workbook(file_path, encoding_override='utf-8')
        table = data.sheets()[0]
        nrows = table.nrows  # 行数
        ncols = table.ncols  # 列数
        row_list = list()
        if method == 'r':
            row_list = [table.row_values(i) for i in range(0, nrows)]  # 所有行的数据
        elif method == 'c':
            col_list = [table.col_values(i) for i in range(0, ncols)]  # 所有列的数据
        index = 1
        err_list = list()
        for i in row_list[1:]:
            index += 1
            if not all([i[0], i[1], i[2], i[3], i[4], i[6], i[7], i[8], i[10], i[11]]):
                err_list.append(str(index))
        if len(err_list) != 0:
            results['code'] = RET.SERVERERROR
            m = ""
            for i in err_list:
                m = m + i + ','
            results['msg'] = "第" + m + "行缺少必填参数!"
            return jsonify(results)

        sum_order_code = sum_code()
        parent_id = SqlData().insert_task_parent(user_id, sum_order_code)

        i = 1
        for one in row_list[1:]:
            task_code = sum_order_code + '-' + str(i)
            country = one[0].strip()
            if not one[1]:
                task_run_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                task_run_time = excel_to_data(one[1])
            asin = one[2].strip()
            key_word = one[3].strip()
            kw_location = one[4].strip()
            store_name = one[5].strip()
            good_name = one[6].strip()
            good_money = one[7]
            good_link = one[8].strip()
            pay_method = one[9].strip()
            serve_class = one[10].strip()
            mail_method = one[11].strip()
            note = one[12].strip()
            review_title = one[13].strip()
            review_info = one[14].strip()
            feedback_info = one[15].strip()

            try:
                SqlData().insert_task_detail(parent_id, task_code, country, asin, key_word, kw_location, store_name,
                                             good_name, good_money, good_link, pay_method, task_run_time, serve_class,
                                             mail_method, note, review_title, review_info, feedback_info)
                i += 1
            except Exception as e:
                logging.error(str(e))
                return jsonify({'code': RET.SERVERERROR, 'msg': '上传失败!'})
        return jsonify(results)
