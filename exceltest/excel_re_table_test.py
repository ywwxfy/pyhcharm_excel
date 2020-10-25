# -*- coding:utf-8 -*
import datetime

import xlrd as xlrd
import xlwt
import datetime
from datetime import date, datetime
import re
import sys

file = "d://test3.xlsx"


class AotuGenerate:

    def read_excel(self):

        wb = xlrd.open_workbook(filename=file)  # 打开文件
        print(wb.sheet_names())  # 获取所有表格名字
        print(wb.sheet_names().__len__())

        wb.close()

    def read_ddl_text(self, filename):

        sql = """
                        create table t0311_rpt_bill_m (
                        user_id SERIAL, ----自增序列
                        acct_month varchar(6),
                        test_num character varying(6),
                        bill_fee numeric(16,2) ,
                        user_info text 
                )
                WITH (
                Aappendonly=true, -- 对于压缩表跟列存储来说，前提必须是appendonly表
                
                orientation=column,-- 列存 row
                
                compresstype=zlib,-- 压缩格式 --QUICKLZ
                
                COMPRESSLEVEL=5, -- 压缩等级 0--9 一般为5足够 压缩表占用存储空间小，读磁盘操作少，查询速度快
                
                OIDS=FALSE
                
                );
                alter table t0311_rpt_bill_m2 partition();
                ;test ewew 
                create table t0311_rpt_bill_m2 (

                        user_id SERIAL, ----自增序列
                        
                        acct_month varchar(6),
                        test_num character varying(6),
                        
                        bill_fee numeric(16,2) ,
                        
                        user_info text 

                )
                with excel;
                alter table t0311_rpt_bill_m2 partition();
                create table t0311_rpt_bill_m3 partition(data_date)(
                 acct_month varchar(6),
                        test_num character varying(6),
                        
                        bill_fee numeric(16,2) ,
                        
                        user_info text 
                        )
                """
        # res = re.findall('CREATE TABLE [\s\S][^;]*', sql,re.I)
        # sql='abc(dda)dcd)'
        # res = re.findall('CREATE TABLE [\s\S][^;][(](.*)+[)]', sql, re.I|re.M)
        res = re.findall('CREATE TABLE [\s\S]+[(].*[)$]', sql, re.I|re.M)
        res = re.findall(r'CREATE TABLE [\s\S]+(.*)[\s\S]+(.*)', sql, re.I|re.M)
        res = re.findall(r'CREATE TABLE [\s\S]+(\w*\.*\w*[\@]?[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\w*)', sql, re.I|re.M)

        # source_tables = re.findall(
        #     '''[\s\n\r\t]+from[\s\n\r\t\\\\]+(\w*\.*\w*[\@]?[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\w*)''',
        #     job_task_content_ori[i][3], re.I)

        res = re.findall(r'CREATE TABLE [\s\n\r\t]+(\w*.*\w*)', sql, re.I)
        '''
            1 ‘*’ 匹配0个或者多个，\s代表 任意空白字符
        '''
        res = re.findall(r'CREATE TABLE [\s]*(\w*)(.*)', sql, re.I)
        # res = re.findall(r'TABLE [\s\n\r\t]+(\w*)', sql, re.I)
        # res = re.findall('[(](.*)[)]', sql, re.I)
        for ele in res:
            print(ele)
            # splits = ele.strip().split('\n')
            # print(f'解析到的行数 lines={len(splits)}')
            # self.match_create_table_cols(splits)
        # print(res)

    def match_create_table_cols(self, splits):
        arr_len = len(splits)
        if arr_len > 0:
            first_line = splits[0]
            table_lines = first_line.split(' ')
            if len(table_lines) > 1:
                hive_table = table_lines[2]
            else:
                hive_table = ''
                print('解析hive_table　出问题')
            print(hive_table)
        for index in range(1, arr_len):
            arr = splits[index]
            val = arr.strip()
            if val:
                if val == ')':
                    print(f' continue {val}')
                    break
                cols = val.replace(',', '').split(' ', 1)
                print(cols)

    def readtextfile(self,filename):
        # f = open(filename, 'r',encoding='utf-8')
        # line = f.readline()
        # while line:
        #     print(line.strip())
        #     line = f.readline()
        #
        # f.close()
        with open(filename,'r',encoding='utf-8') as f :
            line = f.readline()
            while line :
                print(line.strip())
                line=f.readline()

    def test_re(self):

        string = 'abe(ac)ad)'
        # p1 = re.compile(r'[(](.*?)[)]', re.S)  # 最小匹配
        p1 = re.compile(r'[(](.*?)[)]', re.I)  # 最小匹配
        p2 = re.compile(r'[(](.*)[)]', re.I)  # 贪婪匹配
        print(re.findall(p1, string))
        print(re.findall(p2, string))


if __name__ == '__main__':
    auto = AotuGenerate()
    auto.read_ddl_text('test')
    # auto.test_re()
    # auto.readtextfile("d://sql_ddl.txt")
