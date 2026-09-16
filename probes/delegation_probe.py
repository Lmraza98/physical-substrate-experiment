import os,json,base64,urllib.parse,urllib.request,time

def oidc():
 print('=== OIDC_PROBE_BEGIN ===')
 u=os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL'); t=os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
 print('request_url_present=',bool(u),'request_token_present=',bool(t))
 if u and t:
  url=u+('&' if '?' in u else '?')+urllib.parse.urlencode({'audience':'physical-substrate-experiment'})
  req=urllib.request.Request(url,headers={'Authorization':'bearer '+t})
  with urllib.request.urlopen(req,timeout=15) as r: obj=json.load(r)
  p=obj['value'].split('.')[1]; p += '='*((4-len(p)%4)%4); claims=json.loads(base64.urlsafe_b64decode(p))
  safe={k:claims.get(k) for k in ['iss','aud','sub','repository','repository_owner','repository_id','ref','sha','workflow','job_workflow_ref','runner_environment','event_name','actor','exp','iat'] if k in claims}
  print(json.dumps(safe,sort_keys=True))
 print('=== OIDC_PROBE_END ===')

def ce_req(path,data=None):
 h={'Accept':'application/json','User-Agent':'physical-substrate-experiment/1.0'}
 if data is not None: h['Content-Type']='application/json'; data=json.dumps(data).encode()
 q=urllib.request.Request('https://godbolt.org'+path,data=data,headers=h)
 with urllib.request.urlopen(q,timeout=30) as r: return r.status,json.load(r)

def external():
 print('=== EXTERNAL_EXECUTION_SUBMISSION_BEGIN ==='); print('submit_unix_ns=',time.time_ns())
 status,cs=ce_req('/api/compilers/c++'); print('compiler_list_http=',status,'count=',len(cs))
 ids=[str(c.get('id','')) for c in cs if str(c.get('id','')).startswith('g')]
 ids=list(dict.fromkeys(reversed(ids)))[:40]
 source='''#include <iostream>\n#include <fstream>\n#include <string>\n#include <sys/utsname.h>\n#include <cpuid.h>\nstatic void file(const char*p){std::ifstream f(p);std::string s;if(f){std::cout<<"FILE "<<p<<" BEGIN\\n";int n=0;while(std::getline(f,s)&&n++<80)std::cout<<s<<"\\n";std::cout<<"FILE "<<p<<" END\\n";}}\nint main(){std::cout<<"PROBE_BEGIN\\n";struct utsname u{};if(uname(&u)==0)std::cout<<"uname="<<u.sysname<<" "<<u.nodename<<" "<<u.release<<" "<<u.version<<" "<<u.machine<<"\\n";unsigned a,b,c,d;if(__get_cpuid(1,&a,&b,&c,&d))std::cout<<"cpuid1_ecx=0x"<<std::hex<<c<<std::dec<<" hypervisor="<<((c>>31)&1)<<"\\n";file("/proc/cpuinfo");file("/proc/1/cgroup");file("/proc/sys/kernel/random/boot_id");file("/sys/devices/virtual/dmi/id/product_name");file("/sys/devices/virtual/dmi/id/sys_vendor");file("/proc/sys/kernel/perf_event_paranoid");std::cout<<"PROBE_END\\n";}'''
 payload={'source':source,'options':{'userArguments':'-O2','executeParameters':{'args':[],'stdin':'','runtimeTools':[]},'compilerOptions':{'executorRequest':True},'filters':{'execute':True},'tools':[],'libraries':[]},'lang':'c++','allowStoreCodeDebug':False,'bypassCache':2}
 for cid in ids:
  try:
   st,out=ce_req('/api/compiler/'+cid+'/compile',payload)
   text=json.dumps(out,sort_keys=True)
   if 'PROBE_BEGIN' in text:
    print('execution_http=',st,'compiler_id=',cid); print(text); break
  except Exception as e: print('candidate_failed=',cid,type(e).__name__)
 else: print('NO_EXECUTOR_ACCEPTED')
 print('=== EXTERNAL_EXECUTION_SUBMISSION_END ===')

if __name__=='__main__': oidc(); external()
