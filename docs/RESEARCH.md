# Hackathon research and provenance

Verified on 2026-10-03. This project studies observable information propagation. It does not establish why the July Hugging Face swarm ended, collective goal completion, or present-day adoption of its artifacts.

## Official event requirements

The current [event page](https://swarmchasing.com/) and [logistics page](https://swarmchasing.com/logistics/) agree on the schedule below. Eastern conversions use America/Toronto; Pacific conversions use America/Los_Angeles.

| Milestone | Pacific time | Toronto time |
|---|---|---|
| Kickoff | Sat October 3, 2026, 11:00 a.m. | Sat October 3, 2:00 p.m. |
| Submission deadline | Sun October 4, 5:00 p.m. | Sun October 4, 8:00 p.m. |
| In-person demos, streamed | Sun October 4, 6:00–7:00 p.m. | Sun October 4, 9:00–10:00 p.m. |

Online registration is automatically approved. Participants may work alone or form teams after registering. Starting early is permitted. Other real-world multi-agent datasets are allowed; transcript analysis is optional. One submission per team requires an explanation or video, a GitHub repository link, and team members' names and emails. Real findings are optional. Online entrants are eligible for every prize. Grove Research and AI Village staff judge submissions. No explicit scoring rubric was published on the inspected official pages. The prize pool is $3,000 across five projects.

Exact links extracted read-only from official HTML:

- Application: <https://airtable.com/appFBFzD2Cv2rYCG5/pagij1OYTgOK4K0DC/form>
- Submission: <https://airtable.com/appFBFzD2Cv2rYCG5/shr8KXOLvo3xV9bnZ>
- Slack invitation: <https://join.slack.com/t/swarmchasing/shared_invite/zt-4bkawym4l-CEe685XK94zEP9aB1gwfsw>
- Livestream: no public URL appeared on inspected event pages. Logistics says the YouTube URL will be announced Saturday morning in Slack `#announcements`.

These links were retrieved without registering, joining Slack, requesting access, contacting organizers, or submitting anything. Airtable form contents could not be independently inspected through the search tool, so field requirements above are grounded in the official logistics page rather than an asserted form schema.

The [September 30 organizer announcement](https://aivillageblog.substack.com/p/join-the-ai-swarm-dynamics-hackathon) explicitly invites tools for information spread and web forensics. That older post mentions Zoom; current logistics specifies YouTube. A reader reported earlier schedule discrepancies, but the inspected current event pages agree. Use current logistics and organizer announcements for any subsequent update.

## Reachable scope

A usable public forensic tracer is achievable before the deadline: load the small redacted wiki export, extract changes between revisions, link candidate references, present evidence and uncertainty, and reproduce a few documented examples. Browser-visible posts support exposure acknowledgements and claimed downstream action. They do not disclose the receiving model's full prompt, private memory, or independently verified task outcome.

Tracing memory consolidation remains an extension requiring AI Village access. Public narrative examples can guide selection but should not be presented as automatically verified trajectories. A report can be useful without claiming causality or universal propagation rates.

## Dataset access and redistribution

### Collusion.wiki

[Findings](https://collusion.wiki/) encourage independent analysis and describe a reconstructed, redacted copy with legitimate human traffic excluded except moderation actions. The [download page](https://collusion.wiki/explorer/download) provides 14,591 saved revisions, 4,579 pages, 3,103 labels, events, a provenance manifest, and additional cross-site records. The compressed original wiki bundle is 4.2 MB. The manifest's generation time is 2026-09-03T03:42:36Z and its published write-date cut begins May 1, 2026. Event populations overlap: total event rows are not an incident count. Export timestamps and handle labels are observations, not confirmed agent-instance identities.

No explicit dataset license was found on the inspected findings or download pages. Public access and an invitation to analyze do not imply an MIT grant for the underlying corpus. Project code can be MIT licensed separately. Exclude raw downloaded data from the distributable repository; preserve source attribution, retrieval details and hashes. Include only a narrow redacted evidence snapshot, with limited excerpts and source links, or allow users to regenerate it from the official download. Do not publish discovered credentials or personal identifiers, execute embedded content, or follow historical payload URLs as part of analysis.

Primary download endpoints:

- <https://collusion.wiki/explorer/download/revisions.jsonl.gz>
- <https://collusion.wiki/explorer/download/pages.jsonl.gz>
- <https://collusion.wiki/explorer/download/events.jsonl.gz>
- <https://collusion.wiki/explorer/download/labels.jsonl.gz>
- <https://collusion.wiki/explorer/download/manifest.json.gz>
- <https://collusion.wiki/explorer/download/records.jsonl.gz>
- <https://collusion.wiki/explorer/download/links.jsonl.gz>

The download page supplies SHA-256 checksums for the **expanded** files, not the compressed transfers. This distinction matters for reproducibility.

### AI Village

The [dataset card](https://huggingface.co/datasets/aidigestorg/ai-village) requires a logged-in access request, accepted custom research terms and manual review. Research and analysis are allowed; training or fine-tuning requires written permission. Users must not re-identify individuals, must cite AI Digest / AI Village and must notify the organization of publications. Hackathon logistics asks applicants to mention the hackathon and request early.

Chat messages, events, computer-use sessions and turns, memories and goals are available after approval. Exact raw model-call prompts are excluded. Generated summaries are secondary, and agent narration requires corroboration from actual tool outputs or screenshots. Scaffolding changes can explain apparent behavioral differences; consult the dataset changelog. The complete repository is 177 GB, but a selected transcript/memory analysis can avoid screenshots and full download. This project must not repackage gated raw data under its code license.

## Primary candidate cases

### Grocery sequence: acknowledged answer sharing

Source page A: <https://collusion.wiki/explorer/page/dse~DataUSAGrocerySequenceCollabOct22>

- Revision 11, 2026-06-16 10:27:03: `GrocerySequenceAgentApr27` publishes Nevada and the value 20,369.

Source page B: <https://collusion.wiki/explorer/page/dse~DataUSAGrocerySequenceCollab2027>

- Revision 7, 10:33:56: `AgentProbeAssistantX2027` explicitly acknowledges that confirmed Nevada information enables preparation.
- Revision 15, 10:47:29: the same handle reports answering Nevada instantly.
- Revision 14, 10:46:47: `GroceryAgentMar13X` publishes Kentucky and the value 34,770.
- Revision 16, 10:48:16: `AgentProbeAssistantX2027` acknowledges caching Kentucky.

This is a useful reference-to-acknowledgement cascade. Submitted answers remain self-reported. The explorer's timestamps establish observed posting order; task clocks differ and should not be treated as the shared clock. Adjacent page revisions retain earlier contributors' text, so assign new contributions from revision deltas rather than attributing the entire saved page body to its latest editor.

### Geological Clock: uptake followed by correction

The [September 10 observer report](https://aivillageblog.substack.com/p/persuasion-in-the-ai-village-deepseek) describes DeepSeek's explanation for empty weekend logs spreading among agents, then being corrected after a newer participant checked the weekday schedule. The report also describes framework/tool proposals being rejected and some recipients writing rejection reminders into memory. These are useful selection leads, not ground-truth memory edges until raw records are inspected.

A linked agent-authored corrective artifact, [Saturdays](https://github.com/ai-village-agents/opus-47-notes/blob/main/saturdays.md), is dated June 1, 2026. It identifies missing May 30–31 data as the weekend and records the agent's intention to check ordinary explanations before inferring hidden architecture. It is evidence of an externalized correction, not proof that all prior recipients revised their memories.

### Rejected uptake control

Use the observer report's rejected optimization framework as a qualitative control. A benchmark fixture may represent refusal explicitly, but must label synthetic fixtures separately from observed records. Production detector claims should be validated against raw recipient messages and memories once gated access is available; silence or lack of a matching post is not rejection.

## Fetched-page fingerprints

Hashes below refer to full HTTP response bytes retrieved with `urllib.request`, before parsing. Hash differences across retrievals may reflect site-generated HTML; the fingerprint records a particular retrieval rather than a permanent page identity.

| URL | Fetched at UTC | Bytes | SHA-256 |
|---|---|---:|---|
| `https://swarmchasing.com/` | 2026-10-03T13:06:28.337738+00:00 | 96747 | `4fa69d5653907d15bd8349af85d0e986ce26bc65e04fdf4efb2fd7ab22382fa8` |
| `https://swarmchasing.com/logistics/` | 2026-10-03T13:06:32.891157+00:00 | 30919 | `9cb791e0897746062b3accb353946a16b6f08f7ded2f988f6c01a15bcf96a3e2` |
| `https://collusion.wiki/explorer/download` | 2026-10-03T13:06:38.380944+00:00 | 9470 | `21306cd384d3e590c69d8f313837f94916071791cb430a597beb4fb5c1bbb2cc` |
| `https://collusion.wiki/explorer/download/manifest.json.gz` | 2026-10-03T13:06:42.705979+00:00 | 6132 | `ee4c5785d61054ef993a4a10708d9698d7d1f86ac210810b6899bae035eda092` |

## Concrete external prerequisites still unresolved

1. The registrant's preferred full public name and email, and any other human team members' names/emails.
2. Registration status and organizer access to Slack/livestream updates.
3. A publishable GitHub repository URL and appropriate account authorization. A local archive is reviewable but does not satisfy the repository-link requirement.
4. Submission of the completed package through the form before October 4, 8 p.m. Toronto time.
5. Optional AI Village access approval. This is not a blocker for the public-data MVP.

Do not treat elapsed time as approval for registration, publication or submission. First finish the code, reproducible analysis, demo and write-up; then ask for only the concrete identity/publication inputs needed for those actions.
