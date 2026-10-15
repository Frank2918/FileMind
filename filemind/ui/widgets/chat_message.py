"""Markdown-aware conversation message bubble for Orbit."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QPixmap, QResizeEvent, QTextDocument
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy, QTextBrowser,
                               QVBoxLayout, QWidget)

from filemind.chat_models import ChatMessage


class LocalMarkdownView(QTextBrowser):
    """Render text without automatically loading model-supplied local images."""

    def loadResource(self, resource_type: int, name: QUrl) -> object:
        if resource_type == QTextDocument.ResourceType.ImageResource:
            return QPixmap()
        return None


class ChatMessageBubble(QWidget):
    """Render a user or assistant message with safe, local Markdown display."""

    def __init__(self, message: ChatMessage, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        is_user = message.role == "user"
        row = QHBoxLayout(self)
        row.setContentsMargins(8, 5, 8, 5)
        if is_user:
            row.addStretch(1)
        self.bubble = QFrame()
        self.bubble.setObjectName("OrbitUserBubble" if is_user else "OrbitAssistantBubble")
        self.bubble.setMaximumWidth(720)
        column = QVBoxLayout(self.bubble)
        column.setContentsMargins(15, 12, 15, 12)
        caption = QLabel("你" if is_user else "Orbit")
        caption.setObjectName("OrbitMessageCaption")
        column.addWidget(caption)
        self.attachment_label = QLabel("  ·  ".join(message.attachments))
        self.attachment_label.setObjectName("OrbitMessageAttachments")
        self.attachment_label.setWordWrap(True)
        self.attachment_label.setVisible(bool(message.attachments))
        column.addWidget(self.attachment_label)
        self.content = LocalMarkdownView()
        self.content.setFrameShape(QFrame.Shape.NoFrame)
        self.content.setObjectName("OrbitMessageContent")
        self.content.setReadOnly(True)
        self.content.setOpenExternalLinks(False)
        self.content.setOpenLinks(False)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content.setMinimumHeight(34)
        self.content.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.content.document().setDefaultStyleSheet(
            "pre, code { font-family: Consolas, 'Cascadia Code', monospace; "
            "background: #F1EFFA; color: #32235B; }"
            "blockquote { color: #64748B; border-left: 3px solid #B8A6F3; }"
        )
        if is_user:
            self.content.setPlainText(message.content)
        else:
            self.content.setMarkdown(message.content)
        column.addWidget(self.content)
        row.addWidget(self.bubble, 0 if is_user else 1)
        self._resize_to_document()

    def _resize_to_document(self) -> None:
        document = self.content.document()
        document.setTextWidth(max(120, self.content.viewport().width()))
        height = max(34, math.ceil(document.size().height()) + 8)
        if self.content.height() != height:
            self.content.setFixedHeight(height)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        QTimer.singleShot(0, self._resize_to_document)
