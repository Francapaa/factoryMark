## Purpose

Prevents the #1 quality risk in `project2.md` §11 (bad local photos): every owner photo is checked before it can enter a render, auto-fixed where safe, and otherwise bounced back to the owner with guidance — never silently rendered ugly.

## ADDED Requirements

### Requirement: Pre-render photo checks

The system SHALL check each uploaded photo for minimum resolution (≥ 720 px on the short side for 9:16 output), severe blur, and severe underexposure before admitting it to the render set. (Implementation with OpenCV/Pillow is a future change; thresholds live here.)

#### Scenario: Good photo admitted

- **WHEN** a sharp, well-lit ≥ 720 px photo is uploaded
- **THEN** it is admitted and addressable as `photo_id`

#### Scenario: Bad photo bounced with guidance

- **WHEN** a photo fails any check
- **THEN** it is rejected with a plain-language reason (e.g. "está muy oscura, ¿subís otra con más luz?") and never enters a scene

### Requirement: Automatic vertical crop

The system SHALL auto-crop admitted photos to 9:16 with the subject centered (saliency/face-center heuristic in the future implementation) without owner intervention.

#### Scenario: Horizontal photo adapted

- **WHEN** a 16:9 photo is admitted
- **THEN** the render uses a centered 9:16 crop, original preserved
