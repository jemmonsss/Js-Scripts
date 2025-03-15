import sys
import os
import requests
import subprocess
from PyQt5 import QtCore, QtWidgets

GITHUB_API_URL = "https://api.github.com"
GITHUB_USER = "jemmonsss"

class DownloadTab(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # Reference to main window
        self.exe_assets = []  # List to store found EXE info
        self.init_ui()
        # Automatically refresh the list when the tab is created
        self.load_exe_assets()
    
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        
        self.desc_label = QtWidgets.QLabel("Available EXE Releases")
        layout.addWidget(self.desc_label)
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh List")
        self.refresh_btn.clicked.connect(self.load_exe_assets)
        layout.addWidget(self.refresh_btn)
        
        self.exe_combo = QtWidgets.QComboBox()
        layout.addWidget(self.exe_combo)
        
        self.download_btn = QtWidgets.QPushButton("Download Selected EXE")
        self.download_btn.clicked.connect(self.download_exe)
        layout.addWidget(self.download_btn)
        
        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def load_exe_assets(self):
        self.status_label.setText("Loading repositories...")
        self.exe_combo.clear()
        self.exe_assets = []
        
        repos_url = f"{GITHUB_API_URL}/users/{GITHUB_USER}/repos"
        try:
            repos_resp = requests.get(repos_url)
            repos_resp.raise_for_status()
            repos = repos_resp.json()
        except requests.RequestException as e:
            self.status_label.setText("Failed to load repositories.")
            QtWidgets.QMessageBox.critical(self, "Error", f"Error fetching repositories: {e}")
            return
        
        for repo in repos:
            repo_name = repo.get("name")
            releases_url = f"{GITHUB_API_URL}/repos/{GITHUB_USER}/{repo_name}/releases"
            try:
                releases_resp = requests.get(releases_url)
                if releases_resp.status_code != 200:
                    continue
                releases = releases_resp.json()
                if not releases:
                    continue
                for release in releases:
                    assets = release.get("assets", [])
                    for asset in assets:
                        asset_name = asset.get("name", "")
                        if asset_name.lower().endswith(".exe"):
                            self.exe_assets.append({
                                "repo": repo_name,
                                "release": release.get("tag_name", "N/A"),
                                "asset_name": asset_name,
                                "download_url": asset.get("browser_download_url")
                            })
                            break  # Only take the first .exe per repository
                    else:
                        continue
                    break
            except requests.RequestException:
                continue
        
        if not self.exe_assets:
            self.status_label.setText("No EXE assets found.")
        else:
            for idx, item in enumerate(self.exe_assets):
                display_text = f"{item['repo']} ({item['release']}) - {item['asset_name']}"
                self.exe_combo.addItem(display_text, idx)
            self.status_label.setText("EXE assets loaded.")
    
    def download_exe(self):
        idx = self.exe_combo.currentData()
        if idx is None:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Please select an asset.")
            return
        asset_info = self.exe_assets[idx]
        download_url = asset_info["download_url"]
        self.status_label.setText("Downloading...")
        try:
            r = requests.get(download_url, stream=True)
            r.raise_for_status()
            file_path = os.path.join(os.getcwd(), asset_info["asset_name"])
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            self.status_label.setText(f"Downloaded: {asset_info['asset_name']}")
            QtWidgets.QMessageBox.information(self, "Download Complete", f"Downloaded to:\n{file_path}")
            self.parent.downloaded_tab.add_downloaded_file(asset_info['asset_name'], file_path)
        except requests.RequestException as e:
            self.status_label.setText("Download failed.")
            QtWidgets.QMessageBox.critical(self, "Error", f"Error downloading: {e}")

class DownloadedTab(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(layout)
        
        self.desc_label = QtWidgets.QLabel("Downloaded EXE Files")
        layout.addWidget(self.desc_label)
        
        self.list_widget = QtWidgets.QListWidget()
        layout.addWidget(self.list_widget)
        
        self.run_btn = QtWidgets.QPushButton("Run Selected EXE")
        self.run_btn.clicked.connect(self.run_exe)
        layout.addWidget(self.run_btn)
        
        self.status_label = QtWidgets.QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def add_downloaded_file(self, display_name, file_path):
        item = QtWidgets.QListWidgetItem(display_name)
        item.setData(QtCore.Qt.UserRole, file_path)
        self.list_widget.addItem(item)
    
    def run_exe(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item:
            QtWidgets.QMessageBox.warning(self, "Selection Error", "Select a file to run.")
            return
        file_path = selected_item.data(QtCore.Qt.UserRole)
        if file_path and os.path.exists(file_path):
            try:
                subprocess.Popen([file_path], shell=True)
                self.status_label.setText("EXE launched.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to run EXE: {e}")
        else:
            QtWidgets.QMessageBox.warning(self, "File Missing", "File not found.")

class GitHubExeManager(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub EXE Manager")
        self.setMinimumSize(700, 500)
        self.init_ui()
    
    def init_ui(self):
        self.tabs = QtWidgets.QTabWidget()
        self.download_tab = DownloadTab(self)
        self.downloaded_tab = DownloadedTab(self)
        self.tabs.addTab(self.download_tab, "Download")
        self.tabs.addTab(self.downloaded_tab, "Downloaded")
        self.setCentralWidget(self.tabs)
        self.apply_styles()
    
    def apply_styles(self):
        # A modern, minimalist dark theme with subtle accent colors.
        style = """
            QWidget {
                background-color: #2b2b2b;
                color: #dcdcdc;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabWidget::pane {
                border: 0;
            }
            QTabBar::tab {
                background: #3c3f41;
                border: none;
                padding: 10px 20px;
                margin: 2px;
                border-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #4e5254;
                font-weight: bold;
            }
            QComboBox, QListWidget {
                background: #3c3f41;
                border: 1px solid #4e5254;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #5e2a7e;
                border: none;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7b3aa7;
            }
            QLabel {
                font-size: 14px;
            }
        """
        self.setStyleSheet(style)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = GitHubExeManager()
    window.show()
    sys.exit(app.exec_())
