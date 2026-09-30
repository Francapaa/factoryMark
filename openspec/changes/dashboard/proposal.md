## Why

Post-onboarding users land on a raw analysis form: no home, no Instagram connection, no FODA view, no video studio, no history. The pipeline produces competitors, opportunities, and drafts, but the product has nowhere to *show* them as an ongoing business tool. Meanwhile Instagram integration — the delivery channel of everything FactoryMark creates — has no written plan, and Meta's multi-business requirements (Advanced Access, App Review, Business Verification) can stall publishing for weeks if discovered mid-build. This change specs the dashboard as the product surface and stages Instagram so value ships before Meta approves anything.

## What Changes

- Six new capability specs: `dashboard-overview` (layout + states), `instagram-connect` (Instagram-Login OAuth, token lifecycle, App Review as separate milestone), `foda-matrix` (full F/O/D/A with own-business reviews + Strategist expansion), `competitors-view` (who the rivals are), `video-studio` (simple: pick draft → upload photos/audios → generate → preview → approve), `publication-history` (draft/published list; metrics explicitly future).
- No code in this change — specs only, zero cost.

## Capabilities

### New Capabilities

- `dashboard-overview`: Post-onboarding home — business summary, FODA, competition, video studio, publications sections; empty/loading/error/disconnected states; Spanish UI strings.
- `instagram-connect`: Instagram-Login flavor OAuth ("entrá con tu Instagram", no Facebook Page needed), encrypted token storage + refresh, connection states, v1 = connect + read profile (publish gated on App Review approval).
- `foda-matrix`: Complete matrix rules — O from existing opportunities; F/D from own-shop reviews (1 extra cached Details call per analysis); A from competitor trends; Strategist expansion spec'd.
- `competitors-view`: Rival cards/table (name, rating, distance, score, source, Maps link), ordering, no-data view.
- `video-studio`: Simple studio — select draft, drag & drop owner photos/audios, generate scene (existing `scene-schema` contract), render-job status, preview, approve. No scene editor.
- `publication-history`: Draft/published list with states; metrics endpoints defined but disabled (future version requiring extra permission + review).

### Modified Capabilities

(none — `video-module` contracts are reused, not modified)

## Impact

- Docs only: 1 proposal + 1 design + 6 specs + tasks. Zero code, zero dependencies, zero API cost.
- Sets up the implementation order for builder agents: overview → history → competitors/FODA display → studio → instagram-connect → publish (post-App-Review).
- Explicitly out of scope: real publishing, metrics collection, scene editor, TikTok, multi-account.
