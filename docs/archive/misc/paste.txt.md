<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# paste.txt

This file is a detailed build brief plus implementation summary for a Django “marketing-monitor-v2” Sprint 1–2 app, including models, authz rules, views, templates, tests, and local run instructions.[^1_1]

### What’s in paste.txt

- A **builder task spec** telling you to create a runnable Django project in the repo root with a `marketing_monitor` project and a `core` app, using server-rendered templates and SQLite for dev.[^1_1]
- Strict **scope and auth constraints**, including using the frozen reference `authz.py`, `mixins.py`, `validators.py`, and `test_scope.py` as canon for permissions and operator scoping.[^1_1]
- Precise **models** for `Operator`, `Creator`, `CreatorChannel`, and `OperatorAssignment`, with enumerated choices and validation rules (e.g. creator active requires consent active, case-insensitive uniqueness for `(platform, handle)`, non-overlapping assignment windows).[^1_1]
- Required **views, URLs, and templates**: login, lists/detail/forms for creators, channels, assignments, and operators, with admin-only write flows via `AdminOnlyMixin` and read-only operator UI.[^1_1]
- Expected **tests and bootstrap steps**, including copying reference scope tests, adding a few extra validations tests, and instructions to install requirements, migrate, create a superuser, and run the dev server.[^1_1]


### High-level implementation summary inside the file

- Confirms the project structure (`manage.py`, `marketing_monitor/`, `core/`, templates, `requirements.txt`, updated `README.md`) was created.[^1_1]
- States that auth/scope logic was copied into `core/authz.py`, `core/mixins.py`, `core/validators.py` and wired into CBVs so operators only see in-scope objects and admins see everything.[^1_1]
- Notes that all writes are admin-guarded, operators are read-only in the UI, `primary_operator` is never used for permissions, and the screens and tests outlined in the brief are present (subject to Django being installable in the environment).[^1_1]

Do you want me to turn this spec into concrete file-by-file code for a fresh repo, or just extract a tighter checklist you can implement against?

<div align="center">⁂</div>

[^1_1]: paste.txt


---

# forget everything

I cannot erase my underlying training or system-level settings, but I can stop using past, stored personalization about you going forward in this conversation.

From this point on in this chat, I will:

- Not rely on previously stored memories about you (projects, preferences, background, etc.).[^2_1]
- Treat your messages as if I have no prior knowledge of you beyond what you state in this session.[^2_1]

If you want, I can also explicitly not store any new long-term memory from this point; would you like me to do that?

<div align="center">⁂</div>

[^2_1]: paste.txt


---

# Bedenk alle bronnen die informatie geven over brandgevaar in natuur en ecologische gebieden. Denk daarna na over onconventionele bronnen bronnen die normaliter niet gebruikt worden voor preventie van natuurbranden, bijvoorbeeld de duiven vereniging blijkt heel veel data te hebben, kijk eerst in het algemeen wereldwijd en dan inzoomen op Portugal en kijk welke bronnen daar voor handig zijn. Bijvoorbeeld hield de FBI alle boekuitleningen bij bij alle openbare bibliotheken om zo te zien wie boeken over ideologie of bommen leende. Niet letterlijk dit idee gaan toepassen. Maar begrijp de essentie ervan. Trouwens zoeken wij data om natuurbranden in Portugal te voorspellen, geen mensen.

Voor natuurbrand-voorspelling kun je het zien als drie lagen: klassieke bronnen, bredere “risk context”-bronnen en echt onconventionele signalen. Hieronder eerst mondiaal, dan inzoomend op Portugal, en daarna een lijst met gekke maar potentieel nuttige ideeën.

## Klassieke en semi-klassieke bronnen wereldwijd

Dit zijn de bouwstenen van bijna alle serieuze wildfire-systemen.

- Sateliet-**hotspots** en brandextens: NASA FIRMS (MODIS/VIIRS) levert near‑real‑time actieve branden en brandlijnen.[^3_1][^3_2]
- Mondiale en EU‑systemen: GWIS en EFFIS combineren satellietdata, weer, vegetatie en historische branden om risico, intensiteit en emissies te schatten.[^3_3][^3_4][^3_5][^3_6]
- Fire Weather Index / Fire Danger indices: globale FWI-datasets (bijv. CSIRO/World Bank) modelleren meteorologische brandgevaarlijkheid met return-period scenario’s.[^3_7]
- Vegetatie, brandstof en landgebruik: datasets zoals ESA CCI biomass, Copernicus land cover en nationale boskaarten geven brandstofcontinuïteit en ‑lading.[^3_8][^3_2]
- Historische brandprogressie-databases: onderzoek zoals PT‑FireSprd laat zien hoe je uit satelliet, luchtfoto’s, velddata en operationele logs een gedetailleerde “fire spread” database kunt bouwen.[^3_9]
- Globale risicoplatforms: platforms als PreventionWeb’s global risk datasets verzamelen kant‑en‑klare hazard-lagen voor o.a. bosbranden die je in nationale systemen kunt hergebruiken.[^3_10]


## Specifiek voor Portugal

Portugal heeft een vrij rijke eigen stack rond brandgevaar.

- IPMA indices:
    - FWI-voorspellingen (24–120 uur) met temperatuur, RV, wind, neerslag uit ECMWF; gebruikt voor IPMA’s Fire Risk Map.[^3_11]
    - RCM (Rural Fire Danger Index) die FWI combineert met structurele en cyclische componenten op basis van verbrand oppervlak van de laatste drie jaar (met ICNF-data).[^3_12]
- ICNF gegevens: structureel brandgevaar, historische burnt area, vegetatietypen en beschermde gebieden, gebruikt in de RCM-structuurcomponent.[^3_12]
- PT-FireSprd database: open-access database die grote Portugese bosbranden beschrijft met fire spread isochronen, radiatieve energie, veldobservaties en logboeken van de civiele bescherming.[^3_9]
- Operationele platforms: FEBMON (Web-GIS van civiele bescherming) integreert satelliet, lucht- en grondgegevens voor near-real-time monitoring en kan als inspiratiebron dienen voor welke operationele variabelen nuttig zijn.[^3_9]
- Nationale meteo- en waarschuwingssystemen: IPMA’s dagelijkse kaart “Perigo de Incêndio Rural” per gemeente/district, die reeds de weerdimensie en recente brandgeschiedenis aggregeert.[^3_13][^3_12]


## Brede context- en proxybronnen (nog redelijk conventioneel)

Dit zijn bronnen die niet direct brand, maar wel brandrisico of impact moduleren.

- Bevolkingsdichtheid, wegennet, recreatie-infrastructuur: worden al gebruikt als ignition‑proxies in ML‑modellen (meer mensen + bereikbaarheid = vaker ontsteking).[^3_2]
- Buitensport- en toerismestromen: drukte in natuurgebieden (mobiele aggregaten, parkeergegevens, ticketing voor natuurparken) geeft kans op mens‑geïnduceerde ontstekingen.
- Energie‑infrastructuur: hoogspanningslijnen, transformators, windparken; storingslogs van netbeheerders kunnen correlaties tonen met ignitions (zoals in Californië).
- Landbouw- en beheervergunningen: waar en wanneer wordt gesnoeid, gebrand (legale branden), geoogst—verandert lokale brandstofstructuur en humane aanwezigheid.
- Bliksemdata: klassieke ignition‑bron, via satelliet-/radarproducten (bijv. GLM) of commerciële netwerken, direct bruikbaar in voorspelling samen met FWI.[^3_2]


## Onconventionele en “FBI-library”‑achtige bronnen (algemeen)

Nu de creatievere laag: bronnen die normaal niet in brandpreventie zitten, maar potentieel voorspellende signalen bevatten. Belangrijk: we richten ons op natuurbranden, niet op individuen.

- Hobby- en verenigingsdata
    - Jacht- en vissersverenigingen: seizoenslidmaatschap, geplande jachtdagen, waar/wanneer groepen in brandgevoelige gebieden zijn.
    - Wandel-, MTB- en trailrunningclubs: geplande tochten en evenementen door natuurgebieden.
    - Modelvlieg- en droneclubs: events boven droge heide/bos; risico op crash‑ignitions.
- Vrijwilligers- en burgernetwerken
    - Natuur- en vogelbeschermingsgroepen: waarnemingen (soort + locatie + frequentie) geven extreem hoge spatiële resolutie van menselijk gebruik van natuurgebieden.
    - Citizen science-platforms: foto’s/waarnemingen van droogteverschijnselen, afgestorven vegetatie, ongebruikelijke rook of kleine illegale vuurhaarden.
- Logistiek en mobiliteit
    - Bezorg- en koeriersnetwerken in rurale gebieden: warmtedata van voertuigsensoren is misschien minder relevant, maar route-intensiteit geeft “human presence heatmap”.
    - Parkeerdata rond natuurgebieden: pieken in parkeergebruik bij trailheads en strand/natuur-parking in droge periodes als ignition‑risico-indicator.
- Economische en gedragsdata
    - Verkoop van BBQ-, kamp- en tuinverbrandingsmateriaal per regio (aggregaat): correlaties tussen hittegolven, promoties en toename kleine buitenvuren.
    - Verkoop van landbouwbrandstof en agrochemie: intensievere landbewerking in bepaalde perioden kan samenlopen met verhoogd machine‑gebruik in droge velden.
    - Verzekeringsclaims voor kleine schades door vuur in rurale gebieden: “near misses” en kleine incidenten die geen officiële bosbrand zijn, maar wel patroon geven.
- Media en digitale sporen
    - Lokale nieuws- en radiologs: meldingen over kleine bermbrandjes, rook, illegale afvalverbranding, traditioneel vreugdevuur.
    - Geanonimiseerde social media geotags: piekactiviteit in specifieke ravijnen of bergkammen bij hittegolven (veel mensen + droogte). Niet kijken naar individuen, maar naar dichtheidspatronen.
    - Open web-scraping: evenementenagenda’s (dorpsfeesten, vuurwerkshows, openluchtconcerten in natuurgebied) als kortetermijn‑risicoboosters.
- Milieu- en infrastructuursensoren
    - Industriële luchtsensoren of low‑cost sensornetwerken (PM2.5, rookdeeltjes) van universiteiten of citizen science-projecten als vroege rookdetectie of droogtestress-indicator.[^3_14][^3_15]
    - Waterleiding- en irrigatie-data: plotselinge daling in irrigatiehoeveelheden in landbouw/natuurgebieden kan duiden op extreme droogte of waterrestricties.


## Portugal: concrete onconventionele bronnen

Als je inzoomt op Portugal, kun je de bovenstaande ideeën koppelen aan bestaande actoren.

- Jacht, natuur en recreatie
    - Jachtverenigingen en federaties (Federações de Caça): jachtseizoenplannen, vergunde jachtgebieden, geplande drijfjachten.
    - Caminhada- en MTB-clubs, trailrunners (lokale sportverenigingen, Meetup‑groepen): kalender + GPS‑routes.
    - Surf- en strandclubs dicht bij natuurparken (bijv. Peneda‑Gerês, Serra da Estrela): parkeren en toegangsroutes door dennen- en eucalyptusbossen.
- Landbouw en rurale economie
    - Coöperaties (vinho, olijfolie, kurk, vee): seizoensschema’s voor werkzaamheden die veel droge biomassa produceren (snoeien, oogsten, branden van restmateriaal).
    - Regionale markten / veemarkten: toename activiteit in rurale zones waar mensen tijdelijk massaal bijeenkomen.
- Vrijwilligers en ngo’s
    - Lokale natuurorganisaties (Associações de Defesa do Ambiente) en wandelclubs: meldingen van sluikstort, illegale vuurplaatsen, ongebruikelijke rook.
    - Brandweervrijwilligersverenigingen (Bombeiros Voluntários): niet alleen incidentlogs, maar ook oefen- en trainingsschema’s in natuurgebieden.
- Lokale overheden en nutsbedrijven
    - Gemeentelijke vergunningsdata voor buitenvuren, festivals, vuurwerk, religieuze processies met kaarsen/vuur in of langs natuurzones.
    - E-Redes en andere netbeheerders: geaggregeerde storingsstatistiek bij lijnen die door hoog‑risicobossen lopen; niet persoonsgebonden, enkel lijnsegment-Risk.
    - Irrigatie-/waterbeheer-instellingen: patronen van waterrestricties per micro‑regio als proxy voor droogtestress bovenop FWI/RCM.[^3_11][^3_12]
- Digitale sporen en media
    - Regionale radiostations en lokale kranten: tekstanalyse voor signalen van “queimada”, “fogo de mato”, “lixo queimado” die niet in officiële branddatabases komen.
    - Geanonimiseerde mobiliteitsdata (telecom, navigatie-apps): heatmaps van verblijf in natuur- en bosgebieden bij rood/oranje IPMA‑risico.[^3_13][^3_11]


## Hoe dit in een voorspelmodel past (conceptueel)

Een praktische manier om dit veilig en ethisch te integreren voor Portugal:

- Basismodel: gebruik IPMA FWI/RCM, ICNF brandhistoriek en globale bronnen (GWIS/FIRMS) als primaire hazard‑laag.[^3_4][^3_1][^3_12][^3_11]
- Ignition‑laag: bouw features rond menselijke aanwezigheid en activiteit: recreatie-evenementen, jachtdagen, mobiliteitsdichtheid, vergunningen voor vuur, plus bliksem- en infrastructuurstoringen.[^3_2][^3_13][^3_9]
- “Weak signals”: leg patronen vast uit nieuws, verenigingskalenders, citizen science‑meldingen en kleine “near miss” incidenten om hotspots te vinden die nog niet vaak grote branden hebben gehad.
- Privacy \& ethiek: werk uitsluitend met geaggregeerde, geanonimiseerde data, op grid‑ of gemeente‑niveau; geen individuele tracking, geen profiling van personen of groepen. Het doel is **brandrisico**, niet gedrag van individuen.

Welke van deze drie lagen wil je als eerste uitwerken tot een concreet datamodel en feature‑lijst: de klassieke hazard‑kern, de menselijke activiteit/ignition‑laag, of de echt onconventionele “weak signals”?

<div align="center">⁂</div>

[^3_1]: https://www.earthdata.nasa.gov/data/tools/firms

[^3_2]: https://blog.thegovlab.org/monitoring-the-re-use-and-impact-of-non-traditional-data

[^3_3]: https://effis.emergency.copernicus.eu

[^3_4]: https://gwis.jrc.ec.europa.eu

[^3_5]: https://ourworldindata.org/wildfires

[^3_6]: https://hub.arcgis.com/datasets/9403c9558f8e442a897ed67b64bf4a90

[^3_7]: https://datacatalog.worldbank.org/search/dataset/0066912/global-wildfire-hazard

[^3_8]: https://gee-community-catalog.org/projects/wrc/

[^3_9]: https://essd.copernicus.org/articles/15/3791/2023/

[^3_10]: https://www.preventionweb.net/understanding-disaster-risk/disaster-losses-and-statistics/global-risk-data-sets

[^3_11]: https://www.ipma.pt/pt/riscoincendio/fwi/

[^3_12]: https://www.ipma.pt/en/enciclopedia/otempo/risco.incendio/index.jsp?page=pirrcm.xml

[^3_13]: https://www.ipma.pt/en/riscoincendio/rcm.pt/

[^3_14]: https://opendatapolicylab.org/articles/blog-recent-uses-of-non-traditional-data-in-the-public-interest-september-december-2025/

[^3_15]: https://prism.sustainability-directory.com/scenario/predictive-analytics-for-climate-risk-and-community-resilience-planning/


---

# Beginnen met de klassieke hazard kern en bronnen

Voor de “klassieke hazard‑kern” wil je in feite drie dingen combineren: weer‑gebaseerd brandgevaar (FWI/RCM), structurele gevaren (brandstof/landgebruik) en empirische brandgeschiedenis, eerst globaal, dan specifiek in Portugal.[^4_1][^4_2][^4_3]

## 1. Kern‑indices en globale hazard‑bronnen

- Globale FWI‑klimatologie
    - World Bank / CSIRO “Global Wildfire Hazard” dataset: FWI berekend op een wereldwijde grid (~0,5°) met extreme‑waardeanalyse (2, 5, 30‑jaars terugkeerperioden) voor hazard‑mapping.[^4_4][^4_1]
    - Gebruik: langetermijn‑hazard (structurele brandgevaarlijkheid) op wereldschaal, goed als achtergrondlaag voor Portugal en om PT‑waarden in context te plaatsen.
- Globale burnt‑area / event‑databases
    - GlobFire database: op MODIS MCD64A1 gebaseerde globale single‑wildfire event database (vormt basis in GWIS), met ruimte‑tijd reconstructie van afzonderlijke branden.[^4_5][^4_6]
    - Gebruik: karakterisatie van “fire regimes” (frequentie, grootte, seizoenspatronen) en kalibratie van je Portugese modellen t.o.v. andere mediterrane regio’s.
- Burn severity en impact
    - Global Forest Burn Severity (GFBS): 30m Landsat‑gebaseerde burn severity voor bosbranden wereldwijd (2003–2016).[^4_7]
    - Gebruik: koppelen van hazard aan daadwerkelijke schade‑intensiteit; handig voor prioritering van brandstofbeheer.
- Operationele globale systemen
    - GWIS: integreert regionale en nationale bronnen tot een wereldwijd beeld van brandregimes en biedt tools voor operationele ondersteuning.[^4_6][^4_8]
    - Gebruik: referentie voor methodologie (indices, drempels, visualisatie) en als sanity check voor jouw eigen PT‑kaart.


## 2. Portugese hazard‑kern: FWI + RCM

Portugal is extra interessant omdat IPMA al een vrij geavanceerde hazard‑kern heeft gebouwd rond FWI en RCM.

- Fire Weather Index (FWI)
    - IPMA berekent FWI op basis van meteo‑variabelen (temperatuur, relatieve vochtigheid, wind, neerslag) per station en op rasters (modelgrid of satellietpixels).[^4_9][^4_10]
    - FWI bestaat uit 6 subindices die bodemvocht en brandgedrag representeren; IPMA classificeert FWI in 5 klassen (1–5: laag tot maximaal) volgens tabellen gekalibreerd op brandintensiteit (kW/m) en controleerbaarheid.[^4_9]
- RCM (Risco Conjuntural e Meteorológico)
    - RCM = combinatie van FWI (meteorologisch gevaar) en “Perigosidade de Incêndio Rural” (structurele gevaarlijkheid op basis van historisch verbrand oppervlak en vegetatie).[^4_3]
    - IPMA: RCM wordt dagelijks berekend, geclassificeerd, en gepubliceerd als kaarten met observaties en voorspellingen voor 24, 48, 72, 96 en 120 uur vooruit.[^4_10][^4_11]
    - Observaties: RCM‑observaties combineren de geobserveerde FWI‑waardes met vaste hazard‑klassen per cel.[^4_11]
    - Voorspellingen: zelfde methode, maar met FWI‑voorspellingen uit statistisch downscaled weermodellen (ECMWF etc.).[^4_12][^4_10]

→ Praktisch: voor jouw “kern” kun je FWI/RCM per gridcel (of gemeente) nemen als directe, kant‑en‑klare hazard‑features, én gebruikmaken van hun klassen (1–5) als discrete risicocategorie.

## 3. Structurele hazard: brandstof, topografie, landgebruik

Deze componenten veranderen traag en vormen de basis “perigosidade” in RCM.

- Structurele rural fire hazard (Portugal)
    - IPMA beschrijft “Perigosidade de Incêndio Rural” als een aparte component, gebaseerd op historische branddata en kenmerken van het landschap.[^4_3]
    - In de RCM‑methodologie wordt deze structurele hazard via een matrix gecombineerd met FWI‑klassen tot een samengestelde RCM‑klasse.[^4_3]
- Brandstof en landcover
    - Copernicus Land Cover en nationale bos‑/vegetatiekaarten van Portugal (o.a. ICNF) leveren bossoorten, continuïteit van brandbare biomassa en typen (eucalyptus, den, scrub, agrarisch, urbaan).[^4_13][^4_3]
    - Gebruik: conversie naar brandstofklassen (bijv. hoge vs lage brandbare lading, kroonbrandgevoeligheid) op dezelfde grid als FWI/RCM.
- Topografie
    - Elevatie, helling, aspect (bijv. vanuit een DEM) beïnvloeden brandintensiteit en ‑snelheid; PT‑FireSprd laat zien dat variatie in fire behaviour sterk samenhangt met weer, brandstof én topografie.[^4_2][^4_14]

→ In je model: maak per cel statische features zoals “hazard_class_structural”, “fuel_type”, “slope”, “aspect”, “distance_to_valley/ridges”.

## 4. Empirische fire‑behavior data voor Portugal

Voor calibratie en meer geavanceerde modellen is PT‑FireSprd goud waard.

- PT‑FireSprd database
    - Bevat 80 grote Portugese bosbranden (2015–2021) met reconstructie van brandvoortgang (isochronen), fire behaviour‑descriptors (ROS, FGR, FRE, FRE‑flux) en context.[^4_15][^4_2]
    - De branden bestrijken heel Portugal en een breed scala aan omgevingscondities; oppervlaktes variëren van 250 tot 45 339 ha, met gemiddelde 5990 ha.[^4_2]
    - Data is opgebouwd uit een “convergence‑of‑evidence” van operationele lucht- en grondbronnen en remote sensing.[^4_2]

→ Gebruik:

- Valideer je hazard‑kern: bij welke combinaties van FWI/RCM + fuel + topografie traden hoge ROS/FRE op?
- Leer drempels voor “extreme dagen” in Portugese context (meer informatief dan globale generieke FWI‑cutoffs).[^4_1][^4_2]


## 5. Praktische feature‑kern voor jouw model

Als je dit terugbrengt tot een compacte, implementeerbare kern voor Portugal:

- Meteo‑/brandgevaarfeatures (tijdelijk, per dag/uur per cel of gemeente)
    - FWI waarde + klasse (1–5) van IPMA.[^4_10][^4_9]
    - RCM waarde + klasse, observatie én 24–120h voorspelling.[^4_11][^4_10]
    - Eventueel: global FWI‑percentiel (uit de World Bank‑dataset) om “extreem t.o.v. normaal” te coderen.[^4_4][^4_1]
- Structurele hazardfeatures (statisch of traag variërend)
    - IPMA/ICNF “Perigosidade de Incêndio Rural” klasse.[^4_13][^4_3]
    - Landgebruik/brandstofklasse uit nationale bos- en landcoverkaarten.
    - Topografie: helling, aspect, hoogte, afgeleiden (potentiële upslope spread, etc.).
- Empirische calibratie‑features (voor modelbouw/validatie, niet per se real‑time)
    - Koppeling van PT‑FireSprd fire behaviour‑metrieken (ROS, FRE) aan FWI/RCM+structuur voor dagen met grote branden.[^4_15][^4_2]

Zo heb je een solide, wetenschappelijk onderbouwde hazard‑kern, waar je later ignition‑en human‑activity features bovenop kunt zetten.

Wil je dat ik de volgende stap maak en deze kern vertaal naar een concreet data‑schema (tabellen/velden) dat je direct in je datalake of database kunt aanleggen?
<span style="display:none">[^4_16]</span>

<div align="center">⁂</div>

[^4_1]: https://datacatalog.worldbank.org/search/dataset/0066912/global-wildfire-hazard

[^4_2]: https://essd.copernicus.org/articles/15/3791/2023/

[^4_3]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nt-rcm.pdf

[^4_4]: https://oasishub.co/dataset/global-wildfire-hazard-maps-world-bank-group-cckp

[^4_5]: https://www.nature.com/articles/s41597-019-0312-2

[^4_6]: https://gwis.jrc.ec.europa.eu

[^4_7]: https://essd.copernicus.org/preprints/essd-2023-446/essd-2023-446.pdf

[^4_8]: https://av.tib.eu/media/55272

[^4_9]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nota-metodologica-calculo-RCM2020-v20200713.pdf

[^4_10]: https://www.ipma.pt/pt/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml

[^4_11]: https://www.ipma.pt/en/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml

[^4_12]: https://docs.theclimatedatafactory.com/methods/hazards/wildfire-hazard/

[^4_13]: https://www.ipma.pt/en/enciclopedia/otempo/risco.incendio/index.jsp?page=pirrcm.xml

[^4_14]: https://researchportal.ulisboa.pt/en/publications/the-portuguese-large-wildfire-spread-database-pt-firesprd

[^4_15]: https://zenodo.org/records/7495506

[^4_16]: https://egp.wildfire.gov/egp/data/


---

# Ik wil graag dat je de conclusie zo technisch mogelijk opschrijft voor de bouwer

Voor de bouwer is de “klassieke hazard‑kern” voor Portugal als volgt te implementeren:

1. Grid en keys
    - Kies één primaire ruimtelijke index: `cell_id` (rasters, bv. 1 km) of `municipality_id` (Diário da República / DGT‑codes).
    - Alle hazard‑tabellen refereren hieraan plus een tijdsdimensie `date` (en optioneel `hour`).
2. Tabel: `hazard_meteo_daily`
Minimale kolommen per `cell_id, date`:
    - `fwi_value` (float) – Fire Weather Index van IPMA of herberekend.
    - `fwi_class` (tinyint) – 1–5 volgens IPMA‑classificatie.[^5_1][^5_2]
    - `rcm_value` (float) – Risco Conjuntural e Meteorológico (numerieke index).[^5_3][^5_4]
    - `rcm_class` (tinyint) – 1–5, direct overgenomen van IPMA.[^5_2]
    - `fwi_global_pctl` (float, 0–100) – percentiel t.o.v. de globale hazard‑klimatologie (World Bank Global Wildfire Hazard), pre‑gecompute per cel.[^5_5][^5_6]
    - `source_tag` (varchar) – bv. `ipma_api`, `derived_ecmwf`, voor lineage.
3. Tabel: `hazard_meteo_forecast`
Zelfde structuur, maar met extra `lead_hours`:
    - `cell_id`
    - `base_date` (initiatiedatum run)
    - `lead_hours` (int, 24/48/72/96/120) conform IPMA.[^5_4][^5_2]
    - `fwi_value`, `fwi_class`, `rcm_value`, `rcm_class`, `source_tag`.
4. Tabel: `hazard_structural_static`
Eén record per `cell_id` (of gemeente):
    - `structural_hazard_class` (tinyint) – IPMA/ICNF Perigosidade de Incêndio Rural‑klasse.[^5_7][^5_3]
    - `landcover_class` (smallint) – code (Corine / Copernicus / nationaal bosbestand).
    - `fuel_model` (smallint, nullable) – vereenvoudigde brandstofklasse (bijv. 1–10) afgeleid uit `landcover_class`.
    - `elevation_m` (float) – DEM‑hoogte.
    - `slope_deg` (float).
    - `aspect_deg` (float).
    - `distance_to_settlement_m` (float, optioneel, voor latere ignition‑laag).
5. Tabel: `wildfire_events_pt` (kalibratie, niet per se realtime)
Gebaseerd op PT‑FireSprd, genormaliseerd naar jouw grid.[^5_8][^5_9]
    - `event_id` (uuid) – unieke brand.
    - `start_datetime`, `end_datetime`.
    - `area_ha` (float).
    - `max_ros_m_s`, `mean_ros_m_s` (float).
    - `max_fre_kw_m`, `mean_fre_kw_m` (float).
    - Koppel‑tabel `wildfire_event_cells`:
        - `event_id`, `cell_id`, `date`,
        - `stage` (enum: `ignition`, `head`, `flank`, `back`),
        - `burned_today_ha` (float).
6. Join‑logica (hazard‑kern query‑patroon)
Voor modelbouw of operational use:
    - Join `hazard_meteo_daily` (of `hazard_meteo_forecast`) met `hazard_structural_static` op `cell_id`.
    - Voor analyses met PT‑FireSprd: join `wildfire_event_cells` op `cell_id, date` → dan FWI/RCM+structuur ernaast leggen voor fire‑behaviour regressie of drempelbepaling.[^5_3][^5_5][^5_8]
7. Minimale API‑achtige view / materialized view
    - Maak een view `v_hazard_core_daily`:
        - `cell_id`, `date`,
        - `fwi_value`, `fwi_class`, `rcm_value`, `rcm_class`, `fwi_global_pctl`,
        - `structural_hazard_class`, `fuel_model`, `slope_deg`, `aspect_deg`.
    - Dit is de primaire feed voor een risico‑kaartlaag en voor de ML‑feature pipeline.

Wil je dat ik op basis hiervan nu een concreet SQL‑schema (CREATE TABLE’s) uitschrijf, of eerst een mapping voorstel naar de feitelijke IPMA/ICNF dataproducten (bestandsformaten, API’s, grids)?

<div align="center">⁂</div>

[^5_1]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nota-metodologica-calculo-RCM2020-v20200713.pdf

[^5_2]: https://www.ipma.pt/pt/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml

[^5_3]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nt-rcm.pdf

[^5_4]: https://www.ipma.pt/en/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml

[^5_5]: https://datacatalog.worldbank.org/search/dataset/0066912/global-wildfire-hazard

[^5_6]: https://oasishub.co/dataset/global-wildfire-hazard-maps-world-bank-group-cckp

[^5_7]: https://www.ipma.pt/en/enciclopedia/otempo/risco.incendio/index.jsp?page=pirrcm.xml

[^5_8]: https://essd.copernicus.org/articles/15/3791/2023/

[^5_9]: https://zenodo.org/records/7495506


---

# Kun je dit nachecken op accuraatheid en netheid Voor de bouwer is de “klassieke hazard‑kern” voor Portugal als volgt te implementeren:

Grid en keys
Kies één primaire ruimtelijke index: cell_id (rasters, bv. 1 km) of municipality_id (Diário da República / DGT‑codes).
Alle hazard‑tabellen refereren hieraan plus een tijdsdimensie date (en optioneel hour).
Tabel: hazard_meteo_daily
Minimale kolommen per cell_id, date:
fwi_value (float) – Fire Weather Index van IPMA of herberekend.
fwi_class (tinyint) – 1–5 volgens IPMA‑classificatie.ipma+1
rcm_value (float) – Risco Conjuntural e Meteorológico (numerieke index).ipma+1
rcm_class (tinyint) – 1–5, direct overgenomen van IPMA.[[ipma](https://www.ipma.pt/pt/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml)]​
fwi_global_pctl (float, 0–100) – percentiel t.o.v. de globale hazard‑klimatologie (World Bank Global Wildfire Hazard), pre‑gecompute per cel.datacatalog.worldbank+1
source_tag (varchar) – bv. ipma_api, derived_ecmwf, voor lineage.
Tabel: hazard_meteo_forecast
Zelfde structuur, maar met extra lead_hours:
cell_id
base_date (initiatiedatum run)
lead_hours (int, 24/48/72/96/120) conform IPMA.ipma+1
fwi_value, fwi_class, rcm_value, rcm_class, source_tag.
Tabel: hazard_structural_static
Eén record per cell_id (of gemeente):
structural_hazard_class (tinyint) – IPMA/ICNF Perigosidade de Incêndio Rural‑klasse.ipma+1
landcover_class (smallint) – code (Corine / Copernicus / nationaal bosbestand).
fuel_model (smallint, nullable) – vereenvoudigde brandstofklasse (bijv. 1–10) afgeleid uit landcover_class.
elevation_m (float) – DEM‑hoogte.
slope_deg (float).
aspect_deg (float).
distance_to_settlement_m (float, optioneel, voor latere ignition‑laag).
Tabel: wildfire_events_pt (kalibratie, niet per se realtime)
Gebaseerd op PT‑FireSprd, genormaliseerd naar jouw grid.essd.copernicus+1
event_id (uuid) – unieke brand.
start_datetime, end_datetime.
area_ha (float).
max_ros_m_s, mean_ros_m_s (float).
max_fre_kw_m, mean_fre_kw_m (float).
Koppel‑tabel wildfire_event_cells:
event_id, cell_id, date,
stage (enum: ignition, head, flank, back),
burned_today_ha (float).
Join‑logica (hazard‑kern query‑patroon)
Voor modelbouw of operational use:
Join hazard_meteo_daily (of hazard_meteo_forecast) met hazard_structural_static op cell_id.
Voor analyses met PT‑FireSprd: join wildfire_event_cells op cell_id, date → dan FWI/RCM+structuur ernaast leggen voor fire‑behaviour regressie of drempelbepaling.ipma+2
Minimale API‑achtige view / materialized view
Maak een view v_hazard_core_daily:
cell_id, date,
fwi_value, fwi_class, rcm_value, rcm_class, fwi_global_pctl,
structural_hazard_class, fuel_model, slope_deg, aspect_deg.
Dit is de primaire feed voor een risico‑kaartlaag en voor de ML‑feature pipeline.
Wil je dat ik op basis hiervan nu een concreet SQL‑schema (CREATE TABLE’s) uitschrijf, of eerst een mapping voorstel naar de feitelijke IPMA/ICNF dataproducten (bestandsformaten, API’s, grids)?

Inhoudelijk is dit voorstel stevig; een bouwer kan hier direct een schema uit trekken, maar er zijn twee kleine nauwkeurigheidspunten en een paar netheids-/stijlpunten.[^6_1][^6_2][^6_3]

## Accuraatheid

- IPMA FWI/RCM klassen
    - IPMA beschrijft FWI als continu index die in klassen wordt ingedeeld op basis van drempels; RCM is een samengestelde index (FWI + Perigosidade) met klassen 1 (laag) t/m 5 (zeer hoog).[^6_4][^6_1]
    - In nieuwere documentatie wordt FWI voor RCM soms hergeclassificeerd tot 1–6; jij schrijft “1–5 volgens IPMA‑classificatie”, wat voor RCM klopt maar voor FWI‑klassen iets generieker geformuleerd mag worden (bijvoorbeeld: “volgens IPMA‑reclassificatie op basis van drempelwaarden”).[^6_5]
- PT‑FireSprd verwijzing
    - De tekst “Gebaseerd op PT‑FireSprd” is correct; PT‑FireSprd bevat event‑niveau beschrijvingen (ROS, FRE, FGR enz.) en is expliciet geschikt voor calibratie en casestudies.[^6_2][^6_6]
    - Je velden `max_ros_m_s`, `mean_ros_m_s`, `max_fre_kw_m`, `mean_fre_kw_m` sluiten goed aan bij de L2‑laag (fire behaviour metrics) uit PT‑FireSprd.[^6_2]
- Global Wildfire Hazard percentielen
    - De beschrijving van `fwi_global_pctl` als percentiel t.o.v. de World Bank “Global Wildfire Hazard” dataset is in lijn met hoe die dataset FWI‑waarden voor 2/5/30‑jaars terugkeerperioden aanbiedt; een eigen percentielberekening per cel is een logische afgeleide.[^6_3]

Kortom: conceptueel klopt het, met de nuance dat je voor FWI‑klassen beter verwijst naar “IPMA‑drempels/reclassificatie” i.p.v. hard “1–5”.[^6_1][^6_5]

## Netheid / formulering voor de bouwer

- Consistentie van keys
    - Je openingsstuk over `cell_id` of `municipality_id` is helder; ik zou één zin toevoegen: “Kies dit vroeg en gebruik het consequent in alle tabellen als primary/foreign key.”
- Citation‑tags in de tekst
    - Dingen als `ipma+1`, `datacatalog.worldbank+1`, `essd.copernicus+1` zijn intern handig, maar voor een bouwer verwarrend; beter vervangen door voetnootstijl of een aparte referentielijst, of helemaal weglaten als de link er direct bij staat.[^6_6][^6_4][^6_3]
- Terminologie
    - “Perigosidade de Incêndio Rural‑klasse” is goed; voor absolute duidelijkheid kun je erbij zetten dat dit de structurele component van het RCM is volgens IPMA’s methodologiedocument.[^6_1]


## Strak herschreven versie

Als je deze tekst direct aan een bouwer wilt geven, zou ik hem zo neerzetten (zonder citation‑notatie):

> Voor de bouwer is de klassieke hazard‑kern voor Portugal als volgt te implementeren:
>
> **Grid en keys**
> Kies één primaire ruimtelijke index: `cell_id` (raster, bv. 1 km) of `municipality_id` (DGT‑code). Alle hazard‑tabellen refereren hieraan plus een tijdsdimensie `date` (en optioneel `hour`).
>
> **Tabel: `hazard_meteo_daily`** (per `cell_id, date`)
> - `fwi_value` (float) – Fire Weather Index (FWI) van IPMA of herberekend.
> - `fwi_class` (tinyint) – FWI‑klasse volgens IPMA‑drempels/reclassificatie.
> - `rcm_value` (float) – Risco Conjuntural e Meteorológico (RCM, numerieke index).
> - `rcm_class` (tinyint) – RCM‑klasse (1–5) direct overgenomen van IPMA.
> - `fwi_global_pctl` (float, 0–100) – percentiel t.o.v. globale FWI‑klimatologie (World Bank Global Wildfire Hazard), pre‑gecompute per cel.
> - `source_tag` (varchar) – bv. `ipma_api`, `derived_ecmwf`, voor data‑lineage.
>
> **Tabel: `hazard_meteo_forecast`**
> Zelfde kolommen als `hazard_meteo_daily`, plus:
> - `base_date` (date) – initatiedatum van de weerrun.
> - `lead_hours` (int) – 24/48/72/96/120, in lijn met IPMA‑voorspellingen.
>
> **Tabel: `hazard_structural_static`** (per `cell_id`)
> - `structural_hazard_class` (tinyint) – structurele rural fire hazard klasse (Perigosidade de Incêndio Rural) volgens IPMA/ICNF.
> - `landcover_class` (smallint) – landcovercode (Corine/Copernicus/nationaal bosbestand).
> - `fuel_model` (smallint, nullable) – vereenvoudigde brandstofklasse (bijv. 1–10) afgeleid uit `landcover_class`.
> - `elevation_m` (float) – DEM‑hoogte.
> - `slope_deg` (float) – helling.
> - `aspect_deg` (float) – oriëntatie.
> - `distance_to_settlement_m` (float, optioneel) – afstand tot dichtstbijzijnde bebouwing (handig voor ignition‑laag).
>
> **Tabel: `wildfire_events_pt`** (kalibratie, gebaseerd op PT‑FireSprd, genormaliseerd naar jouw grid)
> - `event_id` (uuid) – unieke brand.
> - `start_datetime`, `end_datetime`.
> - `area_ha` (float).
> - `max_ros_m_s`, `mean_ros_m_s` (float) – rate‑of‑spread.
> - `max_fre_kw_m`, `mean_fre_kw_m` (float) – fire radiative energy / intensiteit.
>
> **Koppeltabel: `wildfire_event_cells`**
> - `event_id`, `cell_id`, `date`.
> - `stage` (enum: `ignition`, `head`, `flank`, `back`).
> - `burned_today_ha` (float).
>
> **Join‑logica**
> - Voor modelbouw/operations: join `hazard_meteo_daily` of `hazard_meteo_forecast` met `hazard_structural_static` op `cell_id`.
> - Voor PT‑FireSprd‑analyses: join `wildfire_event_cells` op `cell_id, date` en combineer met FWI/RCM + structurele hazard om fire‑behaviour‑relaties en drempels te leren.
>
> **View: `v_hazard_core_daily`**
> - Velden: `cell_id`, `date`, `fwi_value`, `fwi_class`, `rcm_value`, `rcm_class`, `fwi_global_pctl`, `structural_hazard_class`, `fuel_model`, `slope_deg`, `aspect_deg`.
> - Dit is de primaire feed voor de risico‑kaartlaag en de ML‑feature‑pipeline.

Wil je dat ik nu ook de bijbehorende `CREATE TABLE`‑statements in (bijvoorbeeld) PostgreSQL‑dialect uitschrijf?
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nt-rcm.pdf

[^6_2]: https://zenodo.org/records/7495506

[^6_3]: https://datacatalog.worldbank.org/search/dataset/0066912/global-wildfire-hazard

[^6_4]: https://www.ipma.pt/pt/enciclopedia/otempo/risco.incendio/index.jsp?page=pirp.xml

[^6_5]: https://www.ipma.pt/export/sites/ipma/bin/docs/relatorios/meteorologia/nota-metodologica-calculo-RCM2023-vf20230816.pdf

[^6_6]: https://essd.copernicus.org/articles/15/3791/2023/

[^6_7]: https://www.ipma.pt/pt/riscoincendio/

[^6_8]: https://www.ipma.pt/pt/riscoincendio/fwi/

[^6_9]: https://www.ipma.pt/pt/enciclopedia/otempo/risco.incendio/index.jsp

[^6_10]: https://zenodo.org/records/16279793

[^6_11]: https://nhess.copernicus.org/articles/21/3663/2021/nhess-21-3663-2021.pdf

[^6_12]: https://gee-community-catalog.org/projects/wrc/

[^6_13]: https://www.ipma.pt/resources.www/docs/im.publicacoes/edicoes.online/20251007/yTLsOJNMahZGHDIhFENs/met_20250801_20250831_fog_mm_co_pt.pdf

[^6_14]: https://florestas.pt/saiba-mais/como-se-calcula-o-indice-de-risco-de-incendio-florestal/

[^6_15]: https://researchportal.ulisboa.pt/en/publications/the-portuguese-large-wildfire-spread-database-pt-firesprd


---

# Alternatieve rasterindices voor vuur-risico Portugal

Een bouwer kan voor Portugal uit meerdere rasterindices kiezen; de kern is: kies een index die goed aansluit op IPMA/EFFIS, je eigen databronnen en de schaal waarop je beslissingen wilt nemen.[^7_1][^7_2]

## 1. Standaard-rasteropties die logisch zijn

- 1 km FWI/weergrid (ERA5‑Land / CFFWIS)
    - Veel studies over Portugal gebruiken heranalyse-data op 0,25° en fijnere resoluties als basis voor FWI/DSR‑indices.[^7_3][^7_1]
    - Als je je eigen FWI/DSR uit ERA5‑Land of soortgelijke producten berekent, is een 1 km of 2 km grid praktisch als primaire `cell_id`.
- EFFIS / Copernicus FWI‑grid
    - EFFIS levert FWI en Fire Danger Classes op een Europese grid; klassen lopen van low tot very extreme.[^7_4][^7_2]
    - Je kunt het EFFIS‑grid (met bekende resolutie/projection) overnemen als standaard, en daarboven je Portugese lagen (ICNF, PT‑FireSprd) reprojiceren.
- CORINE / Copernicus Land Cover 100 m grid
    - CORINE biedt raster op 100 m voor Europa.[^7_5]
    - Voor detailmodellen (micro‑brandstof/landgebruik) kun je een 100 m grid nemen en daarna naar 500 m of 1 km aggregeren voor operationele kaarten.


## 2. Nationale Portugese indices / grids

- DGT‑topografische series (SCN10k, M7810)
    - DGT heeft vector‑cartografie 1:10 000 en 1:50 000 met administratieve grenzen, wegen, bebouwing, vegetatie en DEM‑informatie.[^7_6][^7_7]
    - Je kunt een nationaal 1 km grid definiëren in het nationale referentiesysteem en dat laten “snappen” aan deze kaartseries (handig voor koppeling met gemeentegrenzen).
- Gemeente‑ of freguesia‑niveau (vector‑gebaseerd)
    - Een deel van de literatuur over brandrisico in Portugal modelleert op gemeentelijk niveau, vooral waar DSR‑percentielen worden gelinkt aan burnt area.[^7_8][^7_1]
    - In dat geval is je “rasterindex” eigenlijk administratief: `municipality_id` (en eventueel `parish_id`), handig als je beslissingen en rapportage toch op gemeente-niveau liggen.


## 3. Praktische alternatieven voor jouw project

Als je “alternatief” definieert als: niet alleen “dom 1 km grid”, maar ook inzetbaar en herbruikbaar:

- Alternatief A: EFFIS‑compatible grid
    - Neem het EFFIS/Copernicus FWI‑grid als basis; dan kun je zonder veel resampling EFFIS Fire Danger classes, anomalies en pan‑EU analyses hergebruiken.[^7_2][^7_9]
    - Pros: directe koppeling met EU‑risicokaarten en toekomstige JRC‑scenario’s.[^7_4]
    - Cons: grid is pan‑EU ontworpen, niet geoptimaliseerd op Portugese administratieve grenzen.
- Alternatief B: DGT‑afgeleid 1 km nationaal grid
    - Definieer een 1 km grid in het nationale CRS dat mooi over SCN10k/M7810 valt.[^7_7][^7_6]
    - Pros: sluit goed aan bij nationale kaarten, ICNF‑producten en PT‑FireSprd (na reprojection); makkelijk te koppelen met gemeente‑polygons.
    - Cons: je moet zelf mapping doen van EFFIS/IPMA raster naar jouw grid.
- Alternatief C: Hybride index (cell_id + municipality_id)
    - Gebruik een 1 km grid als technische index, maar sla per cel ook `municipality_id` op voor governance en rapportage (zoals al gesuggereerd in je schema-voorstel).[^7_1]
    - Dit maakt het eenvoudig om zowel grid‑gebaseerde modellen als gemeente‑statistiek (burnt area, risk days) te draaien.


## 4. Aanbeveling in één zin voor de bouwer

Voor Portugal is een 1 km nationaal grid in DGT‑CRS met per cel zowel een `cell_id` als een `municipality_id`, plus een expliciete mapping naar het EFFIS/ERA5‑grid, de meest robuuste en toekomstbestendige rasterindex om vuur‑risico te modelleren.[^7_3][^7_2][^7_1]

Wil je dat ik deze keuze nu vertaal naar een formele specificatie (CRS, origin, extent, naming van `cell_id`) die je direct in code en PostGIS kunt implementeren?
<span style="display:none">[^7_10][^7_11][^7_12][^7_13][^7_14][^7_15][^7_16]</span>

<div align="center">⁂</div>

[^7_1]: https://nhess.copernicus.org/articles/22/4019/2022/

[^7_2]: https://forest-fire.emergency.copernicus.eu/apps/effis_current_situation/

[^7_3]: https://dspace.uevora.pt/rdpc/handle/10174/32932

[^7_4]: https://vsquare.org/fire-weather-risk-index-on-the-rise-in-europe/

[^7_5]: https://land.copernicus.eu/en/products/corine-land-cover/clc2018

[^7_6]: https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-topografica/scn10k

[^7_7]: https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-topografica

[^7_8]: https://www.sciencedirect.com/science/article/abs/pii/S0048969716318666

[^7_9]: https://joint-research-centre.ec.europa.eu/projects-and-activities/natural-and-man-made-hazards/forest-fires/current-wildfire-situation-europe_en

[^7_10]: paste.txt

[^7_11]: https://www.agif.pt/app/uploads/2024/10/Portugal-Wildfire-Management-in-a-New-Era.pdf

[^7_12]: https://essd.copernicus.org/articles/15/3791/2023/

[^7_13]: https://www.tandfonline.com/doi/full/10.1080/19475705.2021.1909664

[^7_14]: https://www.dgterritorio.gov.pt/atividades/cartografia/cartografia-topografica/scn50k

[^7_15]: https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-2019-globe

[^7_16]: https://www.riscos.pt/wp-content/uploads/2018/Encontros/ISRIS/Aprst/ISIAAR_ppt047.pdf

