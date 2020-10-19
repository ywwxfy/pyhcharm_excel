
# -*- coding:utf-8 -*-

import xlwt
import xlrd
import xlsxwriter
import collections
import os
import re
import sys
sys.path.append("E:/Program Files (x86)/software/pyhcharm/exceltest/")
import get_col_type
#sys.path.append("/data02/dcadmin/scripts/common")
#reload(sys)
#sys.setdefaultencoding('utf-8')


class AotuGenerate:

    def __init__(self):
        self.filename = sys.argv[1]
        self.model_name = sys.argv[2]
        self.failed_match_model_name = sys.argv[3]
        self.source_flag = sys.argv[4]
        # path = os.path.dirname(self.filename)
        # name = os.path.basename(self.filename).split('.')[0]
        #self.basename="e://files/model-test.xlsx"
        self.basename=self.filename
        # self.data_item_name = path + name + '_数据项.xls'
        # self.sql_name = path +'/'+ name + '_执行sql.xlsx'
        self.all_info = None
        self.interface_dic = {}
        # p08_load_way 加载模式，有就拿下来，没有就置空,需要问具体的意思
        # p05_f_table_filt 源表过滤条件，原封不动
        # p07_table_style 表类型 c:当前 s:切片 l:拉链 原封不动保存
        # p17_view_key 分布键,暂时不管
        # p08_key_cols 主键字段集合，逗号分隔开，替换成Y,N，原来的不正确
        self.jobs_info = {"p08_load_way":"","p05_f_table_filt":"","p07_table_style":"","p08_key_cols":[]}

        # self.job_params_key={"p08_load_way":}
        # self.db_columns_type = {}
        #numberic格式映射
        # NUMERIC(20,2) NUMERIC(12)

        self.match_type = {
                           'bigint': ['NUMBER'],
                           'decimal': ['NUMBER']}
        ## NUMERIC(20,2)==> decimal(20,2) NUMERIC(12) => bigint

        self.fields = {}
    '''
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
    '''
    def get_interface_index_source(self):
            global fail_sheets_list
            # 读取配置文件
            basefilename = self.basename
            category_info = self.interface_dic
            print("get_interface_index_source 打开"+basefilename)
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
                        print(" 接口目录表第 %d 行 hive table 为空，跳过 " %rowindex+1)
                        continue
                    #更新频率 日/月/空白
                    update_frequence = cols[6].strip()
                    #保存周期类型,就是清理规则
                    clean_rule = cols[7].strip()
                    #增量 / 全量(每日)，对应到 加载策略要变化，是追加还说覆盖
                    #todo 不给默认值

                    data_rule = cols[8].strip()
                    load_rule=''
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
                    if hive_table not in category_info:
                        t_message=(source_name,'',hive_table,t_ch_name,load_rule,update_frequence,data_rule,clean_rule,save_mons,save_days,mark)
                        category_info.setdefault(hive_table,t_message)
                    else :
                        print(f'hive table ={hive_table} 重复了,从dict 中踢出去')
                        e=category_info.pop(hive_table)
                        fail_sheets_list.setdefault(hive_table,e)
                        # print(e)

            self.interface_dic=category_info
            #print(self.interface_dic)
            print("get_interface_index_source 总共读取excel %d 行，解析到的模型数目为 num=%d 个" %(allrows,len(self.interface_dic)))
    '''
        1 解决 贴源sheet 里面表名写错的问题，导致漏了模型
    '''
    def check_job_params_in_needed(self,job_param_name):
        jobs_info = self.jobs_info
        flag=False
        if job_param_name in jobs_info:
            # jobs_info.setdefault(job_param_name,job_param_val)
            # self.jobs_info=jobs_info
            flag=True
        return flag
    # 逗号分隔
    def get_job_pri_keys(self,param_val):
        keys_col=[]
        if param_val :
            if param_val != 'null' and param_val !='':
                splits = param_val.replace("，",",").split(",")
                if len(splits) >0:
                    # keys_col=splits
                    for ele in splits:
                        keys_col.append(ele.strip().lower())
            else :
                print('2 param_val 其他情况，不是null,也不是空字符串')
        else :
            print('1 param val 第一次判断即不存在')

        return keys_col



    '''
        1 读取作业参数信息sheet
    '''
    def get_job_config_source(self):
        filename=self.filename
        data=xlrd.open_workbook(filename)
        table = data.sheet_by_name('作业参数登记')

        jobs_info=collections.OrderedDict()
        cols_dict = {}
        wrong_table_dict = {}
        if data.sheet_loaded("作业参数登记"):
            nrows = table.nrows
            for index in range(3,nrows):
                row_value = table.row_values(index)
                #作业名	作业参数名	参数类型	参数描述	参数值	其他
                job_name=row_value[0].strip().upper()
                job_param_name=row_value[1].strip().lower()
                param_type=row_value[2]
                param_desc=row_value[3]
                try :
                    param_value=row_value[4].strip().lower()
                except Exception as e:
                    param_value=row_value[4]
                flag = self.check_job_params_in_needed(job_param_name)
                ## 主键的情况 :null,没主键 为空，多个主键，逗号分隔
                # keys_col=[]
                if flag :
                    print(flag)
                    if job_param_name =='p08_key_cols':
                        param_value = self.get_job_pri_keys(param_value)
                        print(f'主键集合 {param_value}')

                else :
                    print('continue')
                    continue

                # p08_load_way 加载模式，有就拿下来，没有就置空,需要问具体的意思
                # p05_f_table_filt 源表过滤条件，原封不动
                # p07_table_style 表类型 c:当前 s:切片 l:拉链 原封不动保存
                # p17_view_key 分布键,暂时不管
                # p08_key_cols 主键字段集合，逗号分隔开，替换成Y,N，原来的不正确
                # key :作业表名,cols:[],p07_table_style:"",p08_load_way:"",p05_f_table_filt:
                if job_name :
                    if job_name not in jobs_info:
                        # jobs_info.setdefault(job_name,job_name)
                        jobs_info[job_name]={"job_name":job_name,job_param_name:param_value}

                    else :
                        jobs_info[job_name].setdefault(job_param_name,param_value)
                    #
                    #     print(f'重复的jobname {job_name}')
                else :
                    print(f'job_name 为空或者不存在 job_name={job_name}')

        print(jobs_info)

    '''
    # 读取配置文件
    ##字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
    ##目录表
    ##贴源表字段，字段都可能为空
    ##表英文名 表中文名 字段英文名 字段中文名 字段类型 是否主键 是否分布键 备注 上线日期
    '''
    def get_config_file_source(self):
        # 读取配置文件
        filename = self.filename
        data = xlrd.open_workbook(filename)
        # 通过索引获取，例如打开第一个sheet表格
        # table = data.sheet_by_index(0)
        table = data.sheet_by_name("接口明细-贴源")
        ##那个内容都是5行，每次相当于从下标为6开始
        row_index = 1
        ## 用于存放各数据项 的set集合和 映射字典
        all_type_set=set()
        cols_dict={}
        wrong_table_dict={}
        if data.sheet_loaded("接口明细-贴源"):  # 检查某个sheet是否导入完毕
            nrows = table.nrows  # 获取该sheet中的有效行数
            i = 1
            all_info = collections.OrderedDict()
            table_index = 1
            print("----------------读取 贴源 config begin -----------------------")
            for row_num in range(1, nrows):
                row_vaule = table.row_values(row_num)
                #print(row_vaule)

                # hive_db = row_vaule[0].strip().lower()
                hive_table = row_vaule[0].strip().lower()
                t_name = row_vaule[1].strip() ##表中文名
                en_name = row_vaule[2].strip().lower() ##表字段英文名

                ch_name = row_vaule[3]
                ##表字段中文名 处理
                ch_name=self.data_type_rule_exec(ch_name)
                # if ch_name == 42:
                #     ch_name=''
                data_type=row_vaule[4].strip().lower()
                if hive_table in wrong_table_dict :
                    # print("这张表有问题 hive_table=%s 跳过" %hive_table)
                    continue
                if not data_type or data_type=='()' or data_type=='none' :
                    print ("data_type is empty :hive_table='%s',t_name='%s',col_name='%s'"%(hive_table,t_name,en_name))
                    wrong_table_dict[hive_table]=hive_table
                    continue
                # if data_type =='' :
                #     print('--------------------------------data_type 是空串')
                #     continue
                new_data_type = self.data_type_process(all_type_set, cols_dict, data_type)

                #print(ch_name)
                pkey = row_vaule[5].strip()
                distribute = row_vaule[6].strip()
                mark = row_vaule[7]
                create_day = row_vaule[8]
                #字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
                ## 表英文名 表中文名 字段英文名 字段中文名 字段类型 是否主键 是否分布键 备注 上线日期
                #print(table_index)
                #col_tuple = (table_index, en_name, ch_name, data_type, '', pkey, '', '', distribute, '', mark)
                col_tuple = (en_name, ch_name, new_data_type, '', pkey, '', '', distribute, '', mark)
                # print(col_tuple)
                if hive_table =='':
                    print("接口明细贴源 sheet 的hive_table is empty: 跳过 第 "+str(row_num+1)+" 行")
                elif hive_table not in all_info:
                    table_index = 0
                    #print("table_index=0")
                    all_info[hive_table] = {'hive_table': hive_table, 'columns': [col_tuple],
                                            'table_name': t_name}
                else:

                    if en_name not in all_info[hive_table]['columns']:
                        #table_index += 1
                        col_tuple = (en_name, ch_name, new_data_type, '', pkey, '', '', distribute, '', mark)
                        all_info[hive_table]['columns'].append(col_tuple)
                    # row_index =row_num+5



            self.all_info = all_info
            print(f"data_type 为空的模型数目为 {len(wrong_table_dict)}")
            # print(f"找到的模型数目为 {len(all_info)}")
            print("****************************** 读取config end*******************")
    '''
        调用 数据项纠正方法处理 数据项的问题，得到新的 data_type值
    '''
    def data_type_process(self, all_type_set, cols_dict, data_type):
        ## 对错误的 en_name 进行纠正
        right_data_type = col_type.check_columns_to_right_rule(data_type, all_type_set)
        if right_data_type:
            col_type.columns_mapping_proc(right_data_type, cols_dict)
            new_data_type = cols_dict.get(right_data_type)
            # print("映射以后的 ="+new_data_type)
            if not new_data_type:
                print("1 get_config_file_source 未找到对应的映射类型 key='%s' value='%s' " % (data_type, right_data_type))
        else:
            # print("2 get_config_file_source data_type='%s' check_right='%s'" % (data_type, right_data_type))
            new_data_type = right_data_type
        return new_data_type

    def data_type_rule_exec(self,data_type):
        try :
            if data_type == 42:
                data_type = ''
            elif data_type.startswith('#'):
                data_type=data_type.replace('#','')

            if data_type== 'N/A':
                data_type=''
            # print('old #data_type ='+data_type)
        except Exception as e :
            # print(e)
            return data_type
        return data_type

    '''
        1 读取 接口明细-非贴源 的sheet 页
        特点 ： 第一行为空行
        2 目前只有模型中英文名称和字段，没有原系统来源，需要行方手工梳理，有150多个这样的模型
        3 
    '''

    def get_no_source_config_file(self):
        # 读取配置文件
        filename = self.filename
        data = xlrd.open_workbook(filename)
        # 通过索引获取，例如打开第一个sheet表格
        table = data.sheet_by_name('接口明细-非贴源')
        ##那个内容都是5行，每次相当于从下标为6开始
        row_index=1
        # self.all_info
        category_dict={}
        wrong_model_dict={}

        all_type_set=set()
        cols_dict={}
        wrong_table_dict={}

        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            nrows = table.nrows  # 获取该sheet中的有效行数
            i = 1
            all_info = collections.OrderedDict()
            t_name_index=0
            for row_num in range(1, nrows):
                row_vaule = table.row_values(row_num)
                # print(row_vaule)
                #hive_db = row_vaule[0].strip().lower()
                try :
                    hive_table = row_vaule[0].strip().lower()
                except :
                    # print('exception hive_table ='+str(row_vaule[0]))
                    hive_table=row_values[0]
                ch_name = row_vaule[1].strip()
                ch_name=self.data_type_rule_exec(ch_name)
                # print(ch_name)
                # if ch_name.startswith('#'):
                #     # ch_name=ch_name[1:]
                #     ch_name=ch_name.replace('#','')
                    # print("#chname="+ch_name)
                #if ch_name =='属性名':
                ##每次都从第一次出现模型名称的row_num 上加5行，开始才是我想要的结果
                # t_name=''
                if ch_name =='LDM':
                    row_index=row_num+5
                    #存放t_name 的行数
                    t_name_index=row_num+1
                    # print(t_name_index)
                if row_num == t_name_index:
                    t_ch_name=row_vaule[2]
                    # print("hive_table=%s t_name=%s" %(hive_table,t_ch_name))
                if row_num <row_index :
                    # print("跳过第"+str(row_num))
                    continue

                pkey = row_vaule[2].strip().lower().replace('yes','Y').replace('no','N')
                fkey = row_vaule[3].strip()
                empty = row_vaule[4]
                #en_name = re.sub("\s", "",table_name)
                ch_name2 = row_vaule[5].strip()
                en_name = row_vaule[6].strip().lower()
                distribute = row_vaule[7].strip().lower().replace('pi','Y')
                empty2 = row_vaule[8].strip()
                old_data_type = row_vaule[9].strip().lower()
                # if hive_table in wrong_model_dict :
                #     # print("这张表有问题 hive_table=%s 跳过" %hive_table)
                #     continue
                # if not old_data_type or old_data_type=='()' or old_data_type=='none' :
                #     print ("data_type is empty :hive_table='%s',t_name='%s',col_name='%s'"%(hive_table,t_ch_name,en_name))
                #     wrong_table_dict[hive_table]=hive_table
                #     # 失败模型的项目
                #     wrong_model_dict.setdefault(hive_table, en_name)
                #     continue
                ##纠正以后的 data_type
                data_type = self.data_type_process(all_type_set, cols_dict, old_data_type)
                if data_type=='varchar':
                    print('data_type=varchar hive_table=%s en_name=%s' %(hive_table,en_name))
                source_type = row_vaule[10]
                ## 每一列的字段备注，如仓库中间层，CDMA应用，加工来源
                col_mark = row_vaule[11]
                # print("colmark="+col_mark)
                ## 抽取规则，详细的规则备注，比如每月第一天怎么处理

                fetch_mark = row_vaule[12]
                if fetch_mark :
                    if col_mark :
                        mark=col_mark+";"+fetch_mark
                    else :
                        mark=fetch_mark
                else:
                    mark=col_mark
                mark=mark.replace('\n','').replace('\r','')
                # print("fetch_mark="+fetch_mark)
                ## 分区字段为Y
                # partition = row_vaule[13].strip()
                # index = row_vaule[14].strip()
                # create_day = row_vaule[15]

                ##最后需要生成的 excel 一级主题 二级主题 实体英文简称	实体中文名 加载策略(追加，覆盖) 更新频率 增全量规则 保存周期类型
                # 是否保存月底数	数据保存天数	备注
                # t_message = (source_name, '', hive_table, t_ch_name, load_rule, update_frequence, data_rule, clean_rule, save_mons,
                if hive_table not in category_dict:
                    t_message = ('', '', hive_table, t_ch_name, '', '', '', '', '','', mark)
                    category_dict.setdefault(hive_table, t_message)

                #  col_tuple = (en_name, ch_name, new_data_type, '', pkey, '', '', distribute, '', mark)
                if not en_name :
                    # print('-----------en_name 不存在,跳过 '+en_name)
                    # wrong_model_dict.setdefault(hive_table, en_name)
                    if hive_table not in all_info:
                        wrong_model_dict.setdefault(hive_table,1)
                    continue
                if not data_type or data_type=='()':
                    print('***************%s read  col=%s data_type is  %s' %(hive_table,en_name,data_type))
                    # row_values = (en_name, ch_name, data_type, '', pkey, '', '', distribute, '', mark)
                    # print(row_values)
                    wrong_model_dict.setdefault(hive_table,en_name)
                    continue

                #字段序号 字段英文名 字段中文名	字段类型 长度 主键否	空值验证 标准代码编号 分布键	分区键 备注
                row_values=(en_name,ch_name,data_type,'',pkey,'','',distribute,'',mark)
                if hive_table == '':
                    print("接口明细非贴源 sheet 的hive_table is empty: 跳过 第 " + str(row_num + 1) + " 行")
                elif hive_table not in all_info:
                    all_info[hive_table] = {'hive_table': hive_table, 'columns': [row_values],
                                            'table_name': t_ch_name}
                else:
                    if en_name not in all_info[hive_table]['columns']:
                        # table_index += 1
                        all_info[hive_table]['columns'].append(row_values)

            self.all_info = all_info
            self.interface_dic=category_dict
            print("接口目录的模型个数=%d" %len(category_dict))
            print("接口模型 数据项 data_type 为空的模型个数=%d" %len(wrong_model_dict))
            print(wrong_model_dict)
            # print(all_info)
            print("******************** 读取非贴源sheet 信息完成*************")

    # 往 excel 中插入模型和数据项的数据，如果没匹配上的就全部写一个新的excel
    def insert_model_data(self, workbook,worksheet):
        global fail_sheets_list
        ##目录索引的样式设置
        categroy_style = workbook.add_format()
        categroy_style.set_border(1)
        categroy_style.set_align("left")
        categroy_style.set_font_size(12)

        iter_info = self.interface_dic
        sequence = 2

        ##拿到所有的贴源表信息，数组
        columns_array=self.all_info
        ## 存放未匹配上的模型 hive_table:'',cols[]
        # fail_sheets_list={}
        for hive_table,tuple in iter_info.items():
            #row_values = [hive_table.decode('UTF-8'), table_name, whether, u'事实表', u'公有模型', u'离线']
            row_values=tuple
            sheet_name=hive_table
            sheet_len=len(hive_table)
            if sheet_len>35:
                sheet_name=hive_table[8:]
                # print('截取之后的 sheet_name=%s hive_table=%s' % (sheet_name, hive_table))
            elif sheet_len >31:
                sheet_name=hive_table[5:]
                # print('截取之后的 sheet_name=%s hive_table=%s' %(sheet_name,hive_table))

            try :
                # if hive_table == ''
                table_dic=columns_array[hive_table]
                columns_values = table_dic["columns"]
                #print("找到一个模型 "+hive_table)
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

                wb_cols,model_sheet = self.create_model_sheet_xlsx(workbook, sheet_name, model_sheet_headings)
                ##内容格式
                content_style = wb_cols.add_format()
                content_style.set_border(1)
                content_style.set_align("left")
                content_style.set_font_size(10)
                ## 序号格式
                seq_style = wb_cols.add_format()
                seq_style.set_align("right")
                seq_style.set_border(1)
                col_index=1
                #print("列的元祖长度=%d" %len(columns_values))
                for seq in range(0,len(columns_values)):
                    ##只写某个单元格
                    model_sheet.write(seq+7,0,col_index,seq_style)
                    #print(columns_values[seq])
                    model_sheet.write_row('B%d'%(seq+8),columns_values[seq],content_style)
                    col_index +=1
                #= HYPERLINK(“{}”, “{}”)’.format(链接,“链接名称”)
                #worksheet.default_url_format()
                worksheet.write_row('A' + str(sequence), row_values, categroy_style)
                #ws.write(i, 1, "=HYPERLINK(\"#sheet2!a{}\")\r".format(i))
                #worksheet.
                #write_table_of_sheet0.write(13, 2, xlwt.Formula(u"HYPERLINK(\"#链接!a1\", \"链接\")\r"), hyper_style)
                #print("第%d"%sequence)
                #link_style = self.get_link_style()
                url_format = model_sheet.default_url_format
                url_format.set_font_size(11)
                link_format = workbook.add_format({'color': '#800080',
                                                   'underline': True,
                                                   'text_wrap': True})

                url_format.set_font_color("#800080")
                worksheet.write_formula(sequence-1,2,"=HYPERLINK(\"#{}!A1\",\"{}\")".format(hive_table,hive_table),link_format)
                #这是写入 url的方式
                #worksheet.write_url(sequence-1,2,"=HYPERLINK(\"#{}!A1\",\"{}\")".format(hive_table,hive_table),link_format)
                ##在子sheet 上增加一个返回键
                model_sheet.write('L1',"=HYPERLINK(\"#目录索引!a1\",\"返回\")",url_format)
                sequence += 1
            except Exception as e:
                print(" key=%s is　not exists %s" %(hive_table,str(e)))
                #print(row_values)
                # fail_sheets_list.append(row_values)
                if hive_table not in fail_sheets_list:
                    fail_sheets_list.setdefault(hive_table,row_values)
                # fail_sheet.write_row('A' + str(fail_sequence), row_values, categroy_style)
                #print("失败 %d" %fail_sequence)
                # fail_sequence += 1
        print("insert_model_data 总共成功的数目为 num=%d" %(sequence-2))
        fail_len=len(fail_sheets_list)
        if fail_len >0:
            fail_sequence = 2
            headings = ['一级主题', '二级主题', '实体英文简称', '实体中文名', '加载策略', '更新频率', '增全量规则', '保存周期类型',
                        '是否保存月底数', '数据保存天数', '备注']
            fail_sheet, wb = self.create_fail_model_excel_xlsx(failed_match_model_name, "模型目录", headings)
            for table,rowValue in fail_sheets_list.items():
                fail_sheet.write_row('A' + str(fail_sequence), rowValue, categroy_style)
                fail_sequence += 1
            wb.close()
        print("insert_model_data 模型数据项和模型目录失败的匹配数目为 num=%d" %fail_len)
        print('*********** insert_model_data 写入数据完成*************')


    ##创建第一个变更记录 sheet
    def create_update_notes_sheet_xlsx(self,wb,sheetname):
        worksheet = wb.add_worksheet(sheetname)
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 6)
        worksheet.set_column('B:F', 12)
        worksheet.set_column('G:G', 6)
       #序号	中文表名	英文表名	变更说明	变更人	变更日期	备注
        # 定义一个格式
        style = wb.add_format()
        style.set_border(2)
        style.set_bg_color("#AEAAAA")
        style.set_font_size(12)
        style.set_font("等线")
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
        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:D', 15)
        worksheet.set_column('E:G', 8.8)
        worksheet.set_column('H:H', 12)
        worksheet.set_column('I:K', 8.8)
        worksheet.set_column('L:L', 10.88)

        # style=wb.add_format(format)
        style = wb.add_format()
        style.set_border(1)
        style.set_align("left")
        style.set_valign("vcenter")
        style.set_border_color("black")

        first_style=wb.add_format()
        first_style.set_border(1)
        first_style.set_valign('vcenter')
        first_style.set_align("left")
        first_style.set_bg_color('#CCFFCC')
        first_style.set_font_size(10)
        #表头的格式
        head_style=wb.add_format()
        # #CCFFFF
        head_style.set_border(1)
        head_style.set_bg_color("#CCFFFF")
        head_style.set_font_size(10)


        ##中文名	理财产品成交信息
        # 英文名	t_fs_conclude_inf
        # 唯一索引
        # 非唯一索引
        # 描述
        #worksheet.merge_range('B4:D4', 'Merged Range', merge_format)
        #worksheet.merge_range(3, 1, 3, 3, 'Merged Range', merge_format)
        worksheet.set_default_row(18)
        #print(model_headings)
        for i in range(0,len(model_headings)):
            if i ==len(model_headings)-1:
                worksheet.merge_range(i,0,i+1,0, model_headings[i][0],first_style)
                worksheet.merge_range(i, 1, i+1, 10, model_headings[i][1],style)
                #print(model_headings[i][0])
            else :
                worksheet.write('A%d'%(i+1),model_headings[i][0],first_style)
                worksheet.merge_range(i,1,i,10,model_headings[i][1],style)
        #worksheet.write('A2',"英文名")
        #merge_range(first_row, first_col, last_row, last_col, data[, cell_format]) #Merge a range of cells.
        # worksheet.merge_range(4,0,5,0,"描述")
        # 设置表头 字段序号	字段英文名	字段中文名 字段类型 长度 主键否	空值验证 标准代码编号	分布键	分区键	备注
        headings = ['字段序号', '字段英文名', '字段中文名', '字段类型', '长度', '主键否', '空值验证','标准代码编号','分布键','分区键','备注']
        # 横向写入数据
        worksheet.write_row('A7', headings, head_style)
        return  wb,worksheet
        # 插入数据
        # self.insert_model_data(worksheet, style)


    # 创建一个xlsx的excel
    def create_model_excel_xlsx(self,modelName):
        # 新建一个Excel文件
        workbook = xlsxwriter.Workbook(modelName)
        print(" create_model_excel_xlsx 最后生成的文档名称："+modelName)
        # 新建一个名为model的sheet
        self.create_update_notes_sheet_xlsx(workbook,"变更记录")
        #创建第二个sheet
        worksheet = workbook.add_worksheet('目录索引')
        # 设定第一列(A)宽度像素
        worksheet.set_row(0,22)
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:C', 15)
        worksheet.set_column('C:D', 30)
        worksheet.set_column('E:K', 8.88)
        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # #8497B0
        style.set_bg_color("#8497B0")
        style.set_bold(True)
        style.set_font("等线")
        #style.set_font_size(12)
        # 设置表头
        headings = ['一级主题', '二级主题', '实体英文简称', '实体中文名', '加载策略', '更新频率', '增全量规则', '保存周期类型',
                    '是否保存月底数', '数据保存天数', '备注']
        # 横向写入数据

        worksheet.write_row('A1', headings, style)
        #worksheet.merge_range(0,0,1,0, headings, style)
        # 插入数据
        self.insert_model_data(workbook,worksheet)
        # 关闭并保存文件
        workbook.close()

        # 创建一个xlsx的excel
    def create_fail_model_excel_xlsx(self,name,sheet_name,headings):
        # 新建一个Excel文件
        workbook = xlsxwriter.Workbook(name)
        # 创建第二个sheet
        worksheet = workbook.add_worksheet(sheet_name)
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:C', 15)
        worksheet.set_column('C:D', 25)
        worksheet.set_column('E:K', 8.88)

        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        return worksheet,workbook



    def main(self):
        global failed_match_model_name

        source_type = self.source_flag
        failed_match_model_name=self.failed_match_model_name
        model_name=self.model_name
        self.get_job_config_source()
        return
        # 非贴源的表
        if source_type == 'no_source':
            # 读取配置文件
            path = os.path.dirname(failed_match_model_name)
            name = os.path.basename(failed_match_model_name).split('.')[0]
            failed_match_model_name=path+'\\'+source_type+'_'+name+'.xlsx'
            path = os.path.dirname(model_name)
            name = os.path.basename(model_name).split('.')[0]
            model_name=path+"\\"+source_type+'_'+name+'.xlsx'
            ## python 3.6 之后的做法
            print(f'fail_match_model_name={failed_match_model_name} target_model_name={model_name}')
            self.get_no_source_config_file()
        else :
            self.get_config_file_source()
            ##读取接口目录的配置文件
            self.get_interface_index_source()

        # 生成模板excel
        self.create_model_excel_xlsx(model_name)

        # 生成数据项excel
        #self.create_excel_xls()
        # 生成抽取sql
        #self.create_excel_sql()
        print("main 执行完成！！！")


# 判断输入参数
def judge_input_parameters_num():
    if len(sys.argv) != 5:
        print(len(sys.argv))
        print("""
          请输入正确的是参数： 
        aotu_generate_model_config_file.py e:\files\model-test.xlsx e:\files\model-test_模型.xlsx e:\files\fail_match_model.xlsx
        """)
        sys.exit(1)


if __name__ == '__main__':
    judge_input_parameters_num()
    aotu = AotuGenerate()
    fail_sheets_list = {}
    # 初始化一个对象，得到col_type
    col_type = get_col_type.colType()
    failed_match_model_name=''
    # col_type.check_columns_to_right_rule()
    aotu.main()
