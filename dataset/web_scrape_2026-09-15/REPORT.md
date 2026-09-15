# Web scrape report — batch `web_2026-09-15`

_Generated 2026-09-15 13:10. Files only — nothing loaded into Supabase._

| Source | Records | Chars | Est. chunks | Languages | Verification | Authority |
|---|---:|---:|---:|---|---|---|
| staging | 40 | 15,526 | 40 | en 40 | benchmark 26, unverified 11, estimated 3 | third_party 40 |
| fcdo | 20 | 22,204 | 31 | en 20 | verified 20 | primary 20 |
| wikivoyage | 487 | 665,699 | 875 | fr 373, en 114 | unverified 487 | third_party 487 |
| osm | 196 | 183,668 | 319 | en 196 | unverified 196 | secondary 196 |
| mintoul | 99 | 111,547 | 170 | fr 94, en 5 | verified 66, unverified 33 | primary 99 |
| **total** | **842** | **998,644** | **1435** | | | |

## Filters and drops per source

- **staging**: kept=40, limit=None, seconds=0
- **fcdo**: parts=6, kept=20, limit=None, seconds=1
- **wikivoyage**: pages: en.wikivoyage.org=30, pages: fr.wikivoyage.org=97, dropped: too short=1, dropped: duplicate=1, kept=487, limit=None, seconds=174
- **osm**: regions indexed=10, towns=390, pois=1899, skipped: unnamed / unlocated / other=286, kept=196, limit=None, seconds=543
- **mintoul**: skipped: spam title=47, dropped: fetch failed / 404=32, dropped: no content container=80, dropped: spam=5, dropped: placeholder page=1, dropped: post language not fr/en=1, pages crawled=250, dropped: too short=11, dropped: missing content=14, dropped: duplicate=7, scrubbed: ID numbers=17, kept=99, limit=None, seconds=221

## Region coverage (all sources)

(none): 459, West: 66, Centre: 56, North-West: 45, Littoral: 36, South: 31, Littoral / South-West: 31, South-West: 26, Far North: 22, Centre / South / East: 20, Adamawa: 16, North / Far North: 14, East: 12, North: 8

## Samples

**[staging] Hôtel Ilomba — Boukarou (entry room)** — `benchmark` / `third_party` — <dataset/touriscam_kribi_to_west_staging.csv>

> Hôtel Ilomba — Hotel, Kribi, Bwambe (Route des Chutes de la Lobé). Boukarou (entry room) — price (FCFA): 40000. Amenities: Pool, Beach, Spa, Restaurant, WiFi, Beach bar. Phone: +237 699 91 29 23. Confidence: VERIFIED_PHONE. Source note: Phone/site verified via hotelilomba.com; price range from Petit Futé (not published on official site). Prices are indicative and may have changed; verify before tr…

**[staging] Douala-Edéa National Park — Boat charter day-trip** — `unverified` / `third_party` — <dataset/touriscam_kribi_to_west_staging.csv>

> Douala-Edéa National Park — Mangrove Ecotourism, Edéa / Sanaga River area. Boat charter day-trip — price (FCFA): 25000-45000. Amenities: Mangroves, Manatees, Sea turtles, Chimpanzees. Confidence: UNCONFIRMED_ALL. Source note: Reclassified as National Park in 2018 - no public booking phone found; book via private tour agencies e.g. Cameroon Travel and Tours. Prices are indicative and may have chang…

**[fcdo] UK travel advice (FCDO): Warnings and insurance** — `verified` / `primary` — <https://www.gov.uk/foreign-travel-advice/cameroon/warnings-and-insurance>

> Your travel insurance could be invalidated if you travel against advice from the Foreign, Commonwealth & Development Office (FCDO).  Areas where FCDO advises against travel:  Bakassi Peninsula:  FCDO advises against all travel to Bakassi Peninsula.  Cameroon-Central African Republic border:  FCDO advises against all travel to within 40km of the border with Central African Republic.  Cameroon-Chad …

**[fcdo] UK travel advice (FCDO): Safety and security — Transport risks** — `verified` / `primary` — <https://www.gov.uk/foreign-travel-advice/cameroon/safety-and-security>

> Road travel:  If you are planning to drive in Cameroon, see information on driving abroad .  You can use a UK photocard driving licence to drive in Cameroon for up to 6 months. If you still have a paper driving licence, you may need to update it to a photocard licence or get the correct version of the international driving permit ( IDP ) .  If you are staying for more than 6 months, you must get a…

**[wikivoyage] Adamaoua — Overview** — `unverified` / `third_party` — <https://en.wikivoyage.org/w/index.php?title=Adamaoua&oldid=5264061>

> Adamaoua is a region in central Cameroon that stretches across the middle of the country from the Nigerian border east to the border with the Central African Republic.  Cities:  Ngaoundéré — the gateway to the province  Understand:  Adamaoua is one of the geographically diverse regions in Cameroon. It consists of mountainous and sparsely populated terrain, divided into the savannah north and jungl…

**[wikivoyage] Foumban — Se loger** — `unverified` / `third_party` — <https://fr.wikivoyage.org/w/index.php?title=Foumban&oldid=664412>

> Hôtel Pekassa de Karché , BP 79 Foumban ( Rond-point Camtel ), ☎ + 237 690 80 49 87 , + 237 673 27 35 35 , hotelpekassa@gmail.com . 10000 FCFA . situé au centre-ville de Foumban, à proximité des principaux points d’intérêt. Il propose des chambres à partir de 10 000 F , allant des chambres classiques aux suites royales et VIP. Équipements et services : Chambres propres et spacieuses, équipées d’ea…

**[osm] Accommodation in Adamawa region: Banyo, Ngaoundéré (OpenStreetMap)** — `unverified` / `secondary` — <https://www.openstreetmap.org/relation/2750694>

> Accommodation in Adamawa region, Cameroon, as mapped on OpenStreetMap (community data; may be incomplete or outdated): - Hôtel Amin (hotel) — Banyo; 6.7492, 11.8098 [osm node/10215240618] - ADAMAOUA (hotel, 2 stars) — Ngaoundéré; 7.3354, 13.5878; phone: 699468302 [osm node/5934581143] - AL HERR (hotel, 1 stars) — Ngaoundéré; 7.3225, 13.5743; phone: 696982210 [osm node/5934581136] - APHRODITE (hote…

**[osm] Attractions and viewpoints in Littoral region: Deido, Dibombari, Douala (OpenStreetMap)** — `unverified` / `secondary` — <https://www.openstreetmap.org/relation/2750851>

> Attractions and viewpoints in Littoral region, Cameroon, as mapped on OpenStreetMap (community data; may be incomplete or outdated): - Le Jardin Sonore de Bonamouti (artwork) — Deido; 4.0719, 9.7115; website: http://lucas.grandin.free.fr/jardinsonore.html [osm node/4995138937] - Manège (attraction) — Deido; 4.0600, 9.7031 [osm node/6633294458] - Chez Ruth Ndoumbe (artwork) — Dibombari; 4.1539, 9.6…

**[mintoul] Cameroun en découverte** — `verified` / `primary` — <https://mintoul.gov.cm/cameroun-en-decouverte/>

> Première visite  Carte d’identité du cameroun Pratiques des affaires Se déplacer au cameroun Se rendre au cameroun...  Sites touristiques  Nos meilleurs endroits à vsiter et à dcouvrir  Quelques icônes  Nom Periode Profil Ahmadou AHIDJO 1960-1982 Paul BIYA 1982 OUM NYOBE DOUALA MANGA Bell Littoral...  Cuisine  Les mets emblématiques du Cameroun, issus de ses quatre aires culturelles, allient plais…

**[mintoul] Informations, communications, TIC et télécommunications** — `verified` / `primary` — <https://mintoul.gov.cm/infos-pratiques/informations-communications-tic-et-telecommunications/>

> Services informatiques et web, agences de communication, imprimeries, centres d’appels. Le Cameroun a consenti d’importants investissements dans les infrastructures de communication. Le réseau est numérisé avec une boucle de 5 000 km de fibre optique à travers tout le territoire. Le haut débit est présent dans toutes les capitales régionales. Le taux de pénétration de la téléphonie mobile est de 9…

