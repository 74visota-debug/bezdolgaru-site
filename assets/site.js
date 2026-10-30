(function(){
  // ---- Калькулятор «самозанятый или ИП» (цифры 2026 года)
  var LIMIT_NPD = 2400000, FIX = 57390, ONE_PCT_FROM = 300000, USN = 0.06;
  var rub = function(n){ return Math.round(n).toLocaleString('ru-RU') + ' ₽'; };
  var go = document.getElementById('c-go');
  if (go) {
    var inc = document.getElementById('c-income'), payer = document.getElementById('c-payer'),
        res = document.getElementById('c-res'), err = document.getElementById('c-err');
    inc.addEventListener('input', function(){ err.hidden = true; });
    var calc = function(){
      var d = parseFloat(inc.value);
      if (!(d > 0)) { err.hidden = false; res.innerHTML = ''; return; }
      err.hidden = true;
      var npdOk = d <= LIMIT_NPD, npd = d * parseFloat(payer.value);
      var vzn = FIX + Math.max(0, d - ONE_PCT_FROM) * 0.01;
      var ip = Math.max(0, d * USN - vzn) + vzn;   // налог уменьшается на взносы
      var winNpd = npdOk && npd <= ip, html = '';
      html += '<div class="res-row ' + (npdOk ? (winNpd ? 'win' : '') : 'no') + '"><span>Самозанятый</span><b>' +
              (npdOk ? rub(npd) + ' в год' : 'нельзя: доход выше 2,4 млн') + '</b></div>';
      html += '<div class="res-row ' + (!winNpd ? 'win' : '') + '"><span>ИП на УСН 6%<br><span class="small muted">в т. ч. взносы ' + rub(vzn) + '</span></span><b>' + rub(ip) + ' в год</b></div>';
      if (npdOk) {
        var diff = Math.abs(ip - npd);
        html += '<div class="verdict">' + (winNpd ? 'Выгоднее самозанятость: экономия ' : 'Выгоднее ИП: экономия ') + rub(diff) + ' в год</div>';
      } else {
        html += '<div class="verdict">При таком доходе нужен ИП. Подскажем, как открыть его и счёт онлайн.</div>';
      }
      res.innerHTML = html;
      goal('calc');
    };
    go.addEventListener('click', calc);
    inc.addEventListener('keydown', function(e){ if (e.key === 'Enter') calc(); });
  }
  // ---- Фильтры таблицы банков
  var chips = document.querySelectorAll('.chip');
  chips.forEach(function(c){
    c.addEventListener('click', function(){
      chips.forEach(function(x){ x.classList.remove('on'); }); c.classList.add('on');
      var f = c.getAttribute('data-f');
      document.querySelectorAll('#banks tbody tr').forEach(function(tr){
        tr.style.display = (f === 'all' || (' ' + tr.getAttribute('data-tags') + ' ').indexOf(' ' + f + ' ') > -1) ? '' : 'none';
      });
    });
  });
  // ---- Цели Метрики: клики по кнопкам бота, банков, CTA
  function goal(name){ try { if (window.ym && window.YM_ID) ym(window.YM_ID, 'reachGoal', name); } catch(e) {} }
  document.addEventListener('click', function(e){
    var a = e.target.closest('[data-goal]');
    if (a && a.tagName === 'A') goal(a.getAttribute('data-goal'));
  });
  // ---- Закрывать мобильное меню по клику на пункт
  document.querySelectorAll('.nav a').forEach(function(a){ a.addEventListener('click', function(){ document.body.classList.remove('menu-open'); }); });
})();
// ---- Тест «Подходит ли банкротство»
(function(){
  var go=document.getElementById('q-go'); if(!go) return;
  var val=function(n){var x=document.querySelector('input[name="'+n+'"]:checked');return x?x.value:null;};
  var debtEl=document.getElementById('q-debt'), err=document.getElementById('q-err'), out=document.getElementById('q-out');
  debtEl.addEventListener('input',function(){err.hidden=true;});
  go.addEventListener('click',function(){
    var d=parseFloat(debtEl.value);
    if(!(d>0)){err.hidden=false;out.innerHTML='';return;}
    var late=val('q-late'), fssp=val('q-fssp'), prop=val('q-prop');
    if(late===null||fssp===null||prop===null){err.textContent='Ответьте на все вопросы';err.hidden=false;return;}
    err.hidden=true; err.textContent='Введите сумму долга';
    var lead=window.LEAD_URL||'#', cls='mid', h='', t='';
    if(d<25000){cls='no';h='Банкротство, скорее всего, не нужно';t='При долге меньше 25 000 ₽ ни МФЦ, ни суд обычно не подходят. Попробуйте договориться с кредитором о рассрочке. <a href="/voprosy/restrukturizatsiya-ili-bankrotstvo/">Какие есть варианты</a>.';}
    else if(d<=1000000 && fssp==='1' && prop==='0'){cls='ok';h='Похоже, вам может подойти банкротство через МФЦ — бесплатно';t='Проверьте остальные условия и список документов: <a href="/voprosy/bankrotstvo-cherez-mfc-usloviya/">условия МФЦ</a>, <a href="/voprosy/dokumenty-dlya-bankrotstva-cherez-mfc/">документы</a>.';}
    else if(d<=1000000 && fssp==='2'){cls='mid';h='Нужно уточнить статус у приставов';t='Если исполнительное производство закрыто из-за отсутствия имущества, возможен МФЦ — бесплатно. Проверьте в банке данных ФССП. Если нет — подойдёт судебное банкротство. <a href="'+lead+'" rel="nofollow" data-goal="lead">Бесплатная консультация</a>.';}
    else {cls='mid';h=(d>500000&&late==='1')?'Вам подходит судебное банкротство — и закон обязывает подать заявление':'Вам может подойти судебное банкротство';t='Судебная процедура платная: депозит управляющему 25 000 ₽ и расходы на публикации, плюс услуги юриста. '+(prop==='1'?'Имущество, кроме единственного жилья, могут продать. ':'')+'Чтобы оценить шансы и стоимость, <a href="'+lead+'" rel="nofollow" data-goal="lead">получите бесплатную консультацию</a>.';}
    out.innerHTML='<div class="q-res '+cls+'"><b>'+h+'</b>'+t+'</div>';
    try{ if(window.ym&&window.YM_ID) ym(window.YM_ID,'reachGoal','quiz_done'); }catch(e){}
  });
})();
