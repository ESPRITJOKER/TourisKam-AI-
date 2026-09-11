# Knowledge Base — verification policy

This folder holds the **source documents** for TourisCam AI's RAG system. Each
file is cleaned, chunked, embedded, and stored in Supabase `knowledge_documents`.

## Golden rule

> **Never fabricate facts, sources, prices, or contacts.**
> If something cannot be verified, mark it `unverified` or `unavailable`.
> The agent must prefer retrieved verified information over model memory, and
> say *"I couldn't verify that information"* rather than guess.

## Folder layout

```
knowledge/
├── destinations/   # cities, towns, regions
├── attractions/    # sites, parks, museums, beaches, waterfalls
├── tariffs/        # benchmark price references (NOT official tariffs)
├── hotels/         # accommodation
├── guides/         # verified/certified guides
├── emergency/      # emergency contacts
└── regulations/    # tourism rules, visa/entry notes, ecotourism rules
```

## Document format

Each fact-bearing markdown file starts with frontmatter carrying provenance:

```markdown
---
title: <human title>
source_type: destination | attraction | tariff | hotel | guide | emergency | regulation | general
language: en | fr | pidgin
source: <where this came from — a real, checkable reference, or "pending citation">
verification_status: verified | benchmark | estimated | unverified | unavailable
last_verified: YYYY-MM-DD | null
---

<body text>
```

## Verification status meanings

| status | meaning |
|---|---|
| `verified` | Established public fact; formal citation attached or pending. |
| `benchmark` | Typical market range. **Not** an official tariff. |
| `estimated` | Rough estimate; use with an explicit caveat. |
| `unverified` | Placeholder — must be confirmed before the competition demo. |
| `unavailable` | We have no trustworthy data; agent says so. |

## Initial geographic scope

Douala · Yaoundé · Limbe · Kribi · West Region (Foumban, Bafoussam, Dschang).
