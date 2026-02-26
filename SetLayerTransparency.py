# -----------------------------------------------------------------------------#
# Title:       SetLayerTransparency                                            #
# Author:      Mike Elstermann (#geoObserver)                                  #
# Version:     v0.4                                                            #
# Created:     15.10.2025                                                      #
# Last Change: 25.02.2026                                                      #
# see also:    https://geoobserver.de/qgis-plugins/                            #
#                                                                              #
# This file contains code generated with assistance from an AI                 #
# No warranty is provided for AI-generated portions.                           #
# Human review and modification performed by: Mike Elstermann (#geoObserver)   #
# -----------------------------------------------------------------------------#

import os
from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.core import QgsProject

plugin_dir = os.path.dirname(__file__)

class TransparencyDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, initial_value=50, layers=None, preview_default=False):
        super().__init__(parent)
        self.setWindowTitle("Set Transparency")
        self.setLayout(QtWidgets.QVBoxLayout())

        self.layers = layers or []
        self.original_opacities = {lyr: lyr.opacity() for lyr in self.layers}

        # Label
        self.label = QtWidgets.QLabel(f"Transparency: {initial_value} %")
        self.layout().addWidget(self.label)

        # Horizontal Container for Slider + SpinBox
        hbox = QtWidgets.QHBoxLayout()

        self.slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(initial_value)
        self.slider.setMinimumWidth(250)
        hbox.addWidget(self.slider)

        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(0, 100)
        self.spin.setValue(initial_value)
        hbox.addWidget(self.spin)

        # Signals
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self._update_label)
        self.slider.valueChanged.connect(self._maybe_preview)

        self.layout().addLayout(hbox)

        # Live-Preview Checkbox
        self.preview_checkbox = QtWidgets.QCheckBox("Live-Preview")
        self.preview_checkbox.setChecked(preview_default)
        self.layout().addWidget(self.preview_checkbox)

        # OK / Cancel Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self._restore_original)
        buttons.rejected.connect(self.reject)
        self.layout().addWidget(buttons)

        # Info Label
        info_label = QtWidgets.QLabel()
        info_label.setTextFormat(QtCore.Qt.TextFormat.RichText)
        info_label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextBrowserInteraction)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        info_label.setText(
            'Set Layer Transparency v0.5 (Qt5/6)<br>'
            '<a href="https://geoobserver.de/qgis-plugins/">Other #geoObserver Tools ...</a>'
        )
        self.layout().addWidget(info_label)

    def _update_label(self, value):
        self.label.setText(f"Transparency: {value} %")

    def _maybe_preview(self, value):
        if self.preview_checkbox.isChecked():
            self._apply_preview(value)

    def _apply_preview(self, value):
        opacity_value = 1 - (value / 100.0)
        for lyr in self.layers:
            try:
                lyr.setOpacity(opacity_value)
                lyr.triggerRepaint()
            except Exception as e:
                name = getattr(lyr, "name", lambda: "unknown")()
                print(f"Preview Error {name}: {e}")

    def _restore_original(self):
        if not self.preview_checkbox.isChecked():
            return
        for lyr, orig_opacity in self.original_opacities.items():
            try:
                lyr.setOpacity(orig_opacity)
                lyr.triggerRepaint()
            except Exception as e:
                name = getattr(lyr, "name", lambda: "unknown")()
                print(f"Restore Error {name}: {e}")

    def value(self):
        return self.slider.value()

    def preview_enabled(self):
        return self.preview_checkbox.isChecked()


class SetLayerTransparency:
    def __init__(self, iface):
        self.iface = iface
        self.toolbar = None
        self.actions = []

    def initGui(self):
        self.toolbar = self.iface.mainWindow().findChild(QtWidgets.QToolBar, "geoObserverTools")
        if not self.toolbar:
            self.toolbar = self.iface.addToolBar("geoObserverTools")
            self.toolbar.setObjectName("geoObserverTools")
            self.toolbar.setToolTip("geoObserver Tools ...")

        icon = os.path.join(plugin_dir, 'logo.png')
        self.action = QtGui.QAction(QtGui.QIcon(icon), 'Set Layer Transparency', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.toolbar.addAction(self.action)
        self.actions.append(self.action)

    def unload(self):
        for action in self.actions:
            self.toolbar.removeAction(action)
        self.actions.clear()

    def run(self):
        settings = QtCore.QSettings()
        last_value = settings.value("geoObserver/transparency", 50, type=int)
        last_preview = settings.value("geoObserver/previewEnabled", False, type=bool)

        all_layers = list(QgsProject.instance().mapLayers().values())
        if not all_layers:
            self.iface.messageBar().pushWarning("Set Layer Transparency", "No Layers found in project.")
            return

        selected_layers = self.iface.layerTreeView().selectedLayers()
        target_layers = selected_layers if selected_layers else all_layers

        dlg = TransparencyDialog(self.iface.mainWindow(), last_value, target_layers, last_preview)

        # exec_ → exec für Qt6
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return

        transparency_percent = dlg.value()
        preview_enabled = dlg.preview_enabled()

        # Save settings
        settings.setValue("geoObserver/transparency", int(transparency_percent))
        settings.setValue("geoObserver/previewEnabled", preview_enabled)
        settings.sync()

        # Apply final opacity
        opacity_value = 1 - (transparency_percent / 100.0)
        for lyr in target_layers:
            try:
                lyr.setOpacity(opacity_value)
                lyr.triggerRepaint()
            except Exception as e:
                name = getattr(lyr, "name", lambda: "unknown")()
                print(f"Apply Error {name}: {e}")

        self.iface.messageBar().pushSuccess(
            "Set Layer Transparency",
            f"{len(target_layers)} Layer set to {transparency_percent}% Transparency "
            f"(Opacity {opacity_value:.2f}, Preview {'On' if preview_enabled else 'Off'})."
        )