import math, paramiko, time, os
from sys import argv
from testargv import getopts
lst = list()
res = {}

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


def get_arcs():
    remote_conn.send("echo $ORACLE_SID\n")
    time.sleep(1)
    remote_conn.send("sqlplus / as sysdba\n")
    time.sleep(2)
    remote_conn.send("set linesize 3000\nSELECT FIRST_CHANGE#, BLOCK_SIZE, RECID, STAMP, NAME,THREAD#, SEQUENCE#, RESETLOGS_CHANGE#, BLOCKS*BLOCK_SIZE,TO_CHAR(SYS_EXTRACT_UTC(CAST(FIRST_TIME AS TIMESTAMP)), 'yyyy/mm/dd hh24:mi:ss'), TO_CHAR(SYS_EXTRACT_UTC(CAST(NEXT_TIME AS TIMESTAMP)), 'yyyy/mm/dd hh24:mi:ss') FROM V$ARCHIVED_LOG WHERE STATUS != 'D' AND CREATOR != 'LGWR';\n")
    time.sleep(4)
    output = remote_conn.recv(200000)
    sqlplus = output.decode("utf-8")
    lines = sqlplus.splitlines(True)
    rng = range(0, len(lines))
    f = open(outfile, 'w')
    for i in rng:
        if not lines[i].startswith('[') and 'echo $ORACLE_SID' in lines[i].strip():
                sid = lines[i + 2]
        if lines[i].strip().find('SELECT') == 0:
            res = lines[i:]
            for i in res:
                print >> f, i.strip()
                yield i.strip(), sid.split()[0]


for line, sid in get_arcs():
    if len(line.split()) == 13:
        lst.append(int(line.split()[-5]))


def convert_size(size_bytes):
   if (size_bytes == 0):
       return '0B'
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes/p, 2)
   return '%s %s' % (s, size_name[i])
print 'The size of %s archived logs is %s' % (sid.encode(), convert_size(sum(lst)))

?
