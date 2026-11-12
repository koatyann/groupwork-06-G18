"""録音した音声ファイルを文字起こしするモジュール。

GUI（audio_gui.py）からの使い方:
    from audio_transcribe import transcribe, TranscribeThread

    # そのまま呼ぶ（数秒かかるので、その間 GUI は固まる）
    text = transcribe("python-audio-output.wav")

    # GUI を固めずに呼ぶ（推奨）
    self.thread = TranscribeThread("python-audio-output.wav")
    self.thread.finished_text.connect(結果を受け取る関数)   # 引数: 文字起こし結果 str
    self.thread.failed.connect(エラーを受け取る関数)        # 引数: エラーメッセージ str
    self.thread.start()
"""
from pathlib import Path

# このファイルがあるフォルダ（どこから実行してもモデルを見つけられるようにする）
BASE_DIR = Path(__file__).resolve().parent

# 文字起こしする音声ファイル（audio_record.py の出力）
INPUT_FILE = BASE_DIR / "python-audio-output.wav"

# whisper モデルの置き場所
MODEL_PATH = BASE_DIR / "whisper-base-mlx"

# 文字起こしの言語
LANGUAGE = "ja"


def _load_audio(audio_file, start_sec=None, end_sec=None):
    """音声ファイルを読み込み、whisper が扱える形（16kHz・モノラル）の配列にする。"""
    import numpy as np
    from pydub import AudioSegment

    sound = AudioSegment.from_file(str(audio_file), format="wav")

    # 開始・終了時間が指定されていれば切り出す（秒 → ミリ秒）
    start_ms = int(start_sec * 1000) if start_sec is not None else 0
    end_ms = int(end_sec * 1000) if end_sec is not None else len(sound)
    sound = sound[start_ms:end_ms]

    sound = sound.set_frame_rate(16000).set_sample_width(2).set_channels(1)

    # Metal(GPU)が扱える NumPy 配列（-1.0〜1.0）に変換する
    return np.array(sound.get_array_of_samples()).astype(np.float32) / 32768.0


def transcribe(audio_file=INPUT_FILE, start_sec=None, end_sec=None):
    """音声ファイルを文字起こしして、テキスト（str）を返す。

    start_sec, end_sec を指定すると、その範囲だけを文字起こしする。
    """
    import mlx_whisper

    audio_file = Path(audio_file)
    if not audio_file.exists():
        raise FileNotFoundError(f"音声ファイルが見つかりません: {audio_file}（先に録音してください）")
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"whisper モデルが見つかりません: {MODEL_PATH}")

    audio = _load_audio(audio_file, start_sec, end_sec)
    result = mlx_whisper.transcribe(
        audio, path_or_hf_repo=str(MODEL_PATH), language=LANGUAGE
    )
    return result["text"].strip()


try:
    from PySide6.QtCore import QThread, Signal

    class TranscribeThread(QThread):
        """GUI を固めずに文字起こしするためのスレッド。"""

        finished_text = Signal(str)  # 文字起こし成功時: 結果のテキスト
        failed = Signal(str)         # 失敗時: エラーメッセージ

        def __init__(self, audio_file=INPUT_FILE, start_sec=None, end_sec=None, parent=None):
            super().__init__(parent)
            self.audio_file = audio_file
            self.start_sec = start_sec
            self.end_sec = end_sec

        def run(self):
            try:
                text = transcribe(self.audio_file, self.start_sec, self.end_sec)
                self.finished_text.emit(text)
            except Exception as error:
                self.failed.emit(str(error))

except ImportError:
    # PySide6 がない環境でも transcribe() だけは使えるようにする
    pass


def main():
    """単体で動作確認する（録音済みの python-audio-output.wav を文字起こしする）。"""
    print("文字起こしを開始します...")
    try:
        text = transcribe()
        print("文字起こしが完了しました。")
        print(text)
    except Exception as error:
        print(f"エラーが発生しました: {error}")


if __name__ == "__main__":
    main()
