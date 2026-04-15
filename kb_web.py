"""
Knowledge Base Web Management Interface
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, sys, os

sys.path.insert(0, os.path.expanduser("~/knowledge-base"))
from kb_system import search, get_stats, index_files

PORT = 8898

HTML_PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>占卜知识库</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'PingFang SC',sans-serif;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh;color:#e0e0e0}
.header{text-align:center;padding:40px 20px 20px}
.header h1{font-size:2em;background:linear-gradient(90deg,#f093fb,#f5576c,#ffd200);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{color:#999;margin-top:8px}
.stats{display:flex;justify-content:center;gap:30px;padding:20px;flex-wrap:wrap}
.stat-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:16px;padding:20px 40px;text-align:center;min-width:150px}
.stat-card .num{font-size:2.5em;font-weight:bold;background:linear-gradient(90deg,#f093fb,#f5576c);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-card .label{color:#888;font-size:.9em;margin-top:4px}
.container{max-width:800px;margin:20px auto;padding:0 20px}
.search-box{display:flex;gap:10px;margin-bottom:30px}
.search-box input{flex:1;padding:16px 24px;border-radius:30px;border:1px solid rgba(255,255,255,.15);background:rgba(255,255,255,.05);color:#fff;font-size:1em;outline:none}
.search-box input:focus{border-color:#f5576c}
.search-box button{padding:16px 32px;border-radius:30px;border:none;background:linear-gradient(90deg,#f093fb,#f5576c);color:#fff;font-size:1em;cursor:pointer;font-weight:bold}
.actions{display:flex;justify-content:center;gap:15px;margin:30px 0;flex-wrap:wrap}
.actions button{padding:12px 28px;border-radius:25px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.05);color:#ccc;cursor:pointer;font-size:.95em}
.actions button:hover{background:rgba(255,255,255,.1)}
.results{display:flex;flex-direction:column;gap:16px}
.result-card{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:16px;padding:20px 24px}
.result-card .source{color:#f5576c;font-size:.85em;margin-bottom:8px}
.result-card .content{line-height:1.8;color:#ccc}
.empty{text-align:center;color:#555;padding:60px 20px;font-size:1.1em}
.toast{position:fixed;top:20px;right:20px;background:rgba(245,87,108,.9);color:#fff;padding:14px 24px;border-radius:12px;display:none;z-index:99}
.file-list{background:rgba(255,255,255,.03);border-radius:12px;padding:15px 20px;margin-top:15px;max-height:300px;overflow-y:auto}
.file-list div{padding:6px 0;color:#888;font-size:.9em;border-bottom:1px solid rgba(255,255,255,.05)}
</style>
</head>
<body>
<div class="toast" id="toast"></div>
<div class="header"><h1>🔮 占卜知识库</h1><p>头像占卜 · 八字算命 · 六爻占卜</p></div>
<div class="stats">
  <div class="stat-card"><div class="num" id="fc">-</div><div class="label">已索引文件</div></div>
  <div class="stat-card"><div class="num" id="cc">-</div><div class="label">文本块</div></div>
</div>
<div class="actions">
  <button onclick="doIndex()">📥 扫描新文件入库</button>
  <button onclick="showFiles()">📁 查看文件列表</button>
</div>
<div id="fl" style="display:none"></div>
<div class="container">
  <div class="search-box">
    <input type="text" id="q" placeholder="🔍 搜索知识库..." onkeydown="if(event.key==='Enter')doSearch()">
    <button onclick="doSearch()">搜索</button>
  </div>
  <div class="results" id="r"><div class="empty">🔮 输入关键词搜索占卜知识库</div></div>
</div>
<script>
function toast(m){var t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',3000)}
function doSearch(){var q=document.getElementById('q').value.trim();if(!q)return;var r=document.getElementById('r');r.innerHTML='<div class="empty">⏳ 搜索中...</div>';fetch('/api/search?q='+encodeURIComponent(q)).then(x=>x.json()).then(d=>{if(!d.length){r.innerHTML='<div class="empty">没有找到相关内容</div>';return}r.innerHTML=d.map(i=>'<div class="result-card"><div class="source">📄 '+i.source+'</div><div class="content">'+i.content.replace(/</g,'&lt;')+'</div></div>').join('')}).catch(()=>{r.innerHTML='<div class="empty">搜索出错</div>'})}
function doIndex(){toast('📥 正在扫描入库...');fetch('/api/index',{method:'POST'}).then(x=>x.json()).then(d=>{toast('✅ '+d.message);loadStats()}).catch(()=>toast('❌ 出错'))}
function showFiles(){var a=document.getElementById('fl');fetch('/api/files').then(x=>x.json()).then(d=>{a.innerHTML=d.length?'<div class="file-list">'+d.map(f=>'<div>📄 '+f+'</div>').join('')+'</div>':'<div class="file-list"><div>暂无文件</div></div>';a.style.display='block'})}
function loadStats(){fetch('/api/stats').then(x=>x.json()).then(d=>{document.getElementById('fc').textContent=d.indexed_files;document.getElementById('cc').textContent=d.total_chunks})}
loadStats();
</script>
</body>
</html>"""

class KBHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type","text/html;charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        elif self.path.startswith("/api/stats"):
            self._json(get_stats())
        elif self.path.startswith("/api/search"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query).get("q",[""])[0]
            self._json(search(q))
        elif self.path.startswith("/api/files"):
            self._json(get_stats().get("files",[]))
        else:
            self.send_response(404);self.end_headers()
    def do_POST(self):
        if self.path.startswith("/api/index"):
            chunks = index_files()
            self._json({"message": f"索引完成，{chunks} 个文本块"})
        else:
            self.send_response(404);self.end_headers()
    def _json(self,data):
        self.send_response(200)
        self.send_header("Content-Type","application/json;charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data,ensure_ascii=False).encode())
    def log_message(self,*a):pass

if __name__ == "__main__":
    print(f"Knowledge Base running: http://0.0.0.0:{PORT}")
    HTTPServer(("0.0.0.0",PORT),KBHandler).serve_forever()
