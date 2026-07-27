# Source strategy

Priority order for discovering Miami luxury / hospitality events **before** they happen:

1. **Owned organizer pages** (WR Chess, Faena, hotel calendars)
2. **Official civic / destination feeds** (Miami Beach Events iCal, Design District)
3. **Museum / culture calendars** (The Bass RSS/iCal, ICA Miami)
4. **Industry / fashion / culinary** (SOBEWFF, PARAISO, Fashion Week, Boat Show)
5. **Business networking** (Beacon Council, ULI, Bisnow)
6. **Editorial RSS** (Haute Living early signal; World Red Eye mostly same-day/post)
7. **PR / ticketing signals** (PR Newswire filters, Luma Miami calendars)

## Curated source tiers

The live feed now publishes only five primary industries: Hospitality, Sports, Real Estate, Culinary, and Art/Fashion. Generic tours, community classes, family programming, farmers markets, office hours, and similar listings are excluded.

### Top-tier hospitality and clubs

- Faena Miami Beach / Faena Rose
- Delano Miami Beach
- W South Beach
- 1 Hotel South Beach
- The Standard Spa Miami Beach
- The Setai
- Fontainebleau Miami Beach
- Miami Beach EDITION / Beach Club
- Four Seasons at The Surf Club
- St. Regis Bal Harbour
- The Moore Miami
- Soho Beach House
- Casa Tua Club
- ZZ's Club
- The Bath Club
- Casa Neos / MM Club

Private club calendars are not scraped behind authentication. The feed exposes official membership, concierge, newsletter, and application routes instead.

### Industry calendars

- Hospitality: GMBHA and AHLA
- Sports: F1 Miami, Miami Open, Inter Miami, Miami HEAT, FIFA hospitality, WR Chess, The Backgammon Society's official Miami tournament calendar, and the Backgammon Social Miami Luma calendar
- Real Estate: ULI, NAIOP South Florida, MIAMI REALTORS, Bisnow, Beacon Council
- Culinary: SOBEWFF official ICS and event inventory
- Art/Fashion: Art Basel, Design Miami, Design District, ICA and The Bass only when programming has a premium signal such as a private dinner, gala, preview, or reception

## Instagram

Not scraped. Public Instagram discovery is unreliable and restricted. Prefer newsletters and official pages.

## WR Chess / Faena cocktail lesson

For the July 2026 WR Chess opening reception at Faena Forum, the earliest *public* trail was WR Chess’s own event page (press conference + opening reception listed). Haute Living covered the match later as editorial. World Red Eye is typically photography after the fact. Invitation-only dinners often never hit public calendars — those need newsletter / PR inbox ingestion later.

## Blocked / limited sources

Some hotel sites return 403 to automated clients. Those adapters soft-fail and are recorded in `status.json`; subscribe to their newsletters as a manual backup.

## Public connector extraction

The “To Connect With” scan reads only names printed in public World Red Eye captions and professional role text. It prioritizes hosts, venue leaders, developers, and recurring names across curated hospitality, culinary, sports, and real-estate coverage. Every recommendation retains source attribution. No face recognition, private social profile scraping, or private contact collection is used.
