#!/usr/bin/env python3
"""FileDrop mini - LAN file receiver. python3 filedrop.py [-d DIR] [-p PORT]"""
import argparse, os, re, socket, sys, unicodedata
from datetime import datetime
try:
    from flask import Flask, Response, jsonify, request
except ImportError:
    sys.exit("Install Flask:  pip install flask")

DEFAULT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "FileDrop")
app = Flask(__name__)
UPLOAD_DIR = DEFAULT_DIR
BAD = re.compile(r'[\x00-\x1f\x7f<>:"/\\|?*]')

def safe_name(raw):
    raw = (raw or "").replace("\\", "/").split("/")[-1]
    raw = BAD.sub("_", unicodedata.normalize("NFC", raw)).strip().strip(".")
    if not raw or raw in {".", ".."}:
        raw = "upload.bin"
    if len(raw) > 200:
        s, e = os.path.splitext(raw); raw = s[:200 - len(e[:12])] + e[:12]
    return raw

def unique_path(d, name):
    p = os.path.join(d, name)
    if not os.path.exists(p): return p
    stem, ext = os.path.splitext(name); n = 1
    while os.path.exists(os.path.join(d, f"{stem} ({n}){ext}")): n += 1
    return os.path.join(d, f"{stem} ({n}){ext}")

def human(b):
    for u in ("B", "KB", "MB", "GB"):
        if b < 1024 or u == "GB": return f"{b:.0f} {u}" if u == "B" else f"{b:.1f} {u}"
        b /= 1024.0

def get_local_ips():
    ips = []
    # Primary IP via outbound connection trick
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    # All IPs via hostname resolution (works on Windows + Linux)
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except OSError:
        pass
    # Linux only: pick up extra interfaces (docker, vpn, etc.)
    if sys.platform != "win32":
        try:
            import fcntl, struct
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            for _, nm in socket.if_nameindex():
                if nm == "lo":
                    continue
                try:
                    a = fcntl.ioctl(s.fileno(), 0x8915, struct.pack("256s", nm[:15].encode()))[20:24]
                    ip = socket.inet_ntoa(a)
                    if ip not in ips:
                        ips.append(ip)
                except OSError:
                    pass
            s.close()
        except (ImportError, OSError):
            pass
    return ips

PAGE = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>FileDrop</title><style>
:root{--bg:#0c0f14;--pan:#141922;--ln:#28313f;--tx:#e6edf5;--mu:#8b98a9;--ac:#39d98a;--dn:#ff6b6b}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(900px 500px at 50% -10%,#16202c,var(--bg) 60%);
color:var(--tx);font:15px/1.5 system-ui,sans-serif;display:flex;flex-direction:column;align-items:center;padding:32px 16px}
h1{margin:0;font-size:26px}h1 span{color:var(--ac)}.sub{color:var(--mu);font-size:13px;margin:6px 0 24px;text-align:center}
.sub code{background:#1b2230;border:1px solid var(--ln);padding:2px 7px;border-radius:6px}
main{width:100%;max-width:640px}#drop{border:2px dashed var(--ln);border-radius:14px;background:var(--pan);padding:46px 20px;
text-align:center;cursor:pointer;transition:.15s}#drop.hot{border-color:var(--ac);background:#12241c}
#drop .i{font-size:38px;color:var(--ac)}#drop .b{font-size:17px;margin-top:12px;font-weight:600}
#drop .s{color:var(--mu);font-size:13px;margin-top:6px}.br{color:var(--ac);text-decoration:underline}
input{display:none}#list{margin-top:20px;display:flex;flex-direction:column;gap:10px}
.row{background:var(--pan);border:1px solid var(--ln);border-radius:11px;padding:12px 14px;display:grid;
grid-template-columns:1fr auto;gap:4px 12px}.name{font-size:14px;word-break:break-all}
.meta{color:var(--mu);font-size:12.5px;justify-self:end;white-space:nowrap}
.bar{grid-column:1/-1;height:5px;border-radius:99px;background:#1b2230;overflow:hidden;margin-top:6px}
.bar i{display:block;height:100%;width:0;background:var(--ac);transition:width .12s linear}
.row.done .meta{color:var(--ac)}.row.fail .meta{color:var(--dn)}.row.fail .bar i{background:var(--dn);width:100%!important}
#sum{margin-top:16px;text-align:center;color:var(--mu);font-size:13px}</style></head><body>
<h1>File<span>Drop</span></h1><div class="sub">Files land in <code>__DIR__</code> on the host</div>
<main><div id="drop" tabindex="0"><div class="i">&#8613;</div><div class="b">Drop files here</div>
<div class="s">or <span class="br">browse</span> &mdash; multiple files welcome</div></div>
<input type="file" id="pick" multiple><div id="list"></div><div id="sum"></div></main><script>
const d=document.getElementById('drop'),pk=document.getElementById('pick'),L=document.getElementById('list'),
SM=document.getElementById('sum');let q=[],busy=0,ok=0,bad=0;
const fmt=b=>{const u=['B','KB','MB','GB'];let i=0;while(b>=1024&&i<3){b/=1024;i++}return(i?b.toFixed(1):b.toFixed(0))+' '+u[i]};
d.onclick=()=>pk.click();d.onkeydown=e=>{if(e.key=='Enter'||e.key==' '){e.preventDefault();pk.click()}};
pk.onchange=()=>{add([...pk.files]);pk.value=''};
['dragenter','dragover'].forEach(e=>d.addEventListener(e,v=>{v.preventDefault();d.classList.add('hot')}));
['dragleave','drop'].forEach(e=>d.addEventListener(e,v=>{v.preventDefault();d.classList.remove('hot')}));
d.addEventListener('drop',e=>add([...e.dataTransfer.files]));
['dragover','drop'].forEach(e=>document.addEventListener(e,v=>v.preventDefault()));
function add(fs){fs.forEach(f=>{const r=document.createElement('div');r.className='row';
r.innerHTML='<div class="name"></div><div class="meta">queued</div><div class="bar"><i></i></div>';
r.querySelector('.name').textContent=f.name;L.prepend(r);q.push([f,r])});pump()}
function pump(){if(busy||!q.length){if(!busy&&!q.length)tally();return}busy=1;const[f,r]=q.shift();
const m=r.querySelector('.meta'),b=r.querySelector('.bar i'),fd=new FormData();fd.append('file',f,f.name);
const x=new XMLHttpRequest();x.open('POST','/upload');
x.upload.onprogress=e=>{if(e.lengthComputable){b.style.width=e.loaded/e.total*100+'%';m.textContent=fmt(e.loaded)+' / '+fmt(e.total)}};
const fin=(s,t)=>{r.classList.add(s?'done':'fail');if(s){b.style.width='100%';ok++}else bad++;m.textContent=t;busy=0;pump()};
x.onload=()=>{let j={};try{j=JSON.parse(x.responseText)}catch(e){}
x.status==200&&j.ok?fin(1,'saved as '+j.saved+' ✓'):fin(0,j.error||'failed ('+x.status+')')};
x.onerror=()=>fin(0,'connection lost');x.onabort=()=>fin(0,'aborted');x.send(fd)}
function tally(){const p=[];if(ok)p.push(ok+' received');if(bad)p.push(bad+' failed');SM.textContent=p.join(' · ')}
</script></body></html>"""

@app.get("/")
def index():
    return Response(PAGE.replace("__DIR__", UPLOAD_DIR), mimetype="text/html; charset=utf-8")

@app.post("/upload")
def upload():
    f = request.files.get("file")
    if f is None or not f.filename:
        return jsonify(ok=False, error="no file in request"), 400
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        dest = unique_path(UPLOAD_DIR, safe_name(f.filename))
        f.save(dest); size = os.path.getsize(dest)
    except OSError as e:
        return jsonify(ok=False, error=f"cannot write: {e.strerror}"), 500
    print(f"  [{datetime.now():%H:%M:%S}] {request.remote_addr:<15} -> "
          f"{os.path.basename(dest)} ({human(size)})", flush=True)
    return jsonify(ok=True, saved=os.path.basename(dest), size=size)

def main():
    global UPLOAD_DIR
    a = argparse.ArgumentParser(description="FileDrop — LAN file receiver")
    a.add_argument("-d", "--dir", default=DEFAULT_DIR, help="Directory to save uploaded files")
    a.add_argument("-p", "--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    a.add_argument("-H", "--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    o = a.parse_args()
    UPLOAD_DIR = os.path.abspath(os.path.expanduser(o.dir))
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        t = os.path.join(UPLOAD_DIR, ".wtest"); open(t, "w").close(); os.remove(t)
    except OSError as e:
        sys.exit(f"Cannot write to {UPLOAD_DIR}\n  {e}")

    ips = get_local_ips()
    print(f"\n  FileDrop\n  {'-'*52}\n  saving to : {UPLOAD_DIR}\n  bind      : {o.host}:{o.port}")
    print("  open from another device:")
    for ip in ips or ["<this-machine-ip>"]:
        print(f"      http://{ip}:{o.port}/")
    print(f"      http://127.0.0.1:{o.port}/   (this machine)\n  {'-'*52}\n  Ctrl-C to stop\n")
    app.run(host=o.host, port=o.port, threaded=True)

if __name__ == "__main__":
    main()
