"""Riel lateral de secciones y barra superior de la ventana principal."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QKeySequence
from PySide6.QtWidgets import (QLabel, QSizePolicy, QStyle, QToolBar,
                               QWidget)

from ui import ota_ui

SP = QStyle.StandardPixmap


def _icon(win, sp):
    return win.style().standardIcon(sp)


def build_rail(win):
    """Riel vertical: Archivos, Modelos, Editor + botón equipo abajo."""
    rail = QToolBar("Secciones", win)
    rail.setMovable(False)
    rail.setOrientation(Qt.Vertical)
    rail.setFixedWidth(52)
    win.addToolBar(Qt.LeftToolBarArea, rail)

    grp = QActionGroup(win)
    grp.setExclusive(True)
    for sp, name, idx in ((SP.SP_DirIcon, "Archivos", 0),
                          (SP.SP_DriveHDIcon, "Modelos", 1)):
        act = QAction(_icon(win, sp), "", win)
        act.setToolTip(name)
        act.setCheckable(True)
        act.triggered.connect(
            lambda _c, i=idx: win._stack.setCurrentIndex(i))
        grp.addAction(act)
        rail.addAction(act)
        if idx == 0:
            act.setChecked(True)
    rail.addSeparator()

    act_editor = QAction(_icon(win, SP.SP_FileIcon), "", win)
    act_editor.setToolTip("Editor")
    act_editor.setCheckable(True)
    act_editor.setChecked(True)
    act_editor.toggled.connect(win.editor.setVisible)
    rail.addAction(act_editor)

    spacer = QWidget()
    spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    rail.addWidget(spacer)
    act_hw = QAction(_icon(win, SP.SP_ComputerIcon), "", win)
    act_hw.setToolTip("Revisar requerimientos del equipo")
    act_hw.triggered.connect(win._scan_hw)
    rail.addAction(act_hw)
    return rail


def build_toolbar(win):
    """Barra superior: proyecto, guardar, consola, agente, OTA, estado."""
    tb = QToolBar("Principal", win)
    tb.setMovable(False)
    win.addToolBar(tb)

    act_new = QAction(_icon(win, SP.SP_FileDialogNewFolder),
                      "Nuevo proyecto", win)
    act_new.triggered.connect(win._nuevo_proyecto)
    tb.addAction(act_new)

    act_dir = QAction(_icon(win, SP.SP_DirOpenIcon),
                      "Abrir proyecto", win)
    act_dir.triggered.connect(win._pick_dir)
    tb.addAction(act_dir)

    act_save = QAction(_icon(win, SP.SP_DialogSaveButton), "", win)
    act_save.setToolTip("Guardar (Ctrl+S)")
    act_save.setShortcut(QKeySequence.Save)
    act_save.triggered.connect(win.editor.editor.save)
    tb.addAction(act_save)
    tb.addSeparator()

    act_console = QAction(_icon(win, SP.SP_TitleBarNormalButton),
                          "Consola", win)
    act_console.triggered.connect(
        lambda: win._dock.setVisible(not win._dock.isVisible()))
    tb.addAction(act_console)

    act_self = QAction(_icon(win, SP.SP_FileDialogContentsView),
                       "Mejorar agente", win)
    act_self.setCheckable(True)
    act_self.toggled.connect(win._toggle_self_mode)
    tb.addAction(act_self)

    act_ota = QAction(_icon(win, SP.SP_BrowserReload), "Actualizar", win)
    act_ota.triggered.connect(
        lambda: ota_ui.check_and_prompt(win, win.chat, manual=True))
    tb.addAction(act_ota)

    tb.addWidget(QLabel("   "))
    win.lbl_status = QLabel("Ollama …")
    win.lbl_status.setStyleSheet("color:#7ab3e0;")
    tb.addWidget(win.lbl_status)
    return tb
