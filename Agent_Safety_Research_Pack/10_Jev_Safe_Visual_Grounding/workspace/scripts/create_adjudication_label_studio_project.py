"""Run inside `label-studio shell` to create the final adjudication project."""

import json
from pathlib import Path

from data_import.serializers import ImportApiSerializer
from io_storages.localfiles.models import LocalFilesImportStorage
from projects.models import Project
from tasks.models import Task
from users.models import User


root = Path.cwd().resolve()
title = "JEV Final Adjudication"
config = (root / "annotation_tools" / "label_studio" / "adjudication_config.xml").read_text(encoding="utf-8")
tasks = json.loads((root / "data" / "academic_2000" / "annotation_round_1" / "adjudication_project_tasks.json").read_text(encoding="utf-8"))

existing = Project.objects.filter(title=title).order_by("id").first()
if existing:
    if Task.objects.filter(project=existing).count() != len(tasks):
        raise RuntimeError(f"Existing project {existing.id} has an unexpected task count")
    project = existing
    project.label_config = config
    project.save(update_fields=["label_config"])
    state = "EXISTING_UPDATED"
else:
    user = User.objects.get(id=1)
    project = Project.objects.create(
        title=title,
        description=(
            "Author adjudication of cases flagged after two independent annotations. "
            "Decide from the screenshot and written instruction without consulting Jev predictions."
        ),
        label_config=config,
        created_by=user,
        organization=user.active_organization,
        show_instruction=False,
        show_skip_button=True,
    )
    serializer = ImportApiSerializer(data=tasks, many=True, context={"project": project, "user": user})
    serializer.is_valid(raise_exception=True)
    serializer.save(project=project)
    LocalFilesImportStorage.objects.create(project=project, path=str(root / "data"))
    state = "CREATED"

print(json.dumps({"state": state, "project_id": project.id, "title": project.title, "tasks": Task.objects.filter(project=project).count()}))
