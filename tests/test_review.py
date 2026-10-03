"""Independent checks of evidence validity and untrusted-content handling.

Run with: PYTHONPATH=src python -m unittest discover -s tests -v
These checks intentionally avoid asserting the particular demo's edge count.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import tempfile
import unittest

from swarm_tracer.pipeline import generate_edges, normalize_revisions


def revision(seq, body, *, page="dse/ReviewPage", actor="ResearchAlpha", time="2026-06-20T12:00:00Z"):
    return {
        "rev_id": f"{page.replace('/', '~')}@{seq}",
        "page_id": page,
        "page_key": page.replace("/", "~"),
        "wiki": page.split("/")[0],
        "name": page.split("/")[-1],
        "seq": seq,
        "body": body,
        "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "label": actor,
        "time": time,
        "time_grade": "reqlog" if time else "unknown",
        "hunks": [],
        "diff_base": None,
    }


class IndependentEvidenceReview(unittest.TestCase):
    def test_unchanged_snapshot_is_not_new_content(self):
        body = "ResearchAlpha: distinctive answer-vector 14927, 57381, 99013."
        events = normalize_revisions([
            revision(1, body),
            revision(2, body, actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        later = next(e for e in events if e["source_revision_id"].endswith("@2"))
        self.assertEqual(later["text"], "")
        self.assertEqual(generate_edges(events), [])

    def test_inherited_url_is_not_attributed_to_later_editor(self):
        first = "ResearchAlpha: https://example.invalid/unique-task-result?id=185729301"
        events = normalize_revisions([
            revision(1, first),
            revision(2, first + "\nResearchBeta: hello, I am still working.", actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        later = next(e for e in events if e["source_revision_id"].endswith("@2"))
        self.assertNotIn("unique-task-result", later["text"])
        self.assertEqual(generate_edges(events), [])

    def test_generic_completion_words_do_not_create_reuse(self):
        events = normalize_revisions([
            revision(1, "Task complete. DONE. Thanks for your help. I will continue working.", page="dse/One", actor="ResearchAlpha"),
            revision(1, "Task complete. DONE. Thanks for your help. I will continue working.", page="dse/Two", actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        self.assertEqual(generate_edges(events), [])

    def test_minor_line_edit_does_not_create_new_attribution(self):
        url = "https://example.invalid/unique-task-result?id=185729301"
        events = normalize_revisions([
            revision(1, f"ResearchAlpha: answer at {url}", page="dse/One"),
            revision(1, f"Copy from ResearchAlpha: answer at {url}. Status pending.", page="dse/Two", actor="ResearchGamma", time="2026-06-20T12:01:00Z"),
            revision(2, f"Copy from ResearchAlpha: answer at {url}. Status checked.", page="dse/Two", actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        later = next(e for e in events if e["source_revision_id"] == "dse~Two@2")
        related = [edge for edge in generate_edges(events) if later["id"] in (edge["source"], edge["target"])]
        self.assertEqual(related, [], "An unchanged artifact in a modified line is inherited content, not a newly authored reuse")

    def test_conflicting_duplicate_revision_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_revisions([revision(1, "first body"), revision(1, "different body")])

    def test_handle_prefix_is_not_an_explicit_reference(self):
        url = "https://example.invalid/unique-answer-set?id=185729301"
        events = normalize_revisions([
            revision(1, f"AgentA: answer at {url}", page="dse/One", actor="AgentA"),
            revision(1, f"AgentB: AgentAB shared answer at {url}", page="dse/Two", actor="AgentB", time="2026-06-20T12:02:00Z"),
        ])
        edges = generate_edges(events)
        self.assertTrue(edges)
        self.assertTrue(all(edge["status"] != "observed" for edge in edges), "A prefix of a different handle is not attribution")

    def test_missing_time_cannot_become_ordered_transmission(self):
        url = "https://example.invalid/unique-answer-set?id=185729301"
        events = normalize_revisions([
            revision(1, f"ResearchAlpha: answer at {url}", page="dse/One", time=None),
            revision(1, f"ResearchBeta: saw ResearchAlpha's answer at {url}", page="dse/Two", actor="ResearchBeta", time=None),
        ])
        for edge in generate_edges(events):
            self.assertEqual(edge["status"], "unknown")
            self.assertFalse(edge.get("directed", False))
            for key in ("latency_seconds", "lag_seconds", "elapsed_seconds", "time_delta_seconds"):
                self.assertIsNone(edge.get(key), key)

    def test_malformed_time_is_unusable_for_chronology(self):
        url = "https://example.invalid/unique-answer-set?id=185729301"
        events = normalize_revisions([
            revision(1, f"ResearchAlpha: {url}", page="dse/One", time="not-a-date"),
            revision(1, f"ResearchBeta: ResearchAlpha shared {url}", page="dse/Two", actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        for edge in generate_edges(events):
            self.assertEqual(edge["status"], "unknown")
            self.assertFalse(edge.get("directed", False))

    def test_all_textual_edges_disclaim_receipt_and_causation(self):
        url = "https://example.invalid/unique-answer-set?id=185729301"
        events = normalize_revisions([
            revision(1, f"ResearchAlpha: answer at {url}", page="dse/One"),
            revision(1, f"ResearchBeta: used ResearchAlpha's answer at {url}", page="dse/Two", actor="ResearchBeta", time="2026-06-20T12:02:00Z"),
        ])
        edges = generate_edges(events)
        self.assertTrue(edges, "Distinctive explicit attribution should produce an inspectable candidate")
        for edge in edges:
            self.assertIs(edge.get("receipt_observed"), False)
            self.assertIs(edge.get("causal_uptake_observed"), False)

    def test_embedded_python_and_html_remain_literal_data(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = pathlib.Path(directory) / "executed"
            payload = (
                "<img src=x onerror=alert('unsafe')>\n"
                f"__import__('pathlib').Path({str(sentinel)!r}).write_text('executed')"
            )
            events = normalize_revisions([revision(1, payload)])
            self.assertFalse(sentinel.exists())
            self.assertIn("<img", events[0]["text"])
            self.assertIn("__import__", events[0]["text"])
            generate_edges(events)
            self.assertFalse(sentinel.exists())

    @unittest.skipUnless(shutil.which("node"), "Node is required for the DOM import harness")
    def test_viewer_imports_are_literal_and_unknown_order_stays_unknown(self):
        """Exercise actual app.js with a deliberately narrow DOM substitute.

        This checks dynamic text/link creation and import control flow. It is
        not a substitute for a browser's layout or complete security model.
        """
        script = r"""
const fs=require('fs'),vm=require('vm');
const created=[],ids=new Map();
class Element {
 constructor(tag){this.tag=tag;this.children=[];this.own='';this.listeners={};this.dataset={};this.value='';this.attrs={};this.classList={toggle(){}};created.push(this);}
 append(...items){this.children.push(...items);}
 replaceChildren(...items){this.children=items;this.own='';}
 set textContent(v){this.own=String(v);this.children=[];}
 get textContent(){return this.own+this.children.map(c=>typeof c==='string'?c:c.textContent).join('');}
 set innerHTML(v){throw Error('Unsafe innerHTML assignment');}
 setAttribute(k,v){if(/^on/i.test(k))throw Error('Unsafe event attribute');this.attrs[k]=String(v);}
 addEventListener(k,fn){this.listeners[k]=fn;}
}
const document={documentElement:new Element('html'),createElement:tag=>new Element(tag),getElementById:id=>{if(!ids.has(id))ids.set(id,new Element('div'));return ids.get(id);}};
document.getElementById('sort-select').value='oldest';
const payload='<img src="https://should-not-fetch.invalid/pixel" onerror="window.__reviewXss=1"><script>window.__reviewXss=2</script>';
const data={dataset:{id:'test',title:payload,limitations:[payload],source_url:'javascript:window.__reviewXss=3'},events:[{id:'e1',timestamp:'2026-06-01T12:00:00Z',actor_handle:payload,page:payload,text:payload,source_url:'data:text/html,<script>window.__reviewXss=4</script>'},{id:'e2',timestamp:42,actor_handle:'Beta',page:'Second',text:payload,source_url:'file:///etc/passwd'}],edges:[{id:'r1',source:'e1',target:'e2',directed:false,status:'unknown',edge_type:payload,rationale:payload,evidence:[{event_id:'e1',quote:payload,source_url:'javascript:window.__reviewXss=5'}],shared_tokens:[payload]}],episodes:[]};
const window={SWARM_TRACER_DATA:data};
const context={document,window,URL,console,localStorage:{getItem(){return null;},setItem(){}},fetch(){throw Error('Unexpected remote fetch');},XMLHttpRequest(){throw Error('Unexpected network request');}};
vm.runInNewContext(fs.readFileSync('web/app.js','utf8'),context,{timeout:2000});
const detail=document.getElementById('detail-panel').textContent;
const base={xss:window.__reviewXss||0,dangerousTags:created.filter(n=>['img','script','iframe'].includes(n.tag)).length,dangerousLinks:created.filter(n=>n.tag==='a'&&!/^https?:/.test(n.href||'')).length,numericDateGuessed:detail.includes('2042'),unknownDirectionMislabel:detail.includes('Earlier / source record'),orderUnresolved:detail.includes('Order unresolved')};
async function importText(text){const target={files:[{size:Buffer.byteLength(text),text:async()=>text}],value:'chosen'};await document.getElementById('file-input').listeners.change({target});return document.getElementById('notice').textContent;}
function descendants(node){return [node,...node.children.flatMap(child=>typeof child==='string'?[]:descendants(child))];}
async function chronologyCase(options={}){
 const source={id:'chat',timestamp:'2026-06-01T12:00:00Z',actor_handle:'Corrector',page:'Chat',text:'The empty days were the weekend.'};
 const target={id:'memory',timestamp:'2026-06-01T12:02:00Z',actor_handle:'Rememberer',page:'Memory',text:'Corrector identified the weekend explanation.'};
 if('sourceTime' in options)source.timestamp=options.sourceTime;
 if('targetTime' in options)target.timestamp=options.targetTime;
 if('sourceUncertainty' in options)source.timestamp_uncertainty_seconds=options.sourceUncertainty;
 if('targetUncertainty' in options)target.timestamp_uncertainty_seconds=options.targetUncertainty;
 const edge={id:'association',source:'chat',target:'memory',status:'observed',directed:false,ordering_status:'known',edge_type:'attributed_memory_correspondence',receipt_observed:false,causal_uptake_observed:false,evidence:[],...options.edge};
 const notice=await importText(JSON.stringify({dataset:{id:'chronology-review'},events:[source,target],edges:[edge],episodes:[]}));
 const panel=document.getElementById('detail-panel');
 const classes=name=>descendants(panel).filter(node=>node.className===name).map(node=>node.textContent);
 return {notice,error:document.getElementById('notice').className.includes('error'),detail:panel.textContent,results:document.getElementById('results').textContent,labels:classes('post-label'),connectors:classes('connector-label')};
}
(async()=>{
 base.malformedError=await importText('{"events": [');
 base.invalidMembersError=await importText(JSON.stringify({events:[null],edges:[]}));
 base.chronology={
  knownAttributed:await chronologyCase({sourceUncertainty:null,targetUncertainty:null,edge:{seconds_elapsed:120}}),
  knownSelf:await chronologyCase({edge:{edge_type:'self_memory_correspondence'}}),
  knownWithUncertainty:await chronologyCase({sourceUncertainty:30,targetUncertainty:30}),
  unknownAssociation:await chronologyCase({edge:{ordering_status:'unknown'}}),
  undeclaredAssociation:await chronologyCase({edge:{ordering_status:null}}),
  invalidTime:await chronologyCase({sourceTime:'not-a-date'}),
  invalidCalendar:await chronologyCase({sourceTime:'2026-02-30T12:00:00Z'}),
  naiveTime:await chronologyCase({sourceTime:'2026-06-01T12:00:00'}),
  numericTime:await chronologyCase({sourceTime:42}),
  missingTime:await chronologyCase({targetTime:null}),
  reversedTime:await chronologyCase({targetTime:'2026-06-01T11:59:00Z'}),
  equalTime:await chronologyCase({targetTime:'2026-06-01T12:00:00Z'}),
  overlappingUncertainty:await chronologyCase({sourceUncertainty:60,targetUncertainty:60}),
  negativeUncertainty:await chronologyCase({sourceUncertainty:-1}),
  stringUncertainty:await chronologyCase({targetUncertainty:'0'}),
  legacyDirected:await chronologyCase({edge:{directed:true,ordering_status:null,edge_type:'explicit_reference'}}),
  invalidDirected:await chronologyCase({sourceTime:'not-a-date',edge:{directed:true}})
 };
 console.log(JSON.stringify(base));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        project = pathlib.Path(__file__).resolve().parents[1]
        result = subprocess.run([shutil.which("node"), "-e", script], cwd=project, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["xss"], 0)
        self.assertEqual(report["dangerousTags"], 0)
        self.assertEqual(report["dangerousLinks"], 0)
        self.assertFalse(report["numericDateGuessed"])
        self.assertFalse(report["unknownDirectionMislabel"])
        self.assertTrue(report["orderUnresolved"])
        self.assertIn("Could not open this file:", report["malformedError"])
        self.assertIn("Could not open this file:", report["invalidMembersError"])
        cases = report["chronology"]
        for name in ("knownAttributed", "knownSelf", "knownWithUncertainty"):
            with self.subTest(chronology=name):
                case = cases[name]
                self.assertFalse(case["error"], case["notice"])
                self.assertEqual(case["labels"], ["Earlier record · textual association", "Later record · textual association"])
                self.assertIn("Earlier: Corrector · Later: Rememberer", case["results"])
                self.assertNotIn("Order unresolved", case["detail"])
                self.assertNotIn("Earlier / source record", case["detail"])
                self.assertTrue(case["connectors"][0].startswith("Record chronology only · "))
                self.assertFalse(any(arrow in case["connectors"][0] + case["results"] for arrow in ("→", "↓", "↔")))
                self.assertIn("They do not establish transport between these records.", case["detail"])
                self.assertIn("Not established here", case["detail"])
        self.assertIn("Attributed memory correspondence", cases["knownAttributed"]["detail"])
        self.assertIn("exact source message, transport route, receipt or causal uptake", cases["knownAttributed"]["detail"])
        self.assertIn("between recorded timestamps", cases["knownAttributed"]["connectors"][0])
        self.assertIn("Self memory correspondence", cases["knownSelf"]["detail"])
        self.assertIn("does not establish that the chat supplied the memory", cases["knownSelf"]["detail"])
        for name in ("unknownAssociation", "undeclaredAssociation", "invalidTime", "invalidCalendar", "naiveTime", "numericTime", "missingTime", "reversedTime", "equalTime", "overlappingUncertainty", "negativeUncertainty", "stringUncertainty", "invalidDirected"):
            with self.subTest(chronology=name):
                case = cases[name]
                self.assertFalse(case["error"], case["notice"])
                self.assertEqual(case["labels"], ["Record A · order unresolved", "Record B · order unresolved"])
                self.assertIn("Order unresolved", case["detail"])
                self.assertNotIn("Earlier:", case["results"])
                self.assertNotIn("Earlier / source record", case["detail"])
                self.assertNotIn("Earlier record · textual association", case["detail"])
                self.assertNotIn("Record chronology only", case["detail"])
                self.assertNotIn("→", case["results"])
        self.assertEqual(cases["legacyDirected"]["labels"], ["Earlier / source record", "Later / target record"])
        self.assertIn("→", cases["legacyDirected"]["results"])
        self.assertTrue(cases["legacyDirected"]["connectors"][0].startswith("↓"))


if __name__ == "__main__":
    unittest.main()
