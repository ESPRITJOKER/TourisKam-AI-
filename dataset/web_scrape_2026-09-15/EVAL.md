# Retrieval eval — before vs after web corpus

_Generated 2026-09-15 14:08. Exact cosine. Current rows: 118; with web: 1451 (+1333 chunks). ★ = new web chunk._

## Summary

| Metric (top-5, 15 questions) | Before | After | After + rerank |
|---|---:|---:|---:|
| Official results (primary or verified) | 75/75 | 16/75 | 31/75 |
| Distinct records | 75 | 61 | 68 |
| From new web chunks | 0/75 | 69/75 | 60/75 |
| Top-1 similarity above before | — | 14/15 | 13/15 |

_Rerank = raw similarity ≥ 0.5, max 2 chunks per record, ordered by similarity + authority boost (+0.04 primary/verified, +0.02 secondary/benchmark)._

## What can I see in Limbe?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.770 Limbe `destination/verified` | 0.785 ★ Limbe — See and do `wikivoyage/unverified/third_party` | 0.770 Limbe `destination/verified` |
| 2 | 0.720 Côte et plages de Limbe `attraction/verified/primary` | 0.770 Limbe `destination/verified` | 0.785 ★ Limbe — See and do `wikivoyage/unverified/third_party` |
| 3 | 0.677 Foumban `destination/verified` | 0.759 ★ Limbe — Buy `wikivoyage/unverified/third_party` | 0.755 ★ Attractions and viewpoints in South-West regi `osm/unverified/secondary` |
| 4 | 0.670 Yaoundé `destination/verified` | 0.757 ★ Limbe — Understand `wikivoyage/unverified/third_party` | 0.720 Côte et plages de Limbe `attraction/verified/primary` |
| 5 | 0.670 Kribi `destination/verified` | 0.755 ★ Attractions and viewpoints in South-West regi `osm/unverified/secondary` | 0.759 ★ Limbe — Buy `wikivoyage/unverified/third_party` |

## Que voir à Kribi ?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.715 Kribi `destination/verified` | 0.783 ★ Kribi — Voir `wikivoyage/unverified/third_party` | 0.783 ★ Kribi — Voir `wikivoyage/unverified/third_party` |
| 2 | 0.698 Festival MAYI `event/unverified/primary` | 0.764 ★ Kribi — Voir `wikivoyage/unverified/third_party` | 0.764 ★ Kribi — Voir `wikivoyage/unverified/third_party` |
| 3 | 0.697 Festival Culturel et Tradition NGUMA MABI `event/unverified/primary` | 0.764 ★ Kribi — Voir `wikivoyage/unverified/third_party` | 0.715 Kribi `destination/verified` |
| 4 | 0.697 Côte et plages de Kribi `attraction/verified/primary` | 0.752 ★ Kribi — Voir `wikivoyage/unverified/third_party` | 0.720 ★ Attractions and viewpoints in South region: C `osm/unverified/secondary` |
| 5 | 0.689 Chutes de la Lobé `attraction/verified/primary` | 0.733 ★ Kribi — Voir `wikivoyage/unverified/third_party` | 0.698 Festival MAYI `event/unverified/primary` |

## Do I need a visa to visit Cameroon?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.703 Official e-visa portal `practical_information/unverified/primary` | 0.740 ★ UK travel advice (FCDO): Entry requirements — `fcdo/verified/primary` | 0.740 ★ UK travel advice (FCDO): Entry requirements — `fcdo/verified/primary` |
| 2 | 0.640 Tourist visa validity `practical_information/unverified/primary` | 0.727 ★ UK travel advice (FCDO): Entry requirements `fcdo/verified/primary` | 0.727 ★ UK travel advice (FCDO): Entry requirements `fcdo/verified/primary` |
| 3 | 0.630 Douala `destination/verified` | 0.719 ★ Demande de visa `mintoul/verified/primary` | 0.719 ★ Demande de visa `mintoul/verified/primary` |
| 4 | 0.625 Yaoundé `destination/verified` | 0.712 ★ Formalités d’entrée au Cameroun `mintoul/verified/primary` | 0.712 ★ Formalités d’entrée au Cameroun `mintoul/verified/primary` |
| 5 | 0.621 International airports `practical_information/unverified/primary` | 0.703 Official e-visa portal `practical_information/unverified/primary` | 0.703 Official e-visa portal `practical_information/unverified/primary` |

## Is it safe to travel to the North-West region?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.626 HAMAN DAHIROU `guide/unverified/primary` | 0.758 ★ UK travel advice (FCDO): Regional risks — Nor `fcdo/verified/primary` | 0.758 ★ UK travel advice (FCDO): Regional risks — Nor `fcdo/verified/primary` |
| 2 | 0.624 Adama Mirabelle `guide/unverified/primary` | 0.742 ★ UK travel advice (FCDO): Regional risks — Nor `fcdo/verified/primary` | 0.742 ★ UK travel advice (FCDO): Regional risks — Nor `fcdo/verified/primary` |
| 3 | 0.614 Limbe `destination/verified` | 0.738 ★ Northwest Highlands — Overview `wikivoyage/unverified/third_party` | 0.726 ★ UK travel advice (FCDO): Regional risks — Far `fcdo/verified/primary` |
| 4 | 0.605 Yaoundé `destination/verified` | 0.738 ★ UK travel advice (FCDO): Regional risks — Nor `fcdo/verified/primary` | 0.702 ★ UK travel advice (FCDO): Warnings and insuran `fcdo/verified/primary` |
| 5 | 0.603 Douala `destination/verified` | 0.726 ★ UK travel advice (FCDO): Regional risks — Far `fcdo/verified/primary` | 0.700 ★ UK travel advice (FCDO): Safety and security  `fcdo/verified/primary` |

## Which hotels are in Bafoussam?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.671 Festival YANG YANG `event/unverified/primary` | 0.756 ★ Bafoussam — Se loger `wikivoyage/unverified/third_party` | 0.741 ★ Accommodation in West region: Bafoussam (Open `osm/unverified/secondary` |
| 2 | 0.660 CINCINNATI HOTEL `hotel/unverified/primary` | 0.751 ★ Bafoussam — Sleep `wikivoyage/unverified/third_party` | 0.756 ★ Bafoussam — Se loger `wikivoyage/unverified/third_party` |
| 3 | 0.645 BOUN'S HOTEL `hotel/unverified/primary` | 0.749 ★ Musée de Bamendjinda — Se loger `wikivoyage/unverified/third_party` | 0.734 ★ Accommodation in West region: Bafoussam, Bafo `osm/unverified/secondary` |
| 4 | 0.644 CLUB MULTI-FONCTIONNEL MUNDI `hotel/unverified/primary` | 0.741 ★ Accommodation in West region: Bafoussam (Open `osm/unverified/secondary` | 0.751 ★ Bafoussam — Sleep `wikivoyage/unverified/third_party` |
| 5 | 0.642 LE LAGON CLUB & AFFAIRES `hotel/unverified/primary` | 0.737 ★ Bandjoun — Se loger `wikivoyage/unverified/third_party` | 0.731 ★ Accommodation in West region: Bafoussam (Open `osm/unverified/secondary` |

## Parle-moi du lac Nyos

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.629 Mont Cameroun `attraction/verified/primary` | 0.800 ★ Lac Nyos — Comprendre `wikivoyage/unverified/third_party` | 0.800 ★ Lac Nyos — Comprendre `wikivoyage/unverified/third_party` |
| 2 | 0.619 Limbe `destination/verified` | 0.770 ★ Lac Nyos — Présentation `wikivoyage/unverified/third_party` | 0.770 ★ Lac Nyos — Présentation `wikivoyage/unverified/third_party` |
| 3 | 0.606 Jean Oscar NGUILI `guide/unverified/primary` | 0.770 ★ Lac Nyos — Voir `wikivoyage/unverified/third_party` | 0.770 ★ Lac Nyos — Voir `wikivoyage/unverified/third_party` |
| 4 | 0.604 Mont Fébé `attraction/verified/primary` | 0.759 ★ Lac Nyos — Faire `wikivoyage/unverified/third_party` | 0.759 ★ Lac Nyos — Faire `wikivoyage/unverified/third_party` |
| 5 | 0.603 ABOUBAKAR ABDOURASSOULOU `guide/unverified/primary` | 0.749 ★ Lac Nyos — Sécurité `wikivoyage/unverified/third_party` | 0.749 ★ Lac Nyos — Sécurité `wikivoyage/unverified/third_party` |

## How do I climb Mount Cameroon?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.705 Course de l'Espoir `event/unverified/primary` | 0.769 ★ Mount Cameroon — Prepare `wikivoyage/unverified/third_party` | 0.769 ★ Mount Cameroon — Prepare `wikivoyage/unverified/third_party` |
| 2 | 0.668 Limbe `destination/verified` | 0.747 ★ Mount Cameroon — Overview `wikivoyage/unverified/third_party` | 0.747 ★ Mount Cameroon — Overview `wikivoyage/unverified/third_party` |
| 3 | 0.660 Mont Cameroun `attraction/verified/primary` | 0.728 ★ Mount Cameroon — Prepare `wikivoyage/unverified/third_party` | 0.705 Course de l'Espoir `event/unverified/primary` |
| 4 | 0.633 Official e-visa portal `practical_information/unverified/primary` | 0.712 ★ Mount Cameroon National Park (EMICAM) — Permi `staging/benchmark/third_party` | 0.712 ★ Mount Cameroon National Park (EMICAM) — Permi `staging/benchmark/third_party` |
| 5 | 0.625 Douala `destination/verified` | 0.705 Course de l'Espoir `event/unverified/primary` | 0.728 ★ Mount Cameroon — Prepare `wikivoyage/unverified/third_party` |

## Combien coûte l'entrée au Musée maritime de Douala ?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.643 Douala `destination/verified` | 0.781 ★ Musée maritime de Douala — Circuler `wikivoyage/unverified/third_party` | 0.777 ★ Musée Maritime de Douala — Entry (adult resid `staging/benchmark/third_party` |
| 2 | 0.622 Typical individual city taxi course `practical_information/unverified/primary` | 0.777 ★ Musée Maritime de Douala — Entry (adult resid `staging/benchmark/third_party` | 0.781 ★ Musée maritime de Douala — Circuler `wikivoyage/unverified/third_party` |
| 3 | 0.608 Foire Internationale de Douala pour le Dévelo `event/unverified/primary` | 0.756 ★ Douala — Voir `wikivoyage/unverified/third_party` | 0.756 ★ Douala — Voir `wikivoyage/unverified/third_party` |
| 4 | 0.605 Palais de Justice de Douala `attraction/verified/primary` | 0.732 ★ Musée maritime de Douala — Présentation `wikivoyage/unverified/third_party` | 0.732 ★ Musée maritime de Douala — Présentation `wikivoyage/unverified/third_party` |
| 5 | 0.603 Festival Ngondo `event/unverified/primary` | 0.723 ★ Musée maritime de Douala — Comprendre `wikivoyage/unverified/third_party` | 0.723 ★ Musée maritime de Douala — Comprendre `wikivoyage/unverified/third_party` |

## What is there to do in Rhumsiki?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.608 Mont Fébé `attraction/verified/primary` | 0.751 ★ Rhumsiki — Overview `wikivoyage/unverified/third_party` | 0.751 ★ Rhumsiki — Overview `wikivoyage/unverified/third_party` |
| 2 | 0.602 Golf de Tiko `attraction/verified/primary` | 0.724 ★ Rhumsiki — Overview `wikivoyage/unverified/third_party` | 0.724 ★ Rhumsiki — Overview `wikivoyage/unverified/third_party` |
| 3 | 0.594 Foumban `destination/verified` | 0.668 ★ Maroua — Voir `wikivoyage/unverified/third_party` | 0.668 ★ Maroua — Voir `wikivoyage/unverified/third_party` |
| 4 | 0.587 Palais de Justice de Douala `attraction/verified/primary` | 0.654 ★ Northern Cameroon — Overview `wikivoyage/unverified/third_party` | 0.634 ★ Accommodation in Far North region: Roumsiki,  `osm/unverified/secondary` |
| 5 | 0.584 Kribi `destination/verified` | 0.647 ★ Ngoketunjia — See `wikivoyage/unverified/third_party` | 0.614 ★ Rencontres et échanges culturels `mintoul/verified/primary` |

## How do I get from Douala to Yaoundé?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.686 Rail corridor `practical_information/unverified/primary` | 0.750 ★ Yaoundé — Get in `wikivoyage/unverified/third_party` | 0.750 ★ Yaoundé — Get in `wikivoyage/unverified/third_party` |
| 2 | 0.679 Douala `destination/verified` | 0.742 ★ Douala — Get in `wikivoyage/unverified/third_party` | 0.742 ★ Douala — Get in `wikivoyage/unverified/third_party` |
| 3 | 0.657 International airports `practical_information/unverified/primary` | 0.739 ★ Yaoundé — Get in `wikivoyage/unverified/third_party` | 0.739 ★ Yaoundé — Get in `wikivoyage/unverified/third_party` |
| 4 | 0.654 Yaoundé `destination/verified` | 0.733 ★ Yaoundé — Get in `wikivoyage/unverified/third_party` | 0.730 ★ Yaoundé — Aller `wikivoyage/unverified/third_party` |
| 5 | 0.639 Palais des Congrès de Yaoundé `attraction/verified/primary` | 0.730 ★ Yaoundé — Aller `wikivoyage/unverified/third_party` | 0.686 Rail corridor `practical_information/unverified/primary` |

## Visiter la chefferie de Bandjoun

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.670 Foumban `destination/verified` | 0.754 ★ Chefferie de Bandjoun — Museum entry (adult/c `staging/benchmark/third_party` | 0.754 ★ Chefferie de Bandjoun — Museum entry (adult/c `staging/benchmark/third_party` |
| 2 | 0.645 La Chefferie de Bafut `heritage/verified/primary` | 0.720 ★ Bandjoun — Voir `wikivoyage/unverified/third_party` | 0.720 ★ Bandjoun — Voir `wikivoyage/unverified/third_party` |
| 3 | 0.627 Mont Fébé `attraction/verified/primary` | 0.713 ★ Bandjoun — Voir `wikivoyage/unverified/third_party` | 0.694 ★ Heritage and monuments in West region: Bamend `osm/unverified/secondary` |
| 4 | 0.624 Palais de Justice de Douala `attraction/verified/primary` | 0.712 ★ Bandja — Voir `wikivoyage/unverified/third_party` | 0.713 ★ Bandjoun — Voir `wikivoyage/unverified/third_party` |
| 5 | 0.623 Festival NGOUON `event/unverified/primary` | 0.705 ★ Bandjoun — Manger `wikivoyage/unverified/third_party` | 0.712 ★ Bandja — Voir `wikivoyage/unverified/third_party` |

## Where can I see gorillas in Cameroon?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.673 Limbe `destination/verified` | 0.708 ★ Campo Ma'an National Park — Overview `wikivoyage/unverified/third_party` | 0.674 ★ Visiter `mintoul/verified/primary` |
| 2 | 0.643 Parc national de Korup `attraction/verified/primary` | 0.706 ★ South Cameroon Plateau — Overview `wikivoyage/unverified/third_party` | 0.673 Limbe `destination/verified` |
| 3 | 0.634 Foumban `destination/verified` | 0.705 ★ Ebolowa — Voir `wikivoyage/unverified/third_party` | 0.673 ★ Visiter `mintoul/verified/primary` |
| 4 | 0.628 Dja Faunal Reserve `heritage/verified/primary` | 0.697 ★ Lobéké National Park — See `wikivoyage/unverified/third_party` | 0.690 ★ Campo Ma'an National Park — Entry permit (per `staging/benchmark/third_party` |
| 5 | 0.628 Kribi `destination/verified` | 0.692 ★ Korup National Park — Overview `wikivoyage/unverified/third_party` | 0.708 ★ Campo Ma'an National Park — Overview `wikivoyage/unverified/third_party` |

## What festivals happen in Foumban?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.763 Festival NGOUON `event/unverified/primary` | 0.763 Festival NGOUON `event/unverified/primary` | 0.763 Festival NGOUON `event/unverified/primary` |
| 2 | 0.719 Festival YANG YANG `event/unverified/primary` | 0.729 ★ Ngoketunjia — See `wikivoyage/unverified/third_party` | 0.719 Festival YANG YANG `event/unverified/primary` |
| 3 | 0.716 Foumban `destination/verified` | 0.728 ★ Ngoketunjia — See `wikivoyage/unverified/third_party` | 0.716 Foumban `destination/verified` |
| 4 | 0.695 Festival Mendumba `event/unverified/primary` | 0.726 ★ Ngoketunjia — See `wikivoyage/unverified/third_party` | 0.695 Festival Mendumba `event/unverified/primary` |
| 5 | 0.680 Festival Mpo’o `event/unverified/primary` | 0.721 ★ Ngoketunjia — See `wikivoyage/unverified/third_party` | 0.691 ★ Foires, Salon, Festivals,… `mintoul/verified/primary` |

## Quel est le prix d'un taxi à Douala ?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.729 Typical individual city taxi course `practical_information/unverified/primary` | 0.774 ★ Douala — Circuler `wikivoyage/unverified/third_party` | 0.735 ★ Transport Interne `mintoul/verified/primary` |
| 2 | 0.702 Taxi minimum city fare `practical_information/unverified/primary` | 0.735 ★ Transport Interne `mintoul/verified/primary` | 0.774 ★ Douala — Circuler `wikivoyage/unverified/third_party` |
| 3 | 0.684 Airport taxi daytime `practical_information/unverified/primary` | 0.729 Typical individual city taxi course `practical_information/unverified/primary` | 0.729 Typical individual city taxi course `practical_information/unverified/primary` |
| 4 | 0.674 Airport taxi night `practical_information/unverified/primary` | 0.702 Taxi minimum city fare `practical_information/unverified/primary` | 0.702 Taxi minimum city fare `practical_information/unverified/primary` |
| 5 | 0.667 Douala `destination/verified` | 0.698 ★ Douala — Get in `wikivoyage/unverified/third_party` | 0.684 Airport taxi daytime `practical_information/unverified/primary` |

## What should I know about the Far North region?

| # | Before | After | After + rerank |
|---|---|---|---|
| 1 | 0.588 Yaoundé `destination/verified` | 0.683 ★ Northern Cameroon — Overview `wikivoyage/unverified/third_party` | 0.675 ★ UK travel advice (FCDO): Regional risks — Far `fcdo/verified/primary` |
| 2 | 0.587 HAMAN DAHIROU `guide/unverified/primary` | 0.675 ★ UK travel advice (FCDO): Regional risks — Far `fcdo/verified/primary` | 0.647 ★ Présentation du Cameroun `mintoul/verified/primary` |
| 3 | 0.587 Foumban `destination/verified` | 0.672 ★ Maroua — Overview `wikivoyage/unverified/third_party` | 0.666 ★ Accommodation in Far North region: Kaélé, Kou `osm/unverified/secondary` |
| 4 | 0.584 Adama Mirabelle `guide/unverified/primary` | 0.669 ★ Northwest Highlands — Overview `wikivoyage/unverified/third_party` | 0.683 ★ Northern Cameroon — Overview `wikivoyage/unverified/third_party` |
| 5 | 0.582 Douala `destination/verified` | 0.666 ★ Accommodation in Far North region: Kaélé, Kou `osm/unverified/secondary` | 0.662 ★ Accommodation in Far North region: Yagoua (Op `osm/unverified/secondary` |

