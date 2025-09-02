import os
from qgis.PyQt import QtWidgets, QtCore
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from qgis.core import QgsProject

plugin_dir = os.path.dirname(__file__)

#class TransparencyDialog(QtWidgets.QDialog):
#    def __init__(self, parent=None, start_value=50):
#        super().__init__(parent)
#        self.setWindowTitle("Set Transparency")
#        self.setLayout(QtWidgets.QVBoxLayout())
#
#        self.label = QtWidgets.QLabel(f"Transparency: {int(start_value)} %")
#        self.layout().addWidget(self.label)
#
#        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
#        self.slider.setRange(0, 100)
#        self.slider.setValue(int(start_value))
#        self.slider.valueChanged.connect(self._update_label)
#        self.layout().addWidget(self.slider)
#
#        buttons = QtWidgets.QDialogButtonBox(
#            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
#        )
#        buttons.accepted.connect(self.accept)
#        buttons.rejected.connect(self.reject)
#        self.layout().addWidget(buttons)
#
#    def _update_label(self, value):
#        self.label.setText(f"Transparency: {value} %")
#
#    def value(self):
#        return int(self.slider.value())
class TransparencyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, initial_value=50):
        super().__init__(parent)
        self.setWindowTitle("Transparenz einstellen")
        self.setLayout(QtWidgets.QVBoxLayout())

        # Label
        self.label = QtWidgets.QLabel(f"Transparenz: {initial_value} %")
        self.layout().addWidget(self.label)

        # Horizontaler Container für Slider + SpinBox
        hbox = QtWidgets.QHBoxLayout()

        # Slider
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(initial_value)
        hbox.addWidget(self.slider)

        # SpinBox
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, 100)
        self.spin.setValue(initial_value)
        self.slider.setMinimumWidth(250)   # Breite anpassen
        hbox.addWidget(self.spin)

        # Signale verbinden
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self._update_label)

        self.layout().addLayout(hbox)

        # OK / Cancel Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)

    def _update_label(self, value):
        self.label.setText(f"Transparenz: {value} %")

    def value(self):
        return self.slider.value()

class SetLayerTransparency:
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.actions = []

    def initGui(self):
        # Prüfen, ob gemeinsame Toolbar schon existiert
        self.toolbar = self.iface.mainWindow().findChild(QtWidgets.QToolBar, "#geoObserverTools")
        if not self.toolbar:
            # Nur beim ersten Plugin anlegen
            self.toolbar = self.iface.addToolBar("#geoObserver Tools")
            self.toolbar.setObjectName("#geoObserverTools")

        # Button/Aktion erstellen
        icon = os.path.join(plugin_dir, 'logo.png')
        self.action = QAction(QIcon(icon), 'Set Layer Transparency', self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Aktion in gemeinsame Toolbar einfügen
        self.toolbar.addAction(self.action)
        self.actions.append(self.action)

    def unload(self):
        # Nur eigene Buttons entfernen
        for action in self.actions:
            self.toolbar.removeAction(action)
        self.actions.clear()

    def run(self):
        # QSettings für persistente Speicherung
        settings = QtCore.QSettings()
        last_value = settings.value("geoObserver/transparency", 50, type=int)

        # Dialog mit gespeicherten Wert öffnen
        dlg = TransparencyDialog(self.iface.mainWindow(), last_value)

        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            print("TransparencyDialog abgebrochen.")
            return

        transparency_percent = dlg.value()
        settings.setValue("geoObserver/transparency", int(transparency_percent))
        settings.sync()

        opacity_value = 1 - (transparency_percent / 100.0)

        # ------------------------------
        # Layer-Prüfung und Auswahl-Logik
        # ------------------------------
        all_layers = list(QgsProject.instance().mapLayers().values())

        if not all_layers:
            self.iface.messageBar().pushWarning(
                "Set Layer Transparency",
                "Keine Layer im Projekt gefunden."
            )
            return

        selected_layers = self.iface.layerTreeView().selectedLayers()

        if selected_layers:
            target_layers = selected_layers
            print(f"Set transparency for {len(target_layers)} selected layer(s).")
        else:
            target_layers = all_layers
            print("No layers selected → applying to ALL layers.")

        # ------------------------------
        # Transparenz anwenden
        # ------------------------------
        for layer in target_layers:
            try:
                layer.setOpacity(opacity_value)
                layer.triggerRepaint()
            except Exception as e:
                print(f"Layer '{getattr(layer, 'name', lambda: 'unknown')()}': {e}")

        self.iface.messageBar().pushSuccess(
            "Set Layer Transparency",
            f"{len(target_layers)} layer(s) set to {transparency_percent}% transparency "
            f"(Opacity {opacity_value:.2f}).",
        )
