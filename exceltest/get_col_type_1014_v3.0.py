# -*- coding:utf-8 -*-
import re
import xlrd
import xlsxwriter
import sys
import os
class colType:

    def __init__(self):
        #self.filename = sys.argv[1]
        #path = os.path.dirname(self.filename)
        #name = os.path.basename(self.filename).split('.')[0]
        #self.model_name = path +"/"+ name + '_模型.xlsx'
        #self.basename="e://files/model-test.xlsx"
        #self.basename=self.filename
        self.db_columns_type = {}
        #特殊的排除在外，单独罗列出来
        self.match_type = {'varcahr2': 'varchar',
                           'varchar2': 'varchar',
                           'varcahr': 'varchar',
                           'varchar': 'varchar',
                           'character': 'varchar',
                           'character varying': 'varchar',
                           'char': 'varchar',
                           'date': 'varchar',
                           'lvarchar':'varchar'

                           }
        self.time_match_type = {
            'timestamp with time zone': 'string',
            'time':'timestamp',
            'timestamp':'timestamp',
            'timestampwithtimezone':'timestamp',
        }
        ## bigint 的key是我自己加的
        self.num_match_type = {
            'integer': 'bigint',
            'number': 'bigint',
            'nuber': 'bigint',
            'numeric': 'bigint',
            'decimal': 'decimal',
            'smallint': 'bigint',
            'bigint': 'bigint',
            'clob': 'string'
        }
    ## 处理decimal(12,0) 这样的类型问题，返回得到 bigint
    def get_data_length(self,type_name):
        #得到decimal(12,3) 这样的数字，12,3
        all_num = re.findall("\d+", type_name)
        arrlen = len(all_num)
        ##这里导致了一个bug ,把 decimal15,2 数字替换成空，多了个逗号
        findArr = re.split(r"\d", type_name, 1)
        pre_str = findArr[0]
        if arrlen == 2:
            ##替换掉char5 这种格式，可能是excel写错了的 decimal15,处理得到 decimal(15)
            # print("pre decimal12,5="+type_name)
            name = pre_str + "(" + all_num[0] + "," + all_num[1] + ")"
        elif arrlen == 1:
            if type_name == "varchar2":
                ##个人加的，对varchar2的，默认加个长度(200)
                # print('get_data_length ='+type_name)
                name=type_name
            else :
                name = pre_str + "(" + all_num[0] + ")"
            # if pre_str == 'lvarchar':
            #     print("lvarchar find "+name)

        elif arrlen > 2:
            name = type_name
            print("应该没有这种情况的出现 all_num >3 ")
        else:
            name = type_name
        return name
    #字段规则映射生成
    def cols_mapping_rule(self,pre_str,old_type_name,col_dict):
        ##把重新拼接好的值赋值给原有的type_name
        # print(" 拼接前 type_name1="+type_name)
        ##原来的name 保存不变，新的是type_name
        type_name = old_type_name
        # col_dict={}
        #用于统计不重复的字段类型
        types = set()
        ##开始建立数据项的一一映射关系
        # if type_name == "varchar2":
        #     print("cols_mapping_rule varchar2=" + type_name)

        if pre_str == "time" or pre_str.startswith("timestamp"):
            col_dict[old_type_name] = "string"
            # print( "match pre_str %s, %s, => %s" %(pre_str,type_name,"string"))
            ##处理 varchar这样的数据类型的映射关系
        elif pre_str in self.match_type:
            # col_dict.
            # if type_name == "varchar2":
            #     print(" 1 varchar2=" + type_name)
            newpre = self.match_type.get(pre_str)
            if type_name =='date(14)':
                # print("cols_mapping_rule "+type_name)
                type_name="string"
            elif type_name== 'date':
                type_name="varchar(10)"
                # print("cols_mapping_rule "+type_name)
            else :
                if type_name ==  "varchar2":
                    # print("varchar2="+type_name)
                    type_name="varchar"
                else :
                    type_name = str(type_name).replace(pre_str, newpre)
                # print('替换之后 key=%s,v=%s' %())
            # if type_name.startswith("lvarchar"):
            #     print(" cols_mapping_rule lvarchar="+type_name)

            # print( "match pre_str %s, %s, => %s" %(pre_str,name,type_name))
            col_dict[old_type_name] = type_name
            ##处理 numric(5) numric(6,2)这种数据格式
        elif pre_str in self.num_match_type:
            # todo
            decimal = re.search("\d+\,", type_name)
            # print("type_name="+str(decimal))
            if pre_str.startswith("decimal"):
                # print('pre_str =%s typename=%s' % (pre_str, type_name))
                if type_name == 'decimal(17)':
                    newname = 'varchar(17)'
                else:
                    # newname = re.sub('\)', ',2)', type_name)
                    newname = "decimal(20,2)"
                data_type = newname
            elif pre_str == 'clob':
                data_type="string"
                # print("cols_mapping_rule clob "+data_type)
            elif decimal:
                # print(decimal)
                all_num = re.findall("\d+", type_name)
                # print(all_num)
                all_len=len(all_num)
                if all_len ==2 :
                    # print("decimal all_num="+all_num[1])
                    ## 字符串0和数字0 不一样
                    if all_num[1] =='0':
                        data_type="bigint"
                        # print("data_type bigint")
                    else :
                        data_type = type_name.replace(pre_str, "decimal")
                else :
                    data_type = type_name.replace(pre_str, "decimal")
            else:
                data_type = "bigint"
            # print( "num match %s，%s => %s" %(pre_str,type_name,data_type))
            # data_type=re.sub(',\(','(',data_type)
            col_dict[old_type_name] = data_type

        else:
            # print("type_name2="+type_name)

            col_dict[old_type_name] = type_name
        #     types.add(pre_str)
        # print("-----------------pre_str 前缀类型--------------")
        # print(types)
        # return col_dict

    ##看数据项格式是否是含有括号的格式 如 varchar(20),有就截取前面的部分作为前缀 前缀最后是要替换的
    # 如果不含括号，也可能带有数字，需要我们自己手动加括号
    #处理如  decimal15,2 特殊映射规则如下
    #   char => varchar
    # date => varchar(10)
    # numeric(2,0) => bigint
    # clob => string
    def columns_mapping_proc(self,type_name,cols_dict):
        first = type_name.find("(")
        pre_str = ''
        ##最后返回的就是前缀
        name = ''
        if first != -1:
            if not type_name.endswith(")"):
                #如果存在半个括号的，加上一个括号，把空括号替换掉
                type_name=(type_name+")").replace("()","")

            pre_str = type_name[0:first]
            name=type_name
        else:
            # all_num = re.findall("\d+", type_name)
            # arrlen = len(all_num)
            # ##这里导致了一个bug ,把 decimal15,2 数字替换成空，多了个，
            name = self.get_data_length(type_name)
            findArr = re.split(r"\d", name, 1)
            pre_str = findArr[0]
            # if name =="varchar2":
            #     print("prestr=%s name=%s"%(pre_str,name))

        self.cols_mapping_rule(pre_str, name,cols_dict)
        #return cols_dic
    #处理列类型的人工错误情况，比如：
    # 1 中文括号 逗号
    # 2 空括号，半个括号的情况
    # 3 data_type 为空的情况
    # 4 decimal (12,5) 中间非法空格的问题
    def check_columns_to_right_rule(self,type_name,all_type):
        ##存放原有类型
        # all_type=set()
        type_name = type_name.replace('（', '(').replace('）', ')').replace('()', '').replace("，", ",")
        if not type_name or type_name == 'none':
            # print("check_columns_to_right_rule type_name 不存在="+type_name)
            all_type.add(type_name)
            return ''
        ##开始处理各个字段类型的映射关系以及位数更正
        if type_name.startswith("character varying"):
            # print("type_name= character varying")
            all_type.add(type_name)
        elif type_name.startswith("timestamp"):
            all_type.add(type_name)
        else:
            # type_name = re.sub(",\(", "(", type_name)
            # print("type_name ="+type_name)
            type_name = type_name.replace(" ", "")
            # if type_name.startswith("lvar"):
            #     print("find ="+type_name)
            # all_type.append(type_name)
            ## set 集合使用 add 方法
            all_type.add(type_name)

        return type_name.strip()

    def get_config_file_source(self):
        # 读取配置文件
        basefilename = "e://files/types.xlsx"
        print("get_interface_index_source 打开" + basefilename)
        data = xlrd.open_workbook(basefilename)
        # 通过索引获取，例如打开第一个sheet表格
        #table = data.sheet_by_name("接口目录")
        table = data.sheet_by_index(0)
        allrows = 0
        col_dict={}
        all_type_set=set()
        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            allrows = table.nrows  # 获取该sheet中的有效行数
            for rowindex in range(1, allrows):
                cells = table.row_values(rowindex)
                type_name = cells[0].strip().lower()
                # #print(type_name) 替换中文的括号,替换掉空括号
                # type_name=type_name.replace('（','(').replace('）',')').replace('()','').replace("，",",")
                # if not type_name or type_name=='none':
                #     #print("replace 替换之后的 type_name="+type_name)
                #     continue
                # ##开始处理各个字段类型的映射关系以及位数更正
                # if type_name.startswith("character varying"):
                #     # print("type_name= character varying")
                #     all_type.append(type_name)
                # elif type_name.startswith("timestamp"):
                #     all_type.append(type_name)
                # else:
                #     #type_name = re.sub(",\(", "(", type_name)
                #     #print("type_name ="+type_name)
                #     type_name=type_name.replace(" ","")
                #     # if type_name.startswith("lvar"):
                #     #     print("find ="+type_name)
                #     all_type.append(type_name)
                new_type_name = self.check_columns_to_right_rule(type_name, all_type_set)
                if new_type_name :
                    ## 开始处理 type_name
                    self.columns_mapping_proc(new_type_name,col_dict)
                # else :
                #     print("type_name 为空串")
        headings=['GP数据项类型','HIVE_数据项类型','mark']
        worksheet,wb = self.create_fail_model_excel_xlsx("e://files/gp_hive_mapping.xlsx", 'mapping', headings)
        sequence=2
        for val in col_dict.items():
            # print(key+" = "+value)
            worksheet.write_row("A"+str(sequence),val)
            sequence +=1
            # if value.startswith("char"):
            #     print("2 char60=" + value)
        wb.close()
        print(len(all_type_set))

        # 创建一个xlsx的excel
    def create_fail_model_excel_xlsx(self, name, sheet_name, headings):
        # 新建一个Excel文件
        workbook = xlsxwriter.Workbook(name)
        # 创建第二个sheet
        worksheet = workbook.add_worksheet(sheet_name)
        # 设定第一列(A)宽度像素
        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 15)

        # 定义一个格式
        style = workbook.add_format()
        style.set_border(1)
        # 横向写入数据
        worksheet.write_row('A1', headings, style)
        return worksheet, workbook

    def main(self):
        # 读取配置文件
        self.get_config_file_source()
        print("main 执行完成！！！")


# 判断输入参数
def judge_input_parameters_num():
    if len(sys.argv) != 2:
        print("请输入正确的是参数： aotu_generate_model_config_file.py configuration_files")
        #sys.exit(1)


if __name__ == '__main__':
    #judge_input_parameters_num()
    #分割字符串比查找好，查找如果找不到，返回空数组
    # print(re.split("\d+", "decimal", 1))
    #print(re.findall("\D+", "2344"))
    aotu = colType()
    aotu.main()
    # print(re.findall("([a-z]+)(\,)","hello,(234,23)"))
    # print(re.sub(",\(","(","hello,(234,23)"))
    # print(re.sub(",\(","(","hello ,"))
