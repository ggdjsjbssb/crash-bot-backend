<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" />
  <title>Crash — DEMO 1.2</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg1:#000000;
      --bg2:#000000;
      --panel:#0f0f0f;
      --muted:#a0a0a0;
      --neon-main:#4fe6ff;
      --neon-accent:#4f9ef5;
      --neon-alt:#8a5cff;
      --danger:#ff4d4f;
      --radius:12px;
      --text-main:#ffffff;
    }
    *{box-sizing:border-box}
    html,body{
      margin:0;
      font-family:Inter,system-ui,Segoe UI,Roboto,Arial;
      color:var(--text-main);
      background: var(--bg1);
      -webkit-font-smoothing:antialiased;
      -moz-osx-font-smoothing:grayscale;
      display:flex;
      flex-direction:column;
      align-items:center;
      min-height:100vh;
    }

    header{
      width:100%;
      padding:10px 0;
      text-align:center;
      font-weight:900;
      font-size:18px;
      color:var(--neon-main);
      letter-spacing:0.5px;
    }

    main{
      width:100%;
      max-width:1000px;
      display:grid;
      grid-template-columns:1fr;
      gap:16px;
      padding:12px 8px 80px;
    }

    .game-panel{
      background:var(--panel);
      border-radius:var(--radius);
      padding:12px;
      border:1px solid rgba(255,255,255,0.05);
      box-shadow:0 12px 40px rgba(0,0,0,0.7);
    }

    #grid{
      position:relative;
      width:100%;
      height:400px;
      border-radius:10px;
      overflow:hidden;
      background:var(--bg2);
      border:1px solid rgba(255,255,255,0.05);
      display:flex;
      justify-content:center;
      align-items:center;
    }

    #multTop{
      position:absolute;
      left:12px;
      top:12px;
      z-index:60;
      font-weight:800;
      font-size:20px;
      color:var(--neon-main);
      text-shadow:0 4px 20px rgba(79,158,245,0.12);
    }
    #xHistory{
      position:absolute;
      left:12px;
      top:38px;
      z-index:60;
      color:var(--muted);
      font-size:11px;
    }
    #status{
      position:absolute;
      left:12px;
      bottom:12px;
      z-index:60;
      color:var(--muted);
      font-size:13px;
      font-weight:600;
    }

    #rocket{
      position:absolute;
      width:50px;
      height:50px;
      background-color: #000;
      z-index:50;
      opacity:0;
      transition: transform 300ms cubic-bezier(0.2, 0.9, 0.3, 1), opacity 700ms;
      filter: drop-shadow(0 6px 20px rgba(79,230,255,0.3));
      transform-origin: center;
    }
    .rocket-show{opacity:1;}

    #rocketX{
      position:absolute;
      z-index:90;
      font-weight:800;
      color:var(--neon-main);
      font-size:18px;
      text-shadow:0 4px 20px rgba(79,158,245,0.12);
      pointer-events:none;
    }

    #explosion{
      position:absolute;
      z-index:80;
      font-size:72px;
      display:none;
      pointer-events:none;
      filter:drop-shadow(0 16px 32px rgba(255,100,40,0.45));
    }
    #crashText{
      position:absolute;
      z-index:85;
      display:none;
      font-weight:800;
      color:var(--danger);
      font-size:28px;
      text-shadow:0 8px 32px rgba(255,60,60,0.18);
    }

    .card{
      background:var(--panel);
      border-radius:var(--radius);
      padding:12px;
      border:1px solid rgba(255,255,255,0.05);
      font-size:13px;
    }
    .balance-row{
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap:8px;
    }
    .balance-amount{
      font-weight:800;
      font-size:18px;
      color:var(--neon-main);
      display:flex;
      align-items:center;
      gap:4px;
    }
    .small{
      font-size:11px;
      color:var(--muted);
    }
    input[type=number], input[type=text], input[type=password]{
      background:rgba(255,255,255,0.03);
      border:1px solid rgba(255,255,255,0.1);
      color:var(--text-main);
      padding:10px 12px;
      border-radius:8px;
      width:100%;
      font-size:14px;
    }
    .actions{
      display:flex;
      gap:8px;
      margin-top:8px;
      flex-wrap:wrap;
    }
    .btn{
      padding:10px 14px;
      border-radius:8px;
      border:none;
      cursor:pointer;
      font-weight:800;
      font-size:14px;
      letter-spacing:0.2px;
    }
    .primary{
      background:linear-gradient(90deg,var(--neon-accent),var(--neon-alt));
      color:#08101a;
      box-shadow:0 8px 24px rgba(79,158,245,0.12);
    }
    .primary:hover{
      transform:translateY(-2px);
      box-shadow:0 16px 40px rgba(79,158,245,0.18);
    }
    .ghost{
      background:transparent;
      border:1px solid rgba(255,255,255,0.1);
      color:var(--text-main);
      font-size:13px;
      padding:8px 12px;
    }

    #authModal{
      position:fixed;
      inset:0;
      display:flex;
      align-items:center;
      justify-content:center;
      z-index:400;
      background:rgba(0,0,0,0.85);
    }
    .auth-box{
      width:90%;
      max-width:400px;
      border-radius:12px;
      padding:20px;
      background:var(--panel);
      border:1px solid rgba(255,255,255,0.1);
      box-shadow:0 20px 60px rgba(0,0,0,0.9);
    }

    #notification{
      position:fixed;
      top:16px;
      left:50%;
      transform:translateX(-50%);
      background:rgba(0,0,0,0.85);
      color:var(--neon-main);
      padding:10px 18px;
      border-radius:8px;
      z-index:1000;
      opacity:0;
      pointer-events:none;
      transition:opacity 300ms;
      font-size:14px;
      max-width:80%;
      text-align:center;
    }

    .profile-panel,
    .top-panel{
      margin-top:12px;
      background:var(--panel);
      border-radius:var(--radius);
      padding:12px;
      border:1px solid rgba(255,255,255,0.05);
    }
    .profile-tabs{
      display:flex;
      gap:6px;
      margin-bottom:10px;
      overflow-x:auto;
    }
    .profile-tab{
      padding:6px 10px;
      border-radius:8px;
      cursor:pointer;
      font-size:12px;
      font-weight:600;
      color:var(--muted);
      border:1px solid transparent;
      white-space:nowrap;
    }
    .profile-tab.active{
      color:var(--neon-main);
      border-color:rgba(79,230,255,0.3);
      background:rgba(79,230,255,0.05);
    }
    .profile-content,
    .top-content{
      max-height:400px;
      overflow-y:auto;
      font-size:12px;
      color:var(--muted);
      line-height:1.5;
    }

    .achievement, .case-item{
      display:flex;
      align-items:center;
      gap:8px;
      margin:6px 0;
      padding:6px;
      border-radius:8px;
      background:rgba(255,255,255,0.02);
      font-size:16px;
    }
    .achievement span, .case-item span{
      font-size:20px;
    }
  </style>
</head>
<body>
  <header>Crash — DEMO 1.2</header>
  <div id="notification"></div>
  <main>
    <section class="game-panel">
      <div id="grid" aria-live="polite">
        <div id="multTop">1.00x</div>
        <div id="xHistory">История: —</div>
        <div id="status">Ожидание раунда...</div>
        <div id="rocket"></div>
        <div id="rocketX">1.00x</div>
        <div id="explosion">💥</div>
        <div id="crashText"></div>
        <div id="countdownOverlay" style="display:none">
          <div id="countdownBox">
            <div id="countText" style="font-size:14px;color:var(--muted);margin-bottom:6px">Раунд начнётся через</div>
            <div id="countNumber">5</div>
          </div>
        </div>
      </div>

      <div style="display:flex;justify-content:space-between;gap:8px;align-items:center;font-size:12px">
        <div class="small">Ставки игроков</div>
        <div class="small" id="roundTimer">—</div>
      </div>
      <div id="playersList" class="card" style="max-height:100px;overflow:auto">
        <div id="playerList">Пока никто не ставил</div>
      </div>

      <div class="card" style="margin-top:8px">
        <div id="historyBox" style="margin-top:6px;font-size:12px;color:var(--muted)"></div>
      </div>
    </section>

    <aside class="control-panel">
      <div class="card">
        <div class="balance-row">
          <div>
            <div class="small">Баланс</div>
            <div class="balance-amount" id="balance">0</div>
          </div>
          <div style="text-align:right">
            <div class="small">Профиль</div>
            <div id="profileName">—</div>
          </div>
        </div>

        <div style="margin-top:8px">
          <div class="small">Ставка (мин 10)</div>
          <div style="display:flex;gap:6px;margin-top:6px">
            <input id="inpBet" type="number" min="10" value="10">
            <button class="btn ghost" id="btnMax" style="padding:8px 10px;font-size:13px">Макс</button>
          </div>
        </div>

        <div style="margin-top:8px">
          <div class="small">Авто-вывод (x)</div>
          <div style="display:flex;gap:6px;margin-top:6px;align-items:center;flex-wrap:wrap">
            <input id="inpAuto" type="number" step="0.1" min="1.1" value="2.0" disabled style="width:auto">
            <label style="display:flex;align-items:center;gap:4px;font-size:12px;color:var(--muted);cursor:pointer">
              <input type="checkbox" id="autoEnabled" style="width:12px;height:12px">
              Вкл.
            </label>
          </div>
        </div>

        <div class="actions">
          <button class="btn primary" id="btnPlace">Сделать ставку</button>
          <button class="btn primary" id="btnCash" disabled>Забрать</button>
          <button class="btn ghost" id="btnProfile">Профиль</button>
          <button class="btn ghost" id="btnTop">ТОП</button>
        </div>
      </div>

      <!-- ПРОФИЛЬ -->
      <div class="card" id="profilePanel" style="display:none;margin-top:12px">
        <div class="profile-tabs">
          <div class="profile-tab active" data-tab="history">📜 История</div>
          <div class="profile-tab" data-tab="achievements">🏆 Достижения</div>
          <div class="profile-tab" data-tab="levels">📈 Уровни</div>
          <div class="profile-tab" data-tab="cases">🎁 Кейсы</div>
        </div>
        <div class="profile-content" id="profileContent">
          <div id="profileHistory">
            <div id="localHistory" style="max-height:200px;overflow:auto;color:var(--muted);font-size:12px;margin-top:6px"></div>
          </div>
          <div id="profileAchievements" style="display:none;"></div>
          <div id="profileLevels" style="display:none;"></div>
          <div id="profileCases" style="display:none;"></div>
        </div>
      </div>

      <!-- ПРОМОКОДЫ -->
      <div class="card" style="margin-top:12px">
        <div class="small">🎟️ Промокод</div>
        <input type="text" id="inpPromo" placeholder="Введите промокод" style="margin-top:6px">
        <button class="btn primary" id="btnApplyPromo" style="margin-top:8px;width:100%">Применить</button>
        <div id="promoStatus" class="small" style="margin-top:6px"></div>
      </div>

      <!-- ТОП -->
      <div class="top-panel" id="topPanel" style="display:none">
        <div class="top-content" id="topContent">
          Загрузка...
        </div>
      </div>

      <div style="height:80px;"></div>
    </aside>
  </main>

  <div id="authModal">
    <div class="auth-box" id="authBox">
      <h3 style="color:var(--neon-main);margin:0 0 8px 0;font-size:18px">Вход / Регистрация</h3>
      <div><input id="loginName" placeholder="Имя" style="margin-bottom:8px"></div>
      <div><input id="loginPass" type="password" placeholder="Пароль"></div>
      <div style="display:flex;gap:8px;margin-top:12px;flex-wrap:wrap">
        <button class="btn primary" id="btnLogin" style="flex:1;min-width:100px">Войти</button>
        <button class="btn ghost" id="btnRegister" style="flex:1;min-width:100px">Регистрация</button>
      </div>
    </div>
  </div>
    <script>
    // ================= CONFIG =================
    const API_URL = 'https://crash-bot-pioy.onrender.com';  // ← ЭТА СТРОКА ОБНОВЛЕНА
    const MIN_BET = 10;

    // ================= STATE =================
    let currentUser = null;
    let currentRound = null;
    let roundTimerInterval = null;

    // ================= DOM =================
    const notification = document.getElementById('notification');
    const authModal = document.getElementById('authModal');
    const loginName = document.getElementById('loginName');
    const loginPass = document.getElementById('loginPass');
    const btnLogin = document.getElementById('btnLogin');
    const btnRegister = document.getElementById('btnRegister');
    const balanceEl = document.getElementById('balance');
    const profileNameEl = document.getElementById('profileName');
    const inpBet = document.getElementById('inpBet');
    const btnMax = document.getElementById('btnMax');
    const inpAuto = document.getElementById('inpAuto');
    const autoEnabled = document.getElementById('autoEnabled');
    const btnPlace = document.getElementById('btnPlace');
    const btnCash = document.getElementById('btnCash');
    const btnProfile = document.getElementById('btnProfile');
    const btnTop = document.getElementById('btnTop');
    const profilePanel = document.getElementById('profilePanel');
    const profileContent = document.getElementById('profileContent');
    const topPanel = document.getElementById('topPanel');
    const topContent = document.getElementById('topContent');
    const inpPromo = document.getElementById('inpPromo');
    const btnApplyPromo = document.getElementById('btnApplyPromo');
    const promoStatus = document.getElementById('promoStatus');
    const multTop = document.getElementById('multTop');
    const xHistoryEl = document.getElementById('xHistory');
    const statusEl = document.getElementById('status');
    const roundTimer = document.getElementById('roundTimer');
    const rocket = document.getElementById('rocket');
    const rocketX = document.getElementById('rocketX');
    const grid = document.getElementById('grid');
    const playerList = document.getElementById('playerList');
    const historyBox = document.getElementById('historyBox');

    // ================= UTILS =================
    function showNotification(text) {
      notification.textContent = text;
      notification.style.opacity = '1';
      setTimeout(() => { notification.style.opacity = '0'; }, 3000);
    }

    async function apiCall(endpoint, method = 'GET', body = null) {
      const url = `${API_URL}/api${endpoint}`;
      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      };
      if (body) options.body = JSON.stringify(body);
      const res = await fetch(url, options);
      if (!res.ok) throw new Error('Сервер не отвечает');
      return res.json();
    }

    // ================= AUTH =================
    async function login(name, pass) {
      try {
        await apiCall('/auth/login', 'POST', { name, password: pass });
        currentUser = name;
        await loadUserData();
        authModal.style.display = 'none';
        showNotification('✅ Вход выполнен');
      } catch (e) {
        showNotification('❌ ' + (e.message || 'Ошибка'));
      }
    }

    async function register(name, pass) {
      try {
        await apiCall('/auth/register', 'POST', { name, password: pass });
        await login(name, pass);
      } catch (e) {
        showNotification('❌ ' + (e.message || 'Ошибка'));
      }
    }

    // ================= GAME =================
    async function loadUserData() {
      try {
        const data = await apiCall('/user');
        balanceEl.innerHTML = `${data.balance.toFixed(2)} <span style="font-size:18px">💎</span>`;
        profileNameEl.textContent = data.name;
        renderProfile(data);
      } catch (e) {
        console.error(e);
      }
    }

    async function loadRound() {
      try {
        const data = await apiCall('/round');
        currentRound = data;
        multTop.textContent = data.multiplier.toFixed(2) + 'x';
        rocketX.textContent = data.multiplier.toFixed(2) + 'x';
        
        if (data.status === 'bet') {
          statusEl.textContent = `Приём ставок — ${data.bet_time}s`;
          roundTimer.textContent = data.bet_time + 's';
          btnPlace.disabled = false;
          btnCash.disabled = true;
          playerList.innerHTML = data.bets.length ? 
            data.bets.map(b => `<div>${b.name}: ${b.amount.toFixed(2)}</div>`).join('') :
            'Пока никто не ставил';
          if (roundTimerInterval) clearInterval(roundTimerInterval);
          let time = data.bet_time;
          roundTimerInterval = setInterval(() => {
            roundTimer.textContent = (--time) + 's';
            if (time <= 0) clearInterval(roundTimerInterval);
          }, 1000);
          rocket.classList.remove('rocket-show');
          rocket.style.opacity = '0';
          rocketX.style.opacity = '0';
        } else if (data.status === 'flight') {
          statusEl.textContent = 'В полёте...';
          btnPlace.disabled = true;
          btnCash.disabled = !data.bets.some(b => b.name === currentUser && !b.cashed);
          rocket.classList.add('rocket-show');
          rocket.style.opacity = '1';
          rocketX.style.opacity = '1';
          const scale = 1 + Math.min(2, (data.multiplier - 1) / 10);
          rocket.style.transform = `scale(${scale})`;
          rocketX.style.transform = `scale(${Math.min(1.5, scale)})`;
        } else if (data.status === 'crash') {
          statusEl.textContent = `CRASH ${data.crashX?.toFixed(2) || '1.00'}x`;
          btnPlace.disabled = true;
          btnCash.disabled = true;
          const explosion = document.getElementById('explosion');
          const crashText = document.getElementById('crashText');
          explosion.style.display = 'block';
          crashText.style.display = 'block';
          crashText.textContent = `CRASH ${data.crashX?.toFixed(2) || '1.00'}x`;
          setTimeout(() => {
            explosion.style.display = 'none';
            crashText.style.display = 'none';
          }, 2000);
        }
        xHistoryEl.innerHTML = 'История: ' + (data.xHistory || []).map(x => {
          const v = parseFloat(x);
          let color = v < 2 ? '#ff5252' : v < 10 ? '#ffcc00' : '#4cd964';
          return `<span style="color:${color};font-weight:800;margin-right:8px">${v.toFixed(2)}x</span>`;
        }).join('');
      } catch (e) {
        console.error(e);
      }
    }

    // ================= ACTIONS =================
    async function placeBet() {
      const amount = parseFloat(inpBet.value) || 0;
      if (amount < MIN_BET) return showNotification(`Минимум ${MIN_BET}`);
      try {
        await apiCall('/round/bet', 'POST', { amount });
        await loadUserData();
        showNotification('✅ Ставка принята');
      } catch (e) {
        showNotification('❌ ' + (e.message || 'Ошибка'));
      }
    }

    async function cashOut() {
      try {
        const data = await apiCall('/round/cashout');
        await loadUserData();
        showNotification(`✅ Вывел ${data.win.toFixed(2)} при x${data.multiplier.toFixed(2)}`);
      } catch (e) {
        showNotification('❌ ' + (e.message || 'Ошибка'));
      }
    }

    async function applyPromo(code) {
      if (!code.trim()) return;
      try {
        const data = await apiCall('/promo', 'POST', { code: code.trim() });
        await loadUserData();
        promoStatus.textContent = `✅ +${data.amount} 💎`;
      } catch (e) {
        promoStatus.textContent = '❌ ' + (e.message || 'Неверный промокод');
      }
    }

    // ================= RENDER =================
    function renderProfile(data) {
      const histDiv = document.getElementById('localHistory');
      histDiv.innerHTML = (data.history || []).slice(0,20).map(item => `<div>${item}</div>`).join('');
      
      const achievements = data.achievements || {};
      let achHtml = '';
      for (const key in {lucky1:1,lucky2:1,lucky3:1,profit1:1,profit2:1,profit3:1}) {
        const earned = achievements[key];
        const names = {
          lucky1: {name:"Удачливый", desc:"Забрать X > 5", emoji:"★"},
          lucky2: {name:"Удачливый II", desc:"Забрать X > 10", emoji:"🍀"},
          lucky3: {name:"Удачливый III", desc:"Забрать X > 50", emoji:"♣️"},
          profit1: {name:"Прибыль 1", desc:"Чистыми 1000", emoji:"🎁"},
          profit2: {name:"Прибыль 2", desc:"Чистыми 5000", emoji:"⭐"},
          profit3: {name:"Прибыль 3", desc:"Чистыми 10000", emoji:"🏛️"}
        };
        achHtml += `
          <div class="achievement" style="${earned ? 'border:1px solid var(--neon-main);' : 'opacity:0.5;'}">
            <span>${names[key].emoji}</span>
            <div>
              <div><b>${names[key].name}</b> ${earned ? '✅' : ''}</div>
              <div class="small">${names[key].desc}</div>
            </div>
          </div>
        `;
      }
      document.getElementById('profileAchievements').innerHTML = achHtml;
      
      const level = data.level || 0;
      const totalWin = data.total_win || 0;
      const nextReq = level < 10 ? [10000,20000,30000,40000,50000,60000,70000,80000,90000,100000][level] : 'MAX';
      const progress = level < 10 ? `${totalWin.toFixed(2)} / ${nextReq}` : 'MAX';
      const roman = ['I','II','III','IV','V','VI','VII','VIII','IX','X'][level - 1] || level;
      document.getElementById('profileLevels').innerHTML = `
        <div>Уровень: <b>${level}</b> (${roman})</div>
        <div style="margin-top:8px;padding:6px;background:rgba(255,255,255,0.02);border-radius:8px;font-size:12px">
          Прогресс: ${progress}
        </div>
      `;
      
      const completed = Object.keys(achievements).length;
      let caseHtml = '';
      [
        {id:'case1', name:"Кейс 1", desc:"За 3 достижения", req:3, reward:500, emoji:"📦"},
        {id:'case2', name:"Кейс 2", desc:"За 6 достижений", req:6, reward:1000, emoji:"🎁"}
      ].forEach(c => {
        const earned = (data.cases || []).includes(c.id);
        const canClaim = completed >= c.req && !earned;
        caseHtml += `
          <div class="case-item" style="${completed >= c.req ? 'border:1px solid var(--neon-main);' : 'opacity:0.5;'}">
            <span>${c.emoji}</span>
            <div>
              <div><b>${c.name}</b> ${earned ? '✅' : ''}</div>
              <div class="small">${c.desc} (${completed}/${c.req})</div>
            </div>
            ${canClaim ? `<button class="btn primary" onclick="claimCase('${c.id}', ${c.reward})" style="font-size:12px;padding:4px 8px;margin-left:8px;">Забрать ${c.reward} 💎</button>` : ''}
          </div>
        `;
      });
      document.getElementById('profileCases').innerHTML = caseHtml;
    }

    async function claimCase(caseId, reward) {
      try {
        await apiCall('/case', 'POST', { caseId });
        await loadUserData();
        showNotification(`🎉 Кейс открыт! +${reward} монет`);
      } catch (e) {
        showNotification('❌ ' + (e.message || 'Ошибка'));
      }
    }

    function renderTopList() {
      apiCall('/top/x').then(data => {
        topContent.innerHTML = data.map((item, i) => `<div>${i+1}. ${item.name} — <b>${item.x.toFixed(2)}x</b></div>`).join('') || 'Пусто';
      }).catch(e => topContent.innerHTML = 'Ошибка');
    }

    function renderTopBalanceList() {
      apiCall('/top/balance').then(data => {
        topContent.innerHTML = data.map((item, i) => `<div>${i+1}. ${item.name} — <b>${item.balance.toFixed(2)}</b></div>`).join('') || 'Пусто';
      }).catch(e => topContent.innerHTML = 'Ошибка');
    }

    function renderTopLevelList() {
      apiCall('/top/level').then(data => {
        topContent.innerHTML = data.map((item, i) => `<div>${i+1}. ${item.name} — <b>Уровень ${item.level}</b></div>`).join('') || 'Пусто';
      }).catch(e => topContent.innerHTML = 'Ошибка');
    }

    // ================= EVENTS =================
    btnRegister.onclick = () => register(loginName.value, loginPass.value);
    btnLogin.onclick = () => login(loginName.value, loginPass.value);
    btnPlace.onclick = placeBet;
    btnCash.onclick = cashOut;
    btnApplyPromo.onclick = () => applyPromo(inpPromo.value);

    btnProfile.onclick = () => {
      profilePanel.style.display = profilePanel.style.display === 'none' ? 'block' : 'none';
      if (topPanel.style.display === 'block') topPanel.style.display = 'none';
      if (currentUser) loadUserData();
    };

    btnTop.onclick = () => {
      topPanel.style.display = topPanel.style.display === 'none' ? 'block' : 'none';
      if (profilePanel.style.display === 'block') profilePanel.style.display = 'none';
      if (topPanel.style.display === 'block') renderTopList();
    };

    setTimeout(() => {
      topPanel.innerHTML += `
        <div style="display:flex;gap:8px;margin-top:12px">
          <button class="btn ghost" onclick="renderTopList()">ТОП по X</button>
          <button class="btn ghost" onclick="renderTopBalanceList()">ТОП по БАЛАНСУ</button>
          <button class="btn ghost" onclick="renderTopLevelList()">ТОП по LVL</button>
        </div>
      `;
    }, 100);

    // ================= INIT =================
    setInterval(loadRound, 500);
    authModal.style.display = 'flex';
  </script>
</body>
</html>
