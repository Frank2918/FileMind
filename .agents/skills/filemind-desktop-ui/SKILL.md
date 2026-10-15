---
name: filemind-desktop-ui
description: Improve FileMind PySide6 Widgets layouts, plan previews, Orbit chat, and local lock screens using isolated UI checks. Use for this project's interface work; not for unrelated web apps or model/provider changes.
---

# FileMind desktop UI

Read the actual page and its service/controller call sites before editing. Claude may have changed code after the handoff document was written.

## Project boundaries

- The preview consumes an OperationPlan. Its tree is not a filesystem browser: do not enumerate directories or invent destination nodes that are absent from the plan.
- Filter a selected destination file by exact Path equality and a folder by path ancestry. A substring filter incorrectly includes siblings such as 文档2.
- PlanTargetTree.drawBranches paints the indentation background and local SVG arrows. Generic branch QSS can suppress Fusion's native arrows or leave a blue selection block; a transparent branch background alone does not fix it in offscreen rendering.
- LocalLockDialog performs PBKDF2 and private writes through TaskWorker. Authenticate before constructing MainWindow; its pages load model settings.
- Keep the local lock's random DPAPI token separate from Windows API credential storage. A remembered token is not a saved password.
- Orbit Markdown message height follows the actual viewport width. A fixed height cap combined with hidden inner scrollbars silently clips replies.

## Design and validation

Reuse colors, fonts, and states in filemind/ui/styles/theme.py. Use a quiet white/blue workspace, lavender as an Orbit accent, and clear folder icons. Keep long paths selectable and visible through details/tooltips. Put primary actions outside scrolling page content.

Run tools/review_ui.py for temporary, generated data. ReviewSettings must never read .env, environment API keys, OS model credentials, or real chat history. Inspect 1024×700 and 1280×850; the local lock also supports 760×600. Use --snapshot to generate screenshots, or launch without it for native review.

Run relevant tests, then the full pytest suite and compileall. Dispose Qt views before QApplication; tests/conftest.py owns that lifecycle. Do not replace tests with screenshots or report mocked provider responses as real connectivity.
