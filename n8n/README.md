# TourisCam WhatsApp workflow (n8n)

The P0 demo spine: a tourist messages the **Twilio WhatsApp Sandbox**, n8n runs
the guardrailed RAG pipeline and replies on WhatsApp, and anonymous analytics are
logged to Supabase. n8n is the only orchestrator (no FastAPI/Python service).

- **Live workflow:** `TourisCam WhatsApp` — id `LACeG3RxqrtB7Jwn`
  on <https://thementalist.app.n8n.cloud/workflow/LACeG3RxqrtB7Jwn>
- **Production webhook:** `https://thementalist.app.n8n.cloud/webhook/touriscam-whatsapp`
- **Backup:** `touriscam_whatsapp.workflow.json` (import into a fresh instance if the live copy is lost)
- **Status:** text round-trip + safety advisories + Tariff Guard (2026-09-15). Voice notes = Phase 2.

## Flow
```
WhatsApp Webhook (ACK Twilio instantly, 200 <Response></Response>)
  -> Normalize Message            (From, Body, NumMedia -> queryText, fromPlain)
  -> Has Text?                    (empty body, e.g. voice note -> Send Text-Only Reply
                                   -> Log Unsupported Event, response_status='unsupported_media')
  -> Gemini Embed Query           (gemini-embedding-001, RETRIEVAL_QUERY, dim 768)
  -> Build Retrieval Query        (SQL = match_documents(embedding, 5, 0.5)
                                   + UK FCDO "Regional risks" chunks if a high-risk area is named
                                   + ≤3 tariffs rows if the message asks about prices;
                                   user text reaches SQL only as [a-z0-9-] keywords)
  -> Retrieve Documents           (Supabase Postgres)
  -> Format Context               (trust labels, de-duplicated rows, language/destination/intent)
  -> Add System Prompt            (guardrailed SYSTEM_PROMPT = rag/prompt.py)
  -> Build Generation Request     (system + user prompt, thinking_budget=0)
  -> Gemini Generate Answer       (gemini-flash-latest, temp 0.3, 5 tries / 5 s)
  -> Extract Answer               (**bold** -> *bold*, no # headings, ≤1,500 chars,
                                   tool_used = tariff_guard | tourism_search)
  -> Send WhatsApp Reply          (Twilio REST, async, 3 tries)
  -> Hash Session                 (SHA256(salt + phone) -> session_id, no raw PII)
  -> Log Tourist Query            (tourist_queries)
  -> Log Query Event              (query_events, anonymous analytics)

On any embed / retrieve / generate failure:
  -> Send Fallback Reply -> Log Error Event (query_events, response_status='error')
```
Replies are sent **asynchronously** via the Twilio REST node (not TwiML) so the
multi-call RAG latency never trips Twilio's ~15 s webhook timeout.

## One-time setup

### 1. Create the 3 credentials in n8n (Credentials -> New)
Secrets live ONLY in n8n's credential store — never in the workflow JSON or chat.

| Credential (exact name) | Type | Fields |
|---|---|---|
| **Gemini API** | Header Auth | Name: `x-goog-api-key`  ·  Value: *your Gemini API key* |
| **Supabase Postgres** | Postgres | Host `aws-1-eu-west-1.pooler.supabase.com` · Port `5432` · Database `postgres` · User `postgres.<project-ref>` · Password *(your DB password)* · SSL `require` |
| **Twilio** | Twilio API | Account SID + Auth Token from the Twilio console |

The workflow already references these credentials **by name** — creating them with
the exact names above auto-links them. Otherwise open each HTTP/Postgres/Twilio
node and pick the credential once.

### 2. Session-hash salt
n8n Cloud blocks `$env` inside nodes (`N8N_BLOCK_ENV_ACCESS_IN_NODE`), so the salt
is a random constant set directly in the **Hash Session** node of the live
workflow. The repo backup stores the placeholder `<SESSION_HASH_SALT>` instead —
a public salt would let anyone brute-force the hashed phone numbers. When
importing the backup, replace the placeholder with a new random value
(`python -c "import secrets; print(secrets.token_hex(24))"`).

### 3. Enable the Twilio WhatsApp Sandbox
1. Twilio Console -> Messaging -> Try it out -> **Send a WhatsApp message**.
2. From your phone, send the **join `<code>`** to **+1 415 523 8886** to join the sandbox.
3. In the sandbox settings, set **"When a message comes in"** to the n8n
   **Production** webhook URL (POST):
   `https://thementalist.app.n8n.cloud/webhook/touriscam-whatsapp`

### 4. Activate the workflow
Toggle the workflow to **Active** in n8n (the production webhook only serves when active).

## Verify (definition of done)
From a phone that joined the sandbox (each reply should arrive in < 30 s, be
≤1,600 characters, and use WhatsApp formatting):
| Message | Expect |
|---|---|
| `What can I see in Limbe?` | English answer, **starts with the UK FCDO South-West advisory** |
| `Que voir à Kribi ?` | French answer with trust labels |
| `Wetin I fit see for Limbe?` | Pidgin reply |
| `Do I need a visa to visit Cameroon?` | e-visa / FCDO entry info, sources named |
| `Parle-moi du lac Nyos` | French answer that mentions the North-West advisory |
| `Taxi price from Douala airport at night?` | 5,000 FCFA (MINTOUL, indicative); `tool_used = tariff_guard` |
| `Combien coûte l'entrée au Musée maritime de Douala ?` | 3,500 FCFA from the tariff table |
| `How much is a hotel in Garoua?` | says the price is unavailable — no invented number |
| `Who won the World Cup?` | polite Cameroon-only redirect |
| a voice note | "please type your question" reply; event `unsupported_media` |

Then confirm rows: `select * from tourist_queries order by created_at desc limit 5;`
(hashed `session_id`, no raw phone) and
`select tool_used, response_status, language from query_events order by created_at desc limit 10;`

### Dry-run in n8n before the phone test (once credentials exist)
Open the workflow, **Execute Workflow**, and on the `WhatsApp Webhook` node use
"Listen for test event" — or pin this body on the webhook and run:
```json
{
  "From": "whatsapp:+237600000000",
  "Body": "What can I see in Limbe?",
  "NumMedia": "0"
}
```
Watch each node's output; the answer should appear at `Extract Answer` and a
message should be sent by `Send WhatsApp Reply`.

## Tech notes (don't rediscover — these cost debugging time)
- `gemini-flash-latest` is a *thinking* model -> `thinking_config.thinking_budget=0`
  is set, otherwise it spends the whole token budget on hidden thoughts and returns
  empty text.
- Embeddings request `output_dimensionality=768` to match the `vector(768)` column.
- Supabase is reached via the **Session pooler** host (IPv4); the direct `db.*`
  host is IPv6-only and unreachable from n8n Cloud.
- Retrieval uses the tested `match_documents` RPC via the native Postgres node,
  sidestepping pgvector-over-PostgREST casting friction.
- The embedding is inlined into the SQL as a numeric `'[...]'::vector` literal
  (safe — floats only) because n8n's `queryReplacement` splits on commas. Tariff
  keywords are reduced to `[a-z0-9-]` before being inlined, for the same reason.
- `$env.*` expressions fail on n8n Cloud with "access to env vars denied" — keep
  configuration in node parameters or credentials instead.
- Test changes with the MCP `test_workflow` tool and pinned Twilio/Postgres/Gemini
  nodes: it runs every Code/IF node without sending WhatsApp messages or writing rows.

## Phase 2 — voice notes (planned)
Insert an `IF isVoice` after `Normalize Message`: on true, HTTP GET the Twilio
media URL (Twilio predefined credential, basic auth) -> Gemini `generateContent`
with inline audio (`thinking_budget=0`) to transcribe -> set `queryText` to the
transcript -> merge back into `Gemini Embed Query`.

## Security
Rotate the Supabase DB password, the Gemini API key, and the n8n API key **after
the competition** — all were handled during setup.
