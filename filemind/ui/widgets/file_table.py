"""Qt model/view table and restrained category badge delegate."""

from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem

from filemind.models import OperationPlan, PlannedOperation


HEADERS = ("原路径", "目标路径", "原文件名", "建议新文件名", "分类", "整理理由", "来源", "校验状态")
CATEGORY_COLORS = {"文档": "#EEF2FF", "图片": "#F3E8FF", "视频": "#E0F2FE", "其他": "#F1F5F9"}


class FilePlanTableModel(QAbstractTableModel):
    """Expose a validated operation plan through Qt's model/view interface."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.operations: tuple[PlannedOperation, ...] = ()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.operations)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.operations):
            return None
        operation = self.operations[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_data(operation, index.column())
        if role == Qt.ItemDataRole.ToolTipRole:
            return self._tooltip(operation, index.column())
        if role == Qt.ItemDataRole.ForegroundRole and operation.warning:
            return QColor("#D97706")
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() == 4:
            return Qt.AlignmentFlag.AlignCenter
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return HEADERS[section]
        return None

    def set_plan(self, plan: OperationPlan | None) -> None:
        """Replace preview rows from a complete plan."""
        self.beginResetModel()
        self.operations = plan.operations if plan else ()
        self.endResetModel()

    @staticmethod
    def _display_data(operation: PlannedOperation, column: int) -> str:
        values = (str(operation.source), str(operation.target), operation.original_name, operation.new_name,
                  operation.classification.category, operation.classification.reason,
                  operation.classification.source, operation.warning or "通过")
        return values[column]

    @staticmethod
    def _tooltip(operation: PlannedOperation, column: int) -> str:
        if column == 0:
            return str(operation.source)
        if column == 1:
            return str(operation.target)
        if column == 5:
            return operation.classification.reason
        if column == 7:
            return operation.warning or "本地安全校验通过；尚未执行"
        return FilePlanTableModel._display_data(operation, column)


class CategoryDelegate(QStyledItemDelegate):
    """Draw category cells as soft pills without replacing the model data."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if index.column() != 4:
            super().paint(painter, option, index)
            return
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        background = CATEGORY_COLORS.get(text, "#F1F5F9")
        rect = option.rect.adjusted(12, 8, -12, -8)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QColor("#475569"))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()
