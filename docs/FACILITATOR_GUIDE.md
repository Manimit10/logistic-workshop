# Facilitator guide: running the 45-minute workshop

**Audience:** 2nd-4th year Logistics students (EUM), about 40, laptops (some forgotten). **You:** the only speaker.
**One idea to leave with:** *lead time decides how far ahead you must forecast, and a forecast is a range you turn into a decision.*

## Run sheet

| Min | Block | What you do |
|---|---|---|
| 0-7 | **Talk** (lecture note A) | Zara vs Shein: near-shore vs far-away, LATR, lead times, the EU €3 duty. End on the hook: *"A dress goes viral. Where is your stock?"* |
| 7-11 | **Join** | URL + QR + PIN on screen. Groups of 3, one role each. Forgot the laptop → sit with a team. Team of 2 → take two roles. |
| 11-13 | **Rules** (2 min, no more) | Read the 4 rules below aloud. |
| 13-28 | **Play: 6 rounds × 2.5 min** | You press Start / Close (or auto-close). Walk around; don't explain strategy. |
| 28-32 | **Debrief** | Presenter view. Turn on "students can see ranking". Reveal what really happened. |
| 32-43 | **Fork** (decide at minute ~28) | **A:** lecture note B1 (business). **B:** Colab (technical). See below. |
| 43-45 | **Close** | One sentence of message + bridge to the round table at 17:00. |

## The 4 rules (say them, don't read slides)

1. Each round is **two weeks** of sales. You order at the start; **nothing you order arrives this round**, not even by plane (air takes 1 round).
2. **Three roles, three different screens.** Planner sees forecasts, Logistics sees shipping options, Finance sees money and approves. Talk to each other.
3. Shipping: **sea** = 3 rounds, cheap · **near-shore** (Turkey/Morocco-style) = 2 rounds, a bit dearer · **air parcel** = 1 round, expensive **and** the EU €3 duty per item applies.
4. The season ends after round 6. **Anything still at sea or in stock is marked down to 50%.** Highest net worth wins; the AI baseline is playing too.

## Settings to use (instructor screen)

- Seconds per round: **180 for round 1, then 120-150**. (Change the number, **Apply**, then press Start.)
- **Auto-close on** keeps you on schedule. Turn it **off** if the room clearly needs more time.
- "Students can see the ranking": **off** during play (private by default), **on** for the debrief.

## What happens in the game (your answer key)

| Round | Event | Lesson |
|---|---|---|
| Start | Items already at sea are due in rounds 2 and 3 (the round-3 one will slip, see round 2). Everyone starts equal. | Pipeline = information you must read |
| **2** | **Port congestion** banner: sea shipments still in transit slip by one round | Round 3 will be short of stock. Teams that notice can bridge it with **air** on high-margin items (coat, dress), not on the cheap tee |
| **3** | The **viral item** starts to explode (×5, ×6, ×4, ×2.5 in rounds 3-6). Not announced; it shows in the sales history from round 4 | Sea can't react in time; near-shore (ordered by round 4) and air (by round 5) can. A forecast built on the past is blind to a spike. Chasing it is roughly break-even (air margin on this item is thin): a good discussion of *when reacting is worth it* |
| **4+** | Sea orders no longer arrive before the season ends | **End-of-horizon thinking**: why order what arrives after the sale? (sea last useful order: round 3; near-shore: round 4; air: round 5) |
| Any | Cheap tee by air loses money | Landed cost vs margin: air is for high-margin or urgent items |

Reference numbers (average net worth over 12 random scenarios; the AI baseline is a bot, not the best possible player):
**AI baseline ≈ €44.4k** · naive "average of last 4 rounds by sea" ≈ €41.0k · "last round's demand by air" ≈ €37.5k · order nothing ≈ €30.3k.
Insight that pays: **bridging the round-3 port gap with air on the coat and the dress** gave ≈ +€2.0k over the baseline and won in 11 of 12 scenarios. Chasing the viral spike on top did not add anything on average (see the round-3 row above). Scores below ≈ €30k mean a team spent more than it earned back.
The bot's rule: sum the median forecasts until the order arrives, plus a **quantile** of the arrival-round forecast set by the newsvendor ratio *margin lost ÷ (margin lost + overstock cost)*, minus stock and shipments already on the way.

## Debrief (4 min): ask, don't tell

1. "Who got burned in round 3? What did you see in round 2?" (the banner)
2. "Who noticed the viral item, and when?" (round 4, one round late for sea)
3. Show the **What really happened** table: forecasts are ranges, the spike was outside them.
4. "The AI baseline is on the board. Where did it beat you, where did you beat it?"
5. Finance: "Which service-level % did you use? Why is it 74% for a tee and 50% for the viral item by air?"

## Choosing the fork (minute ~28)

- Questions about **costs, customs, why Shein, where do we put stock** → **Path A: lecture note B1** (business-logistics, 11 min).
- Questions about **"how does the model know?"**, laptops open, technical faces → **Path B: Colab** (11 min; run-all, few code blocks, charts).
- Either way, finish with the same sentence: *"Forecast a range, then turn it into a decision."*

## If something goes wrong

| Problem | Do this |
|---|---|
| Server won't load | Wait 60 s (free host waking). Still nothing → Plan B tunnel from your laptop (see DEPLOYMENT.md §3C) |
| Nobody can log in | Check the PIN on screen. Wrong PIN is the usual cause |
| Server restarts mid-game | Students see "session expired"; they re-join with the same names; you Reset and run 3 rounds instead of 6 |
| A team is stuck / a role missing | Rule built in: if nobody in the team holds a role, the others can do its actions |
| A team never approves | That's data: the admin table shows who hasn't. Press Close anyway; no order = no new stock |
| Running late | Cut the game to 5 rounds: press nothing more after round 5, debrief from there |
| Zero laptops | Print the three role views (screenshots), run it on paper with you as the "server". Unlikely, but have the page ready |

## Pre-flight (day before + 30 min before)

See the checklist at the end of `DEPLOYMENT.md`. Also: laptop charger, HDMI/USB-C adapter, mobile hotspot as a backup network, this guide open on your phone.

## Honest caveats to tell students if asked

- All numbers in the game are **teaching simplifications**, not Shein's real figures. Shein's public claims (batches of 100-200 units, restock "in as little as 5 days") come from the company itself; treat them as claims.
- The EU rule is real: €150 customs exemption removed, a flat **€3 duty per item category** on small parcels from 1 July 2026 until 2028 (transitional). The game applies €3 per air unit as a simplification.
- The 40-50-day sea figure is a planning assumption; routes through Suez and around Africa differ and change with events.
