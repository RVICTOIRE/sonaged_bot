const backend = 'http://127.0.0.1:5000';
let rid = null;
function setMsg(t, ok){ const m=document.getElementById('msg'); m.textContent=t; m.className = ok? 'ok':'error'; }

// Prefill from localStorage
(function init(){
  const sRid = localStorage.getItem('dailyReportId');
  if (sRid){ 
    rid = Number(sRid); 
    const ridBox = document.getElementById('ridBox');
    if (ridBox) ridBox.value = rid;
  }
  const sAgentName = localStorage.getItem('agentName');
  if (sAgentName){ 
    const matriculeField = document.getElementById('matricule');
    if (matriculeField) matriculeField.value = sAgentName;
  }
  
  // Afficher les informations récupérées
  console.log('dailyDR - Récupéré depuis localStorage:', {
    rid: rid,
    agentName: sAgentName
  });
})();

document.getElementById('saveBtn').addEventListener('click', async ()=>{
  if (!rid){ setMsg('Créez d\'abord le rapport (pages précédentes).', false); return; }
  const diff = document.getElementById('diffBox').value;
  const reco = document.getElementById('recoBox').value;
  try {
    let res = await fetch(`${backend}/rapport_journalier/${rid}/difficultes`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ text: diff }) });
    if (!res.ok) throw new Error(await res.text());
    res = await fetch(`${backend}/rapport_journalier/${rid}/recommandations`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ text: reco }) });
    if (!res.ok) throw new Error(await res.text());
    setMsg('Enregistré', true);
  } catch(e){ setMsg('Erreur: '+e.message, false); }
});

document.getElementById('recapBtn').addEventListener('click', async ()=>{
  const r = document.getElementById('recap');
  r.textContent='';
  if (!rid){ setMsg('Créez d\'abord le rapport.', false); return; }
  try{
    const data = await (await fetch(`${backend}/rapport_journalier/${rid}`)).json();
    r.textContent = JSON.stringify(data, null, 2);
  }catch(e){ setMsg('Erreur: '+e.message, false); }
});

// Finalisation depuis la page DR
const finalizeBtnDR = document.getElementById('finalizeBtnDR');
if (finalizeBtnDR){
  finalizeBtnDR.addEventListener('click', async ()=>{
    if (!rid){ setMsg('Créez d\'abord le rapport (pages précédentes).', false); return; }
    try{
      const resp = await fetch(`${backend}/rapport_journalier/${rid}/completion`);
      const comp = resp.ok ? await resp.json() : { sections:{} };
      const sections = comp.sections || {};
      const missing = Object.entries(sections).filter(([k,v])=> Number(v||0)===0).map(([k])=>k);
      const ok = confirm(missing.length? `Sections manquantes: ${missing.join(', ')}. Finaliser quand même ?` : 'Finaliser ce rapport ?');
      if (!ok) return;
      const res = await fetch(`${backend}/rapport_journalier/${rid}/finaliser`, { method:'POST' });
      if (!res.ok) throw new Error(await res.text());
      setMsg('Rapport finalisé', true);
      // Reset session/localStorage et UI
      try{
        localStorage.removeItem('dailyReportId');
        localStorage.removeItem('agentId');
        localStorage.removeItem('agentName');
      }catch(_e){}
      rid = null;
      const ridBox = document.getElementById('ridBox');
      if (ridBox) ridBox.value = '';
      const mat = document.getElementById('matricule');
      if (mat) mat.value = '';
    }catch(e){ setMsg('Erreur: '+e.message, false); }
  });
}

// Export PDF/Word (client-side)
async function buildReportHtml(data){
  const esc = (s)=> (s==null? '' : String(s));
  return `
    <html><head><meta charset="utf-8"><title>Rapport ${esc(data.id)||''}</title>
      <style>body{font-family:Arial,Segoe UI,Helvetica,sans-serif;font-size:12px} h2{margin:0 0 8px} table{border-collapse:collapse;width:100%;margin:8px 0} th,td{border:1px solid #ccc;padding:6px;text-align:left}</style>
    </head><body>
      <h2>Rapport journalier #${esc(data.id)||''}</h2>
      <div>Date: ${esc(data.date_rapport)||''}</div>
      <div>Unité/Commune: ${esc(data.unite_commune)||''}</div>
      <div>Agent ID: ${esc(data.agent_id)||''}</div>

      <h3>Collecte - Indicateurs</h3>
      <table><tbody>
        <tr><td>Planifiés</td><td>${esc(data.collecte_indicateurs?.circuits_planifies)||0}</td></tr>
        <tr><td>Collectés</td><td>${esc(data.collecte_indicateurs?.circuits_collectes)||0}</td></tr>
        <tr><td>Tonnage</td><td>${esc(data.collecte_indicateurs?.tonnage)||0}</td></tr>
        <tr><td>Dépôts récurrents</td><td>${esc(data.collecte_indicateurs?.depots_recurrents)||0}</td></tr>
        <tr><td>Levés</td><td>${esc(data.collecte_indicateurs?.depots_recurrents_leves)||0}</td></tr>
      </tbody></table>

      <h3>Collecte - Circuits</h3>
      <table><thead><tr><th>Nom</th><th>N° porte</th><th>Début</th><th>Fin</th><th>Durée</th><th>Poids</th><th>Obs.</th></tr></thead>
      <tbody>
        ${(data.collecte_circuits||[]).map(c=>`<tr><td>${esc(c.nom)}</td><td>${esc(c.numero_porte)}</td><td>${esc(c.heure_debut)}</td><td>${esc(c.heure_fin)}</td><td>${esc(c.duree)}</td><td>${esc(c.poids)}</td><td>${esc(c.observation)}</td></tr>`).join('')}
      </tbody></table>

      <h3>Poly-benne</h3>
      <table><tbody>
        <tr><td>Sites de caisses</td><td>${esc(data.polybenne?.sites_caisse)||0}</td></tr>
        <tr><td>Nb caisses</td><td>${esc(data.polybenne?.nb_caisses)||0}</td></tr>
        <tr><td>Nb caisses levées</td><td>${esc(data.polybenne?.nb_caisses_levees)||0}</td></tr>
        <tr><td>Poids collecté</td><td>${esc(data.polybenne?.poids_collecte)||0}</td></tr>
      </tbody></table>

      <h3>Nettoiement</h3>
      <table><tbody>
        <tr><td>Kilométrage planifié</td><td>${esc(data.nettoiement?.km_planifie||data.nettoiement?.km_planifie)}</td></tr>
        <tr><td>Kilométrage balayé</td><td>${esc(data.nettoiement?.km_balayes||data.nettoiement?.km_balaye)}</td></tr>
        <tr><td>Kilométrage désensablé</td><td>${esc(data.nettoiement?.km_desensables||data.nettoiement?.km_desensable)}</td></tr>
      </tbody></table>

      <h3>Mobilier urbain</h3>
      <table><thead><tr><th>Libellé</th><th>Sites</th><th>Bacs</th><th>Levés</th><th>Obs.</th></tr></thead><tbody>
        ${(data.bacs_indicateurs||[]).map(b=>`<tr><td>${esc(b.libelle)}</td><td>${esc(b.sites)}</td><td>${esc(b.nb_bacs)}</td><td>${esc(b.nb_bacs_leves)}</td><td>${esc(b.observation)}</td></tr>`).join('')}
      </tbody></table>

      <h3>Interventions</h3>
      <table><tbody>
        <tr><td>Agents mobilisés</td><td>${esc(data.moyens_equipements?.nb_agents)||0}</td></tr>
        <tr><td>Pelles mécaniques</td><td>${esc(data.moyens_equipements?.nb_pelles_mecaniques)||0}</td></tr>
        <tr><td>Tasseuses</td><td>${esc(data.moyens_equipements?.nb_tasseuses)||0}</td></tr>
        <tr><td>Camions ciel ouvert</td><td>${esc(data.moyens_equipements?.nb_camions_ouvert)||0}</td></tr>
        <tr><td>Sites</td><td>${esc(data.moyens_equipements?.sites_quartiers|| (data.sites_intervention||[]).join(', '))}</td></tr>
      </tbody></table>

      <h3>Effectifs</h3>
      <pre>${esc(JSON.stringify(data.effectifs||[], null, 2))}</pre>

      <h3>Difficultés</h3>
      <ul>${(data.difficultes||[]).map(d=>`<li>${esc(d)}</li>`).join('')}</ul>
      <h3>Recommandations</h3>
      <ul>${(data.recommandations||[]).map(d=>`<li>${esc(d)}</li>`).join('')}</ul>

      <h3>Photos</h3>
      <ul>${(data.photos||[]).map(p=>`<li>${esc(p)}</li>`).join('')}</ul>
    </body></html>
  `;
}

document.getElementById('exportPdfBtn').addEventListener('click', async ()=>{
  if (!rid){ setMsg('Créez d\'abord le rapport.', false); return; }
  try{
    const data = await (await fetch(`${backend}/rapport_journalier/${rid}`)).json();
    const html = await buildReportHtml(data);
    const w = window.open('', '_blank');
    w.document.open(); w.document.write(html); w.document.close();
    w.focus(); w.print();
  }catch(e){ setMsg('Erreur export PDF: '+e.message, false); }
});

document.getElementById('exportWordBtn').addEventListener('click', async ()=>{
  if (!rid){ setMsg('Créez d\'abord le rapport.', false); return; }
  try{
    const data = await (await fetch(`${backend}/rapport_journalier/${rid}`)).json();
    const html = await buildReportHtml(data);
    const blob = new Blob([html], { type: 'application/msword' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = `rapport_${rid}.doc`; a.click();
    URL.revokeObjectURL(url);
  }catch(e){ setMsg('Erreur export Word: '+e.message, false); }
});

function readTable(tableId, periode){
  const rows = Array.from(document.querySelectorAll(`#${tableId} tbody tr`));
  return rows.map(tr => {
    const inputs = Array.from(tr.querySelectorAll('input'));
    return {
      periode,
      categorie: inputs[0].value || '',
      effectifs: Number(inputs[1].value||0),
      presents: Number(inputs[2].value||0),
      absents: Number(inputs[3].value||0),
      malades: Number(inputs[4].value||0),
      conges: Number(inputs[5].value||0),
      remplacement: Number(inputs[6].value||0)
    };
  });
}

document.getElementById('saveEffBtn').addEventListener('click', async ()=>{
  const msg = document.getElementById('effMsg'); msg.textContent='';
  if (!rid){ msg.textContent = 'Créez d\'abord le rapport'; return; }
  const items = [ ...readTable('tabMatin','matin'), ...readTable('tabApres','apres_midi') ];
  try{
    const res = await fetch(`${backend}/rapport_journalier/${rid}/effectifs`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ items }) });
    if (!res.ok) throw new Error(await res.text());
    msg.textContent = 'Effectifs enregistrés';
  }catch(e){ msg.textContent = 'Erreur: '+e.message; }
});
