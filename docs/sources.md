# Source strategy

Priority order for discovering Miami luxury / hospitality events **before** they happen:

1. **Owned organizer pages** (WR Chess, Faena, hotel calendars)
2. **Official civic / destination feeds** (Miami Beach Events iCal, Design District)
3. **Museum / culture calendars** (The Bass RSS/iCal, ICA Miami)
4. **Industry / fashion / culinary** (SOBEWFF, PARAISO, Fashion Week, Boat Show)
5. **Business networking** (Beacon Council, ULI, Bisnow)
6. **Editorial RSS** (Haute Living early signal; World Red Eye mostly same-day/post)
7. **PR / ticketing signals** (PR Newswire filters, Luma Miami calendars)

## Instagram

Not scraped. Public Instagram discovery is unreliable and restricted. Prefer newsletters and official pages.

## WR Chess / Faena cocktail lesson

For the July 2026 WR Chess opening reception at Faena Forum, the earliest *public* trail was WR Chess’s own event page (press conference + opening reception listed). Haute Living covered the match later as editorial. World Red Eye is typically photography after the fact. Invitation-only dinners often never hit public calendars — those need newsletter / PR inbox ingestion later.

## Blocked / limited sources

Some hotel sites return 403 to automated clients. Those adapters soft-fail and are recorded in `status.json`; subscribe to their newsletters as a manual backup.
