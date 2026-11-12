# Label Studio setup for two independent annotators

## 1. Prepare the images and blind task files

From the project root:

```bash
.venv/bin/python scripts/materialize_academic_images.py --source all --prepare-jev
.venv/bin/python annotation_tools/label_studio/prepare_projects.py
```

This creates two imports with the same case IDs in different orders:

- `annotator_a_tasks.json`
- `annotator_b_tasks.json`

Neither file includes source labels, boxes, Jev predictions, or the other annotator’s answers.

## 2. Install and start Label Studio

Use a separate environment because the research runner is pinned independently:

```bash
python3 -m venv .label-studio-venv
source .label-studio-venv/bin/activate
python -m pip install label-studio
export LOCAL_FILES_SERVING_ENABLED=true
export LOCAL_FILES_DOCUMENT_ROOT="$PWD"
label-studio start
```

Open `http://localhost:8080`.

## 3. Create two isolated projects

Create project `JEV Annotation A` and import only `annotator_a_tasks.json`. Create project `JEV Annotation B` and import only `annotator_b_tasks.json`. In both projects, open **Settings → Labeling Interface → Custom template** and paste `config.xml`.

Give each annotator access only to their own project. If the installed edition cannot enforce project-level access, use separate local Label Studio installations and the prepared per-annotator ZIP packages. Independence is more important than using one shared server.

Before full annotation, have both annotators label the same 20-case training set that is excluded from the study. Discuss only those training cases, update the written rules if needed, then restart blind annotation on the study cases.

## 4. Export

When each project is complete, use **Export → JSON**. Save the files as:

- `annotator_a_export.json`
- `annotator_b_export.json`

Do not export to YOLO or COCO for the handoff. Raw Label Studio JSON preserves the status choice, boxes, notes, annotator identity, timestamps, and original task data. Bounding boxes are stored as percentages of image dimensions and will be converted back to pixels by the research pipeline.

Send both JSON exports to the research workspace. The pipeline will join them by `case_id`, calculate agreement, create the adjudication queue, and freeze the final manifest.
