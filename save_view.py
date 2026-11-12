"""文字起こし結果をテキストファイルに保存するボタン（GUI 部品）。

大枠のウィンドウ（audio_gui.py）からの使い方:
    from transcribe_view import TranscribeView
    from save_view import SaveView

    self.transcribe_view = TranscribeView()
    # 保存するテキストの取り出し方（関数）を渡す
    self.save_view = SaveView(get_text=self.transcribe_view.get_text)
    layout.addWidget(self.transcribe_view)
    layout.addWidget(self.save_view)

    # 必要なら、保存が終わったことを受け取れる
    self.save_view.saved.connect(関数)  # 引数: 保存したファイルのパス str
"""
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout,
)

# このファイルがあるフォルダ（相対パスはここを基準に保存する）
BASE_DIR = Path(__file__).resolve().parent

# 保存先の初期値
DEFAULT_FILE = "output.txt"


def save_text(text, file_path):
    """テキストをファイルに保存して、保存先のパスを返す。"""
    if not text.strip():
        raise ValueError("保存する文字起こし結果がありません（先に文字起こししてください）")

    path = Path(file_path)
    if not path.is_absolute():
        path = BASE_DIR / path

    path.write_text(text, encoding="utf-8")
    return path


class SaveView(QGroupBox):
    """保存先の入力欄・参照ボタン・保存ボタン。"""

    saved = Signal(str)  # 保存完了時: 保存したファイルのパス

    def __init__(self, get_text, default_file=DEFAULT_FILE, parent=None):
        super().__init__("保存", parent)
        self.get_text = get_text  # 保存するテキストを返す関数

        self.path_edit = QLineEdit(default_file)
        self.browse_button = QPushButton("参照…")
        self.save_button = QPushButton("テキスト保存")
        self.save_button.setMinimumHeight(40)
        self.status_label = QLabel()

        row = QHBoxLayout()
        row.addWidget(QLabel("保存先:"))
        row.addWidget(self.path_edit)
        row.addWidget(self.browse_button)

        layout = QVBoxLayout(self)
        layout.addLayout(row)
        layout.addWidget(self.save_button)
        layout.addWidget(self.status_label)

        self.browse_button.clicked.connect(self.choose_file)
        self.save_button.clicked.connect(self.save)
        self._set_status("未保存", "#9e9e9e")

    def choose_file(self):
        """保存先をダイアログで選ぶ。"""
        path, _ = QFileDialog.getSaveFileName(
            self, "保存先を選択", str(BASE_DIR / self.path_edit.text()), "テキスト (*.txt)"
        )
        if path:
            self.path_edit.setText(path)

    def save(self):
        """文字起こし結果を保存する。"""
        try:
            path = save_text(self.get_text(), self.path_edit.text().strip() or DEFAULT_FILE)
        except Exception as error:
            self._set_status(f"エラー: {error}", "#e53935")
            return
        self._set_status(f"テキスト保存完了（{path.name}）", "#1e88e5")
        self.saved.emit(str(path))

    def _set_status(self, text, color):
        self.status_label.setText(f"状態: {text}")
        self.status_label.setStyleSheet(
            f"color: white; background-color: {color}; padding: 4px; border-radius: 4px;"
        )


if __name__ == "__main__":
    # 単体で動作確認する: python save_view.py
    # （文字起こし欄の代わりに、入力欄のテキストを保存する）
    import sys
    from PySide6.QtWidgets import QApplication, QTextEdit, QWidget

    app = QApplication(sys.argv)
    window = QWidget()
    text_edit = QTextEdit("保存テスト用のテキストです。")
    save_view = SaveView(get_text=text_edit.toPlainText)
    layout = QVBoxLayout(window)
    layout.addWidget(text_edit)
    layout.addWidget(save_view)
    window.resize(420, 320)
    window.show()
    sys.exit(app.exec())
