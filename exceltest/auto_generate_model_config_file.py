#!/data03/apps/python2715/bin/python
# -*- coding:utf-8 -*-

import xlwt
import xlrd
import xlsxwriter
import collections
import os
import re
import pymysql
import sys
sys.path.append("/data02/dcadmin/scripts/common")
sys.setdefaultencoding('utf-8')


class AotuGenerate:

    def __init__(self):
        self.filename = sys.argv[1]
        path = os.path.dirname(self.filename)
        name = os.path.basename(self.filename).split('.')[0]
        self.model_name = path + name + '_模型.xlsx'
        self.data_item_name = path + name + '_数据项.xls'
        self.sql_name = path + name + '_执行sql.xlsx'
        self.all_info = None
        self.db_columns_type = {}
        self.match_type = {'TIMESTAMP': ['DATE', 'DATETIME'],
                           'BIGINT': ['NUMBER'],
                           'INT': ['NUMBER']}
        self.partition_conditions = {'MONTH_NO_': '${yyyyMM}',
                           'DATE_NO_': '${yyyyMMdd}',
                           'LATN_ID_': 'latn_id_',
                           'LATN_ID_': 'latn_id_'}
        self.fields = {}




    # 连接mysql查询
    def connect_mysql_to_selct(self, tns, sql):
        try :
            tns_info = re.findall("(\w+)\/(.*?)@(\d+\.\d+\.\d+\.\d+):(\d+)/(\w+)", tns)
            if tns_info and len(tns_info[0]) == 5:
                tns_info = tns_info[0]
                user = tns_info[0]
                passwd = tns_info[1]
                host = tns_info[2]
                port = int(tns_info[3])
            else:
                print ("连接信息解析失败")
                print (tns_info)
                sys.exit(1)
            # 打开数据库连接
            coon = pymysql.connect(host=host, user=user,passwd=passwd,port=port,charset='utf8')
            cursor = coon.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            # print (data)
            # 关闭数据库连接
            cursor.close()
            coon.close()
            return data
        except Exception as e:
            print('mysql 查询失败')
            print (e)
            sys.exit(2)

    # 读取配置文件
    def get_config_file(self):
        # 读取配置文件
        filename = self.filename
        # 解决中文文件读取错误问题
        filename = filename.decode('utf-8')
        data = xlrd.open_workbook(filename)
        # 通过索引获取，例如打开第一个sheet表格
        table = data.sheet_by_index(0)
        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            nrows = table.nrows  # 获取该sheet中的有效行数
            i = 1
            all_info = collections.OrderedDict()
            for row_num in range(1, nrows):
                row_vaule = table.row_values(row_num)
                hive_db = row_vaule[0].strip().lower()
                hive_table = row_vaule[1].strip().upper()
                table_name = row_vaule[2].strip()
                ch_name = row_vaule[3].strip()
                en_name = row_vaule[4].strip().upper()
                en_name = re.sub("\s", "", en_name)
                partition = row_vaule[5].strip().upper()
                if partition.isspace() == False and partition != '':
                    whether = '是'
                else:
                    whether = '否'
                data_type = row_vaule[6].strip()
                cycle_type = row_vaule[7].strip()
                explain = row_vaule[8].strip()
                tns = row_vaule[9].strip()
                resource_info = row_vaule[10].strip().upper()
                database_type = row_vaule[11].strip().upper()
                if self.fields.has_key(ch_name) == False:
                    self.fields[en_name] = ch_name
                if all_info.has_key(hive_table):
                    if en_name not in all_info[hive_table]['columns']:
                        all_info[hive_table]['columns'].append(en_name)
                else:
                    all_info[hive_table] = {'hive_db': hive_db, 'table_name': table_name,'columns':[en_name],
                                            'partition': partition, 'data_type': data_type, 'cycle_type': cycle_type,
                                            'whether': whether, 'explain': explain, 'tns': tns,
                                            'resource_info': resource_info, 'database_type': database_type}
            self.all_info = all_info
            #print all_info

    # 连接数据库,对比字段是否一致
    def db_compare_columns(self):
        all_info = self.all_info
        for hive_table in all_info:
            resource_info = all_info[hive_table]['resource_info']
            database_type = all_info[hive_table]['database_type']
            tns = all_info[hive_table]['tns']
            if tns.isspace() == False and tns != '':
                table_list = resource_info.split('.')
                if len(table_list)>1:
                    owner=table_list[0]
                    resource_table=table_list[1]
                else:
                    print ("配置原表名请加上用户名")
                    sys.exit(1)
                db_columns_info = None
                if database_type == 'ORACLE':
                    sql = '''SELECT upper(COLUMN_NAME) as aa,upper(ORACLE_TYPE) 
                 FROM (SELECT A.COLUMN_NAME,
                       A.DATA_TYPE AS ORACLE_TYPE
                  FROM ALL_TAB_COLUMNS A
                 WHERE A.TABLE_NAME = UPPER('%s')
                   AND A.OWNER = UPPER('%s')
                 ORDER BY A.COLUMN_ID)''' % (resource_table, owner)
                    db_columns_info = self.connect_database_to_select(tns, sql)
                elif database_type == 'MYSQL':
                    sql = '''SELECT upper(COLUMN_NAME) AS COLUMN_NAME, upper(DATA_TYPE) 
                            FROM
                                (SELECT COLUMN_NAME,DATA_TYPE
                                    FROM
                                        information_schema.COLUMNS
                                    WHERE
                                        TABLE_NAME = '%s'
                                    AND TABLE_SCHEMA = '%s'
                                    ORDER BY
                                        ordinal_position
                                ) AS A''' % (resource_table, owner)
                    db_columns_info = self.connect_mysql_to_selct(tns, sql)
                else:
                    print("未知的数据库类型")
                    sys.exit(1)
                if len(db_columns_info) > 1:
                    cf_columns = all_info[hive_table]['columns']
                    self.db_columns_type[hive_table] = {i[0]: i[1] for i in db_columns_info}
                    db_columns = [i[0] for i in db_columns_info]
                    result = None
                        #cmp(db_columns,cf_columns)
                    if result==0:
                        continue
                    else:
                        print ("{0} 字段不一致,以数据库为准：".format(hive_table))
                        self.all_info[hive_table]['columns'] = db_columns
                        # self.compare_columns(cf_columns,db_columns)
                        intersection = [col for col in db_columns if col in cf_columns]
                        db_intersection = [col for col in db_columns if col not in intersection]
                        cf_intersection = [col for col in cf_columns if col not in intersection]
                        if len(db_intersection) != 0:
                            print (hive_table, ':')
                            print ("字段个数不一致，数据库字段个数超长： ")
                            for column in db_intersection:
                                if self.fields.has_key(column) == False:
                                    self.fields[column] = column
                                print (column)
                        if len(cf_intersection) != 0:
                            print ("字段个数不一致，数据字典字段个数超长： ")
                            for column in cf_intersection:
                                print (column)
                else:
                    print("未查询到表字段")
                    print (sql)
                    sys.exit(2)
        print ("----------------------------------------------------")

    # 插入数据
    def insert_model_data(self, worksheet, style):
        all_info = self.all_info
        sequence = 2
        for hive_table in all_info:
            columns = all_info[hive_table]['columns']
            table_name = all_info[hive_table]['table_name'].decode('UTF-8')
            whether = all_info[hive_table]['whether'].decode('UTF-8')
            partition = all_info[hive_table]['partition']
            data_type = all_info[hive_table]['data_type'].decode('UTF-8')
            cycle_type = all_info[hive_table]['cycle_type'].decode('UTF-8')
            explain = all_info[hive_table]['explain'].decode('UTF-8')
            tns = all_info[hive_table]['tns']
            i = 1
            for en_name in columns:
                row_values = [hive_table.decode('UTF-8'), table_name, whether, u'事实表', u'公有模型', u'离线',
                              data_type, cycle_type, en_name, i, u'是', u'否', u'否', explain]
                worksheet.write_row('A'+str(sequence), row_values, style)
                sequence += 1
                i += 1
            if tns.isspace() == False and tns != '':
                row_values = [hive_table.decode('UTF-8'), table_name, whether, u'事实表', u'公有模型', u'离线',
                              data_type, cycle_type, 'LOAD_TIME', i, u'否', u'否', u'否', explain]
                worksheet.write_row('A' + str(sequence), row_values, style)
                sequence += 1
                i += 1
            if partition.isspace() == False and partition != '':
                partitions = partition.split(",")
                for part in partitions:
                    row_values = [hive_table.decode('UTF-8'), table_name, whether, u'事实表', u'公有模型', u'离线',
                                  data_type, cycle_type, part, i, u'否', u'否', u'是', explain]
                    worksheet.write_row('A' + str(sequence), row_values, style)
                    sequence += 1
                    i += 1

    # 创建一个xls的excel
    def create_model_excel_xlsx(self):
        # 新建一个Excel文件
        workbook = xlsxwriter.Workbook(self.model_name.decode('utf-8'))
        # 新建一个名为model的sheet
        worksheet = workbook.add_worksheet('model')
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:C', 35)
        worksheet.set_column('C:H', 8.88)
        worksheet.set_column('I:I', 25)
        worksheet.set_column('J:J', 8.88)
        worksheet.set_column('K:M', 12)
        worksheet.set_column('N:N', 30)
        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # 设置表头
        headings = ['实体英文名', '实体中文名', '是否分区', '类型', '表模型', '数据类型', '数据模式', '周期类型',
                    '数据项英文名称', '属性顺序', '是否允许为空', '是否为主键', '是否分区键', '说明']
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        # 插入数据
        self.insert_model_data(worksheet, style)
        # 关闭并保存文件
        workbook.close()

    # 插入数据
    def insert_data_item_data(self, worksheet, style):
        sequence = 1
        all_info = self.all_info
        for en_name in self.fields:
            ch_name = self.fields[en_name]
            worksheet.write(sequence, 0, ch_name, style)
            worksheet.write(sequence, 1, "97[%]其它类[%]", style)
            worksheet.write(sequence, 2, en_name, style)
            worksheet.write(sequence, 3, "属性", style)
            worksheet.write(sequence, 4, "STRING", style)
            worksheet.write(sequence, 8, "否", style)
            worksheet.write(sequence, 9, "否", style)
            worksheet.write(sequence, 17, "一级（不加密）", style)
            sequence += 1

    # 查询已有字段
    def check_exist_fields(self):
        columns =  self.fields.keys()
        # 查询已有字段
        sql = "select upper(data_item_name), upper(field_define) from td_reg_data_item where upper(data_item_name) in" + "('" + "','".join(
            columns) + "') order by field_define, data_item_name"
        column_result = self.connect_postgresql_to_select(sql)
        if len(column_result) != 0:
            all_info = self.all_info
            for hive_table in all_info:
                content = ""
                out_format = "{0:<20}\t{1:<20}\t{2:<20}\t{3}\r\n"
                table_columns = all_info[hive_table]['columns']
                for column_list in column_result:
                    db_column = column_list[0]
                    db_type = column_list[1]
                    if self.fields.has_key(db_column):
                        self.fields.pop(db_column)
                    if db_type != 'STRING':
                        if db_column in table_columns:
                            if self.db_columns_type:
                                column_dict = self.db_columns_type[hive_table]
                                re_type = column_dict[db_column]
                                if self.match_type.has_key(db_type):
                                    if re_type in self.match_type[db_type]:
                                        content += out_format.format(db_column, db_type, re_type, "")
                                    else:
                                        content += out_format.format(db_column, db_type, re_type, "类型不兼容")
                                    continue
                                content += out_format.format(db_column, db_type, re_type, "未知")
                            else:
                                content += out_format.format(db_column, db_type, "", "")
                if content != "":
                    print ("{0}: 已有数据项类型非STRING字段：".format(hive_table))
                    print (content)
        print ("----------------------------------------------------")

    # 创建一个xls的excel
    def create_excel_xls(self):
        # 查询已有字段
        self.check_exist_fields()
        if len(self.fields) == 0:
            print ("所有字段都已存在，不生成数据项excel！")
        else:
            # 创建一个workbook 设置编码
            workbook = xlwt.Workbook(encoding='utf-8')
            # 创建一个worksheet
            worksheet = workbook.add_sheet('data_item')
            # 设置边框
            borders = xlwt.Borders()  # Create Borders
            borders.left = xlwt.Borders.THIN  # 添加边框-虚线边框
            borders.right = xlwt.Borders.THIN  # 添加边框-虚线边框
            borders.top = xlwt.Borders.THIN  # 添加边框-虚线边框
            borders.bottom = xlwt.Borders.THIN  # 添加边框-虚线边框
            style = xlwt.XFStyle()
            style.borders = borders
            # 设置单元格宽度
            #worksheet.col(0).width = 10500
            worksheet.write(0, 0, "中文名称", style)
            worksheet.write(0, 1, "业务分类", style)
            worksheet.write(0, 2, "英文名称", style)
            worksheet.write(0, 3, "数据项类型", style)
            worksheet.write(0, 4, "字段类型定义", style)
            worksheet.write(0, 5, "存储格式", style)
            worksheet.write(0, 6, "默认值", style)
            worksheet.write(0, 7, "用途说明", style)
            worksheet.write(0, 8, "空值检查", style)
            worksheet.write(0, 9, "零值检查", style)
            worksheet.write(0, 10, "维度值范围", style)
            worksheet.write(0, 11, "简单值范围", style)
            worksheet.write(0, 12, "同比上限", style)
            worksheet.write(0, 13, "同比下限", style)
            worksheet.write(0, 14, "环比上限", style)
            worksheet.write(0, 15, "环比下限", style)
            worksheet.write(0, 16, "默认值占比", style)
            worksheet.write(0, 17, "安全级别", style)
            # 插入数据
            self.insert_data_item_data(worksheet, style)
            workbook.save(self.data_item_name.decode('utf-8'))

    def insert_sql_data(self, worksheet, style):
        sequence = 2
        all_info = self.all_info
        for hive_table in all_info:
            hive_db = all_info[hive_table]['hive_db']
            partition = all_info[hive_table]['partition']
            partition_sql = ""
            check_script = ""
            if partition.isspace() == False and partition != '':
                partitions = partition.split(",")
                partition_sql = '''alter table {0}.{1} drop if exists partition ({2});alter table {0}.{1} add if not exists partition ({2});'''
                condition = ""
                for part in partitions:
                    if self.partition_conditions.has_key(part):
                        condition += "{0}='{1}', ".format(part.lower(), self.partition_conditions.get(part))
                    else:
                        print("未知分区字段")
                        sys.exit(part)
                condition = condition.strip(', ')
                partition_sql = partition_sql.format(hive_db.lower(), hive_table.lower(), condition)
                check_format = "/data02/dcadmin/scripts/oracle_extract_check/oracle_extract_check.py -i %s -l 0 -c %s -t 111"
                if 'MONTH_NO_' in partitions:
                    check_script = check_format % (hive_table, "${yyyyMM}")
                if 'DATE_NO_' in partitions:
                    check_script = check_format % (hive_table, "${yyyyMMdd}")
                if 'HOUR_NO_' in partitions:
                    check_script = check_format % (hive_table, "${yyyyMMddHH}")
                if check_script == "":
                    print("未知的分区字段")
                    print(partitions)
                    sys.exit(1)
            tns = all_info[hive_table]['tns']
            execute_sql = ""
            if tns.isspace()==False and tns != '':
                resource_info = all_info[hive_table]['resource_info']
                database_type = all_info[hive_table]['database_type']
                table_list = resource_info.split('.')
                owner = table_list[0]
                resource_table = table_list[1]
                # 抽取sql
                if database_type == 'ORACLE':
                    sql = '''SELECT 'SELECT '
                      FROM DUAL
                    UNION ALL
                    SELECT *
                      FROM (SELECT CASE
                      when A.DATA_TYPE = 'NUMBER' THEN 
                      A.COLUMN_NAME ||','
                      WHEN A.DATA_TYPE = 'DATE' THEN
                      'to_char(' || A.COLUMN_NAME ||
                      ',''yyyy-MM-dd hh24:mi:ss'') as ' || A.COLUMN_NAME || ','
                      WHEN A.DATA_TYPE IN ('BLOB', 'CLOB') THEN
                      'replace(replace(replace(to_char(' || A.COLUMN_NAME ||
                      '),chr(13),\'\'\'\'),chr(9),\'\'\'\'),chr(10),\'\'\'\') as ' ||A.COLUMN_NAME || ','
                      when  A.data_type='BINARY_DOUBLE' or a.data_type='BINARY_FLOAT' then
                       'case when substr(to_char(to_number('||a.COLUMN_NAME||')),1,1)=''.'' then ''0''||to_char(to_number('||a.COLUMN_NAME||'))  when  substr(to_char(to_number('||a.COLUMN_NAME||')),1,2)=''-.'' then ''-0.''||substr(to_char(to_number('||a.COLUMN_NAME||')),3,length(to_char(to_number('||a.COLUMN_NAME||')))-2) else  to_char(to_number('||a.COLUMN_NAME||')) END as '|| A.COLUMN_NAME ||','
                      else
                      'replace(replace(replace(' || A.COLUMN_NAME ||
                      ',chr(13),\'\'\'\'),chr(9),\'\'\'\'),chr(10),\'\'\'\') as ' ||
                      A.COLUMN_NAME || ','
                      END
                      FROM all_tab_columns A
                      WHERE A.OWNER = upper('{0}')
                      AND A.TABLE_NAME = upper('{1}')
                      ORDER BY A.COLUMN_ID) P
                      UNION ALL
                    SELECT 'TO_CHAR(sysdate,''yyyy-mm-dd hh24:mi:ss'') as LOAD_TIME'
                      FROM DUAL
                    union all
                    select ' from {0}.{1}'
                    from dual
                    '''.format(owner, resource_table)
                    result_sql = self.connect_database_to_select(tns, sql)
                elif database_type == 'MYSQL':
                    sql = ''' SELECT 'select '
                            UNION ALL
                            SELECT * FROM 
                            (SELECT CASE 
                            WHEN A.DATA_TYPE IN('bigint','int','double','float','decimal') then 
                            concat(cast(A.COLUMN_NAME as char(200)),',') 
                            WHEN A.DATA_TYPE='datetime' then 
                            concat('CONVERT(',A.COLUMN_NAME,',char(120)) as ',A.COLUMN_NAME,',') 
                            ELSE 
                            concat('replace(replace(replace(',A.COLUMN_NAME,',char(13),\'\'\'\'),char(10),\'\'\'\'),char(9),\'\'\'\') as ',A.COLUMN_NAME,',')
                            END
                            FROM INFORMATION_SCHEMA.COLUMNS A
                            WHERE A.TABLE_NAME='{1}'
                            AND A.TABLE_SCHEMA='{0}'
                            ORDER BY A.ORDINAL_POSITION ) B
                            UNION ALL
                            SELECT 'CONVERT(SYSDATE(),char(120)) as LOAD_TIME from {0}.{1}' '''.format(owner, resource_table)
                    result_sql = self.connect_mysql_to_selct(tns, sql)
                else:
                    print("未知的数据库类型")
                    sys.exit(1)

                if len(result_sql)>1:
                    for s in result_sql:
                        execute_sql += s[0]
            else:
                execute_format = "python /data02/dcadmin/scripts/newftp/all_remote_get_file.py %s %s"
                if partition.isspace() == False and partition != '':
                    partitions = partition.split(",")
                    if 'MONTH_NO_' in partitions:
                        execute_sql = execute_format%(hive_table, "${yyyyMM}")
                    if 'DATE_NO_' in partitions:
                        execute_sql = execute_format%(hive_table, "${yyyyMMdd}")
                    if 'HOUR_NO_' in partitions:
                        execute_sql = execute_format%(hive_table, "${yyyyMMddHH}")
                    if execute_sql == "":
                        print("未知的分区字段")
                        print(partitions)
                        sys.exit(1)
                    check_script = ""
            row_values = [hive_table, partition_sql , execute_sql, check_script]
            worksheet.write_row('A' + str(sequence), row_values, style)
            sequence += 1

    # 创建一个抽取sql的excel
    def create_excel_sql(self):
        # 新建一个Excel文件
        workbook = xlsxwriter.Workbook(self.sql_name.decode('utf-8'))
        # 新建一个名为model的sheet
        worksheet = workbook.add_worksheet('sql')
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 34)
        worksheet.set_column('B:D', 60)
        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # 设置表头
        headings = ['实体英文名', '创建分区' ,'抽取sql/抽取脚本', '稽核语句']
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        # 插入数据
        self.insert_sql_data(worksheet, style)
        # 关闭并保存文件
        workbook.close()

    def main(self):
        # 读取配置文件
        self.get_config_file()
        # 对比字段
        self.db_compare_columns()
        # 生成模板excel
        self.create_model_excel_xlsx()
        # 生成数据项excel
        self.create_excel_xls()
        # 生成抽取sql
        self.create_excel_sql()
        print ("执行成功！！！")


# 判断输入参数
def judge_input_parameters_num():
    if len(sys.argv) != 2:
        print ("请输入正确的是参数： aotu_generate_model_config_file.py configuration_files")
        sys.exit(1)


if __name__ == '__main__':
    judge_input_parameters_num()
    aotu = AotuGenerate()
    aotu.main()
