"""
landing.py - Landing page and privacy policy for domaincheckr.
Mounted on the main FastAPI app at / and /privacy.
"""

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Domain Checker - Instant Domain Availability</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,system-ui,sans-serif;background:#0a0a0a;color:#e0e0e0;line-height:1.6}
.container{max-width:720px;margin:0 auto;padding:40px 20px}
h1{font-size:2rem;color:#fff;margin-bottom:8px}
.tagline{color:#888;font-size:1.1rem;margin-bottom:40px}
.section{background:#151515;border:1px solid #222;border-radius:8px;padding:24px;margin-bottom:24px}
.section h2{font-size:1.2rem;color:#fff;margin-bottom:12px}
.section p,.section li{color:#aaa;font-size:0.95rem}
.section ul{list-style:none;padding:0}
.section li{padding:6px 0;border-bottom:1px solid #1a1a1a}
.section li:last-child{border-bottom:none}
.section li strong{color:#ccc}
.try-it{margin-top:32px;text-align:center}
.try-it input{background:#1a1a1a;border:1px solid #333;color:#fff;padding:12px 16px;
  border-radius:6px 0 0 6px;font-size:1rem;width:280px;outline:none}
.try-it input:focus{border-color:#555}
.try-it button{background:#2563eb;color:#fff;border:none;padding:12px 20px;
  border-radius:0 6px 6px 0;font-size:1rem;cursor:pointer}
.try-it button:hover{background:#1d4ed8}
.result{margin-top:16px;padding:16px;background:#1a1a1a;border-radius:6px;
  font-family:monospace;font-size:0.85rem;display:none;text-align:left;
  max-width:600px;margin-left:auto;margin-right:auto;white-space:pre-wrap;word-break:break-all}
.footer{text-align:center;color:#555;font-size:0.8rem;margin-top:40px}
.footer a{color:#666;text-decoration:none}
code{background:#1a1a1a;padding:2px 6px;border-radius:3px;font-size:0.85rem;color:#aaa}
.available{color:#22c55e}.taken{color:#ef4444}
</style>
</head>
<body>
<div class="container">
<h1>Domain Checker</h1>
<p class="tagline">Instant domain availability via RDAP. Free API. Works with ChatGPT and Claude.</p>

<div class="try-it">
<input type="text" id="d" placeholder="Enter a domain, e.g. coolstartup.com"
  onkeydown="if(event.key==='Enter')checkIt()">
<button onclick="checkIt()">Check</button>
<div class="result" id="r"></div>
</div>

<div class="section">
<h2>What It Does</h2>
<p>Checks whether any domain name is available for registration using the RDAP protocol.
Returns registrar info, expiry dates, and direct registration links.
Available as a REST API, ChatGPT Action, and Claude MCP tool.</p>
</div>

<div class="section">
<h2>API Endpoints</h2>
<ul>
<li><strong>GET /check/{domain}</strong> - Check a single domain</li>
<li><strong>POST /check</strong> - Check up to 50 domains at once</li>
<li><strong>GET /suggest?keyword=</strong> - Generate and check domain ideas</li>
<li><strong>GET /health</strong> - Health check</li>
</ul>
</div>

<div class="section">
<h2>Use With AI Assistants</h2>
<ul>
<li><strong>ChatGPT</strong> - Search "Domain Checker" in the GPT Store</li>
<li><strong>Claude Desktop</strong> - Add as MCP server (remote URL)</li>
<li><strong>Cursor / Windsurf</strong> - Add MCP config</li>
</ul>
</div>

<p class="footer"><a href="/privacy">Privacy Policy</a> &middot; <a href="/docs">API Docs</a></p>
</div>
<script>
async function checkIt(){
  var d=document.getElementById('d').value.trim();
  if(!d)return;
  var r=document.getElementById('r');
  r.style.display='block';
  r.textContent='Checking...';
  try{
    var res=await fetch('/check/'+encodeURIComponent(d));
    var j=await res.json();
    while(r.firstChild)r.removeChild(r.firstChild);
    var status=document.createElement('span');
    if(j.available){
      status.className='available';
      status.textContent='AVAILABLE';
    }else{
      status.className='taken';
      status.textContent='TAKEN';
      var info=document.createTextNode(
        ' ('+(j.registrar||'unknown')+', expires '+(j.expires||'unknown')+')'
      );
    }
    r.appendChild(status);
    if(info)r.appendChild(info);
    r.appendChild(document.createTextNode('\\n\\n'+JSON.stringify(j,null,2)));
  }catch(e){r.textContent='Error: '+e.message}
}
</script>
</body>
</html>"""

PRIVACY_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy Policy - Domain Checker</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,system-ui,sans-serif;background:#0a0a0a;color:#e0e0e0;line-height:1.7}
.container{max-width:640px;margin:0 auto;padding:40px 20px}
h1{font-size:1.6rem;color:#fff;margin-bottom:24px}
h2{font-size:1.1rem;color:#ccc;margin:20px 0 8px}
p{color:#aaa;font-size:0.9rem;margin-bottom:12px}
a{color:#2563eb}
</style>
</head>
<body>
<div class="container">
<h1>Privacy Policy</h1>
<p>Last updated: March 2026</p>

<h2>What We Collect</h2>
<p>When you check a domain, we log the domain name, whether it was available,
and a timestamp. We do not collect personal information, IP addresses, or account data.</p>

<h2>How We Use It</h2>
<p>Logged data is used solely for aggregate analytics (total checks, availability rates).
We do not sell, share, or transfer this data to third parties.</p>

<h2>Affiliate Links</h2>
<p>When a domain is available, we include registration links to domain registrars
(Dynadot, Name.com). These contain affiliate tracking codes. If you register a domain
through these links, we may earn a commission. No personal data is shared with registrars
through these links beyond what you provide during registration.</p>

<h2>Cookies</h2>
<p>This service does not set cookies. Registrar affiliate links may set cookies
on the registrar's domain when clicked.</p>

<h2>Contact</h2>
<p>Questions? Email privacy@domaincheckr.fly.dev</p>
</div>
</body>
</html>"""
