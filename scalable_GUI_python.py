import sys
import json
import subprocess
import keyboard
from PyQt5.QtWidgets import (QLineEdit, QHBoxLayout, QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QAction, QInputDialog, QMessageBox, QShortcut, QKeySequenceEdit, QDialog, QVBoxLayout, QLabel, QPushButton)
from PyQt5.QtGui import (QIcon, QKeySequence)
from PyQt5.QtCore import (Qt, QCoreApplication, QEvent)  # Add this line


config_file = 'config.json'
#insert path to your custom system tray icon. skull24x24 png available in the GIT repository
tray_icon_path = r""

class CustomEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, action):
        super().__init__(CustomEvent.EVENT_TYPE)
        self.action = action

def execute_path_safely(self, path):
    # This method would wrap your existing execute_path method
    # but ensure it's called safely from the main thread
    QCoreApplication.postEvent(self, CustomEvent(lambda: self.execute_path(path)))

# In your MainWindow class, you need to handle the custom event:
def event(self, event):
    if event.type() == CustomEvent.EVENT_TYPE:
        event.action()
        return True
    return super().event(event)

class ShortcutDialog(QDialog):
    def __init__(self, parent=None):
        super(ShortcutDialog, self).__init__(parent)
        self.setWindowTitle('Set Shortcut')
        self.layout = QVBoxLayout(self)

        self.label = QLabel("Set a new keyboard shortcut:", self)
        self.layout.addWidget(self.label)

        self.keySequenceEdit = QKeySequenceEdit(self)
        self.layout.addWidget(self.keySequenceEdit)

        self.okButton = QPushButton("OK", self)
        self.okButton.clicked.connect(self.accept)
        self.layout.addWidget(self.okButton)

        self.cancelButton = QPushButton("Cancel", self)
        self.cancelButton.clicked.connect(self.reject)
        self.layout.addWidget(self.cancelButton)

    def getShortcut(self):
        return self.keySequenceEdit.keySequence().toString(QKeySequence.NativeText)
    
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scalable GUI Python")
        self.setGeometry(100, 100, 400, 300)
        self.config = self.load_config()

        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)
        self.setCentralWidget(self.main_widget)

        self.setup_menu()
        self.populate_buttons()
        self.setup_system_tray_icon()
        self.setup_shortcuts()

    def load_config(self):
        try:
            with open(config_file, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {"buttons": [], "layout": {"columns": 1}}

    def save_config(self):
        with open(config_file, 'w') as file:
            json.dump(self.config, file)

    def execute_path(self, path):
        if path.endswith('.py'):
            subprocess.Popen([sys.executable, path], shell=True)  # Ensure correct execution of .py files
        else:
            subprocess.Popen(path, shell=True)

    def populate_buttons(self):
        for index, btn_config in enumerate(self.config.get('buttons', [])):
            self.add_button(btn_config['text'], btn_config['path'], index)

    def add_button(self, text, path, index):
        btn = QPushButton(text)
        
        # Left-click functionality
        btn.clicked.connect(lambda checked, p=path: self.execute_path(p))
        
        # Create the context menu for the button
        btn_menu = QMenu()
        
        # Add actions to the context menu for right-click
                
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(lambda: self.remove_button(index))
        btn_menu.addAction(remove_action)
        
        reconfigure_action = QAction("Reconfigure", self)
        reconfigure_action.triggered.connect(lambda: self.reconfigure_button(index))
        btn_menu.addAction(reconfigure_action)
        
        # Set the context menu policy for the button
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda point, menu=btn_menu: btn_menu.exec_(btn.mapToGlobal(point)))  # Show menu on right-click
        
        # Add the button to the layout
        self.layout.addWidget(btn)

    def remove_button(self, index):
        reply = QMessageBox.question(self, 'Remove Button', 'Are you sure you want to remove this button?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.config['buttons'].pop(index)
            self.save_config()
            self.refresh_gui()

    def reconfigure_button(self, index):
        btn_config = self.config['buttons'][index]
        
        text, ok = QInputDialog.getText(self, 'Reconfigure Button', 'Enter new button text:', text=btn_config['text'])
        if ok and text:
            path, ok = QInputDialog.getText(self, 'Reconfigure Button Path', 'Enter new script or program path:', text=btn_config['path'])
            if ok and path:
                self.config['buttons'][index] = {"text": text, "path": path}
                self.save_config()
                self.refresh_gui()
   
    def set_shortcut(self, index):
        dialog = ShortcutDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            shortcutString = dialog.getShortcut()
            shortcut = QShortcut(QKeySequence(shortcutString), self)
            btn_config = self.config['buttons'][index]
            shortcut.activated.connect(lambda p=btn_config['path']: self.execute_path(p))
            
            # Optionally, save the shortcut for persistence
            btn_config['shortcut'] = shortcutString
            self.save_config()

    def refresh_gui(self):
        for i in reversed(range(self.layout.count())): 
            widget = self.layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.populate_buttons()

    def setup_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")

        add_btn_action = QAction("Add New Button", self)
        add_btn_action.triggered.connect(self.add_new_button_dialog)
        file_menu.addAction(add_btn_action)

        readme_action = QAction("Readme", self)
        readme_action.triggered.connect(self.show_readme)
        file_menu.addAction(readme_action)

        manage_hotkeys_action = QAction("Manage Hotkeys", self)
        manage_hotkeys_action.triggered.connect(self.manage_hotkeys_dialog)
        file_menu.addAction(manage_hotkeys_action)

    def manage_hotkeys_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Hotkeys")
        layout = QVBoxLayout(dialog)

        for index, btn_config in enumerate(self.config['buttons']):
            row_layout = QHBoxLayout()
            label = QLabel(btn_config['text'])
            hotkey_input = QLineEdit(btn_config.get('hotkey', ''))
            hotkey_input.setPlaceholderText("Enter hotkey...")
            set_btn = QPushButton("Set")
            set_btn.clicked.connect(lambda checked, i=index, hi=hotkey_input: self.set_hotkey_for_button(i, hi.text()))
            row_layout.addWidget(label)
            row_layout.addWidget(hotkey_input)
            row_layout.addWidget(set_btn)
            layout.addLayout(row_layout)

        dialog.setLayout(layout)
        dialog.exec_()
        
    def set_hotkey_for_button(self, index, hotkey):
        # Update the config with the new hotkey
        self.config['buttons'][index]['hotkey'] = hotkey
        self.save_config()
        # Register the hotkey with your hotkey handling library
        self.register_hotkey(hotkey, lambda: self.execute_path(self.config['buttons'][index]['path']))
    
    def register_hotkey(self, hotkey, action):
        try:
            keyboard.add_hotkey(hotkey, action)
            print(f"Hotkey '{hotkey}' registered successfully.")
        except Exception as e:
            print(f"Failed to register hotkey '{hotkey}': {e}")
            
    def add_new_button_dialog(self):
        text, ok = QInputDialog.getText(self, 'Add New Button', 'Enter button text:')
        if ok and text:
            path, ok = QInputDialog.getText(self, 'Button Path', 'Enter script or program path:')
            if ok and path:
                self.config['buttons'].append({"text": text, "path": path})
                self.save_config()
                self.refresh_gui()

    def show_readme(self):
        QMessageBox.information(self, "README", "Functionality:\n- Left-click: Execute/Open\n- Right-click: Remove/Reconfigure")
    def setup_shortcuts(self):
        for index, btn_config in enumerate(self.config.get('buttons', [])):
            shortcut_string = btn_config.get('shortcut')
            if shortcut_string:
                shortcut = QShortcut(QKeySequence(shortcut_string), self)
                shortcut.activated.connect(lambda p=btn_config['path']: self.execute_path(p))

    def setup_system_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(QIcon(tray_icon_path), self)  # Update this path
        tray_menu = QMenu()

        # Add "Open" action to show the window
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.show_window)
        tray_menu.addAction(open_action)

        # Existing "Exit" action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray_icon.showMessage("Scalable GUI Python", "Application minimized to tray.")
   
    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())