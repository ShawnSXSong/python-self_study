#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import paramiko
import datetime

db_user   =''
db_passwd =''
db_port   =''
db_ip     =''
db_sid    =''

insert_time             = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
command_getHostNUser    = """hostname;cat /etc/passwd|grep home|gawk 'BEGIN{FS=":"} {print $1}'"""
command_getSID          = """ps -ef|grep smon|gawk 'BEGIN{FS="_"}{print $3}'"""
sql_getIP               = """select server_ips from dbo.localadmintable where remark='DB';"""
sql_DBA_check           = """select grantee from sys.dba_role_privs where granted_role='DBA' AND GRANTEE NOT IN ('DBSNMP','SYSTEM','SYSMAN','SYS');"""
sql_schema_check        = """
set linesize 500
set pagesize 500
select username
from dba_users
where account_status='OPEN' and initial_rsrc_consumer_group Not LIKE 'SYS_GROUP' and username NOT LIKE 'PERFSTAT' and username NOT LIKE 'TIBCOEAI' and default_tablespace NOT LIKE 'SYSAUX';
"""

conn        = psycopg2.connect(database=db_sid, user=db_user, password=db_passwd, host=db_ip, port=db_port)
cur         = conn.cursor()
cur.execute(sql_getIP)
results     = cur.fetchall()
for ip in range(len(results)):
    index   = int(ip)
    ip      = str(results[int(index)][0])
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=ip, username='oracle', password='0rac!e', allow_agent=False)
        stdin, stdout, stderr = client.exec_command(command_getHostNUser)
        result = stdout.read().decode('utf-8').rstrip("\n").split()
        server_hostname = result.pop(0)
        for i in ['oprofile','oracle','opc_op']:
                if result.count(i)==1:
                        result.remove(i)
        server_user = ';'.join(result)
        stdin1, stdout1, stderr1 = client.exec_command(command_getSID)
        temp        = stdout1.read().decode('utf-8').rstrip("\n").split()
        schema      = []
        dba_schema  = []
        for t in temp:
            oracle_exports          = 'export ORACLE_SID={0}'.format(t)
            check_schema_command    = """source ~/.bash_profile;{0};echo "{1}" | sqlplus -S / as sysdba|sed -e '/rows/d' -e '/+/d'""".format(oracle_exports, sql_schema_check)
            check_DBA_command       = """source ~/.bash_profile;{0};echo "{1}" | sqlplus -S / as sysdba|sed -e '/rows/d' -e '/+/d'""".format(oracle_exports, sql_DBA_check)
            stdin2, stdout2, stderr2 = client.exec_command(check_schema_command)
            stdin3, stdout3, stderr3 = client.exec_command(check_DBA_command)
            schema_info     = stdout2.read().decode('utf-8').rstrip("\n").split()
            DBA_info        = stdout3.read().decode('utf-8').rstrip("\n").split()
            schema_info.pop(0)
            schema_info.pop(0)
            if DBA_info:
                DBA_info.pop(0)
                DBA_info.pop(0)
            else:
                DBA_info.append("None")
            schema_info = ';'.join(schema_info)
            DBA_info    = ';'.join(DBA_info)
            schema.append(str(schema_info))
            dba_schema.append(str(DBA_info))
        schema      = ' / '.join(schema)
        dba_schema  = ' / '.join(dba_schema)
        db_sid      = ' / '.join(temp)
        sql_update  = "update dbo.localadmintable set server_name='{0}', data_inserted_time='{2}', account_name='{3}', db_sid='{4}', db_schema='{5}', dba_schema='{6}' where server_ips='{1}';".format(server_hostname, ip, insert_time, server_user, db_sid, schema, dba_schema)
        cur.execute(sql_update)
        conn.commit()
        client.close()
    except Exception as e:
        print(str(e))
        client.close()
conn.commit()
cur.close()
conn.close()
