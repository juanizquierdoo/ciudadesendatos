// Prueba opcional en navegador (necesita Node.js y Playwright).
// Uso: en otra terminal, "cd web" y "python -m http.server 8765"; luego: node tests/prueba_navegador.js <carpeta para la captura>
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch(); const out = [];
  const ok = (c, m) => out.push((c ? 'OK    ' : 'FALLA ') + m);
  for (const vp of [{width:1280,height:900,name:'escritorio'},{width:390,height:844,name:'móvil'}]) {
    const p = await b.newPage({viewport:{width:vp.width,height:vp.height}});
    const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type()==='error') errs.push(m.text()); });
    // portada + buscador
    await p.goto('http://localhost:8765/');
    const total = await p.locator('#lista li:visible').count();
    await p.fill('#buscador', 'valladolid');
    const v1 = await p.locator('#lista li:visible').count();
    const cuenta = await p.textContent('#cuenta');
    await p.fill('#buscador', 'malaga');           // sin tilde debe encontrar Málaga
    const v2 = await p.locator('#lista li:visible').allTextContents();
    await p.fill('#buscador', 'hospitalet');
    const v3 = await p.locator('#lista li:visible').count();
    ok(total===151 && v1===1 && cuenta.trim()==='1 ciudad', `[${vp.name}] buscador: ${total} → 'valladolid' ${v1} (${cuenta.trim()})`);
    ok(v2.some(t=>t.includes('Málaga')), `[${vp.name}] buscador sin tildes ('malaga' → ${v2.length} resultados)`);
    ok(v3===1, `[${vp.name}] buscador con apóstrofo ('hospitalet' → ${v3})`);
    const scrollW = await p.evaluate(()=>document.documentElement.scrollWidth); ok(scrollW<=vp.width, `[${vp.name}] portada sin scroll horizontal (${scrollW}px)`);
    // ranking: ordenar
    await p.goto('http://localhost:8765/rankings/alquiler-mediano/');
    const prim = async () => (await p.locator('tbody tr').first().locator('th').textContent()).trim();
    const a0 = await prim();
    await p.click('thead button[data-col="6"]'); const a1 = await prim(); const num1 = await p.locator('tbody tr').first().locator('td').first().textContent();
    const rentas = await p.$$eval('tbody tr td:nth-child(7)', tds => tds.map(t=>parseFloat(t.dataset.v)));
    const desc = rentas.every((v,i)=>i===0||rentas[i-1]>=v);
    await p.click('thead button[data-col="6"]'); const rentas2 = await p.$$eval('tbody tr td:nth-child(7)', tds => tds.map(t=>parseFloat(t.dataset.v)));
    const asc = rentas2.every((v,i)=>i===0||rentas2[i-1]<=v);
    await p.click('thead button[data-col="1"]'); const nombres = await p.$$eval('tbody tr th', t=>t.map(x=>x.textContent.trim()));
    const alfa = nombres.every((v,i)=>i===0||nombres[i-1].localeCompare(v,'es')<=0);
    ok(desc && asc && alfa && num1.trim()==='1', `[${vp.name}] ranking ordena por renta (desc y asc), por nombre y renumera (antes 1º ${a0}, por renta 1º ${a1})`);
    // ciudad con mapa
    await p.goto('http://localhost:8765/madrid/');
    const tiles = await p.locator('.tile').count();
    await p.locator('.tile').first().hover(); const panel = await p.textContent('#panel h3');
    await p.click('#mctl button:nth-of-type(2)'); const pressed = await p.getAttribute('#mctl button:nth-of-type(2)','aria-pressed'); const lmin = await p.textContent('#lmin');
    ok(tiles===21 && panel && !panel.includes('media') && pressed==='true' && lmin.includes('€'), `[${vp.name}] mapa Madrid: ${tiles} casillas, panel «${panel}», cambio a «alquiler» (leyenda ${lmin})`);
    const dt = await p.$$eval('#distritos tbody tr td:nth-child(5)', t=>t.map(x=>parseFloat(x.dataset.v)));
    ok(dt.every((v,i)=>i===0||isNaN(v)||dt[i-1]>=v), `[${vp.name}] tabla de distritos de Madrid ordenada por peso del alquiler al cargar`);
    const sw2 = await p.evaluate(()=>document.documentElement.scrollWidth); ok(sw2<=vp.width, `[${vp.name}] Madrid sin scroll horizontal (${sw2}px)`);
    if (vp.name==='móvil') await p.screenshot({path: process.argv[2]+'/madrid_movil.png', fullPage:false});
    // ciudad sin distritos
    await p.goto('http://localhost:8765/siero/'); const h1 = await p.textContent('h1');
    ok(h1.length>0, `[${vp.name}] página sin distritos carga (${h1})`);
    ok(errs.length===0, `[${vp.name}] sin errores de JavaScript en consola ${errs.join(' | ')}`);
    await p.close();
  }
  console.log(out.join('\n')); await b.close();
})();
