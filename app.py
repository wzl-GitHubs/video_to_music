import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QApplication, QSplitter, QMainWindow, QWidget, \
    QMessageBox
import main
from list_widget import FileBrowser
from typt_widget import AudioFormatSelector
from out_widget import LogWindow
import os
import imageio

imageio.plugins.ffmpeg.FFMPEG_BIN = (
    'D:\\ProgramData\\Anaconda3\\envs\\ChatTTS\\Lib\\site-packages\\imageio_ffmpeg\\binaries\\ffmpeg-win64-v4.2.2.exe')

root_dir = os.path.split(os.path.abspath(__file__))[0]


def create_directory(path, exist_ok=True):
    try:
        os.makedirs(path, exist_ok=exist_ok)
    except FileExistsError:
        print(f"目录 '{path}' 已经存在。")


class MainWindow_Ui(QMainWindow):
    def __init__(self, type_list: list = None, file_path: str = ''):
        super().__init__()
        self.paths = None
        self.type_elected_formats = None
        self.new_path = None
        self.new_paths = None
        self.type_list = type_list
        self.file_path = file_path
        self.V_layout = QVBoxLayout()
        self.H_layout = QHBoxLayout()
        self.V_layout1 = QVBoxLayout()
        self.H_layout1 = QHBoxLayout()
        self.showSelectedButton = QPushButton('转换为选中的格式')
        self.showSelectedButton.setStyleSheet("QPushButton { background-color: green; color: white; }")
        self.clear_button = QPushButton("清空")
        self.clear_button.setStyleSheet("QPushButton { background-color: red; color: white; }")
        self.list_widget = FileBrowser(type_list=self.type_list, file_path=self.file_path)
        self.type_widget = AudioFormatSelector()
        self.out_widget = LogWindow()
        self.center_widget = QWidget()

        self.V_layout1.addWidget(self.out_widget)
        self.H_layout1.addWidget(self.showSelectedButton)
        self.H_layout1.addWidget(self.clear_button)
        self.V_layout1.addLayout(self.H_layout1)
        self.center_widget.setLayout(self.V_layout1)

        self.resize(1300, 850)  # 将窗口大小设置为 800x600 像素

        self.splitter = QSplitter()
        self.splitter.addWidget(self.list_widget)
        self.splitter.addWidget(self.type_widget)
        self.splitter.setStretchFactor(0, 1)  # 第一个 widget 的初始占比
        self.splitter.setStretchFactor(1, 1)  # 第二个 widget 的初始占比
        self.Split_v1 = QSplitter(Qt.Vertical)  # 分割
        self.Split_v1.addWidget(self.splitter)
        self.Split_v1.addWidget(self.center_widget)
        self.setCentralWidget(self.Split_v1)

        self.codecs_dict = {
            "MP3": "libmp3lame",
            "WAV": "pcm_s16le",
            "WMA": "wmav2",
            "AAC": "aac",
            "AIFF": "pcm_s16be",
            "M4A": "aac",
            "OGG": "libvorbis",
            "FLAC": "flac",
            "ALAC": "alac",
            "APE": "ape",  # APE可能需要特定的编解码器支持
            "AMR": "libopencore_amrnb",
            "MIDI": "midi",  # MIDI通常不是一个编码格式
            "MKA": "mka",  # Matroska音频，可能包含多种编码
            "MP2": "mp2",
            "OFR": "ofr",  # OptimFROG
            "RA": "real_288",  # RealAudio
            "RM": "ra144",  # RealMedia音频
            "SHN": "shn",  # 需要特定软件支持
            "TTA": "tta",  # True Audio
            "WV": "wavpack",  # WavPack
            "WEBM": "libvorbis"  # 通常包含Opus或Vorbis音频编码
        }
        # for format_, codec in self.codecs_dict.items():
        #     print(f"格式: {format_}, 编解码器: {codec}")

        self.active_threads = 0  # 跟踪活跃线程数量

        self.showSelectedButton.clicked.connect(self.type_widget.showSelectedFormats)
        self.showSelectedButton.clicked.connect(self.On_showSelectedButton)
        self.list_widget.listview1.doubleClicked.connect(self.list_widget.openDirectory)
        self.list_widget.openFolderButton.clicked.connect(self.list_widget.onOpenFolderButtonClicked)
        self.list_widget.listview1.doubleClicked.connect(self.On_update_info_video)
        self.clear_button.clicked.connect(self.out_widget.clear_logs)

    def On_showSelectedButton(self):
        self.active_threads = 0  # 重置活跃线程计数器
        self.file_path, self.new_path = self.list_widget.file_path, self.list_widget.new_path
        self.type_elected_formats = self.type_widget.type_elected_formats
        print(self.type_elected_formats, self.file_path, self.new_path)

        for type_str in self.type_elected_formats:
            codec = self.codecs_dict.get(type_str)
            try:
                self.new_paths = os.path.splitext(self.new_path)[0] + f".{type_str.lower()}"
                worker = main.Worker_Main(self.file_path, self.new_paths, codec)
                self.out_info = f"\t<转换成功>\n已将{self.file_path}转换为了{self.new_paths}\n"

                # 确保使用 lambda 来传递 worker 到槽函数
                worker.finished.connect(lambda: self.on_thread_finished(worker))
                worker.start()  # 启动线程
                self.out_widget.on_update_End(self.out_info)
                self.active_threads += 1  # 增加活跃线程计数
                worker.wait()  # 因为它会阻塞主线程


            except Exception as e:
                self.out_widget.on_update_End(f'请选择需转换的文件,异常提示信息:\n{e}')

    def on_thread_finished(self, worker):
        # 线程完成时的操作
        worker.deleteLater()  # 确保线程结束后释放资源
        # 更新活跃线程计数
        self.active_threads -= 1
        if self.active_threads == 0:
            self.all_threads_finished()  # 所有线程完成后的操作

    def all_threads_finished(self):
        self.out_widget.on_update_End("----------完成转换------------")

    def On_update_info_video(self):
        self.paths = self.file_path
        try:
            str_path = "您选中的视频所在路径为：" + self.paths
            self.out_widget.on_update_End(str_path)
        except TypeError as e:
            self.out_widget.on_update_End(f'请选择需转换的文件{e}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    type_list = ['*.mp4', '*.avi', '*.mkv', '*.mov', '*.wmv', '*.flv', '*.f4v', '*.webm', '*.m4v',
                 '*.ts', '*.mpeg', '*.mpe', '*.mpg', '*.rm', '*.rmvb', '*.vob', '*.m2ts', '*.dts']
    file_path = "resources"
    file_path = os.path.join(root_dir, file_path)
    create_directory(file_path)
    MainWindow = MainWindow_Ui(type_list=type_list, file_path=file_path)
    MainWindow.show()  # 显示主窗口
    sys.exit(app.exec_())
