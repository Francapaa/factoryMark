## Context

See proposal.md (Why). Current state: `/app` renders `AnalyzeForm` directly (business fields per request, real `/api/analyze` with Bearer JWT); no home, no saved-business usage in UI, no social connection, drafts live in memory; `AnalyzeResult` type mirrors the backend contract; Meta docs (Sept 2026) confirm two non-mixable login flavors and the Advanced-Access review path for multi-business apps.

## Goals / Non-Goals

**Goals:**

- Dashboard as the product surface: every pipeline output has a home.
- Instagram staged so v1 ships value (connect + profile) before Meta's review finishes.
- FODA backed by own-business data, not just rival gaps.

**Non-Goals:**

- Real publishing, metrics, scene editor, TikTok, multi-account (recorded as sequenced follow-ups, not this change).

## Decisions

- **Instagram-Login flavor** (owner decision): `graph.instagram.com`, Business Login for Instagram, permissions `instagram_business_basic` (+ `instagram_business_content_publish` only when the publish milestone is built). No Facebook Page required — decisive for small shops. Facebook-Login flavor rejected for v1 (Page-link friction); revisit only if product tagging/ads ever matter.
- **Connect-before-publish staging**: v1 connects and reads the professional profile (username, counts). Publish + insights stay behind the App Review gate. The UI must never promise publishing before approval exists.
- **Own-business reviews feed F/D**: 1 extra cached Details call on the saved anchor per analysis. Threats come from competitor score trends + negative-cluster growth; no new data source.
- **Simple studio, uploads first**: photos/audios are owner files (drag & drop, reusing `asset-upload` + `photo-qc` contracts); scene generation consumes the existing `scene-schema`; render status polls the future job endpoint. No timeline editor in v1.
- **History without metrics**: `Post` entity (draft → approved → scheduled → published → rejected, with `media_url` + `external_id`) ships in v1; metric fields are defined in the type but never collected until the insights permission + review land.
- **Spanish-first UI strings** per the video-module name mapping (Investigador/Estratega/Creativo visible where agent names surface).

## Risks / Trade-offs

- [Risk] App Review takes weeks or fails first attempt → Mitigation: v1 value doesn't depend on it (connect + profile + full local pipeline); submission checklist (screencast, testable build, permission justifications) is a spec'd milestone.
- [Risk] Shops without professional IG accounts can't connect → Mitigation: connect screen explains the 1-tap professional switch + deep link; dashboard remains fully usable disconnected.
- [Risk] Token expiry/rotations break publishing silently → Mitigation: token health check on dashboard load with explicit re-connect state; never fail silently.
- [Risk] FODA with thin own-review data looks empty → Mitigation: quadrants show confidence + evidence counts; low-evidence quadrants say so honestly instead of filling with generic advice.

## Open Questions

- Trial/graduation or scheduling semantics for publish milestone: deferred to the publish change (needs approved review first).
- Whether connect screen should also capture the shop's IG handle for display before OAuth completes: minor UX, decided at implementation.
