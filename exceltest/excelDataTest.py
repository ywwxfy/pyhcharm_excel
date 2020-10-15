# -*- coding:utf-8 -*
import datetime

import xlrd as xlrd
import xlwt
import datetime
from datetime import date,datetime

file="d://test3.xlsx"

def read_excel():

        wb=xlrd.open_workbook(filename=file)#打开文件
        print(wb.sheet_names())#获取所有表格名字
        print(wb.sheet_names().__len__())
        sheet1=wb.sheet_by_index(0)#通过索引获取表格
        sheet2=wb.sheet_by_index(1)#通过索引获取表格
        #sheet2=wb.sheet_by_name('年级')#通过名字获取表格
        print(sheet1,sheet2)
        print(sheet1.name,sheet1.nrows,sheet1.ncols)
        ## 读取Excel中单元格的内容返回的有5种类型，即上面例子中的ctype ctype :  0 empty，1 string，2 number， 3 date，4 boolean，5 error
        print(sheet1.cell(1,2).ctype)
        date_value = xlrd.xldate_as_tuple(sheet1.cell_value(1, 2), wb.datemode)
        print(date_value)
        print(date(*date_value[:3]))##date 转化为日期形式
        print(date(*date_value[:3]).strftime("%Y/%m/%d"))
        rows1=sheet1.row_values(1)#获取行内容,行号从0开始
        rows=sheet1.row_values(2)#获取行内容
        rows3=sheet1.row_values(3)#获取行内容
        print(rows1)
        print(rows3)
        cols=sheet1.col_values(3)#获取列内容
        print(rows)
        print(cols)

        print(sheet1.cell(1,0).value)#获取表格里的内容，三种方式
        print(sheet1.cell_value(1,0))
        print(sheet1.row(1)[0].value)
        ##merged_cells()用法，merged_cells返回的这四个参数的含义是：(row,row_range,col,col_range),其中[row,row_range)
        # 包括row,不包括row_range,col也是一样，即(1, 3, 4, 5)的含义是：
        # 第1到2行（不包括3）合并，(7, 8, 2, 5)的含义是：第2到4列合并。
        print('--------------')
        print(sheet1.merged_cells)
        print(sheet1.cell_value(2, 3))
        print(sheet1.cell_value(5, 1))
        print(sheet1.cell_value(4, 3))
        ###批量获取合并单元格的数据
        merge = []
        print(sheet1.merged_cells)
        for (rlow, rhigh, clow, chigh) in sheet1.merged_cells:
                merge.append([rlow, clow])
        for index in merge:
                print(sheet1.cell_value(index[0], index[1]))
        wb.close()



if __name__ == '__main__'  :
        read_excel()