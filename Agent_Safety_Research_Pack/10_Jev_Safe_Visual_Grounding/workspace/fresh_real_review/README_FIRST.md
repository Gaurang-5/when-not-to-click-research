# Fresh real-interface annotation package

For private research team use. 180 tasks; each of two annotators labels ALL 180 independently. Do not split this package or compare decisions until both exports are complete.

1. Extract the entire ZIP to a permanent folder. Keep images/ beside label_studio_tasks.json.
2. Close any running Label Studio terminal process with Ctrl+C. Run START_LABEL_STUDIO_MAC.command or START_LABEL_STUDIO_WINDOWS.bat from a terminal where Label Studio is installed. This enables local image serving for this folder. Keep that terminal open.
3. Open http://localhost:8080. Create a NEW project named Fresh Real Review A or Fresh Real Review B. Do not change your previous projects.
4. In Settings > Labeling Interface, use the Code editor and paste label_config.xml. Save. Import label_studio_tasks.json.
5. Read INSTRUCTIONS.md. Label each task from the image and instruction only. Zoom to inspect small controls. For unique/multiple, select valid_target and drag a rectangle around the complete clickable element; use one box for unique and all plausible boxes for multiple. For other states draw no boxes. Select confidence, add notes when uncertain, then Submit.
6. Export full JSON after all tasks. Name it fresh_review_A_export.json or fresh_review_B_export.json. Return the JSON file to the authors; keep the task IDs and original screenshots unchanged.

If an image is blank: confirm the ZIP is fully extracted, start Label Studio using the launcher from THIS folder, and restart the server after changing the local-files root. The task URL /data/local-files/?d=images/... must resolve to the images/ file under this folder. Never draw a box on a missing image; report the problem first.

Do not include source ground truth or model predictions in your project. These tasks have no frozen human truth yet. Final class balance is determined by your independent judgments, not by a quota. The authors will calculate agreement and arrange adjudication before any model evaluation.
