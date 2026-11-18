"""Iconos planos Lucide (MIT) renderizados desde SVG con QSvgRenderer."""
from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Trazos Lucide (rejilla 24x24, stroke 2, caps/joins redondos)
ICONS = {
    "folder": '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 '
              '1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 '
              '0 0 0 2 2Z"/>',
    "newfolder": '<path d="M12 10v6"/><path d="M9 13h6"/>'
                 '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 '
                 '0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13'
                 'a2 2 0 0 0 2 2Z"/>',
    "file": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 '
            '2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/>',
    "db": '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
          '<path d="M3 5v14a9 3 0 0 0 18 0V5"/>'
          '<path d="M3 12a9 3 0 0 0 18 0"/>',
    "monitor": '<rect width="20" height="14" x="2" y="3" rx="2"/>'
               '<line x1="8" x2="16" y1="21" y2="21"/>'
               '<line x1="12" x2="12" y1="17" y2="21"/>',
    "save": '<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19'
            'a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
            '<path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/>'
            '<path d="M7 3v4a1 1 0 0 0 1 1h7"/>',
    "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    "bot": '<path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" '
           'rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/>'
           '<path d="M15 13v2"/><path d="M9 13v2"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 '
               '8"/><path d="M21 3v5h-5"/>'
               '<path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 '
               '16"/><path d="M8 16H3v5"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "mic": '<path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"'
           '/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/>'
           '<line x1="12" x2="12" y1="19" y2="22"/>',
    "send": '<path d="M14.5 21.7a.5.5 0 0 0 .94 0l6.5-19a.5.5 0 0 0-.64'
            '-.64l-19 6.5a.5.5 0 0 0 0 .94l7.93 3.18a2 2 0 0 1 1.11 1.11z"'
            '/><path d="m21.85 2.15-10.94 10.94"/>',
    "stop": '<rect width="16" height="16" x="4" y="4" rx="2"/>',
    "download": '<path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 '
                '2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "copy": '<rect width="14" height="14" x="8" y="8" rx="2"/>'
            '<path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 '
            '2 2"/>',
    "sliders": '<line x1="21" x2="14" y1="4" y2="4"/><line x1="10" x2="3" '
               'y1="4" y2="4"/><line x1="21" x2="12" y1="12" y2="12"/>'
               '<line x1="8" x2="3" y1="12" y2="12"/><line x1="21" x2="16" '
               'y1="20" y2="20"/><line x1="12" x2="3" y1="20" y2="20"/>'
               '<line x1="14" x2="14" y1="2" y2="6"/><line x1="8" x2="8" '
               'y1="10" y2="14"/><line x1="16" x2="16" y1="18" y2="22"/>',
}

_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        'fill="none" stroke="{c}" stroke-width="2" stroke-linecap="round" '
        'stroke-linejoin="round">{paths}</svg>')


def _pixmap(name, size, color):
    svg = _SVG.format(c=color, paths=ICONS.get(name, ICONS["file"]))
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    renderer.render(p)
    p.end()
    return pm


def icon(name, size=20, color="#d0d0d6", hover="#4aa3e0"):
    """QIcon plano de `name` (Lucide) a `size` px; cambia de color al hover."""
    ic = QIcon(_pixmap(name, size, color))
    if hover:
        ic.addPixmap(_pixmap(name, size, hover), QIcon.Active)
    return ic
