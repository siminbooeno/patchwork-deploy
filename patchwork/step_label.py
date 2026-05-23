"""Step label and grouping support for pipeline steps."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class StepLabel:
    """Display label and group metadata for a pipeline step."""
    display: str
    group: Optional[str] = None
    icon: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def short(self) -> str:
        """Return icon + display if icon present, else just display."""
        if self.icon:
            return f"{self.icon}  {self.display}"
        return self.display

    def full(self) -> str:
        """Return group-prefixed display name."""
        if self.group:
            return f"[{self.group}] {self.short()}"
        return self.short()

    def as_dict(self) -> Dict:
        return {
            "display": self.display,
            "group": self.group,
            "icon": self.icon,
            "tags": self.tags,
        }


def parse_label(raw: object, fallback_name: str) -> StepLabel:
    """Parse a label from YAML value.

    Accepts:
      - None / missing  -> StepLabel(display=fallback_name)
      - str             -> StepLabel(display=str)
      - dict            -> full StepLabel from keys: display, group, icon, tags
    """
    if raw is None:
        return StepLabel(display=fallback_name)

    if isinstance(raw, str):
        stripped = raw.strip()
        return StepLabel(display=stripped or fallback_name)

    if isinstance(raw, dict):
        display = str(raw.get("display") or fallback_name).strip() or fallback_name
        group = raw.get("group")
        icon = raw.get("icon")
        raw_tags = raw.get("tags") or []
        if isinstance(raw_tags, str):
            raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        tags = [str(t) for t in raw_tags]
        return StepLabel(
            display=display,
            group=str(group).strip() if group else None,
            icon=str(icon).strip() if icon else None,
            tags=tags,
        )

    return StepLabel(display=fallback_name)


def group_labels(labels: Dict[str, StepLabel]) -> Dict[str, List[str]]:
    """Return mapping of group -> [step names] from a name->label dict."""
    groups: Dict[str, List[str]] = {}
    for name, lbl in labels.items():
        key = lbl.group or "(ungrouped)"
        groups.setdefault(key, []).append(name)
    return groups
