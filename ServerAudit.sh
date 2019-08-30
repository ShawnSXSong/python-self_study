#!/bin/bash
#Author: SE

db_sid=""
db_user=""
#db_passwd=""
db_port=""

MAIL=$(which mailx)
LogName="Authority_check_list-$(date +%Y-%m-%d)"
content="Dear All:\n \tPls check the list. Thx\n \tP.S. According to the audit requirements, the administrator account can only be personal account, please check. Thx"
temp=$(mktemp /tmp/log/temp.XXXXXX)
receivers=$(mktemp /tmp/log/receivers.XXXXXX)
receiver=$(mktemp /tmp/log/receiver.XXXXXX)
date=$(date +%Y_%m)

##1. get APowner
psql -d $db_sid -U $db_user -p $db_port <<EOF > $receivers
select distinct(u.mail)
from dbo.userinfotable u,dbo.serverinfotable s,dbo.localadmintable l
where upper(u.uid)=upper(s.pic_user) and upper(s.hostname)=upper(l.server_name);
EOF
receiverLists=$(grep @ $receivers)
##2. Send mail
for j in $receiverLists
do
#2.1 get APowner check list for personal
psql -d $db_sid -U $db_user -p $db_port <<EOF > $temp
select a.*,u.mail
from (
        select m.profileHostname Hostname,m.OS,m.ServerFunction,m.DB_SID,m.DB_Schema,m.DBA_Schema,n.account administrator_account,m.APOwner,m.IP,m.CheckTime
        from (
                select distinct(s.hostname) profileHostname,l.server_name actualHostname,s.os OS,s.server_function ServerFunction,l.db_sid DB_SID,l.db_schema DB_Schema,l.dba_schema DBA_Schema,s.pic_user APOwner,l.server_ips IP,l.data_inserted_time CheckTime
                from dbo.localadmintable l
                inner join dbo.serverinfotable s
                on upper(s.hostname)=upper(l.server_name)) m
        inner join (
                select server_name,string_agg(account_name,';') account
                from dbo.localadmintable
                group by server_name
                order by server_name) n
        on upper(m.profileHostname)=upper(n.server_name)) a,dbo.userinfotable u
where u.uid=a.APOwner and u.mail='$j';
\q
EOF
#2.2 get APowner & relate manager
cat /dev/null > $receiver
for i in uman mail
do
psql -d $db_sid -U $db_user -p $db_port <<EOF >> $receiver
select distinct(u.$i)
from dbo.userinfotable u,dbo.serverinfotable s,dbo.localadmintable l
where upper(u.uid)=upper(s.pic_user) and upper(s.hostname)=upper(l.server_name) and  u.mail='$j';
EOF
done
#2.3 send mail
sed -i '/rows/d' $temp
sed -i '/+/d' $temp
gawk 'BEGIN{FS="|"; OFS=","} {print $1,$2,$3,$4,$5,$6,$7,$8,$9,$10}' $temp > /tmp/log/$LogName\.csv
receiverList=$(grep @ $receiver)
content="Dear AP/DB Owner:\n \tPls check the list. Thx\n \tP.S. According to the audit requirements, the administrator account in AP Server can only be personal account, please check. Thx"
echo -e $content | $MAIL -s "AP/DB Server管理员权限清查_$date" -a /tmp/log/$LogName\.csv $receiverList xxxx@xxx.com
#echo -e $content receiverlist:$receiverList | $MAIL -s "AP/DB Server管理员权限清查_$date" -a /tmp/log/$LogName\.csv "xxxx@xxx.com xxxx@xxx.com"
done
#3. remove temporary file
rm $temp
rm $receivers
rm $receiver
rm /tmp/log/Authority*
