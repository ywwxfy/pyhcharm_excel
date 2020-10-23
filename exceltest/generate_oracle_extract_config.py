#!/data03/apps/python2715/bin/python
# -*- coding:utf-8 -*-

from optparse import OptionParser
import logging
import sys
import traceback
import getopt
import random
import re
import pymysql
import sys
sys.path.append("/data02/dcadmin/scripts/common")
# from connect_postgresql import postgresql_connect
# from connect_mysql import mysql_connect
# from connect_oracle import oracle_connect
# reload(sys)
sys.setdefaultencoding('utf-8')

job_task_content_ori=[]
job_task_content_final=[]
job_resource_conn_info=[]
job_hdfs_dir_info=[]

# pg_conn_factory_new=postgresql_connect("asset_factory")
# pg_conn_register_new=postgresql_connect("asset_register")
# mysql_conn_new=mysql_connect("10.251.80.186")
# oracle_conn=oracle_connect('10.183.2.42')

def generate_resource_hdfsdir_info():
	global job_task_content_final;
	#print(job_task_content_final)
	where_cond=''
	resource_connect_id=''
	hdfs_dir_id=''
	cnt=0
        for i in range(0,len(job_task_content_ori)):
		#print(job_task_content_ori[i])
		cnt+=1
		#print(cnt)
		#print(job_task_content_ori[i])
		where_cond=''
		resource_connect_id=job_task_content_ori[i][2]
		hdfs_dir_id=job_task_content_ori[i][4]
		#print(job_task_content_ori[i][1])
		wheres=re.findall('''(.*)[\s\n\r\t]+where[\s\n\r\t\\\\]+([\s\S]+)(union)*''',job_task_content_ori[i][3],re.I|re.S)
		for where in wheres:
			where_cond=where[1]
			#print("where_cond="+where_cond)
		#source_tables=re.findall('''[\s\n\r\t]+from[\s\n\r\t\\\\]+(\w*\.*\w*)''',job_task_content_ori[i][3],re.I)
		#modify by denghy 20190315 
		#source_tables=re.findall('''[\s\n\r\t]+from[\s\n\r\t\\\\]+(\w*\.*\w*[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\w*)''',job_task_content_ori[i][3],re.I)
		source_tables=re.findall('''[\s\n\r\t]+from[\s\n\r\t\\\\]+(\w*\.*\w*[\@]?[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\w*)''',job_task_content_ori[i][3],re.I)
##添加支持按天分区查询表参数${dd} 比如 partition (D_${dd}) by denghy 20181218
		#partitions=re.findall('''[\s\n\r\t]+partition[\s\n\r\t\\\\]+(\W*\w*\.*[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\W*)''',job_task_content_ori[i][3],re.I)
		partitions=re.findall('''[\s\n\r\t]+partition[\s]*(\W+\w*\.*[\$]*[\{]*\w*[\_]*[+]*\w*[\}]*\W*)''',job_task_content_ori[i][3],re.I)
		p_names=''
		if len(partitions) >0 :
			print ('partition',partitions)
			#if partitions[0].upper().find('(') >=0 and partitions[0].upper().find(')')>=0:
                        p_names=partitions
			
		for source_table in source_tables:
			#print(source_table)
			tmp_task_content={}
###job_id -->seq
			tmp_task_content['seq']=job_task_content_ori[i][0]
###job_name -->interface
			tmp_task_content['interface']=job_task_content_ori[i][1]
###source_table_name -->ora_t
###source_table_name -->ora_u
			tmp_task_content['ora_u']=''
			tmp_task_content['ora_t']=source_table
			if p_names:
				print (source_table+' partition '+p_names[0])
				tmp_task_content['ora_t']=source_table+' partition '+p_names[0]
				
###resource_connect_id
			tmp_task_content['resource_connect_id']=resource_connect_id
###source_where_condition -->ora_cond
			tmp_task_content['ora_cond']=where_cond
###hdfs_dir_id
			tmp_task_content['hdfs_dir_id']=hdfs_dir_id

			tmp_task_content['db_type']=job_task_content_ori[i][5]

			job_task_content_final.append(tmp_task_content)
	#print(len(job_task_content_final))
        #for i in range(0,len(job_task_content_final)):
                #print(job_task_content_final[i])
        #print(len(job_task_content_final))





	

def insert_final_data():
	sql="delete from generate_all_jobs"
	# oracle_sql_exec(sql,'delete')
	cnt=0
	for i in range(0,len(job_task_content_final)):
		cnt+=1
		print(cnt)
		print(job_task_content_final[i])
		sql="insert into generate_all_jobs(SEQ,TNS_TAG,ORA_U,ORA_T,ORA_COND,HIVE_U,HIVE_T,INTERFACE,HIVE_COND,TABLE_COL,db_type) select %s,'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s' from dual "%(job_task_content_final[i]['seq'],job_task_content_final[i]['tns_tag'],job_task_content_final[i]['ora_u'],job_task_content_final[i]['ora_t'],job_task_content_final[i]['ora_cond'].replace("'","''").decode('gbk').encode('gbk'),job_task_content_final[i]['hive_u'],job_task_content_final[i]['hive_t'],job_task_content_final[i]['interface'],job_task_content_final[i]['hive_cond'],job_task_content_final[i]['table_col'],job_task_content_final[i]['db_type'])
		# oracle_sql_exec(sql,'finalinsert')




if __name__ =="__main__":
	in_day=''
	try:
                opts, args = getopt.getopt(sys.argv[1:], "hd:", ["help", "day="])   # sys.argv[1:] 过滤掉第一个参数(它是脚本名称，不是参数的一部分)
        except getopt.GetoptError:
                print("argv error,please input")

        for cmd, arg in opts:  # 使用一个循环，每次从opts中取出一个两元组，赋给两个变量。cmd保存选项参数，arg为附加参数。接着对取出的选项参数进行处理。
                if cmd in ("-h", "--help"):
                        print("help info")
                        sys.exit()
                elif cmd in ("-d", "--day"):
                        in_day=arg
	print(in_day)
	if not in_day:
		print("输入日期错误！正确格式如下：generate_oracle_extract_config.py -d 9999")
		sys.exit(1)

	sql='''
select cast(b.job_id as integer),b.job_name,(a.task_content::json ->>'oracle_extract')::json ->>'resourceConnId',(a.task_content::json ->>'oracle_extract')::json ->>'extractSql',(a.task_content::json ->>'oracle_extract')::json ->>'dirId' ,'oracle' from td_factory_task a ,td_factory_job b,td_schedule c  where upper(a_com_id)='ORACLE_EXTRACT'  and a.job_id=b.job_id  
and (upper(b.job_name) like 'INT%%' or upper(b.job_name) like 'DIM%%') and b.run_env_type=2 /* and c.run_status not in (-3,-4) */  
and b.schedule_id=c.schedule_id /*and job_name='INT_ACT_BIL_ACCOUNT_V3_0841'  */ and job_name not in ('INT_EVT_CRM_P_CRM_FOR_SA_B','INT_EVT_CRM_P_CRM_FOR_SA_EXP_B','INT_EVT_CRM_P_BSS_ORDER_B','INT_EVT_CRM_P_BSS_ORDER','INT_EVT_CRM_P_CRM_FOR_SA_EXP_A','INT_EVT_CRM_P_CRM_FOR_SA') and (b.job_create_time>now()::timestamp + '-%d day' or b.job_modify_time >now()::timestamp + '-%d day')
union all 
select cast(b.job_id as integer),b.job_name,(a.task_content::json ->>'mysql_extract')::json ->>'resourceConnId',(a.task_content::json ->>'mysql_extract')::json ->>'extractSql',(a.task_content::json ->>'mysql_extract')::json ->>'dirId' ,'mysql' from td_factory_task a ,td_factory_job b,td_schedule c  where upper(a_com_id)='MYSQL_EXTRACT' and a.job_id=b.job_id 
and (upper(b.job_name) like 'INT%%' or upper(b.job_name) like 'DIM%%') and b.run_env_type=2 /* and c.run_status not in (-3,-4) */
and b.schedule_id=c.schedule_id /*and job_name='INT_ACT_BIL_ACCOUNT_V3_0841'  */ and job_name not in ('INT_EVT_CRM_P_CRM_FOR_SA_B','INT_EVT_CRM_P_CRM_FOR_SA_EXP_B','INT_EVT_CRM_P_BSS_ORDER_B','INT_EVT_CRM_P_BSS_ORDER','INT_EVT_CRM_P_CRM_FOR_SA_EXP_A','INT_EVT_CRM_P_CRM_FOR_SA') and (b.job_create_time>now()::timestamp + '-%d day' or b.job_modify_time >now()::timestamp + '-%d day')
 '''%(int(in_day),int(in_day),int(in_day),int(in_day))
	if int(in_day) > 50 :
            sql='''
        	select cast(b.job_id as integer),b.job_name,(a.task_content::json ->>'oracle_extract')::json ->>'resourceConnId',(a.task_content::json ->>'oracle_extract')::json ->>'extractSql',(a.task_content::json ->>'oracle_extract')::json ->>'dirId' ,'oracle' from td_factory_task a ,td_factory_job b,td_schedule c  where upper(a_com_id)='ORACLE_EXTRACT'  and a.job_id=b.job_id 
and (upper(b.job_name) like 'INT%%' or upper(b.job_name) like 'DIM%%') and b.run_env_type=2 /* and c.run_status not in (-3,-4) */
and b.schedule_id=c.schedule_id and job_name not in ('INT_EVT_CRM_P_CRM_FOR_SA_B','INT_EVT_CRM_P_CRM_FOR_SA_EXP_B','INT_EVT_CRM_P_BSS_ORDER_B','INT_EVT_CRM_P_BSS_ORDER','INT_EVT_CRM_P_CRM_FOR_SA_EXP_A','INT_EVT_CRM_P_CRM_FOR_SA') 
union all
select cast(b.job_id as integer),b.job_name,(a.task_content::json ->>'mysql_extract')::json ->>'resourceConnId',(a.task_content::json ->>'mysql_extract')::json ->>'extractSql',(a.task_content::json ->>'mysql_extract')::json ->>'dirId' ,'mysql' from td_factory_task a ,td_factory_job b,td_schedule c  where upper(a_com_id)='MYSQL_EXTRACT'  and a.job_id=b.job_id
and (upper(b.job_name) like 'INT%%' or upper(b.job_name) like 'DIM%%') and b.run_env_type=2 /* and c.run_status not in (-3,-4) */
and b.schedule_id=c.schedule_id and job_name not in ('INT_EVT_CRM_P_CRM_FOR_SA_B','INT_EVT_CRM_P_CRM_FOR_SA_EXP_B','INT_EVT_CRM_P_BSS_ORDER_B','INT_EVT_CRM_P_BSS_ORDER','INT_EVT_CRM_P_CRM_FOR_SA_EXP_A','INT_EVT_CRM_P_CRM_FOR_SA')
        '''
	#print(sql)
	generate_resource_hdfsdir_info()
	print("----------------------------------------get conn")

	##partitions
	#get_partition_info()
	print("----------------------------------------get col")
	get_column_info()
	print("-----------------------------------------insert final")
	insert_final_data()

	# oracle_proc_exec('generate_all_jobs_proc')
