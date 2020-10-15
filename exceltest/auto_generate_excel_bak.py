
# -*- coding:utf-8 -*-

import xlwt
import xlrd
import xlsxwriter
import collections
import os
import re
import sys
#sys.path.append("/data02/dcadmin/scripts/common")
#reload(sys)
#sys.setdefaultencoding('utf-8')


class AotuGenerate:

    def __init__(self):
        self.filename = sys.argv[1]
        path = os.path.dirname(self.filename)
        name = os.path.basename(self.filename).split('.')[0]
        self.model_name = path +"/"+ name + '_基础层数据字典_模型.xlsx'
        self.basename="e://files/model-test.xlsx"
        self.data_item_name = path + name + '_数据项.xls'
        self.sql_name = path + name + '_执行sql.xlsx'
        self.all_info = None
        self.interface_dic = {}
        self.db_columns_type = {}
        self.match_type = {'TIMESTAMP': ['DATE', 'DATETIME'],
                           'BIGINT': ['NUMBER'],
                           'INT': ['NUMBER']}
        self.partition_conditions = {'MONTH_NO_': '${yyyyMM}',
                           'DATE_NO_': '${yyyyMMdd}',
                           'LATN_ID_': 'latn_id_',
                           'LATN_ID_': 'latn_id_'}
        self.fields = {}
    ##读取接口目录表，获得中英文名称和对应的加载策略,excel 中结构如下
    #源系统名称	源系统表英文名	源系统表中文名	链接	数据路径	应用计算区表/路径	更新频率
    # 保存周期类型	增量/全量(每日)	保存月底数	保存天数 (不使用)依赖贴源作业名	作业名	备注 指标 积分 应用
    # 个人资产	数据挖掘	变更上线时间	分布键

    ##最后需要生成的 excel 一级主题 二级主题 实体英文简称	实体中文名 加载策略 更新频率 增全量规则	保存周期类型	是否保存月底数	数据保存天数	备注
    ## 一级主题是源系统名称，二级主题空着
    ## 读取名称为 接口目录，数据路径的内容为 贴源(GP-BASE)的值
    ##

    # 读取配置文件
    ##字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
    ##表英文名 表中文名 字段英文名 字段中文名 字段类型 是否主键 是否分布键 备注 上线日期
    def get_interface_index_source(self):
            # 读取配置文件
            basefilename = self.basename
            category_info = self.interface_dic
            data = xlrd.open_workbook(basefilename)
            # 通过索引获取，例如打开第一个sheet表格
            table = data.sheet_by_name("接口目录")
            allrows=0
            if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
                allrows = table.nrows  # 获取该sheet中的有效行数
                for rowindex in range(1,allrows):
                    cols = table.row_values(rowindex)
                    #源系统名称
                    source_name = cols[0].strip()
                    #源系统表英文名
                    t_en_name = cols[1].strip()
                    #源系统表中文名
                    t_ch_name = cols[2].strip()
                    #链接
                    link = cols[3].strip()
                    #数据路径,只取 GP-BASE里面的
                    source_path = cols[4].strip()
                    if source_path !="贴源(GP-BASE)":
                        continue
                    #应用计算区表 / 路径,就是我们的表名
                    hive_table = cols[5].strip().lower()
                    if hive_table == '':
                        print(" 第 %d 行 hive table 为空，跳过 " %rowindex+1)
                        continue
                    #更新频率 日/月/空白
                    update_frequence = cols[6].strip()
                    #保存周期类型,就是清理规则
                    clean_rule = cols[7].strip()
                    #增量 / 全量(每日)，对应到 加载策略要变化，是追加还说覆盖
                    #todo

                    data_rule = cols[8].strip()
                    load_rule='追加'
                    #保存月底数,就是保存多少个月的数据
                    save_mons = cols[9]
                    #保存天数
                    save_days = cols[10]
                    #(不使用)依赖贴源作业名
                    #作业名
                    #备注
                    mark=cols[13].strip()
                    #指标
                    #积分
                    #应用
                    #个人资产
                    #数据挖掘
                    #变更上线时间 20
                    #分布键
                    forignkey_str=cols[20]
                    ##最后需要生成的 excel 一级主题 二级主题 实体英文简称	实体中文名 加载策略(追加，覆盖) 更新频率 增全量规则 保存周期类型
                    # 是否保存月底数	数据保存天数	备注
                    t_message=(source_name,'',hive_table,t_ch_name,load_rule,update_frequence,data_rule,clean_rule,save_mons,save_days,mark)
                    category_info.setdefault(hive_table,t_message)
            self.interface_dic=category_info
            print(self.interface_dic)
            print("总共读取excel %d 行，解析到的模型数目为 num=%d 个" %(allrows,len(self.interface_dic)))


    # 读取配置文件
    ##字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
    ##目录表
    ##贴源表字段，字段都可能为空
    ##表英文名 表中文名 字段英文名 字段中文名 字段类型 是否主键 是否分布键 备注 上线日期
    def get_config_file_source(self):
        # 读取配置文件
        filename = self.filename
        # 解决中文文件读取错误问题
        # filename = filename.decode('utf-8')
        data = xlrd.open_workbook(filename)
        # 通过索引获取，例如打开第一个sheet表格
        table = data.sheet_by_index(0)
        ##那个内容都是5行，每次相当于从下标为6开始
        row_index = 1
        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            nrows = table.nrows  # 获取该sheet中的有效行数
            i = 1
            all_info = collections.OrderedDict()
            table_index = 1
            for row_num in range(1, nrows):
                row_vaule = table.row_values(row_num)
                #print(row_vaule)

                # hive_db = row_vaule[0].strip().lower()
                hive_table = row_vaule[0].strip().lower()
                t_name = row_vaule[1].strip() ##表中文名
                en_name = row_vaule[2].strip().lower() ##表字段英文名
                ch_name = row_vaule[3] ##表字段中文名
                if ch_name == 42:
                    ch_name=''
                data_type=row_vaule[4].strip().lower()
                print(ch_name)
                pkey = row_vaule[5].strip()
                distribute = row_vaule[6].strip()
                mark = row_vaule[7].strip()
                create_day = row_vaule[8].strip()
                #字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
                ## 表英文名 表中文名 字段英文名 字段中文名 字段类型 是否主键 是否分布键 备注 上线日期
                #print(table_index)
                #col_tuple = (table_index, en_name, ch_name, data_type, '', pkey, '', '', distribute, '', mark)
                col_tuple = (en_name, ch_name, data_type, '', pkey, '', '', distribute, '', mark)
                #print(hive_table)
                if hive_table =='':
                    print("hive_table is empty: 跳过 第 "+str(row_num+1)+" 行")
                elif hive_table not in all_info:
                    table_index = 0
                    #print("table_index=0")
                    all_info[hive_table] = {'hive_table': hive_table, 'columns': [col_tuple],
                                            'table_name': t_name}
                else:

                    if en_name not in all_info[hive_table]['columns']:
                        #table_index += 1
                        col_tuple = (en_name, ch_name, data_type, '', pkey, '', '', distribute, '', mark)
                        all_info[hive_table]['columns'].append(col_tuple)
                    # row_index =row_num+5



            self.all_info = all_info
            print(all_info)


    def get_config_file(self):
        # 读取配置文件
        filename = self.filename
        # 解决中文文件读取错误问题
        #filename = filename.decode('utf-8')
        data = xlrd.open_workbook(filename)
        # 通过索引获取，例如打开第一个sheet表格
        table = data.sheet_by_index(0)
        ##那个内容都是5行，每次相当于从下标为6开始
        row_index=1
        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            nrows = table.nrows  # 获取该sheet中的有效行数
            i = 1
            all_info = collections.OrderedDict()
            for row_num in range(1, nrows):
                row_vaule = table.row_values(row_num)
                print(row_vaule)
                #hive_db = row_vaule[0].strip().lower()
                hive_table = row_vaule[0].strip().lower()
                ch_name = row_vaule[1].strip()
                #if ch_name =='属性名':
                ##每次都从第一次出现模型名称的row_num 上加5行，开始才是我想要的结果
                if ch_name =='LDM':
                    row_index=row_num+5
                if row_num <row_index :
                    print("跳过第"+str(row_num))
                    continue

                pkey = row_vaule[2].strip()
                fkey = row_vaule[3].strip()
                empty = row_vaule[4]
                #en_name = re.sub("\s", "",table_name)
                ch_name2 = row_vaule[5].strip()
                en_name = row_vaule[6].strip()
                distribute = row_vaule[7].strip()
                empty2 = row_vaule[8].strip()
                data_type = row_vaule[9].strip()
                source_type = row_vaule[10].strip()
                app_name = row_vaule[11].strip()
                extract_regular = row_vaule[12]
                partition = row_vaule[13].strip()
                index = row_vaule[14].strip()
                create_day = row_vaule[15]

                if ch_name not in self.fields:
                    self.fields[en_name] = ch_name
                if hive_table in all_info:
                    if en_name not in all_info[hive_table]['columns']:
                        all_info[hive_table]['columns'].append(en_name)
                        all_info[hive_table]['data_types'].append(data_type)
                else:
                    #row_index =row_num+5
                    all_info[hive_table] = { 'table_name': hive_table,'columns':[en_name],
                                            'partitions': [partition], 'data_types': [data_type],
                                            'app_names': [app_name], 'ch_name': [ch_name],'pkey':[pkey]}
            self.all_info = all_info
            print(all_info)

    ##插入每个模型的数据项
    def get_link_style(self):
        #wb = xlwt.Workbook()
        #ws = wb.add_sheet('test')
        # 链接
        style = xlwt.easyxf('font: name Times New Roman, color-index red, bold on', num_format_str='#,##0.00')
        al = xlwt.Alignment()
        al.horz = 0x02  # 设置水平居中
        al.vert = 0x01  # 设置垂直居中
        style.alignment = al
        # 链接
        # worksheet.write(11, 2, u"=HYPERLINK(\"#详情!a1\", \"详情\")\r", hyper_style)
        # worksheet.write(13, 2, u"=HYPERLINK(\"#链接!a1\", \"链接\")\r", hyper_style)
        #worksheet.write(11, 2, link, style)
        #worksheet.write(13, 2, link, style)
        return style
    # 插入数据
    def insert_model_data(self, workbook,worksheet, style):
        iter_info = self.interface_dic
        sequence = 2
        ##拿到所有的贴源表信息，数组
        columns_array=self.all_info
        for hive_table,tuple in iter_info.items():
            #row_values = [hive_table.decode('UTF-8'), table_name, whether, u'事实表', u'公有模型', u'离线']
            row_values=tuple
            try :
                table_dic=columns_array[hive_table]
                columns_values = table_dic["columns"]
                print("找到一个模型 "+hive_table)
                ##创建其他模型 sheet
                ##  ##中文名	理财产品成交信息
                # 英文名	t_fs_conclude_inf
                # 唯一索引
                # 非唯一索引
                # 描述
                model_sheet_headings =[]
                tuple=("中文名",row_values[3])
                model_sheet_headings.append(tuple)
                tuple=("英文名",hive_table)
                model_sheet_headings.append(tuple)
                tuple=("唯一索引",'')
                model_sheet_headings.append(tuple)
                tuple=("非唯一索引",'')
                model_sheet_headings.append(tuple)
                tuple=("描述",'')
                model_sheet_headings.append(tuple)

                model_style,model_sheet = self.create_model_sheet_xlsx(workbook, hive_table, model_sheet_headings)
                col_index=1
                print("列的元祖长度=%d" %len(columns_values))
                for seq in range(0,len(columns_values)):
                    ##只写某个单元格
                    model_sheet.write(seq+7,0,col_index,model_style)
                    #print(columns_values[seq])
                    model_sheet.write_row('B%d'%(seq+8),columns_values[seq],model_style)
                    col_index +=1
                #= HYPERLINK(“{}”, “{}”)’.format(链接,“链接名称”)
                #worksheet.default_url_format()
                worksheet.write_row('A' + str(sequence), row_values, style)
                #ws.write(i, 1, "=HYPERLINK(\"#sheet2!a{}\")\r".format(i))
                #worksheet.
                #write_table_of_sheet0.write(13, 2, xlwt.Formula(u"HYPERLINK(\"#链接!a1\", \"链接\")\r"), hyper_style)
                print("第%d"%sequence)
                #link_style = self.get_link_style()
                worksheet.write_formula(sequence-1,2,"=HYPERLINK(\"#{}!A1\",\"{}\")".format(hive_table,hive_table),worksheet.default_url_format)
                ##在子sheet 上增加一个返回键
                model_sheet.write('L1',"=HYPERLINK(\"#目录索引!a1\",\"返回\")",model_sheet.default_url_format)
                sequence += 1
            except Exception as e:
                print(" key=%s is　not exists" %hive_table)

    ##创建第一个sheet
    def create_update_notes_sheet_xlsx(self,wb,sheetname):
        worksheet = wb.add_worksheet(sheetname)
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 8.8)
        worksheet.set_column('B:F', 12)
        worksheet.set_column('G:G', 8.88)
       #序号	中文表名	英文表名	变更说明	变更人	变更日期	备注
        # 定义一个格式
        style = wb.add_format()
        style.set_border(2)
        # 设置表头
        headings = ['序号', '中文表名', '英文表名', '变更说明', '变更人', '变更日期', '备注']
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        # 插入数据
        # self.insert_model_data(worksheet, style)

    ##创建模型sheet，每个模型创建一个sheet
    def create_model_sheet_xlsx(self,wb,sheetname,model_headings):
        #f = xlwt.Workbook(sheetname)
        #f.add_sheet(sheetname,cell_overwrite_ok=True)
        worksheet = wb.add_worksheet(sheetname)

        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:D', 15)
        worksheet.set_column('E:G', 8.8)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:K', 8.8)
        worksheet.set_column('L:L', 10.88)
        # 定义一个格式
        format = {
            'bold': True,  # 字体加粗
            'num_format': '$#,##0',  # 货币数字显示样式
            'align': 'center',  # 水平位置设置：居中
            'valign': 'vcenter',  # 垂直位置设置，居中
            'font_size': 12,  # '字体大小设置'
            'font_name': 'Courier New',  # 字体设置
            'italic': True,  # 斜体设置
            'underline': 1,  # 下划线设置 1.单下划线 2.双下划线 33.单一会计下划线 34双重会计下划线
            'font_color': "red",  # 字体颜色设置
            'border': 2,  # 边框设置样式1
            'border_color': 'green',  # 边框颜色
            'bg_color': '#c7ffec',  # 背景颜色设置

        }
        # style=wb.add_format(format)
        style = wb.add_format()
        style.set_border(1)
        style.set_align("center")
        style.set_valign("vcenter")
        #style.set_border_color("red")
        ##中文名	理财产品成交信息
        # 英文名	t_fs_conclude_inf
        # 唯一索引
        # 非唯一索引
        # 描述
        #worksheet.merge_range('B4:D4', 'Merged Range', merge_format)
        #worksheet.merge_range(3, 1, 3, 3, 'Merged Range', merge_format)
        worksheet.set_default_row(18)
        print(model_headings)
        for i in range(0,len(model_headings)):
            if i ==len(model_headings)-1:
                worksheet.merge_range(i,0,i+1,0, model_headings[i][0],style)
                worksheet.merge_range(i, 1, i+1, 10, model_headings[i][1],style)
                print(model_headings[i][0])
            else :
                worksheet.write('A%d'%(i+1),model_headings[i][0])
                worksheet.merge_range(i,1,i,10,model_headings[i][1])
        #worksheet.write('A2',"英文名")
        #worksheet.merge_range(0,1,0,10,"模型中文名")
        #worksheet.merge_range(1,1,1,10,"模型英文名")
        # worksheet.merge_range(2,1,2,10,"唯一索引")
        # worksheet.merge_range(3,1,3,10,"非唯一索引")
        # worksheet.merge_range(4,1,5,10,"描述信息")
        #merge_range(first_row, first_col, last_row, last_col, data[, cell_format]) #Merge a range of cells.
        # worksheet.merge_range(4,0,5,0,"描述")
        # 设置表头 字段序号	字段英文名	字段中文名 字段类型 长度 主键否	空值验证 标准代码编号	分布键	分区键	备注
        headings = ['字段序号', '字段英文名', '字段中文名', '字段类型', '长度', '主键否', '空值验证','标准代码编号','分布键','分区键','备注']
        # 横向写入数据
        worksheet.write_row('A7', headings, style)
        return  style,worksheet
        # 插入数据
        # self.insert_model_data(worksheet, style)


    # 创建一个xlsx的excel
    def create_model_excel_xlsx(self):
        # 新建一个Excel文件
        #workbook = xlsxwriter.Workbook(self.model_name.decode('utf-8'))
        workbook = xlsxwriter.Workbook(self.model_name)
        print(self.model_name)
        # 新建一个名为model的sheet
        self.create_update_notes_sheet_xlsx(workbook,"变更记录")
        #创建第二个sheet
        worksheet = workbook.add_worksheet('目录索引')
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:C', 15)
        worksheet.set_column('C:D', 25)
        worksheet.set_column('E:K', 8.88)
        # worksheet.set_column('I:I', 25)
        # worksheet.set_column('J:J', 8.88)
        # worksheet.set_column('K:M', 12)
        # worksheet.set_column('N:N', 30)
        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # 设置表头
        headings = ['一级主题', '二级主题', '实体英文简称', '实体中文名', '加载策略', '更新频率', '增全量规则', '保存周期类型',
                    '是否保存月底数', '数据保存天数', '备注']
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        # 插入数据
        self.insert_model_data(workbook,worksheet, style)
        # 关闭并保存文件
        workbook.close()



    def main(self):
        # 读取配置文件
        #self.get_config_file()
        self.get_config_file_source()
        ##读取接口目录的配置文件
        self.get_interface_index_source()
        # 生成模板excel
        self.create_model_excel_xlsx()
        # 生成数据项excel
        #self.create_excel_xls()
        # 生成抽取sql
        #self.create_excel_sql()
        print("执行成功！！！")


# 判断输入参数
def judge_input_parameters_num():
    if len(sys.argv) != 2:
        print("请输入正确的是参数： aotu_generate_model_config_file.py configuration_files")
        #sys.exit(1)


if __name__ == '__main__':
    judge_input_parameters_num()
    aotu = AotuGenerate()
    aotu.main()
