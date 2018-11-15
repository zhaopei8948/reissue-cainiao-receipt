import uuid, sys, time, os, shutil, json, cx_Oracle, codecs
from flask import (
    Flask, request, render_template, Blueprint
)
from flask_json import FlaskJSON, JsonError, json_response, as_json


app = Flask(__name__)
FlaskJSON(app)
bp = Blueprint('cn', __name__, url_prefix='/maintain/cn')


sendDir = r"D:\Data\send\CaiNiao"
sendBackDir = r"D:\Data\send\CaiNiaoBackup"


@bp.route('/reissueByNo')
def reissue_by_orderno_html():
    return render_template('reissue_by_orderno.html')


@bp.route('/reissueByFile')
def reissue_by_file_html():
    return render_template('reissue_by_file.html')


@bp.route('/caiNiaoReissueByNo')
@as_json
def reissue_by_no():
    orderno = ''
    if request.method == 'GET':
        orderno = request.args.get('orderno')
    else:
        orderno = request.form['orderno']
    return generate_by_orderno(orderno)


@bp.route('/caiNiaoReissueByOrderNo/<orderno>')
@as_json
def reissue_by_orderno(orderno):
    return generate_by_orderno(orderno)


def generate_by_orderno(orderno):
    info = {}
    data = []
    filename = "receipt_%s.xml" % (uuid.uuid1())

    con = cx_Oracle.connect("ecssent", "dbwork", "172.16.0.140:1525/tybwtfw")
    cur = con.cursor()
    cur.prepare("select t.customs_code, t.ebp_code, t.ebc_code, t.agent_code, t.cop_no, t.pre_no, t.invt_no from ceb2_invt_head t where t.order_no = :orderno and t.app_status = :app_status")
    cur.execute(None, orderno = orderno, app_status = '800')
    result = cur.fetchone()
    cur.close()
    con.close()
    if result:
        print("result is customs_code:[%s], ebp_code:[%s], ebc_code:[%s], agent_code:[%s], cop_no:[%s], pre_no:[%s], invt_no:[%s]" % (result))
        data.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        data.append('<CEB622Message xmlns="http://www.chinaport.gov.cn/ceb" version="1.0" guid="%s">' % (uuid.uuid1()))
        data.append('    <InventoryReturn>')
        data.append('        <guid>%s</guid>' % (uuid.uuid1()))
        data.append('        <customsCode>%s</customsCode>' % (result[0]))
        data.append('        <ebpCode>%s</ebpCode>' % (result[1]))
        data.append('        <ebcCode>%s</ebcCode>' % (result[2]))
        data.append('        <agentCode>%s</agentCode>' % (result[3]))
        data.append('        <copNo>%s</copNo>' % (result[4]))
        data.append('        <preNo>%s</preNo>' % (result[5]))
        data.append('        <invtNo>%s</invtNo>' % (result[6]))
        data.append('        <orderNo>%s</orderNo>' % (orderno))
        data.append('        <returnStatus>800</returnStatus>')
        data.append('        <returnTime>%s</returnTime>' % (time.strftime("%Y%m%d%H%M%S000")))
        data.append('        <returnInfo>[Code:2600;Desc:放行]</returnInfo>')
        data.append('    </InventoryReturn>')
        data.append('</CEB622Message>')
        print('\n'.join(data))

        f = codecs.open(os.path.join(sendBackDir, filename), 'w', 'utf-8')
        f.write('\n'.join(data))
        f.close()
        print("开始复制文件 %s -> %s" % (os.path.join(sendBackDir, filename), (os.path.join(sendDir, filename))))
        shutil.copy(os.path.join(sendBackDir, filename), os.path.join(sendDir, filename))
        info['success'] = True
        info['info'] = '订单号[%s]补发成功!' % (orderno);
    else:
        print('未找到订单号%s对应在放行清单数据!', (orderno))
        info['success'] = False
        info['info'] = '未找到订单号[%s]对应在放行清单数据!' % (orderno);

    return info


@bp.route('/caiNiaoReissueByFile', methods=['POST', 'GET'])
@as_json
def reissue_by_file():
    info = {}
    infoArray = []
    if request.method == 'POST':
        f = request.files['file']
        if not f:
            info['success'] = False
            info['info'] = '没有[file]参数名称!'
        else:
            while 1:
                lines = f.readlines(100000)
                if not lines:
                    break
                for line in lines:
                    tmpline = line.decode()
                    print("data=[%s]" % (tmpline.strip().strip("\n")))
                    infoArray.append(generate_by_orderno(tmpline.strip().strip("\n")))
            info['success'] = True
            info['info'] = infoArray
    else:
        info['success'] = False
        info['info'] = '请使用POST方式传输!参数名称为[file]'
    return info;


app.register_blueprint(bp)
