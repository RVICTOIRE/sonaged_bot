const backend = 'http://127.0.0.1:5000';
const ridSpan = document.getElementById('rid');
let rid = null;

async function fetchJson(url, opts){
  const res = await fetch(url, opts);
  const ct = res.headers.get('content-type') || '';
  if (!ct.includes('application/json')) {
    const text = await res.text(); throw new Error(text);
  }
  const json = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(json));
  return json;
}

let agentId = null;
async function verifyMatricule(){
  const input = document.getElementById('matriculeInput');
  const nameBox = document.getElementById('agentName');
  const btnCreate = document.getElementById('createBtn');
  agentId = null; nameBox.value = ''; btnCreate.disabled = true;
  const m = (input.value||'').trim(); if (!m) return;
  try{
    const res = await fetchJson(`${backend}/agents?matricule=${encodeURIComponent(m)}`);
    const ag = (res.items||[])[0];
    if (ag){
      agentId = ag.id;
      nameBox.value = ag.nom;
      // Renseigner automatiquement l'unité/commune selon la zone d'affectation de l'agent
      const uniteField = document.getElementById('uniteInput');
      const unitVal = ag.zone_affectation || ag.unite_commune || '';
      if (uniteField && unitVal) uniteField.value = unitVal;
      btnCreate.disabled = false;
    }
  }catch(e){ agentId = null; nameBox.value=''; btnCreate.disabled = true; }
}
document.getElementById('checkMatBtn').addEventListener('click', verifyMatricule);

document.getElementById('createBtn').addEventListener('click', async ()=>{
  const date = document.getElementById('dateInput').value;
  const unite = document.getElementById('uniteInput').value;
  const msg = document.getElementById('createMsg');
  msg.textContent = '';
  try{
    const res = await fetchJson(`${backend}/rapport_journalier`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ date_rapport: date, unite_commune: unite, agent_id: agentId })});
    rid = res.id; ridSpan.textContent = rid;
    msg.textContent = 'Créé'; msg.className='ok';
    // Persist
    localStorage.setItem('dailyReportId', String(rid));
    if (agentId) localStorage.setItem('agentId', String(agentId));
    const agentName = document.getElementById('agentName')?.value || '';
    if (agentName) localStorage.setItem('agentName', agentName);
  }catch(e){ msg.textContent = 'Erreur: '+e.message; msg.className='error'; }
});

      // Prefill from localStorage if present
      (function initFromStorage(){
        const sRid = localStorage.getItem('dailyReportId');
        if (sRid){ rid = Number(sRid); ridSpan.textContent = rid; }
        const sAgentName = localStorage.getItem('agentName');
        if (sAgentName){ const an = document.getElementById('agentName'); if (an) an.value = sAgentName; }
      })();

      // Fonction pour mettre à jour le statut de complétion
      async function updateCompletionStatus() {
        if (!rid) return;
        
        try {
          const response = await fetch(`${backend}/rapport_journalier/${rid}/completion`);
          if (response.ok) {
            const data = await response.json();
            const statusEl = document.getElementById('completionStatus');
            const fillEl = document.getElementById('completionFill');
            const textEl = document.getElementById('completionText');
            
            if (statusEl && fillEl && textEl) {
              statusEl.style.display = 'block';
              fillEl.style.width = `${data.completion_percentage}%`;
              textEl.textContent = `${data.completion_percentage}% - ${data.status.toUpperCase()}`;
              textEl.className = `completion-text ${data.status}`;
            }
          }
        } catch (e) {
          console.error('Erreur lors de la mise à jour du statut:', e);
        }
      }

      // Mettre à jour le statut après chaque sauvegarde
      document.addEventListener('DOMContentLoaded', () => {
        if (rid) {
          updateCompletionStatus();
        }
      });

document.getElementById('saveIndicsBtn').addEventListener('click', async ()=>{
  const msg = document.getElementById('indicsMsg'); msg.textContent='';
  if (!rid){ msg.textContent='Créez d\'abord le rapport'; msg.className='error'; return; }
  const payload = {
    circuits_planifies: Number(document.getElementById('collPlan').value||0),
    circuits_collectes: Number(document.getElementById('collColl').value||0),
    tonnage: Number(document.getElementById('collTonn').value||0),
    depots_recurrents: Number(document.getElementById('collRec').value||0),
    depots_recurrents_leves: Number(document.getElementById('collRecLev').value||0),
    depots_sauvages_identifies: document.getElementById('collSavId').value||null,
    depots_sauvages_traites: document.getElementById('collSavTr').value||null,
  };
  try{
    const url = `${backend}/rapport_journalier/${rid}/collecte/indicateurs`;
    const res = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
          if (!res.ok){ throw new Error(await res.text()); }
          msg.textContent='Enregistré'; msg.className='ok';
          updateCompletionStatus();
  }catch(e){ msg.textContent='Erreur: '+e.message; msg.className='error'; }
});

async function loadCircuits(){
  const tbody = document.getElementById('circuitsTbody'); tbody.innerHTML='';
  if (!rid) return;
  try{
    const data = await fetchJson(`${backend}/rapport_journalier/${rid}`);
    (data.collecte_circuits||[]).forEach((c, idx)=>{
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${c.nom||''}</td><td>${c.numero_porte||''}</td><td>${c.heure_debut||''}</td><td>${c.heure_fin||''}</td><td>${c.duree||''}</td><td>${c.poids||''}</td><td>${c.observation||''}</td><td><button data-idx="${idx}" class="delBtn">Supprimer</button></td>`;
      tbody.appendChild(tr);
    });
    document.querySelectorAll('.delBtn').forEach(btn=>{
      btn.addEventListener('click', async ()=>{ alert('Suppression de circuit non implémentée.'); });
    });
  }catch(e){ console.error(e); }
}

document.getElementById('addCircuitBtn').addEventListener('click', async ()=>{
  const msg = document.getElementById('circuitMsg'); msg.textContent='';
  if (!rid){ msg.textContent='Créez d\'abord le rapport'; msg.className='error'; return; }
  const payload = {
    nom: document.getElementById('cNom').value||null,
    numero_porte: document.getElementById('cPorte').value||null,
    heure_debut: document.getElementById('cDeb').value? document.getElementById('cDeb').value+':00': null,
    heure_fin: document.getElementById('cFin').value? document.getElementById('cFin').value+':00': null,
    duree: document.getElementById('cDur').value||null,
    poids: document.getElementById('cPoids').value||null,
    observation: document.getElementById('cObs').value||null,
  };
  try{
    const url = `${backend}/rapport_journalier/${rid}/collecte/circuits`;
    const res = await fetch(url, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    if (!res.ok){ throw new Error(await res.text()); }
    msg.textContent = 'Ajouté'; msg.className='ok';
    await loadCircuits();
  }catch(e){ msg.textContent='Erreur: '+e.message; msg.className='error'; }
});

document.getElementById('refreshRecap').addEventListener('click', async ()=>{
  const box = document.getElementById('recapBox'); const m = document.getElementById('recapMsg');
  if (!rid){ m.textContent='Créez d\'abord le rapport'; m.className='error'; return; }
  m.textContent='';
  try{
    const data = await fetchJson(`${backend}/rapport_journalier/${rid}`);
    box.textContent = JSON.stringify(data, null, 2);
    await loadCircuits();
  }catch(e){ box.textContent = 'Erreur: '+e.message; }
});

// Finalisation du rapport
const finalizeBtn = document.getElementById('finalizeBtn');
if (finalizeBtn){
  finalizeBtn.addEventListener('click', async ()=>{
    const msg = document.getElementById('recapMsg');
    if (!rid){ msg.textContent = 'Créez d\'abord le rapport'; msg.className='error'; return; }
    msg.textContent = '';
    try{
      const comp = await fetchJson(`${backend}/rapport_journalier/${rid}/completion`);
      const sections = comp.sections || {};
      const missing = Object.entries(sections).filter(([k,v])=> Number(v||0)===0).map(([k])=>k);
      const ok = confirm(missing.length? `Sections manquantes: ${missing.join(', ')}. Finaliser quand même ?` : 'Finaliser ce rapport ?');
      if (!ok) return;
      const res = await fetch(`${backend}/rapport_journalier/${rid}/finaliser`, { method:'POST' });
      if (!res.ok) throw new Error(await res.text());
      msg.textContent = 'Rapport finalisé'; msg.className='ok';
      updateCompletionStatus();
      // Reset session/localStorage et UI
      try{
        localStorage.removeItem('dailyReportId');
        localStorage.removeItem('agentId');
        localStorage.removeItem('agentName');
      }catch(_e){}
      rid = null;
      const ridSpanEl = document.getElementById('rid');
      if (ridSpanEl) ridSpanEl.textContent = '—';
      const agentNameEl = document.getElementById('agentName');
      if (agentNameEl) agentNameEl.value = '';
    }catch(e){ msg.textContent = 'Erreur: '+e.message; msg.className='error'; }
  });
}

document.getElementById('savePolyBtn').addEventListener('click', async ()=>{
  const msg = document.getElementById('polyMsg'); msg.textContent='';
  if (!rid){ msg.textContent='Créez d\'abord le rapport'; msg.className='error'; return; }
  const payload = {
    sites_caisse: Number(document.getElementById('pbSites').value||0),
    nb_caisses: Number(document.getElementById('pbNb').value||0),
    nb_caisses_levees: Number(document.getElementById('pbNbLev').value||0),
    poids_collecte: Number(document.getElementById('pbPoids').value||0)
  };
  try{
    const res = await fetch(`${backend}/rapport_journalier/${rid}/polybenne`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
          if (!res.ok){ throw new Error(await res.text()); }
          msg.textContent='Enregistré'; msg.className='ok';
          updateCompletionStatus();
  }catch(e){ msg.textContent='Erreur: '+e.message; msg.className='error'; }
});

