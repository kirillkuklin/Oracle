import math, paramiko, time, os
from sys import argv
from testargv import getopts

res = {}
db = {}
oralst = list()
newlist = list()

#<editor-fold desc="Establishing connection">
ip = getopts(argv)['-ip']
username = getopts(argv)['-username']
password = getopts(argv)['-password']
outfile = getopts(argv).get('-outfile') or os.getcwd() + '\\' + 'ArchiveLogSelect.log'

# Create instance of SSHClient object
remote_conn_pre = paramiko.SSHClient()

# Automatically add untrusted hosts
remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# initiate SSH connection
remote_conn_pre.connect(ip, username=username, password=password, look_for_keys=False, allow_agent=False)

# Use invoke_shell to establish an 'interactive session'
remote_conn = remote_conn_pre.invoke_shell()
#</editor-fold>


def oratab():
    remote_conn.send("cat /etc/oratab\n")
    time.sleep(1)
    output = remote_conn.recv(5000)
    oratabfile = output.decode("utf-8")
    for i in oratabfile.splitlines():
        if not i.startswith('#') and not i.startswith('['):
            splitted_line = i.rstrip().split()
            if len(splitted_line) > 0 and 'cat' not in splitted_line and 'Last' not in splitted_line:
                yield splitted_line
for i in oratab():
    oralst.append(i[0].encode())
    # db['oratab'] = oralst
for i in oralst:
    newlist.append(i.split(':')[0])


def get_arcs(n):
        remote_conn.send("export ORACLE_SID=" + newlist[n] + "\n")
        time.sleep(1)
        remote_conn.send("echo $ORACLE_SID\n")
        time.sleep(1)
        remote_conn.send("sqlplus / as sysdba\n")
        time.sleep(1)
        remote_conn.send("set linesize 3000\nSELECT FIRST_CHANGE#, BLOCK_SIZE, RECID, STAMP, NAME,THREAD#, SEQUENCE#, RESETLOGS_CHANGE#, BLOCKS*BLOCK_SIZE,TO_CHAR(SYS_EXTRACT_UTC(CAST(FIRST_TIME AS TIMESTAMP)), 'yyyy/mm/dd hh24:mi:ss'), TO_CHAR(SYS_EXTRACT_UTC(CAST(NEXT_TIME AS TIMESTAMP)), 'yyyy/mm/dd hh24:mi:ss') FROM V$ARCHIVED_LOG WHERE STATUS != 'D' AND CREATOR != 'LGWR';\n")
        time.sleep(3)
        remote_conn.send("SELECT OPEN_MODE, LOG_MODE FROM V$DATABASE;\n")
        time.sleep(1)
        output = remote_conn.recv(2000000)
        sqlplus = output.decode("utf-8")
        lines = sqlplus.splitlines(True)
        rng = range(0, len(lines))
        f = open(outfile, 'a')
        for i in rng:
            if lines[i].strip().find('echo $ORACLE_SID') != -1:
                print >> f, ' '
                print >> f, lines[i+1].strip()
                print >> f, ' '
            if lines[i].strip().find('SELECT') == 0:
                for i in lines[i+1:]:
                    if len(i.strip()) > 0 and i.strip()[0].isnumeric():
                        print >> f, (', '.join(list(i.encode() for i in i.strip().split())))
                    yield i.strip()
        remote_conn.send("exit\n")
        time.sleep(1)


def convert_size(size_bytes):
   if (size_bytes == 0):
       return '0B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes/p, 2)
   return '%s %s' % (s, size_name[i])

dbs = range(0, len(newlist))
for i in dbs:
    lst = list()
    for line in get_arcs(i):
        if 'ARCHIVELOG'in line.split() or 'NOARCHIVELOG' in line.split():
            basestatus = line.split()[-1]
        if len(line.split()) == 13:
            lst.append(int(line.split()[-5]))
    if basestatus == 'NOARCHIVELOG' and convert_size(sum(lst)) == '0B':
        print 'The size of %s archived logs is %s because it is in %s mode' % (newlist[i], convert_size(sum(lst)), basestatus)
    else:
        print 'The size of %s archived logs is %s and it is in %s mode' % (newlist[i], convert_size(sum(lst)), basestatus)

