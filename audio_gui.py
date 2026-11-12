import sys

# 外部モジュール
import ffmpeg
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QHBoxLayout, QVBoxLayout,
)
from PySide6 import QtGui, QtCore
from PySide6.QtCore import QThread, QTimer, Signal

# 録音時間（秒）
DURATION = 10

# 出力ファイル名
OUTPUT_FILE = "python-audio-output.wav"

# 状態ごとの(ステータス文言, 背景色)
STATES = {
    "IDLE":         ("待機中", "#dddddd"),
    "RECORDING":    ("録音中", "#ff6b6b"),
    "RECORDED":     ("録音完了", "#74c0fc"),
    "TRANSCRIBING": ("文字起こし中", "#ffd43b"),
    "TRANSCRIBED":  ("文字起こし完了", "#69db7c"),
    "SAVED":        ("テキスト保存完了", "#38d9a9"),
}


class RecordWorker(QThread):
    """マイクから音声を録音して WAV ファイルに保存する（別スレッドで実行）。"""
    recorded = Signal(str)   # 録音成功：保存したファイル名
    failed = Signal(str)     # 録音失敗：エラーメッセージ

    def run(self):
        try:
            # macOS の入力デバイスを指定して録音する
            (
                ffmpeg.input(
                    ":0",
                    format="avfoundation",
                    t=DURATION,
                )
                .output(
                    OUTPUT_FILE,
                    acodec="pcm_s16le",
                    ar="44100",
                    ac=1,
                )
                .run(overwrite_output=True, capture_stderr=True)
            )
            self.recorded.emit(OUTPUT_FILE)

        except ffmpeg.Error as error:
            stderr = error.stderr
            if stderr:
                self.failed.emit(f"FFmpeg エラー: {stderr.decode(errors='replace')}")
            else:
                self.failed.emit(f"FFmpeg エラー: {error}")

        except Exception as error:
            self.failed.emit(f"予期せぬエラー: {error}")


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("音声文字起こしアプリ")
        self.setGeometry(100, 100, 500, 400)

        self.worker = None          # 録音スレッド
        self.remaining = 0          # 録音の残り秒数
        self.timer = QTimer(self)   # 残り秒数の表示用
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.on_timer)

        # ステータス表示ラベル
        self.status_label = QLabel()
        self.status_label.setFont(QtGui.QFont("Arial", 20))
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # テキスト表示部分（文字起こし結果を表示する。読み取り専用）
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setFont(QtGui.QFont("Arial", 14))
        self.text_view.setPlaceholderText("ここに文字起こし結果が表示されます")

        # ボタン
        self.btn_record = QPushButton("録音")
        self.btn_transcribe = QPushButton("文字起こし")
        self.btn_save = QPushButton("保存")
        self.buttons = [self.btn_record, self.btn_transcribe, self.btn_save]
        for btn in self.buttons:
            btn.setFont(QtGui.QFont("Arial", 16))

        layout_buttons = QHBoxLayout()
        for btn in self.buttons:
            layout_buttons.addWidget(btn)

        # 親レイアウトに子レイアウト・ウィジェットを配置
        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.text_view)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

        # ボタンの接続
        self.btn_record.clicked.connect(self.on_record_clicked)          # 本物の録音
        self.btn_transcribe.clicked.connect(self.on_transcribe_demo)     # まだダミー
        self.btn_save.clicked.connect(lambda: self.set_state("SAVED"))   # まだダミー

        self.set_state("IDLE")

    # ---------- 状態表示 ----------
    def set_state(self, state: str):
        """状態に応じてステータスの文言・色・ボタンの有効/無効を切り替える"""
        text, color = STATES[state]
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"background-color: {color};")

        self.btn_record.setEnabled(state not in ("RECORDING", "TRANSCRIBING"))
        self.btn_transcribe.setEnabled(state in ("RECORDED", "TRANSCRIBED", "SAVED"))
        self.btn_save.setEnabled(state == "TRANSCRIBED")

    def set_text(self, text: str):
        """テキスト表示部分を更新する"""
        self.text_view.setPlainText(text)

    # ---------- 録音 ----------
    def on_record_clicked(self):
        self.set_state("RECORDING")
        self.remaining = DURATION
        self.status_label.setText(f"録音中（残り {self.remaining} 秒）")
        self.timer.start()

        self.worker = RecordWorker()
        self.worker.recorded.connect(self.on_recorded)
        self.worker.failed.connect(self.on_record_failed)
        self.worker.start()

    def on_timer(self):
        self.remaining -= 1
        if self.remaining > 0:
            self.status_label.setText(f"録音中（残り {self.remaining} 秒）")

    def on_recorded(self, path: str):
        self.timer.stop()
        self.set_state("RECORDED")
        self.status_label.setText(f"録音完了（{path}）")

    def on_record_failed(self, message: str):
        self.timer.stop()
        self.set_state("IDLE")
        self.status_label.setText("録音エラー")
        self.set_text(message)

    # ---------- 文字起こし（まだダミー） ----------
    def on_transcribe_demo(self):
        self.set_text("これは表示テストです。ここに文字起こし結果が入ります。")
        self.set_state("TRANSCRIBED")

    def closeEvent(self, event):
        # 録音中にウィンドウを閉じたときは、録音の終了を待つ
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_widget = MainWidget()
    main_widget.show()
    sys.exit(app.exec())