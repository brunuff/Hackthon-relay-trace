/* RelayTrace: dependency-free local evidence viewer. Source material is never HTML. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const LABELS = { explicit_reference: 'Explicit reference', shared_artifact: 'Matching artifact', claimed_reuse: 'Recorded claim of reuse', candidate_match: 'Candidate match', textual_acknowledgement:'Recorded acknowledgement', textual_reproduction_attribution:'Recorded reproduction claim', preparation_claim:'Recorded preparation claim', claimed_answer_reuse:'Recorded answer reuse claim', independent_agreement:'Recorded independence claim' };
  const ORDER = { observed: 0, inferred: 1, unknown: 2 };
  const PAGE_SIZE = 40;
  let corpus, eventMap, edgeMap, eventSearch, edgeSearch;
  let view = 'relations', selectedId = null, visibleLimit = PAGE_SIZE, filteredItems = [];

  function string(value, fallback = '') { return typeof value === 'string' ? value : typeof value === 'number' ? String(value) : fallback; }
  function list(value) { return Array.isArray(value) ? value : []; }
  function el(tag, cls, content) { const node = document.createElement(tag); if (cls) node.className = cls; if (content !== undefined) node.textContent = string(content); return node; }
  function clear(node) { node.replaceChildren(); }
  function readableType(value) { return LABELS[value] || string(value).replaceAll('_', ' ') || 'Unspecified relation'; }
  function parsedTime(value) {
    // Do not turn numeric or timezone-less input into a guessed UTC timestamp.
    if(typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(value)) return null;
    const parts = value.slice(0,19).split(/[-T:]/).map(Number);
    const [year,month,day,hour,minute,second] = parts;
    const days = new Date(Date.UTC(year,month,0)).getUTCDate();
    if(month < 1 || month > 12 || day < 1 || day > days || hour > 23 || minute > 59 || second > 59) return null;
    const t = Date.parse(value); return Number.isFinite(t) ? t : null;
  }
  function dateLabel(value, full = false) {
    const t = parsedTime(value);
    if (t === null) return 'Time unknown';
    const d = new Date(t);
    return full ? d.toISOString().replace('T', ' ').replace('.000Z', ' UTC') : d.toISOString().slice(5, 16).replace('T', ' ') + ' UTC';
  }
  function excerpt(value, size = 165) { const s = string(value).replace(/\s+/g, ' ').trim(); return s.length > size ? s.slice(0, size - 1) + '…' : s; }
  function statusBadge(status) { return el('span', 'status ' + status, status); }
  function safeLink(url, label) {
    try {
      const parsed = new URL(string(url));
      if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) return null;
      const link = el('a', 'source-link', label || parsed.href);
      link.href = parsed.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
      return link;
    } catch { return null; }
  }
  function notice(message, error = false) { $('notice').textContent = message; $('notice').className = 'notice' + (error ? ' error' : ''); $('notice').hidden = !message; }
  function normalize(data) {
    if (!data || typeof data !== 'object' || !Array.isArray(data.events) || !Array.isArray(data.edges)) throw new Error('Expected an evidence JSON object with events and edges arrays.');
    if (data.events.length > 100000 || data.edges.length > 200000) throw new Error('This snapshot is too large for the local viewer. Export a focused episode first.');
    if (data.events.some(e => !e || typeof e !== 'object' || Array.isArray(e)) || data.edges.some(e => !e || typeof e !== 'object' || Array.isArray(e))) throw new Error('Each event and relation must be a JSON object.');
    if (list(data.episodes).some(e => !e || typeof e !== 'object' || Array.isArray(e) || typeof e.id !== 'string' || !e.id)) throw new Error('Each episode must be an object with a nonempty string ID.');
    if(new Set(list(data.episodes).map(e => e.id)).size !== list(data.episodes).length) throw new Error('Episode IDs must be unique.');
    const events = data.events.map((entry, i) => ({ ...entry, id: string(entry?.id, 'event-' + i), timestamp: typeof entry?.timestamp === 'string' ? entry.timestamp : '', actor_handle: string(entry?.actor_handle, 'Unknown handle'), page: string(entry?.page, 'Unknown page'), text: string(entry?.text), source_url: string(entry?.source_url), _time: typeof entry?.timestamp === 'string' ? parsedTime(entry.timestamp) : null }));
    const eventIds = new Set(events.map(e => e.id));
    if (eventIds.size !== events.length) throw new Error('Event IDs must be unique.');
    const edges = data.edges.map((entry, i) => ({ ...entry, id: string(entry?.id, 'edge-' + i), source: string(entry?.source), target: string(entry?.target), status: ['observed', 'inferred', 'unknown'].includes(entry?.status) ? entry.status : 'unknown', edge_type: string(entry?.edge_type, 'candidate_match'), rationale: string(entry?.rationale), evidence: list(entry?.evidence), shared_tokens: list(entry?.shared_tokens) }));
    if (new Set(edges.map(e => e.id)).size !== edges.length) throw new Error('Relation IDs must be unique.');
    return { ...data, dataset: data.dataset && typeof data.dataset === 'object' ? data.dataset : {}, events, edges, episodes: list(data.episodes) };
  }
  function option(select, value, label) { const opt = el('option', '', label); opt.value = value; select.append(opt); }
  function populateSelect(id, items, emptyLabel) { const select = $(id); clear(select); option(select, '', emptyLabel); items.forEach(item => option(select, item[0], item[1])); }
  function load(data, imported = false) {
    corpus = normalize(data);
    eventMap = new Map(corpus.events.map(e => [e.id, e]));
    edgeMap = new Map(corpus.edges.map(e => [e.id, e]));
    eventSearch = new Map(corpus.events.map(e => [e.id, [e.id, e.actor_handle, e.page, e.text].join('\n').toLowerCase()]));
    edgeSearch = new Map(corpus.edges.map(e => [e.id, [e.id, e.rationale, e.edge_type, eventSearch.get(e.source) || '', eventSearch.get(e.target) || '', ...e.evidence.map(q => string(q?.quote)), ...e.shared_tokens.map(v => string(v))].join('\n').toLowerCase()]));
    const handles = [...new Set(corpus.events.map(e => e.actor_handle))].sort((a,b) => a.localeCompare(b));
    const pages = [...new Set(corpus.events.map(e => e.page))].sort((a,b) => a.localeCompare(b));
    populateSelect('actor-select', handles.map(v => [v,v]), 'All handles');
    populateSelect('page-select', pages.map(v => [v,v]), 'All pages');
    populateSelect('type-select', [...new Set(corpus.edges.map(e => e.edge_type))].sort().map(v => [v,readableType(v)]), 'All types');
    populateSelect('episode-select', corpus.episodes.map((e,i) => [string(e.id, 'episode-' + i), string(e.title, 'Untitled episode')]), 'All episodes');
    $('dataset-title').textContent = string(corpus.dataset.title, 'Imported evidence snapshot');
    $('dataset-context').textContent = [string(corpus.dataset.acquisition_mode), corpus.dataset.retrieved_at ? 'Retrieved ' + dateLabel(corpus.dataset.retrieved_at, true) : 'Retrieval date not supplied'].filter(Boolean).join(' · ');
    $('event-count').textContent = corpus.events.length.toLocaleString(); $('edge-count').textContent = corpus.edges.length.toLocaleString(); $('handle-count').textContent = handles.length.toLocaleString(); $('page-count').textContent = pages.length.toLocaleString();
    const synthetic = corpus.dataset.synthetic === true || /synthetic|demo_generated/i.test(string(corpus.dataset.acquisition_mode));
    $('dataset-badge').textContent = synthetic ? 'Synthetic example · not findings' : corpus.dataset.access_class === 'restricted-research' ? 'Restricted research snapshot' : corpus.dataset.source_url ? 'Evidence snapshot' : 'Local evidence snapshot';
    $('dataset-badge').className = 'dataset-badge' + (synthetic ? ' synthetic' : '');
    clear($('limitations-list'));
    const limitations = list(corpus.dataset.limitations);
    (limitations.length ? limitations : ['Coverage limitations were not supplied with this dataset.']).forEach(item => $('limitations-list').append(el('li', '', string(item))));
    clear($('dataset-provenance'));
    const provenance = el('div','provenance');
    provenance.append(el('p','', 'Dataset: ' + string(corpus.dataset.id, 'Unspecified')));
    if (corpus.dataset.sha256) provenance.append(el('p','', 'SHA-256: ' + string(corpus.dataset.sha256)));
    for (const [url,label] of [[corpus.dataset.source_url,'Source report ↗'],[corpus.dataset.download_url,'Dataset download ↗']]) { const link = safeLink(url,label); if(link) provenance.append(link); }
    $('dataset-provenance').append(provenance);
    reset(false); selectedId = view === 'relations' ? corpus.edges.find(e => e.status === 'observed')?.id || null : null;
    notice(synthetic ? 'This is a synthetic demonstration. Import a real evidence.json file to analyze sourced records.' : imported ? 'Opened locally. No file content was uploaded or fetched from embedded URLs.' : '');
    render();
  }
  function filters() {
    return { query: $('search-input').value.trim().toLowerCase(), episode: $('episode-select').value, status: $('status-select').value, type: $('type-select').value, actor: $('actor-select').value, page: $('page-select').value, from: $('date-from').value ? Date.parse($('date-from').value + 'T00:00:00Z') : null, to: $('date-to').value ? Date.parse($('date-to').value + 'T23:59:59.999Z') : null };
  }
  function eventFits(event, f, query = true) {
    if (!event) return false;
    if (f.actor && event.actor_handle !== f.actor) return false;
    if (f.page && event.page !== f.page) return false;
    if ((f.from !== null || f.to !== null) && event._time === null) return false;
    if (f.from !== null && event._time < f.from) return false;
    if (f.to !== null && event._time > f.to) return false;
    return !query || !f.query || (eventSearch.get(event.id) || '').includes(f.query);
  }
  function edgeFits(edge,f,episode) {
    if (episode && !list(episode.edge_ids).includes(edge.id)) return false;
    if (f.status && edge.status !== f.status || f.type && edge.edge_type !== f.type) return false;
    const source = eventMap.get(edge.source), target = eventMap.get(edge.target);
    // Handle/page/date filters apply to either endpoint; a match does not prove actor identity.
    if ((f.actor || f.page || f.from !== null || f.to !== null) && !eventFits(source,{...f,query:''},false) && !eventFits(target,{...f,query:''},false)) return false;
    return !f.query || (edgeSearch.get(edge.id) || '').includes(f.query);
  }
  function itemTime(item) { return view === 'posts' ? item._time : eventMap.get(item.target)?._time ?? eventMap.get(item.source)?._time ?? null; }
  function hasEstablishedOrder(edge) {
    const source = eventMap.get(edge.source), target = eventMap.get(edge.target);
    if(edge.directed === false || source?._time === null || target?._time === null || !source || !target) return false;
    const uncertainty = [source.timestamp_uncertainty_seconds,target.timestamp_uncertainty_seconds].reduce((sum,v) => sum + (typeof v === 'number' && Number.isFinite(v) && v > 0 ? v : 0),0);
    return target._time - source._time > uncertainty * 1000;
  }
  function render(selectFirst = false) {
    const f = filters(), episode = corpus.episodes.find(e => string(e.id) === f.episode);
    const matchingEdges = corpus.edges.filter(e => edgeFits(e,f,episode));
    if (view === 'relations') filteredItems = matchingEdges;
    else {
      const relatedIds = new Set(matchingEdges.flatMap(e => [e.source,e.target]));
      filteredItems = corpus.events.filter(e => (!episode || list(episode.event_ids).includes(e.id)) && eventFits(e,f) && (!(f.status || f.type) || relatedIds.has(e.id)));
    }
    const sort = $('sort-select').value;
    filteredItems.sort((a,b) => { if(sort === 'strength' && view === 'relations') { const diff = ORDER[a.status] - ORDER[b.status]; if(diff) return diff; } const at = itemTime(a),bt = itemTime(b); if(at === null || bt === null) return at === bt ? a.id.localeCompare(b.id) : at === null ? 1 : -1; return (sort === 'newest' ? -1 : 1) * (at - bt) || a.id.localeCompare(b.id); });
    $('result-count').textContent = filteredItems.length.toLocaleString() + (view === 'relations' ? ' relations' : ' records') + ' match';
    const times = filteredItems.map(itemTime).filter(t => t !== null);
    $('time-range').textContent = times.length ? new Date(times.reduce((a,b) => Math.min(a,b),Infinity)).toISOString().slice(0,10) + ' – ' + new Date(times.reduce((a,b) => Math.max(a,b),-Infinity)).toISOString().slice(0,10) : '';
    $('episode-context').hidden = !episode; clear($('episode-context'));
    if (episode) { $('episode-context').append(el('h3','',string(episode.title)),el('p','',string(episode.interpretation))); list(episode.limitations).forEach(v => $('episode-context').append(el('p','',string(v)))); }
    if(selectFirst || !filteredItems.some(e => e.id === selectedId)) selectedId = filteredItems[0]?.id || null;
    clear($('results'));
    filteredItems.slice(0,visibleLimit).forEach(item => $('results').append(view === 'relations' ? edgeCard(item) : eventCard(item)));
    if(!filteredItems.length) $('results').append(el('div','empty-results','No records match these filters. Try a broader search or reset the filters.'));
    $('more-button').hidden = filteredItems.length <= visibleLimit;
    $('more-button').textContent = 'Show next ' + Math.min(PAGE_SIZE,filteredItems.length-visibleLimit) + ' of ' + filteredItems.length.toLocaleString();
    renderDetail();
  }
  function select(itemId) { selectedId = itemId; render(); }
  function edgeCard(edge) {
    const source = eventMap.get(edge.source), target = eventMap.get(edge.target);
    const card = el('button','result-card' + (selectedId === edge.id ? ' selected' : ''));
    card.type = 'button'; card.setAttribute('aria-pressed', selectedId === edge.id ? 'true' : 'false'); card.addEventListener('click',() => select(edge.id));
    const top = el('div','card-top'); top.append(statusBadge(edge.status),el('span','card-date',dateLabel(target?.timestamp || source?.timestamp))); card.append(top);
    card.append(el('div','card-title',readableType(edge.edge_type)),el('div','card-path',(source?.actor_handle || 'Missing source') + (hasEstablishedOrder(edge) ? ' → ' : ' ↔ ') + (target?.actor_handle || 'Missing target')));
    card.append(el('p','card-excerpt',excerpt(edge.rationale || target?.text)));
    const bottom = el('div','card-bottom'); bottom.append(el('span','card-tag',target?.page || source?.page || 'Unknown page'),el('span','',edge.evidence.length + ' evidence ' + (edge.evidence.length === 1 ? 'quote' : 'quotes'))); card.append(bottom);
    return card;
  }
  function eventCard(event) {
    const card = el('button','result-card' + (selectedId === event.id ? ' selected' : '')); card.type = 'button'; card.setAttribute('aria-pressed',selectedId === event.id ? 'true' : 'false'); card.addEventListener('click',() => select(event.id));
    const top = el('div','card-top'); top.append(el('span','eyebrow','SOURCE RECORD'),el('span','card-date',dateLabel(event.timestamp))); card.append(top,el('div','card-title',event.actor_handle),el('div','card-path',event.page),el('p','card-excerpt',excerpt(event.text)));
    const count = corpus.edges.filter(e => e.source === event.id || e.target === event.id).length;
    card.append(el('div','card-bottom',count + ' linked ' + (count === 1 ? 'relation' : 'relations'))); return card;
  }
  function section(title) { const node = el('div','detail-section'); if(title) node.append(el('h3','',title)); return node; }
  function flag(label,observed) { const node = el('div','flag'); node.append(el('span','flag-label',label),el('span','flag-value',observed === true ? 'Recorded as observed' : 'Not established here')); return node; }
  function provenanceBlock(event) {
    const block = el('div','provenance'), dl = el('dl');
    const rows = [['Record',event.id],['Revision',string(event.source_revision_id,'Not supplied')],['Extraction',string(event.provenance?.extraction,'Not supplied')],['Clock source',string(event.provenance?.winning_clock,'Not supplied')],['Clock grade',string(event.timestamp_grade,'Not supplied')],['Time uncertainty',typeof event.timestamp_uncertainty_seconds === 'number' ? event.timestamp_uncertainty_seconds + ' s' : 'Not supplied'],['Dataset',string(event.provenance?.dataset_id || corpus.dataset.id,'Not supplied')],['Record path',string(event.provenance?.record_path,'Not supplied')],['SHA-256',string(event.content_sha256,'Not supplied')]];
    rows.forEach(([label,value]) => dl.append(el('dt','',label),el('dd','',value))); block.append(dl);
    const link = safeLink(event.source_url,'Open source URL ↗'); if(link) block.append(link); else if(event.source_url) block.append(el('p','note','Non-HTTP source URL: ' + event.source_url));
    return block;
  }
  function postBox(event,label) {
    const box = el('article','post-box');
    if(!event) { box.append(el('div','post-text','The referenced record is missing from this snapshot.')); return box; }
    const head = el('header',''); head.append(el('div','post-label',label)); const heading = el('div','post-heading'); heading.append(el('strong','',event.actor_handle),el('span','',dateLabel(event.timestamp,true))); head.append(heading,el('p','post-meta',event.page));
    if(event.provenance?.extraction) head.append(el('p','post-meta','Changed-line evidence · ' + string(event.provenance.extraction)));
    if(!event.timestamp || event._time === null) head.append(el('p','post-date-warning','Timestamp unavailable; temporal order is not established.'));
    else if(typeof event.timestamp_uncertainty_seconds === 'number' && event.timestamp_uncertainty_seconds > 0) head.append(el('p','post-date-warning','Publisher timestamp uncertainty: ' + event.timestamp_uncertainty_seconds + ' seconds.'));
    box.append(head,el('pre','post-text',event.text || '[No text supplied]'));
    const details = el('details',''); details.append(el('summary','','Source provenance'),provenanceBlock(event)); box.append(details); return box;
  }
  function renderDetail() {
    const panel = $('detail-panel'); clear(panel);
    if(!selectedId) { const empty = el('div','empty-detail'); empty.append(el('span','empty-symbol','⌁'),el('h2','','No selection'),el('p','','Choose a matching relation or record to inspect its underlying evidence.')); panel.append(empty); return; }
    if(view === 'posts') { renderEventDetail(eventMap.get(selectedId)); return; }
    const edge = edgeMap.get(selectedId); if(!edge) return;
    const source = eventMap.get(edge.source), target = eventMap.get(edge.target);
    const head = el('div','detail-head'); head.append(el('p','eyebrow','SELECTED RELATION')); const title = el('div','detail-title-row'); title.append(el('h2','',readableType(edge.edge_type)),statusBadge(edge.status)); head.append(title,el('p','',edge.rationale),el('div','detail-id',edge.id)); panel.append(head);
    const flags = section('What is established'); const grid = el('div','evidence-flags'); grid.append(flag('Independent receipt evidence',edge.receipt_observed),flag('Causal uptake or goal adoption',edge.causal_uptake_observed)); flags.append(grid,el('p','note','Relation status describes the textual or artifact link. It does not independently verify the underlying claim.')); panel.append(flags);
    const ordered = hasEstablishedOrder(edge);
    const posts = section('Underlying records'); const pair = el('div','source-pair'); pair.append(postBox(source,ordered ? 'Earlier / source record' : 'Record A · order unresolved'));
    let elapsed = ordered ? 'Later publisher timestamp' : 'Order unresolved · association only';
    if(ordered && typeof edge.seconds_elapsed === 'number' && Number.isFinite(edge.seconds_elapsed)) elapsed = edge.seconds_elapsed < 120 ? edge.seconds_elapsed + ' seconds between publisher timestamps' : edge.seconds_elapsed < 7200 ? Math.round(edge.seconds_elapsed / 60) + ' minutes between publisher timestamps' : (edge.seconds_elapsed/3600).toFixed(1) + ' hours between publisher timestamps';
    pair.append(el('div','connector-label',(ordered ? '↓  ' : '↔  ') + elapsed),postBox(target,ordered ? 'Later / target record' : 'Record B · order unresolved')); posts.append(pair);
    if(edge.elapsed_basis) posts.append(el('p','note',string(edge.elapsed_basis)));
    if(ordered && typeof edge.elapsed_uncertainty_seconds === 'number' && edge.elapsed_uncertainty_seconds > 0) posts.append(el('p','note','Elapsed-time uncertainty: ±' + edge.elapsed_uncertainty_seconds + ' seconds.'));
    panel.append(posts);
    const quotes = section('Evidence excerpts');
    if(!edge.evidence.length) quotes.append(el('p','note','No supporting excerpts were supplied.'));
    edge.evidence.forEach((entry,i) => { const container = el('div',''); container.append(el('blockquote','quote',string(entry?.quote)),el('p','quote-meta','Excerpt ' + (i+1) + ' · ' + string(entry?.event_id,'Record not supplied'))); const link = safeLink(entry?.source_url,'Source ↗'); if(link) container.append(link); quotes.append(container); }); panel.append(quotes);
    if(edge.shared_tokens.length) { const tokens = section('Shared artifact strings'); const row = el('div','tokens'); edge.shared_tokens.forEach(t => row.append(el('span','token',string(t)))); tokens.append(row,el('p','note','Matching strings support a connection; they do not establish who read them.')); panel.append(tokens); }
    const notes = section('Interpretation limits'); notes.append(el('p','note',['claimed_reuse','textual_reproduction_attribution','claimed_answer_reuse','preparation_claim'].includes(edge.edge_type) ? 'This relation contains a recorded claim of reuse or preparation. A claim is not an independently verified action or successful reproduction.' : ['shared_artifact','independent_agreement'].includes(edge.edge_type) ? 'Both records contain a matching artifact. Common prompts, shared sources, quotation, or independent discovery can also produce matches.' : 'An explicit reference may support transmission of information. It does not establish that the later actor adopted a broader goal.'));
    list(edge.limitations).forEach(v => notes.append(el('p','note',string(v)))); panel.append(notes);
  }
  function renderEventDetail(event) {
    if(!event) return;
    const panel = $('detail-panel'), head = el('div','detail-head'); head.append(el('p','eyebrow','SELECTED SOURCE RECORD'),el('h2','',event.actor_handle),el('p','',event.page),el('div','detail-id',event.id)); panel.append(head);
    const post = section(); post.append(postBox(event,'Source record')); panel.append(post);
    const relations = corpus.edges.filter(e => e.source === event.id || e.target === event.id), related = section('Relations involving this record');
    if(!relations.length) related.append(el('p','note','No relation involving this record was supplied in the snapshot.'));
    const links = el('div','detail-links'); relations.forEach(edge => { const button = el('button','related-button',readableType(edge.edge_type) + ' · ' + edge.status + ' · ' + edge.id); button.type = 'button'; button.addEventListener('click',() => { changeView('relations'); reset(false); selectedId = edge.id; render(); }); links.append(button); }); related.append(links); panel.append(related);
  }
  function reset(doRender = true) { for(const id of ['search-input','episode-select','status-select','type-select','actor-select','page-select','date-from','date-to']) $(id).value = ''; $('sort-select').value = 'oldest'; visibleLimit = PAGE_SIZE; if(doRender) render(true); }
  function changeView(next) { view = next; selectedId = null; visibleLimit = PAGE_SIZE; $('relations-tab').classList.toggle('active',view === 'relations'); $('posts-tab').classList.toggle('active',view === 'posts'); $('relations-tab').setAttribute('aria-selected',String(view === 'relations')); $('posts-tab').setAttribute('aria-selected',String(view === 'posts')); render(true); }
  for(const id of ['search-input','episode-select','status-select','type-select','actor-select','page-select','date-from','date-to','sort-select']) $(id).addEventListener(id === 'search-input' ? 'input' : 'change',() => { visibleLimit = PAGE_SIZE; render(true); });
  $('reset-button').addEventListener('click',() => reset()); $('relations-tab').addEventListener('click',() => changeView('relations')); $('posts-tab').addEventListener('click',() => changeView('posts'));
  $('more-button').addEventListener('click',() => { visibleLimit += PAGE_SIZE; render(); });
  $('theme-button').addEventListener('click',() => { const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; document.documentElement.dataset.theme = next; $('theme-button').setAttribute('aria-label','Switch to ' + (next === 'dark' ? 'light' : 'dark') + ' theme'); try { localStorage.setItem('relaytrace-theme',next); } catch {} });
  try { const theme = localStorage.getItem('relaytrace-theme'); if(theme === 'light' || theme === 'dark') document.documentElement.dataset.theme = theme; } catch {}
  $('file-input').addEventListener('change',async event => {
    const file = event.target.files?.[0]; if(!file) return;
    try { if(file.size > 64 * 1024 * 1024) throw new Error('Use an episode export smaller than 64 MB.'); const data = JSON.parse(await file.text()); load(data,true); } catch(error) { notice('Could not open this file: ' + string(error?.message,'Invalid evidence JSON.'),true); } finally { event.target.value = ''; }
  });
  try { load(window.SWARM_TRACER_DATA || {dataset:{title:'No snapshot supplied',limitations:['Open a local evidence.json snapshot.']},events:[],edges:[],episodes:[]}); } catch(error) { notice('Could not load the bundled snapshot: ' + string(error?.message),true); }
})();
