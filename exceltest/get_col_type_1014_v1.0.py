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
                           'character': 'char',
                           'character varying': 'varchar',
                           'lvarchar':'varchar'
                           }
        self.time_match_type = {
                           'timestamp with time zone': 'string',
                           'time':'timestamp',
                           'timestamp':'timestamp',
                           'timestampwithtimezone':'timestamp',
                           }

        self.num_match_type = {
                           'integer': 'bigint',
                           'number': 'bigint',
                           'nuber': 'bigint',
                           'numeric': 'bigint',
                           'decimal': 'decimal',
                           'smallint': 'bigint'
                           }
    def get_config_file_source(self):
        # 读取配置文件
        basefilename = "e://files/types.xlsx"
        print("get_interface_index_source 打开" + basefilename)
        data = xlrd.open_workbook(basefilename)
        # 通过索引获取，例如打开第一个sheet表格
        #table = data.sheet_by_name("接口目录")
        table = data.sheet_by_index(0)
        allrows = 0
        types=set()
        col_dict={}
        all_type=[]
        if data.sheet_loaded(0):  # 检查某个sheet是否导入完毕
            allrows = table.nrows  # 获取该sheet中的有效行数
            for rowindex in range(1, allrows):
                cells = table.row_values(rowindex)
                #print(cells)
                type_name = cells[0].strip().lower()
                #print(type_name) 替换中文的括号,替换掉空括号
                type_name=type_name.replace('（','(').replace('）',')').replace('()','').replace("，",",")
                if not type_name or type_name=='none':
                    #print("replace 替换之后的 type_name="+type_name)
                    continue
                ##开始处理各个字段类型的映射关系以及位数更正
                if type_name.startswith("character varying"):
                    # print("type_name= character varying")
                    all_type.append(type_name)
                elif type_name.startswith("timestamp"):
                    all_type.append(type_name)
                else:
                    #type_name = re.sub(",\(", "(", type_name)
                    #print("type_name ="+type_name)
                    type_name=type_name.replace(" ","")
                    all_type.append(type_name)
                ##看数据项格式是否是含有括号的格式 如 varchar(20)
                first = type_name.find("(")
                pre_str=''
                name=''
                if first != -1:
                    name = type_name[0:first]
                    pre_str=name
                else :
                    #print ("old 分割之前 "+type_name)
                    #splits = re.split('\d', name, 1)
                    #print(splits)
                    all_num = re.findall("\d+",type_name)
                    arrlen=len(all_num)
                    ##这里导致了一个bug ,把 decimal15,2 数字替换成空，多了个，
                    findArr = re.split(r"\d",type_name,1)
                    pre_str=findArr[0]
                    if arrlen==2:
                        ##替换掉char5 这种格式，可能是excel写错了的 decimal15,处理得到 decimal(15)
                        #print("pre decimal="+pre_str)
                        name=pre_str+"("+all_num[0]+","+all_num[1]+")"
                    elif arrlen == 1:
                        name=pre_str+"("+all_num[0]+")"
                    elif arrlen>2:
                        print("应该没有这种情况的出现 all_num >3 ")
                    else :
                        name=type_name
                    ##把重新拼接好的值赋值给原有的type_name
                    #print(" 拼接前 type_name1="+type_name)
                    type_name=name
                    #print(" 拼接后 type_name="+type_name)
                #print(" sub pre_str = "+pre_str)
                #if not pre_str:
                 #   pre_str=name
                    #print('not prestr ='+pre_str)
                ##开始建立数据项的一一映射关系
                if pre_str=="time" or pre_str.startswith("timestamp"):
                    col_dict[type_name]="string"
                    #print( "match pre_str %s, %s, => %s" %(pre_str,type_name,"string"))
                ##处理 varchar这样的数据类型的映射关系
                elif pre_str in self.match_type:
                    #col_dict.
                    newpre=self.match_type.get(pre_str)

                    type_name=str(type_name).replace(pre_str,newpre)
                    #print( "match pre_str %s, %s, => %s" %(pre_str,name,type_name))
                    col_dict[pre_str]=type_name
                ##处理 numric(5) numric(6,2)这种数据格式
                elif pre_str in self.num_match_type:
                    #todo
                    # if pre_str =='decimal':
                    #     #data_type=type_name.replace()
                    #     data='decimal'
                    # else :
                    decimal = re.search("\d+\,", type_name)
                    #print("type_name="+str(decimal))

                        # print(decimal)
                    if pre_str.startswith("decimal"):
                        print('pre_str =%s typename=%s'%(pre_str,type_name))
                        if type_name =='decimal(17)':
                            newname='varchar(17)'
                        else :
                            #newname = re.sub('\)', ',2)', type_name)
                            newname = "decimal(20,2)"
                        data_type=newname
                    elif decimal:
                        data_type = type_name.replace(pre_str, "decimal")
                    else:
                        data_type = "bigint"

                    #print( "num match %s，%s => %s" %(pre_str,type_name,data_type))
                    #data_type=re.sub(',\(','(',data_type)
                    col_dict[type_name]=data_type

                else :
                    #print("type_name2="+type_name)
                    col_dict[pre_str]=type_name
                    types.add(pre_str)

        for key,value in col_dict.items():
            print(key+" = "+value)
        #print(all_type)

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
    print(re.split("\d+", "decimal", 1))
    #print(re.findall("\D+", "2344"))
    aotu = colType()
    aotu.main()
    # print(re.findall("([a-z]+)(\,)","hello,(234,23)"))
    # print(re.sub(",\(","(","hello,(234,23)"))
    # print(re.sub(",\(","(","hello ,"))
