<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>9 Products — Trading Intelligence Platform</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600&display=swap');
  :root{--bg:#060b14;--surface:#0b1120;--text:#e8f0ff;--accent:#f0b429;--cyan:#00e5ff;--rose:#ff4d6d;--glass:rgba(255,255,255,0.03);}
  *{margin:0;padding:0;box-sizing:border-box}
  body{font-family:'Inter',system-ui,sans-serif;background:radial-gradient(circle at 30% 20%,#0b1a30 0%,#060b14 70%);color:var(--text);min-height:100vh;overflow-x:hidden;line-height:1.6}
  header{position:relative;overflow:hidden;padding:120px 24px 80px;text-align:center}
  header::before{content:'';position:absolute;inset:0;background:linear-gradient(120deg,rgba(240,180,41,0.08) 0%,rgba(0,229,255,0.06) 50%,rgba(255,77,109,0.08) 100%);animation:gradientShift 12s ease infinite;z-index:0}
  @keyframes gradientShift{0%,100%{transform:translateX(0)}50%{transform:translateX(-20px)}}
  .glow{position:absolute;width:600px;height:600px;background:radial-gradient(circle,rgba(240,180,41,0.25),transparent 70%);border-radius:50%;filter:blur(80px);animation:pulse 6s ease-in-out infinite;z-index:1}
  @keyframes pulse{0%,100%{opacity:0.6;transform:scale(1)}50%{opacity:1;transform:scale(1.15)}}
  .content{position:relative;z-index:2;max-width:1100px;margin:0 auto;padding:0 24px}
  h1{font-family:'Orbitron',system-ui;font-weight:900;font-size:clamp(2.8rem,8vw,6rem);letter-spacing:-0.04em;line-height:1.05;background:linear-gradient(135deg,var(--accent),var(--cyan),var(--rose),var(--accent));background-size:300% 300%;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:textShine 8s ease infinite}
  @keyframes textShine{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
  .subtitle{font-size:1.15rem;color:#8fa3c0;margin-top:16px;font-weight:300;letter-spacing:0.01em}
  .badge-row{display:flex;gap:10px;justify-content:center;margin-top:28px;flex-wrap:wrap}
  .badge{display:inline-flex;align-items:center;gap:6px;padding:8px 16px;border-radius:999px;background:var(--glass);border:1px solid rgba(255,255,255,0.06);font-size:0.82rem;color:#b8c6e0;backdrop-filter:blur(12px);transition:all .2s ease}
  .badge:hover{border-color:rgba(240,180,41,0.35);transform:translateY(-2px)}
  .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:24px;margin-top:80px}
  .card{position:relative;background:linear-gradient(170deg,rgba(255,255,255,0.025) 0%,rgba(255,255,255,0.01) 100%);border:1px solid rgba(255,255,255,0.06);border-radius:24px;padding:32px 28px;overflow:hidden;transition:all .3s ease;backdrop-filter:blur(10px)}
  .card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--cyan),var(--rose));opacity:0.8;transition:opacity .3s}
  .card:hover{border-color:rgba(240,180,41,0.25);transform:translateY(-6px);box-shadow:0 20px 60px rgba(0,0,0,0.4),0 0 0 1px rgba(240,180,41,0.1)}
  .card:hover::before{opacity:1}
  .card h2{font-family:'Orbitron',system-ui;font-size:1.25rem;margin-bottom:8px;color:var(--text)}
  .card .meta{font-size:0.78rem;color:#6b7a94;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px;font-weight:600}
  .card p{color:#b0bdd6;font-size:0.92rem;line-height:1.65;margin-bottom:14px}
  .card .tag{display:inline-block;padding:4px 10px;border-radius:6px;background:rgba(240,180,41,0.1);color:var(--accent);font-size:0.75rem;font-weight:700;margin-right:6px;margin-bottom:4px;letter-spacing:0.02em}
  footer{margin-top:120px;padding:60px 24px;text-align:center;border-top:1px solid rgba(255,255,255,0.06);background:linear-gradient(180deg,transparent 0%,rgba(6,11,20,0.8) 100%);position:relative;overflow:hidden}
  footer .logo-text{font-family:'Orbitron',system-ui;font-weight:900;font-size:2rem;background:linear-gradient(135deg,var(--accent),var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;letter-spacing:-0.03em}
  footer .copy{font-size:0.8rem;color:#55607a;margin-top:8px}
  /* Animated SVG background shapes */
  .float-shape{position:absolute;border-radius:50%;filter:blur(100px);opacity:0.15;animation:float 20s ease-in-out infinite;pointer-events:none;z-index:0}
  @keyframes float{0%,100%{transform:translate(0,0) scale(1)}25%{transform:translate(30px,-40px) scale(1.1)}50%{transform:translate(-20px,20px) scale(0.95)}75%{transform:translate(40px,10px) scale(1.05)}}
  .shape1{width:400px;height:400px;background:var(--accent);top:10%;left:-5%}
  .shape2{width:350px;height:350px;background:var(--cyan);top:50%;right:-5%;animation-delay:-7s;animation-duration:25s}
  .shape3{width:300px;height:300px;background:var(--rose);top:80%;left:20%;animation-delay:-14s;animation-duration:22s}
  /* Interactive hover micro-interaction on badges */
  .badge::after{content:'';position:absolute;inset:-2px;border-radius:inherit;background:linear-gradient(135deg,var(--accent),var(--cyan));opacity:0;z-index:-1;transition:opacity .3s}
  .badge:hover::after{opacity:0.2}
  /* Responsive */
  @media(max-width:600px){.grid{grid-template-columns:1fr}header{padding:80px 20px 60px}}
</style>
</head>
<body>
<header>
  <div class="glow" style="top:-100px;left:50%;transform:translateX(-50%)"></div>
  <div class="float-shape shape1"></div>
  <div class="float-shape shape2"></div>
  <div class="float-shape shape3"></div>
  <div class="content" style="position:relative;z-index:2">
    <h1>9 Buildable Products</h1>
    <p class="subtitle">Trading Intelligence · Gold · Prop Firms · Crypto Security · Fintech Bots</p>
    <div class="badge-row">
      <span class="badge">⚡ Telegram Bot</span>
      <span class="badge">🌐 Flask Web</span>
      <span class="badge">📊 Data Analytics</span>
      <span class="badge">💰 Monetization</span>
      <span class="badge">🔒 Security</span>
    </div>
  </div>
</header>

<main class="content">
  <div class="grid">

    <!-- Product 1 -->
    <article class="card">
      <div class="meta">#1 · Gold · Free Tier Extension</div>
      <h2>Gold Watch Alert Bot</h2>
      <span class="tag">Bot</span><span class="tag">Free Tier</span><span class="tag">XAUUSD</span>
      <p><b>Problem:</b> Traders miss gold entries due to spread/slippage. Most Telegram gold channels are scams.</p>
      <p><b>Solution:</b> <code>/watch XAUUSD style mode</code> made <b>free</b> in EzyAi (previously PRO-only). Uses Binance PAXGUSDT + Yahoo GC=F fallback. Spread-aware stops via existing constants.</p>
      <p><b>Monetize:</b> Free <code>/watch</code> for gold only → upsell <code>/autopilot</code> + fundamentals (DCF/COT) as PRO.</p>
    </article>

    <!-- Product 2 -->
    <article class="card">
      <div class="meta">#2 · Gold · Verification</div>
      <h2>XAUUSD Signal Verifier</h2>
      <span class="tag">Bot</span><span class="tag">Anti-Scam</span>
      <p><b>Problem:</b> Gold Telegram providers post fake MT4 screenshots with cherry-picked entries.</p>
      <p><b>Solution:</b> <code>/verify GOLD PRICE</code> pulls Binance PAXGUSDT tick history and compares claimed entry. Returns <b>VERDICT: REAL / IMPOSSIBLE</b> with gap % and explanation.</p>
      <p><b>Monetize:</b> Free single verify → PRO batch CSV upload + weekly audit reports.</p>
    </article>

    <!-- Product 3 -->
    <article class="card">
      <div class="meta">#3 · Prop Firms · ROI</div>
      <h2>Prop Firm Challenge Calculator</h2>
      <span class="tag">Web</span><span class="tag">Bot</span><span class="tag">EV</span>
      <p><b>Problem:</b> Traders pay $500–$5,000 challenge fees without knowing expected value (~90% fail). Hidden rules (overnight, news bans) buried in T&Cs.</p>
      <p><b>Solution:</b> Flask calculator + <code>/propcalc FEE SIZE PASS%</code> bot command. Calculates EV, scans pasted T&Cs for hidden rules (red/yellow scoring).</p>
      <p><b>Monetize:</b> Free calculator → premium PDF audit + automated forecast.</p>
    </article>

    <!-- Product 4 -->
    <article class="card">
      <div class="meta">#4 · Crypto · Security</div>
      <h2>Telegram Bot Scam Detector</h2>
      <span class="tag">Bot</span><span class="tag">Anti-Malware</span>
      <p><b>Problem:</b> Fake verification bots, malware links, and fake airdrops surged <b>2,000%</b> (OKX Learn 2025).</p>
      <p><b>Solution:</b> <code>/audit @bot_username</code> checks for private-key requests, unregulated broker pushes, missing audit links. Returns <b>SCAM SCORE</b> + checklist.</p>
      <p><b>Monetize:</b> Free scan → PRO daily auto-scan of subscribed channels + malware database.</p>
    </article>

    <!-- Product 5 -->
    <article class="card">
      <div class="meta">#5 · Gold · Calendar</div>
      <h2>Gold Seasonality Calendar</h2>
      <span class="tag">Web</span><span class="tag">Bot Alert</span>
      <p><b>Problem:</b> Traders ignore gold seasonality (Fed windows, CME holidays, jewelry cycles) and spread-widening events.</p>
      <p><b>Solution:</b> Web calendar (<code>/gold-calendar</code>) shows monthly volatility patterns + Fed release windows. Downloadable PDF. Bot pushes <code>/calendar_alert</code> 30 min before events.</p>
      <p><b>Monetize:</b> Free calendar → PRO real-time alert bot.</p>
    </article>

    <!-- Product 6 -->
    <article class="card">
      <div class="meta">#6 · Copy-Trade · Audit</div>
      <h2>Copy-Trade Safety Audit</h2>
      <span class="tag">Bot</span><span class="tag">Fintech</span>
      <p><b>Problem:</b> Influencers push unregulated broker copy-trading; users lose capital through hidden spreads and blowouts.</p>
      <p><b>Solution:</b> <code>/copyaudit BROKER</code> checks regulation (SEC/FCA/ASIC links), negative balance protection, calculates hidden spread cost. Returns <b>SAFE / HIGH RISK</b> + checklist.</p>
      <p><b>Monetize:</b> Free 5 audits → PRO unlimited + weekly portfolio risk report.</p>
    </article>

    <!-- Product 7 -->
    <article class="card">
      <div class="meta">#7 · Forex · Scanner</div>
      <h2>Forex Signal Red-Flag Scanner</h2>
      <span class="tag">Web</span><span class="tag">NLP</span>
      <p><b>Problem:</b> Signal providers claim "100% accuracy", delete losing trades, flood fake reviews, and trap subscribers ($30–$300/mo).</p>
      <p><b>Solution:</b> Web scanner + <code>/scan TEXT</code> bot. NLP flags: "guaranteed", "no risk", "VIP spots left". Checks for verified audit links (MyFXBook/FX Blue).</p>
      <p><b>Monetize:</b> Free text scan → PRO full Telegram group auto-scan + weekly scorecard.</p>
    </article>

    <!-- Product 8 -->
    <article class="card">
      <div class="meta">#8 · IBKR · Affiliate</div>
      <h2>IB Affiliate Revenue Calculator</h2>
      <span class="tag">Web</span><span class="tag">B2B</span>
      <p><b>Problem:</b> IB affiliates face opaque payout rules, compliance overhead, and referred clients complain of buggy platforms / slow withdrawals (BBB ~1.2/5).</p>
      <p><b>Solution:</b> Web calculator (<code>/ib-calc</code>) estimates net revenue after compliance cost + payout timeline. Includes compliance checklist download.</p>
      <p><b>Monetize:</b> Free calculator → PRO automated monthly forecast + audit template.</p>
    </article>

    <!-- Product 9 -->
    <article class="card">
      <div class="meta">#9 · Influencer · Audit</div>
      <h2>Influencer Trading Scam Audit</h2>
      <span class="tag">Bot</span><span class="tag">Viral</span>
      <p><b>Problem:</b> FTC reports <b>$2.1B</b> lost to social-media scams in 2025; ~80% of TikTok financial advice is misleading (Forbes May 2025).</p>
      <p><b>Solution:</b> <code>/audit @influencer_handle</code> audits profile: demands audited trading history (not screenshots), flags luxury props, checks unregulated broker promotions. Free <b>LOSS REPORT TEMPLATE</b> for FTC/CFTC/IC3.</p>
      <p><b>Monetize:</b> Free audit + template → PRO batch audit + automated scam-alert channel.</p>
    </article>

  </div>
</main>

<footer>
  <div style="position:relative;z-index:2">
    <div class="logo-text">printezy · 9 Products</div>
    <p class="copy">Built with Python · Flask · Telegram Bot API · Binance · Yahoo Finance · Stripe · Fly.io</p>
    <p class="copy">Educational research only. Not financial advice. Verify every price with your broker.</p>
    <div style="margin-top:16px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap">
      <a href="#" style="color:#8fa3c0;text-decoration:none;font-size:0.85rem;padding:6px 14px;border:1px solid rgba(255,255,255,0.08);border-radius:999px;transition:all .2s;display:inline-block">📚 Docs</a>
      <a href="#" style="color:#8fa3c0;text-decoration:none;font-size:0.85rem;padding:6px 14px;border:1px solid rgba(255,255,255,0.08);border-radius:999px;transition:all .2s;display:inline-block">⚡ Deploy</a>
      <a href="#" style="color:#8fa3c0;text-decoration:none;font-size:0.85rem;padding:6px 14px;border:1px solid rgba(255,255,255,0.08);border-radius:999px;transition:all .2s;display:inline-block">🔒 Security</a>
    </div>
  </div>
</footer>
</body>
</html>
