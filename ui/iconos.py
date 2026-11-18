"""Iconos planos dibujados con QPainter (sin emoji, sin assets)."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QColor, QIcon, QPainter, QPainterPath, QPen,
                           QPixmap, QPolygonF)


def icon(name, size=20, color="#d0d0d6"):
    """Devuelve QIcon plano de `name` a `size` px, centrado."""
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    c = QColor(color)
    pen = QPen(c)
    pen.setWidthF(max(1.4, size / 13))
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    u = size / 20.0  # rejilla 20x20

    def L(x1, y1, x2, y2):
        p.drawLine(QPointF(x1 * u, y1 * u), QPointF(x2 * u, y2 * u))

    def R(x, y, w, h, r=1.6):
        p.drawRoundedRect(QRectF(x * u, y * u, w * u, h * u), r * u, r * u)

    if name == "folder":
        path = QPainterPath(QPointF(3 * u, 16 * u))
        path.lineTo(3 * u, 6 * u)
        path.lineTo(8 * u, 6 * u)
        path.lineTo(10 * u, 8 * u)
        path.lineTo(17 * u, 8 * u)
        path.lineTo(17 * u, 16 * u)
        path.closeSubpath()
        p.drawPath(path)
    elif name == "newfolder":
        path = QPainterPath(QPointF(2 * u, 16 * u))
        path.lineTo(2 * u, 6 * u)
        path.lineTo(7 * u, 6 * u)
        path.lineTo(9 * u, 8 * u)
        path.lineTo(16 * u, 8 * u)
        path.lineTo(16 * u, 16 * u)
        path.closeSubpath()
        p.drawPath(path)
        L(14.5, 2, 18.5, 2)
        L(16.5, 0.2, 16.5, 4)
    elif name == "file":
        path = QPainterPath(QPointF(5.5 * u, 17 * u))
        path.lineTo(5.5 * u, 3 * u)
        path.lineTo(11.5 * u, 3 * u)
        path.lineTo(14.5 * u, 6 * u)
        path.lineTo(14.5 * u, 17 * u)
        path.closeSubpath()
        p.drawPath(path)
        L(11.5, 3, 11.5, 6)
        L(11.5, 6, 14.5, 6)
    elif name == "db":
        p.drawEllipse(QRectF(4 * u, 3 * u, 12 * u, 5 * u))
        L(4, 5.5, 4, 15)
        L(16, 5.5, 16, 15)
        p.drawArc(QRectF(4 * u, 12 * u, 12 * u, 5.5 * u), 180 * 16, 180 * 16)
        p.drawArc(QRectF(4 * u, 9 * u, 12 * u, 5 * u), 180 * 16, 180 * 16)
    elif name == "monitor":
        R(2.5, 4, 15, 10)
        L(10, 14, 10, 16.5)
        L(6, 17, 14, 17)
    elif name == "save":
        R(4, 3.5, 12, 13)
        R(7, 3.5, 6, 5, 0.8)
        L(7, 12.5, 13, 12.5)
    elif name == "terminal":
        R(2.5, 4, 15, 12)
        L(5.5, 7.5, 8, 10)
        L(8, 10, 5.5, 12.5)
        L(10.5, 12.5, 14.5, 12.5)
    elif name == "gear":
        p.drawEllipse(QPointF(10 * u, 10 * u), 3.4 * u, 3.4 * u)
        for a in range(0, 360, 45):
            import math
            r1, r2 = 5.2, 8
            x1 = 10 + r1 * math.cos(math.radians(a))
            y1 = 10 + r1 * math.sin(math.radians(a))
            x2 = 10 + r2 * math.cos(math.radians(a))
            y2 = 10 + r2 * math.sin(math.radians(a))
            L(x1, y1, x2, y2)
    elif name == "refresh":
        p.drawArc(QRectF(4 * u, 4 * u, 12 * u, 12 * u), 40 * 16, 285 * 16)
        L(16.3, 4.6, 16.3, 8.8)
        L(16.3, 8.8, 12.3, 8.2)
    elif name == "plus":
        L(10, 4.5, 10, 15.5)
        L(4.5, 10, 15.5, 10)
    elif name == "mic":
        R(8, 2.5, 4, 9, 2)
        p.drawArc(QRectF(5.5 * u, 8 * u, 9 * u, 7 * u), 190 * 16, 160 * 16)
        L(10, 15, 10, 17.5)
        L(7, 17.5, 13, 17.5)
    elif name == "send":
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawPolygon(QPolygonF([QPointF(6 * u, 4.5 * u),
                                 QPointF(16 * u, 10 * u),
                                 QPointF(6 * u, 15.5 * u),
                                 QPointF(9 * u, 10 * u)]))
    elif name == "stop":
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(5 * u, 5 * u, 10 * u, 10 * u),
                          1.8 * u, 1.8 * u)
    elif name == "download":
        L(10, 3.5, 10, 12)
        L(6, 8.5, 10, 12.5)
        L(14, 8.5, 10, 12.5)
        L(4.5, 16.5, 15.5, 16.5)
    elif name == "check":
        L(4.5, 10.5, 8.5, 14.5)
        L(8.5, 14.5, 15.5, 6)
    elif name == "x":
        L(6, 6, 14, 14)
        L(14, 6, 6, 14)
    else:  # punto genérico
        p.setBrush(c)
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(10 * u, 10 * u), 4 * u, 4 * u)
    p.end()
    return QIcon(pm)
