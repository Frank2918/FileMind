"""Build and validate safe, reviewable file organization plans."""

import re
from pathlib import Path
from typing import Callable, Mapping

from filemind.models import ClassificationResult, FileInfo, FileSuggestion, OperationPlan, PlannedOperation


INVALID_NAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
RESERVED_NAME = re.compile(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?$", re.IGNORECASE)


def validate_category(category: str) -> str:
    """Reject category labels that could escape the selected directory."""
    normalized = category.strip()
    if not normalized or normalized in {".", ".."} or INVALID_NAME_CHARS.search(normalized):
        raise ValueError(f"不安全的分类文件夹名称：{category!r}")
    if normalized.rstrip(" .") != normalized:
        raise ValueError(f"分类名称不能以空格或句点结尾：{category!r}")
    return validate_file_name(normalized)


def validate_file_name(name: str) -> str:
    """Reject names that are unsafe or invalid on common desktop filesystems."""
    if not name or name in {".", ".."} or INVALID_NAME_CHARS.search(name):
        raise ValueError(f"不安全的文件名：{name!r}")
    if name.endswith((".", " ")) or RESERVED_NAME.fullmatch(name):
        raise ValueError(f"文件名在 Windows 中不可用：{name!r}")
    if len(name.encode("utf-16-le")) // 2 > 255:
        raise ValueError("文件名超过 Windows 单个路径组件的长度限制")
    return name


def validate_relative_subdirectory(directory: str) -> str:
    """Validate model-selected subdirectories as safe relative path segments."""
    if not directory:
        return ""
    if len(directory) > 400 or len(directory.split("/")) > 8:
        raise ValueError("目标子目录过长或层级过深")
    if directory.startswith(("/", "\\")) or "\\" in directory or ":" in directory:
        raise ValueError(f"不安全的目标子目录：{directory!r}")
    segments = directory.split("/")
    if any(not segment or segment in {".", ".."} for segment in segments):
        raise ValueError(f"不安全的目标子目录：{directory!r}")
    return "/".join(validate_file_name(segment) for segment in segments)


def build_plan(
    root: Path,
    files: list[FileInfo],
    classify: Callable[[FileInfo], ClassificationResult],
    suggestions: Mapping[str, FileSuggestion] | None = None,
    rename_files: bool = False,
    failed_file_ids: Mapping[str, str] | set[str] | None = None,
) -> OperationPlan:
    """Create a plan and reject any source or destination outside ``root``."""
    selected_root = root.expanduser().resolve(strict=True)
    if not selected_root.is_dir():
        raise NotADirectoryError(f"所选路径不是文件夹：{selected_root}")

    operations: list[PlannedOperation] = []
    seen_targets: set[str] = set()
    for file_info in files:
        source = file_info.path.resolve(strict=True)
        if source.parent != selected_root or file_info.path.is_symlink() or not source.is_file():
            raise ValueError(f"源文件不在所选目录中或不是普通文件：{file_info.path}")
        file_id = _stable_file_id(file_info.name)
        suggestion = suggestions.get(file_id) if suggestions else None
        classification = (
            ClassificationResult(
                suggestion.category,
                suggestion.reason,
                source="AI",
                target_subdirectory=validate_relative_subdirectory(suggestion.target_subdirectory),
            )
            if suggestion else classify(file_info)
        )
        category = validate_category(classification.category)
        category_path = selected_root / category
        subdirectory = validate_relative_subdirectory(classification.target_subdirectory)
        target_directory = category_path.joinpath(*subdirectory.split("/")) if subdirectory else category_path
        _validate_target_directory(selected_root, target_directory)
        new_name = suggestion.new_name if suggestion and rename_files and suggestion.new_name else file_info.name
        target = target_directory / new_name
        validate_file_name(target.name)
        collision_key = target.as_posix().casefold()
        if collision_key in seen_targets:
            raise ValueError(f"整理计划中存在重复目标：{target}")
        seen_targets.add(collision_key)
        warning = _plan_warning(target, file_id, failed_file_ids)
        operations.append(
            PlannedOperation(
                source,
                target,
                file_info.name,
                new_name,
                classification,
                file_info.size_bytes,
                file_info.modified_ns,
                warning,
            )
        )
    return OperationPlan(selected_root, tuple(operations))


def _validate_target_directory(root: Path, target_directory: Path) -> None:
    resolved = target_directory.resolve(strict=False)
    if not resolved.is_relative_to(root):
        raise ValueError(f"目标目录指向所选目录之外：{target_directory}")
    relative = target_directory.relative_to(root)
    cursor = root
    for segment in relative.parts:
        cursor = cursor / segment
        if cursor.is_symlink():
            raise ValueError(f"目标目录包含符号链接：{cursor}")


def _plan_warning(target: Path, file_id: str,
                  failed_file_ids: Mapping[str, str] | set[str] | None) -> str | None:
    if failed_file_ids and file_id in failed_file_ids:
        if isinstance(failed_file_ids, Mapping):
            return f"AI 批次失败：{failed_file_ids[file_id]}；此行使用本地规则，不能执行整份计划"
        return "AI 批次失败；此行展示本地规则分类，不能执行整份计划"
    if target.is_symlink():
        return "目标路径是符号链接，不能执行"
    if target.exists():
        return "目标位置已存在同名文件，执行时会跳过"
    if any(parent.exists() and not parent.is_dir() for parent in target.parents if parent != target.anchor):
        return "目标路径的上级位置已存在非目录文件"
    return None


def _stable_file_id(file_name: str) -> str:
    """Use the same path-free ID the AI request receives."""
    from hashlib import sha256

    return f"f_{sha256(file_name.encode('utf-8')).hexdigest()[:20]}"
