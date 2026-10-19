"""Root-only installer preserving the bind-mounted file inode and other vhosts."""
import os,sys,subprocess,re
from pathlib import Path
from datetime import datetime,timezone
def install(source, active, backup, run=subprocess.run):
 source=Path(source); content=source.read_text()
 if source.name not in ('nginx-crm.conf','nginx-crm-bootstrap.conf'): raise SystemExit('Unsupported config')
 if source.name=='nginx-crm.conf' and not Path('/etc/letsencrypt/live/service-system-crm/fullchain.pem').is_file(): raise SystemExit('Issue the CRM certificate first')
 active=Path(active)
 start='# BEGIN SERVICE SYSTEM CRM DOMAIN'; end='# END SERVICE SYSTEM CRM DOMAIN'
 old=active.read_text(); base=old
 if start in base:
  if base.count(start)!=1 or base.count(end)!=1: raise SystemExit('Invalid managed block')
  a=base.index(start); b=base.index(end)+len(end); base=base[:a]+base[b:]
 else:
  if any(name in ('crm.analitgaz.ru',) for names in re.findall(r'server_name\s+([^;]+);',base) for name in names.split()): raise SystemExit('CRM domain exists outside the managed block; inspect before proceeding')
 backup=Path(backup);backup.mkdir(mode=0o700,exist_ok=True);os.chmod(backup,0o700)
 name=backup/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.conf')
 fd=os.open(name,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
 with os.fdopen(fd,'w') as f:f.write(old)
 def write_in_place(value):
  with active.open('w') as f:f.write(value);f.flush();os.fsync(f.fileno())
 try:
  write_in_place(base.rstrip()+'\n\n'+start+'\n'+content+'\n'+end+'\n')
  run(['docker','exec','ss_frontend','nginx','-t'],check=True)
  run(['docker','exec','ss_frontend','nginx','-s','reload'],check=True)
 except BaseException:
  write_in_place(old)
  run(['docker','exec','ss_frontend','nginx','-t'],check=False)
  run(['docker','exec','ss_frontend','nginx','-s','reload'],check=False)
  raise
 print('CRM-domain block installed; other virtual hosts preserved. Backup:',name)

if __name__=='__main__':
 if os.geteuid()!=0: raise SystemExit('Run as root on the deployment server')
 if len(sys.argv)!=2: raise SystemExit('Specify a reviewed CRM config file')
 install(sys.argv[1],'/opt/service-system-v2/deploy/https/active.conf','/root/service-system-crm-nginx-backups')
