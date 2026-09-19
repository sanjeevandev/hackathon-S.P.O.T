# S.P.O.T. Onion Defect Human Annotation Guideline

## 1. Scope & Core Principles

- **Multi-Label Rule**: `MULTI_LABEL_ALLOWED = TRUE`. A single onion bulb specimen may simultaneously exhibit multiple defects (e.g. both physical damage and fungal rot).
- **Rule of Evidence**: Annotators must evaluate visible physical evidence only. No assumed defects without visual proof.
- **Source Data Read-Only**: Source images must remain unchanged. Annotations are recorded in standard JSON/CSV schema.

---

## 2. Target Quality Taxonomies

### Category 1: Healthy
- **Definition**: Intact, dry outer skin (tunic), tight unsprouted neck, uniform firm shape, zero rot, zero cuts or mechanical bruises.
- **Inclusion Criteria**: Intact outer husk, no discoloration, no soft spots.
- **Exclusion Criteria**: Any visible skin rupture, sprouting shoot, or fungal mold.

### Category 2: Damaged
- **Definition**: Mechanical cuts, skin tearing, crushing damage, severe surface scrapes, or insect puncture wounds.
- **Inclusion Criteria**: Visible tears in tunic layers revealing inner fleshy scales, deep puncture marks, open wounds.
- **Exclusion Criteria**: Intact dry papery outer skin or natural color variations.

### Category 3: Rotten
- **Definition**: Fungal mold, bacterial soft rot, watery mushy scales, black mold (*Aspergillus niger*), or neck rot decay.
- **Inclusion Criteria**: Black or grey spore masses, dark water-soaked soft lesions, oozing or slimy neck tissue.
- **Exclusion Criteria**: Dry dirt particles or soil smudges that wipe off.

### Category 4: Sprouted
- **Definition**: Visible green shoot emergence from the apex/neck of the bulb or internal greening visible through thin scales.
- **Inclusion Criteria**: Green foliage stem extending $\ge 2\text{mm}$ out of the neck, emerging root shoots at basal plate.
- **Exclusion Criteria**: Dry brownish neck apex without green foliage shoots.

### Category 5: Undersized
- **Definition**: Bulb diameter below standard commercial grade ($\le 40\text{mm}$ for Grade A commercial bulbs).
- **Inclusion Criteria**: Small specimen relative to standard calibration scale marker.
- **Exclusion Criteria**: Normal market size ($\ge 45-60\text{mm}$).

---

## 3. Ambiguous & Borderline Case Resolution

| Scenario | Primary Annotation | Secondary Annotation | Notes |
| :--- | :--- | :--- | :--- |
| Black soil dirt at root plate | Healthy | None | Dirt smudges are not fungal rot |
| Mechanical cut with black mold | Damaged | Rotten | Dual label applied (`MULTI_LABEL_ALLOWED`) |
| Green shoot extending 1mm | Sprouted | None | Apex green shoot present |
| Outer papery skin slightly peeling | Healthy | None | Natural dry skin peeling without fleshy scale damage is not a defect |
