"""文字起こしボタンと文字起こし結果の表示欄（GUI 部品）。

大枠のウィンドウ（audio_gui.py）からの使い方:
    from transcribe_view import TranscribeView

    self.transcribe_view = TranscribeView()
    layout.addWidget(self.transcribe_view)   # 好きな場所に置くだけ

    # 必要なら、文字起こしが終わったことを受け取れる
    self.transcribe_view.transcribed.connect(関数)  # 引数: 文字起こし結果 str
    # 保存するときは、表示中のテキストを取り出す
    text = self.transcribe_view.get_text()
"""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QGroupBox, QLabel, QPushButton, QTextEdit, QVBoxLayout

from audio_transcribe import INPUT_FILE, TranscribeThread


class TranscribeView(QGroupBox):
    """文字起こしボタンと、結果を表示するテキスト欄。"""

    transcribed = Signal(str)  # 文字起こし完了時: 結果のテキスト

    def __init__(self, audio_file=INPUT_FILE, parent=None):
        super().__init__("文字起こし", parent)
        self.audio_file = audio_file
        self.thread = None

        self.button = QPushButton("文字起こし開始")
        self.button.setMinimumHeight(40)

        self.status_label = QLabel()

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText("ここに文字起こし結果が表示されます")

        layout = QVBoxLayout(self)
        layout.addWidget(self.button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_text)

        self.button.clicked.connect(self.start_transcribe)
        self._set_status("待機中", "#9e9e9e")

    def start_transcribe(self):
        """文字起こしを別スレッドで開始する（画面は固まらない）。"""
        self.button.setEnabled(False)
        self.button.setText("文字起こし中…")
        self._set_status("文字起こし中", "#fb8c00")

        self.thread = TranscribeThread(self.audio_file)
        self.thread.finished_text.connect(self._on_finished)
        self.thread.failed.connect(self._on_failed)
        self.thread.start()

    def get_text(self):
        """表示中の文字起こし結果を返す（保存処理で使う）。"""
        return self.result_text.toPlainText()

    def _on_finished(self, text):
        self.result_text.setPlainText(text)
        self._reset_button()
        self._set_status("文字起こし完了", "#43a047")
        self.transcribed.emit(text)

    def _on_failed(self, message):
        self._reset_button()
        self._set_status(f"エラー: {message}", "#e53935")

    def _reset_button(self):
        self.button.setEnabled(True)
        self.button.setText("文字起こし開始")

    def _set_status(self, text, color):
        self.status_label.setText(f"状態: {text}")
        self.status_label.setStyleSheet(
            f"color: white; background-color: {color}; padding: 4px; border-radius: 4px;"
        )


if __name__ == "__main__":
    # 単体で動作確認する: python transcribe_view.py
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    view = TranscribeView()
    view.resize(420, 320)
    view.show()
    sys.exit(app.exec())
