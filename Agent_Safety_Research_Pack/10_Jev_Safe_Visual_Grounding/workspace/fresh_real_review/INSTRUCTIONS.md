# Fresh real-interface review:180 tasks,60 unused source screenshots

Status: CANDIDATES PREPARED, NOT HUMAN LABELED.

Use Label Studio. Import label_studio_tasks.json; paste label_config.xml in Labeling Interface. Enable local-file serving with the document root equal to the fully extracted package folder. The image URLs resolve under images/. Use two separate projects/accounts for two independent annotators and hide all existing annotations.

Read the instruction, inspect visible screenshot pixels, and choose exactly one state: unique, absent, multiple, occluded, offscreen, unclear. Unique: one full clickable box. Multiple: all plausible boxes, at least two. Other states: no boxes. Mark high/medium/low confidence and explain borderline cases. Do not infer invisible/offscreen controls from app knowledge. Use unclear when visual evidence does not support a specific reason. Zoom when necessary; targets may be tiny.

Instructions include original source-positive descriptions, natural descriptions borrowed from another application, and generic button requests. These are candidate construction methods, not true status labels. The generic requests require a judgment of whether multiple plausible matches exist. Reject unrealistic or unresolvable instructions and explain why. Do not force the final status counts to be balanced.

Annotators receive only images/, tasks, schema and instructions. Keep RESEARCHER_ONLY_manifest.json with authors. After both annotations, export full JSON, compute agreement, adjudicate independently, and freeze labels/analysis before API collection. No model predictions have been collected on these tasks.

Source: likaixin/ScreenSpot-Pro, pinned revision listed in status.json. This is a professional desktop source shift, not a balanced desktop/mobile/web sample. Original high-resolution images are retained; future API resizing must be versioned and box coordinates transformed. Exact file names and decoded image pixels were checked against all951 prior cases and duplicates rejected.
