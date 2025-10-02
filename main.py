import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog, 
    QSplitter, QFrame, QGroupBox, QFormLayout, QAction, qApp, QMessageBox,
    QLineEdit, QGridLayout, QComboBox, QSlider, QCheckBox, QRadioButton, QButtonGroup, QInputDialog, QColorDialog
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon, QColor
from PyQt5.QtCore import Qt, QSize, QPoint
from PIL import Image, ImageQt, ImageDraw, ImageFont
import glob

class ImageWatermarkTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_list = []  # 存储导入的图片路径
        self.current_image_index = -1  # 当前选中的图片索引
        
        # 水印相关变量
        self.watermark_text = ""
        self.watermark_position = (0.5, 0.5)  # 默认居中位置（相对坐标）
        self.watermark_font_size = 30
        self.watermark_color = "white"
        self.watermark_opacity = 128  # 0-255，默认为半透明
        self.watermark_font = "simhei.ttf"  # 默认字体
        self.watermark_bold = False  # 粗体
        self.watermark_italic = False  # 斜体
        self.watermark_shadow = False  # 阴影
        self.watermark_stroke = False  # 描边
        self.watermark_stroke_width = 1  # 描边宽度
        self.watermark_stroke_color = "black"  # 描边颜色
        
        # 模板相关变量
        self.templates_dir = os.path.join(os.path.expanduser("~"), ".photo_watermark_templates")
        self.settings_file = os.path.join(self.templates_dir, "last_settings.json")
        self.system_fonts = self.get_system_fonts()  # 获取系统字体列表
        self.load_last_settings()
        
        # 水印预设位置（九宫格）
        self.position_presets = {
            '左上': (0.1, 0.1),
            '上中': (0.5, 0.1),
            '右上': (0.9, 0.1),
            '左中': (0.1, 0.5),
            '居中': (0.5, 0.5),
            '右中': (0.9, 0.5),
            '左下': (0.1, 0.9),
            '下中': (0.5, 0.9),
            '右下': (0.9, 0.9)
        }
        
        # 导出相关配置
        self.export_format = "JPEG"  # 默认导出格式
        self.export_quality = 95  # 默认导出质量
        self.use_suffix = True  # 默认使用后缀
        self.suffix_text = "_watermark"  # 默认后缀文本
        self.save_to_same_dir = False  # 默认不保存到原目录
        self.last_export_dir = os.path.expanduser("~")  # 上次导出目录
        
        # 初始化UI
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口标题和大小
        self.setWindowTitle('图片水印工具')
        self.resize(1200, 800)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧图片列表
        self.create_image_list_panel(main_layout)
        
        # 创建中间预览区域
        self.create_preview_panel(main_layout)
        
        # 创建右侧控制面板
        self.create_control_panel(main_layout)
        
        # 设置拖拽功能
        self.setAcceptDrops(True)
    
    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        
        # 导入图片动作
        import_action = QAction('导入图片', self)
        import_action.setShortcut('Ctrl+I')
        import_action.triggered.connect(self.import_images)
        file_menu.addAction(import_action)
        
        # 导出图片动作
        export_action = QAction('导出图片', self)
        export_action.setShortcut('Ctrl+E')
        export_action.triggered.connect(self.export_image)
        export_action.setEnabled(False)  # 初始时禁用
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出动作
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助')
        
        # 关于动作
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_image_list_panel(self, main_layout):
        # 创建左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 创建导入按钮
        import_button = QPushButton('导入图片')
        import_button.clicked.connect(self.import_images)
        left_layout.addWidget(import_button)
        
        # 创建图片列表
        self.image_list_widget = QListWidget()
        self.image_list_widget.setViewMode(QListWidget.IconMode)
        self.image_list_widget.setIconSize(QSize(120, 120))
        self.image_list_widget.setResizeMode(QListWidget.Adjust)
        self.image_list_widget.setMovement(QListWidget.Static)
        self.image_list_widget.itemClicked.connect(self.on_image_item_clicked)
        left_layout.addWidget(self.image_list_widget)
        
        # 添加到主布局
        main_layout.addWidget(left_panel, 1)
    
    def create_preview_panel(self, main_layout):
        # 创建中间预览区域
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        
        # 创建预览标签
        self.preview_label = QLabel('请导入图片')
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet('border: 1px solid #ccc;')
        self.preview_label.setMinimumSize(600, 400)
        center_layout.addWidget(self.preview_label)
        
        # 添加到主布局
        main_layout.addWidget(center_panel, 3)
    
    def create_control_panel(self, main_layout):
        # 创建右侧控制面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # 文件操作组
        file_group = QGroupBox('文件操作')
        file_layout = QVBoxLayout()
        
        self.export_button = QPushButton('导出图片')
        self.export_button.clicked.connect(self.export_image)
        self.export_button.setEnabled(False)  # 初始时禁用
        file_layout.addWidget(self.export_button)
        
        file_group.setLayout(file_layout)
        right_layout.addWidget(file_group)
        
        # 水印设置组
        watermark_group = QGroupBox('水印设置')
        watermark_layout = QFormLayout()
        
        # 模板管理按钮
        template_layout = QHBoxLayout()
        save_template_btn = QPushButton("保存模板")
        save_template_btn.clicked.connect(self.save_template)
        load_template_btn = QPushButton("加载模板")
        load_template_btn.clicked.connect(self.load_template)
        manage_templates_btn = QPushButton("管理模板")
        manage_templates_btn.clicked.connect(self.manage_templates)
        template_layout.addWidget(save_template_btn)
        template_layout.addWidget(load_template_btn)
        template_layout.addWidget(manage_templates_btn)
        watermark_layout.addRow(template_layout)
        
        # 文本输入
        self.watermark_input = QLineEdit()
        self.watermark_input.setPlaceholderText('请输入水印文本')
        self.watermark_input.textChanged.connect(self.on_watermark_text_changed)
        watermark_layout.addRow('水印文本:', self.watermark_input)
        
        # 字体大小
        self.font_size_combo = QComboBox()
        self.font_size_combo.addItems([str(i) for i in range(10, 71, 5)])
        self.font_size_combo.setCurrentText(str(self.watermark_font_size))
        self.font_size_combo.currentTextChanged.connect(self.on_font_size_changed)
        watermark_layout.addRow('字体大小:', self.font_size_combo)
        
        # 透明度调节
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 255)
        self.opacity_slider.setValue(self.watermark_opacity)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(51)
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)
        watermark_layout.addRow('透明度:', self.opacity_slider)
        
        # 预设位置选择
        position_group = QGroupBox('预设位置')
        position_layout = QGridLayout()
        
        # 创建九宫格位置按钮
        positions = list(self.position_presets.keys())
        grid_positions = [(0,0), (0,1), (0,2),
                          (1,0), (1,1), (1,2),
                          (2,0), (2,1), (2,2)]
        
        self.position_buttons = {}
        for pos_text, (row, col) in zip(positions, grid_positions):
            button = QPushButton(pos_text)
            button.setFixedSize(50, 30)
            button.clicked.connect(lambda checked, p=pos_text: self.set_watermark_position(p))
            self.position_buttons[pos_text] = button
            position_layout.addWidget(button, row, col)
        
        position_group.setLayout(position_layout)
        watermark_layout.addRow(position_group)
        
        # 添加应用水印按钮
        self.apply_watermark_button = QPushButton('应用水印')
        self.apply_watermark_button.clicked.connect(self.apply_watermark_to_preview)
        watermark_layout.addRow(self.apply_watermark_button)
        
        watermark_group.setLayout(watermark_layout)
        right_layout.addWidget(watermark_group)
        
        # 字体选择
        font_layout = QHBoxLayout()
        self.font_combo = QComboBox()
        # 添加一些常用字体
        common_fonts = ["simhei.ttf", "simsun.ttc", "msyh.ttc", "Arial.ttf", "Times.ttf", "Calibri.ttf"]
        self.font_combo.addItems([os.path.splitext(font)[0] for font in common_fonts])
        self.font_combo.setCurrentText("simhei")
        self.font_combo.currentTextChanged.connect(self.on_font_changed)
        font_layout.addWidget(self.font_combo)
        watermark_layout.addRow('字体:', font_layout)

        # 样式设置
        style_layout = QHBoxLayout()
        self.bold_checkbox = QCheckBox('粗体')
        self.bold_checkbox.stateChanged.connect(self.on_bold_toggled)
        self.italic_checkbox = QCheckBox('斜体')
        self.italic_checkbox.stateChanged.connect(self.on_italic_toggled)
        style_layout.addWidget(self.bold_checkbox)
        style_layout.addWidget(self.italic_checkbox)
        watermark_layout.addRow('字体样式:', style_layout)

        # 颜色选择
        color_layout = QHBoxLayout()
        self.color_button = QPushButton('选择颜色')
        self.color_button.setStyleSheet(f"background-color: {self.watermark_color}")
        self.color_button.clicked.connect(self.choose_color)
        self.color_label = QLabel('白色')
        color_layout.addWidget(self.color_button)
        color_layout.addWidget(self.color_label)
        watermark_layout.addRow('字体颜色:', color_layout)

        # 特效设置
        effect_group = QGroupBox('文本特效')
        effect_layout = QVBoxLayout()
        
        self.shadow_checkbox = QCheckBox('添加阴影')
        self.shadow_checkbox.stateChanged.connect(self.on_shadow_toggled)
        effect_layout.addWidget(self.shadow_checkbox)
        
        self.stroke_checkbox = QCheckBox('添加描边')
        self.stroke_checkbox.stateChanged.connect(self.on_stroke_toggled)
        effect_layout.addWidget(self.stroke_checkbox)
        
        stroke_width_layout = QHBoxLayout()
        stroke_width_layout.addWidget(QLabel('描边宽度:'))
        self.stroke_width_spin = QSlider(Qt.Horizontal)
        self.stroke_width_spin.setRange(1, 5)
        self.stroke_width_spin.setValue(self.watermark_stroke_width)
        self.stroke_width_spin.valueChanged.connect(self.on_stroke_width_changed)
        self.stroke_width_label = QLabel(str(self.watermark_stroke_width))
        stroke_width_layout.addWidget(self.stroke_width_spin)
        stroke_width_layout.addWidget(self.stroke_width_label)
        effect_layout.addLayout(stroke_width_layout)
        
        stroke_color_layout = QHBoxLayout()
        stroke_color_layout.addWidget(QLabel('描边颜色:'))
        self.stroke_color_button = QPushButton('选择颜色')
        self.stroke_color_button.setStyleSheet(f"background-color: {self.watermark_stroke_color}")
        self.stroke_color_button.clicked.connect(self.choose_stroke_color)
        self.stroke_color_label = QLabel('黑色')
        stroke_color_layout.addWidget(self.stroke_color_button)
        stroke_color_layout.addWidget(self.stroke_color_label)
        effect_layout.addLayout(stroke_color_layout)
        
        effect_group.setLayout(effect_layout)
        watermark_layout.addRow(effect_group)

        # 导出设置组
        export_group = QGroupBox('导出设置')
        export_layout = QFormLayout()
        
        # 导出格式选择
        self.format_group = QButtonGroup()
        self.jpeg_radio = QRadioButton('JPEG')
        self.png_radio = QRadioButton('PNG')
        self.format_group.addButton(self.jpeg_radio)
        self.format_group.addButton(self.png_radio)
        self.jpeg_radio.setChecked(True)
        self.jpeg_radio.toggled.connect(self.on_format_changed)
        self.png_radio.toggled.connect(self.on_format_changed)
        
        format_layout = QHBoxLayout()
        format_layout.addWidget(self.jpeg_radio)
        format_layout.addWidget(self.png_radio)
        export_layout.addRow('导出格式:', format_layout)
        
        # 导出质量滑块
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(self.export_quality)
        self.quality_slider.setTickPosition(QSlider.TicksBelow)
        self.quality_slider.setTickInterval(20)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        export_layout.addRow('导出质量:', self.quality_slider)
        
        # 导出质量显示
        self.quality_label = QLabel(f'{self.export_quality}%')
        export_layout.addRow('', self.quality_label)
        
        # 使用后缀复选框
        self.suffix_checkbox = QCheckBox('添加后缀')
        self.suffix_checkbox.setChecked(self.use_suffix)
        self.suffix_checkbox.stateChanged.connect(self.on_suffix_toggled)
        export_layout.addRow('', self.suffix_checkbox)
        
        # 后缀文本输入
        self.suffix_edit = QLineEdit(self.suffix_text)
        self.suffix_edit.textChanged.connect(self.on_suffix_text_changed)
        self.suffix_edit.setEnabled(self.use_suffix)
        export_layout.addRow('后缀文本:', self.suffix_edit)
        
        # 保存到原目录复选框（默认禁用，有警告提示）
        self.save_same_dir_checkbox = QCheckBox('保存到原目录')
        self.save_same_dir_checkbox.setChecked(self.save_to_same_dir)
        self.save_same_dir_checkbox.stateChanged.connect(self.on_save_dir_toggled)
        export_layout.addRow('', self.save_same_dir_checkbox)
        
        # 警告提示
        warning_label = QLabel('<font color="red">警告：保存到原目录可能会覆盖原图</font>')
        warning_label.setWordWrap(True)
        export_layout.addRow('', warning_label)
        
        export_group.setLayout(export_layout)
        right_layout.addWidget(export_group)
        
        # 连接导出设置控件的信号到槽函数
        self.format_group.buttonClicked.connect(self.on_format_changed)
        self.quality_slider.valueChanged.connect(self.on_quality_changed)
        self.suffix_checkbox.stateChanged.connect(self.on_suffix_toggled)
        self.suffix_edit.textChanged.connect(self.on_suffix_text_changed)
        self.save_same_dir_checkbox.stateChanged.connect(self.on_save_dir_toggled)
        
        # 填充空间
        right_layout.addStretch()
        
        # 添加到主布局
        main_layout.addWidget(right_panel, 1)
    
    def import_images(self):
        # 创建导入选择对话框
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        
        # 显示选项对话框：选择文件还是文件夹
        choice = QMessageBox.question(
            self, '导入选项', 
            '请选择导入方式：\n\n' 
            '• 选择文件 - 可以选择多个图片文件\n' 
            '• 选择文件夹 - 导入整个文件夹中的所有图片',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if choice == QMessageBox.Cancel:
            return
        
        file_paths = []
        
        if choice == QMessageBox.Yes:  # 选择文件
            file_paths, _ = QFileDialog.getOpenFileNames(
                self, '选择图片', '', '图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)'
            )
        else:  # 选择文件夹
            dir_path = QFileDialog.getExistingDirectory(
                self, '选择文件夹', '', options
            )
            
            if dir_path:
                # 遍历文件夹中的所有图片文件
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        ext = os.path.splitext(file)[1].lower()
                        if ext in ['.jpg', '.jpeg', '.png']:
                            file_paths.append(os.path.join(root, file))
        
        if file_paths:
            self.add_images(file_paths)
    
    def add_images(self, file_paths):
        for file_path in file_paths:
            # 检查文件格式
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png']:
                QMessageBox.warning(self, '格式不支持', f'{file_path} 不是支持的图片格式')
                continue
            
            # 添加到图片列表
            if file_path not in self.image_list:
                self.image_list.append(file_path)
                
                # 创建列表项
                item = QListWidgetItem()
                
                # 加载图片并创建缩略图
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    item.setIcon(QIcon(pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                    
                    # 获取文件名作为显示文本
                    file_name = os.path.basename(file_path)
                    item.setText(file_name)
                    item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                    
                    # 添加到列表
                    self.image_list_widget.addItem(item)
        
        # 如果这是第一次导入图片，自动选中第一张
        if self.image_list and self.current_image_index == -1:
            self.image_list_widget.setCurrentRow(0)
            self.on_image_item_clicked(self.image_list_widget.item(0))
        
        # 启用导出按钮
        self.export_button.setEnabled(True)
        
        # 启用菜单栏中的导出动作
        for action in self.menuBar().actions():
            if action.text() == '文件':
                for sub_action in action.menu().actions():
                    if sub_action.text() == '导出图片':
                        sub_action.setEnabled(True)
                        break
                break
    
    def on_image_item_clicked(self, item):
        # 获取点击项的索引
        index = self.image_list_widget.row(item)
        if 0 <= index < len(self.image_list):
            self.current_image_index = index
            self.update_preview()
    
    def update_preview(self):
        if 0 <= self.current_image_index < len(self.image_list):
            # 获取当前图片路径
            current_image_path = self.image_list[self.current_image_index]
            
            # 加载图片
            image = Image.open(current_image_path)
            
            # 如果有水印文本，应用水印
            if self.watermark_text:
                image = self.add_watermark_to_image(image)
            
            # 转换为QPixmap用于显示
            q_image = self.pil_to_qimage(image)
            pixmap = QPixmap.fromImage(q_image)
            
            if not pixmap.isNull():
                # 调整图片大小以适应预览窗口
                preview_size = self.preview_label.size()
                scaled_pixmap = pixmap.scaled(
                    preview_size.width() - 20, preview_size.height() - 20, 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                
                # 更新预览标签
                self.preview_label.setPixmap(scaled_pixmap)
                
                # 启用导出按钮
                self.export_button.setEnabled(True)
                for action in self.menuBar().actions():
                    if action.text() == '文件':
                        for sub_action in action.menu().actions():
                            if sub_action.text() == '导出图片':
                                sub_action.setEnabled(True)
                                break
                        break
            else:
                # 显示错误信息
                self.preview_label.setText('无法加载图片')
        else:
            self.preview_label.setText('请导入图片')
            self.export_button.setEnabled(False)
            for action in self.menuBar().actions():
                if action.text() == '文件':
                    for sub_action in action.menu().actions():
                        if sub_action.text() == '导出图片':
                            sub_action.setEnabled(False)
                            break
                    break
                    
    def pil_to_qimage(self, pil_image):
        """将PIL Image转换为QImage，确保颜色显示一致"""
        # 确保图像模式正确
        if pil_image.mode != "RGBA":
            pil_image = pil_image.convert("RGBA")
        
        # 获取图像数据
        width, height = pil_image.size
        
        # PIL的RGBA格式是RGBA，但QImage需要的是BGRA
        # 创建一个新的字节数组存储BGRA数据
        bgra_data = bytearray(width * height * 4)
        pixels = pil_image.load()
        
        # 优化颜色通道转换，确保颜色一致性
        for y in range(height):
            for x in range(width):
                try:
                    # 获取像素的RGBA值
                    r, g, b, a = pixels[x, y]
                    # 确保值在有效范围内
                    r = max(0, min(255, r))
                    g = max(0, min(255, g))
                    b = max(0, min(255, b))
                    a = max(0, min(255, a))
                    
                    # 转换为BGRA格式
                    index = (y * width + x) * 4
                    bgra_data[index] = b  # 蓝色
                    bgra_data[index + 1] = g  # 绿色
                    bgra_data[index + 2] = r  # 红色
                    bgra_data[index + 3] = a  # 透明度
                except Exception:
                    # 处理可能的像素访问错误
                    index = (y * width + x) * 4
                    bgra_data[index] = 255  # 蓝色
                    bgra_data[index + 1] = 255  # 绿色
                    bgra_data[index + 2] = 255  # 红色
                    bgra_data[index + 3] = 255  # 透明度
        
        # 创建QImage，使用Format_RGBA8888格式确保颜色通道正确
        q_image = QImage(bgra_data, width, height, width * 4, QImage.Format_RGBA8888)
        
        # 设置设备像素比以确保在高DPI显示器上正确显示
        q_image.setDevicePixelRatio(1.0)
        
        return q_image
        
    def get_system_fonts(self):
        """获取系统已安装的字体列表"""
        fonts = []
        # 尝试从常见的字体目录获取字体
        font_dirs = [
            r'C:\Windows\Fonts',
            r'/usr/share/fonts',
            r'/Library/Fonts',
            r'~/Library/Fonts'
        ]
        
        for font_dir in font_dirs:
            font_dir = os.path.expanduser(font_dir)
            if os.path.exists(font_dir):
                # 查找常见的字体文件
                for ext in ['ttf', 'ttc', 'otf']:
                    fonts.extend(glob.glob(os.path.join(font_dir, f'*.{ext}')))
        
        # 返回字体文件名列表
        return [os.path.basename(font) for font in fonts]
    
    def add_watermark_to_image(self, image):
        """向图片添加文本水印"""
        # 创建可绘制对象
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 获取图片尺寸
        width, height = image.size
        
        # 尝试加载字体，失败则使用默认字体
        try:
            # 尝试使用选择的字体
            font_path = self.watermark_font
            found = False
            
            # 特殊处理常见字体，确保正确加载
            common_fonts = {
                'times': 'times.ttf',
                'times new roman': 'times.ttf',
                'calibri': 'calibri.ttf',
                'arial': 'arial.ttf',
                'courier': 'cour.ttf',
                'verdana': 'verdana.ttf',
                'tahoma': 'tahoma.ttf',
                'comic sans ms': 'comic.ttf',
                'impact': 'impact.ttf',
                'georgia': 'georgia.ttf',
                'palatino': 'pala.ttf',
                'bookman': 'bookman.ttf',
                'century': 'century.ttf'
            }
            
            # 检查是否有完整路径，如果没有则尝试在系统字体中查找
            if not os.path.isfile(font_path):
                # 先尝试在系统字体目录中直接查找
                system_font_dir = r'C:\Windows\Fonts'
                if os.path.exists(system_font_dir):
                    # 转换为小写以进行不区分大小写的匹配
                    font_lower = font_path.lower()
                    
                    # 首先检查是否是常见字体
                    for common_name, common_filename in common_fonts.items():
                        if common_name in font_lower:
                            candidate = os.path.join(system_font_dir, common_filename)
                            if os.path.isfile(candidate):
                                font_path = candidate
                                found = True
                                break
                    
                    # 如果不是常见字体或常见字体文件不存在，尝试更多变体
                    if not found:
                        # 对于常见字体如Times、Calibri，先尝试直接匹配文件名变体
                        font_variants = [
                            font_path,
                            font_path.lower(),
                            font_path.replace(' ', ''),
                            font_path.replace(' ', '-'),
                            font_path.split(' ')[0],  # 只取第一个单词，如'Times New Roman' -> 'Times'
                            font_path.split('-')[0],  # 只取第一个单词，如'Times-New-Roman' -> 'Times'
                            # 添加更多可能的字体名称变体
                            font_path.replace('&', 'and'),  # 将 '&' 替换为 'and'
                            font_path.replace('+', 'plus')   # 将 '+' 替换为 'plus'
                        ]
                        
                        # 尝试添加扩展名
                        for base_name in font_variants:
                            # 尝试常见的字体文件名格式
                            formats = [
                                f'{base_name}{{ext}}',
                                f'{base_name.capitalize()}{{ext}}',
                                f'{base_name.replace(" ", "")}{{ext}}',
                                f'{base_name.upper()}{{ext}}',
                                f'{base_name.lower()}{{ext}}',
                                f'{base_name.split()[-1]}{{ext}}'  # 只取最后一个单词
                            ]
                            
                            for fmt in formats:
                                for ext in ['.ttf', '.ttc', '.otf', '.fon', '.ttx']:
                                    # 尝试直接匹配
                                    candidate = os.path.join(system_font_dir, fmt.format(ext=ext))
                                    if os.path.isfile(candidate):
                                        font_path = candidate
                                        found = True
                                        break
                                    # 尝试在文件名中间添加变体标记
                                    candidate = os.path.join(system_font_dir, fmt.format(ext='') + '_' + ext.lstrip('.'))
                                    if os.path.isfile(candidate):
                                        font_path = candidate
                                        found = True
                                        break
                                if found:
                                    break
                            if found:
                                break
                        
                        # 如果没找到，尝试更宽松的匹配方式
                        if not found:
                            for system_font in self.system_fonts:
                                font_name = os.path.splitext(system_font)[0].lower()
                                font_base = font_path.lower()
                                # 允许部分匹配和变体匹配
                                if any(keyword in font_name for keyword in font_base.split()) or \
                                   any(keyword.replace(' ', '') in font_name.replace(' ', '') for keyword in font_base.split()):
                                    font_path = os.path.join(system_font_dir, system_font)
                                    found = True
                                    break
            
            # 尝试加载带有粗体和斜体样式的字体
            # 先尝试获取字体的基本名称
            font_base_name = os.path.splitext(os.path.basename(font_path))[0]
            system_font_dir = r'C:\Windows\Fonts'
            
            # 构建可能的字体变体名称，增加更多可能的格式和常见字体的特殊处理
            font_variants = []
            if self.watermark_bold and self.watermark_italic:
                # 粗斜体 - 增加更多常见的变体格式
                font_variants.extend([
                    f"{font_base_name} Bold Italic",
                    f"{font_base_name} BoldIt",
                    f"{font_base_name} BI",
                    f"{font_base_name}-BoldItalic",
                    f"{font_base_name}BdIt",
                    f"{font_base_name} BoldOblique",
                    f"{font_base_name}BO",
                    f"{font_base_name}_Bold_Italic",
                    f"{font_base_name}bi",  # 简洁格式
                    f"{font_base_name}bol",  # 可能的缩写
                    f"{font_base_name}boldital",  # 可能的缩写
                    f"{font_base_name}bold_italic",  # 带下划线
                    f"{font_base_name}.bold-italic"  # 带点号
                ])
            elif self.watermark_bold:
                # 粗体 - 增加更多常见的变体格式
                font_variants.extend([
                    f"{font_base_name} Bold",
                    f"{font_base_name}-Bold",
                    f"{font_base_name}Bd",
                    f"{font_base_name}Bold",
                    f"{font_base_name}_Bold",
                    f"{font_base_name}bol",  # 可能的缩写
                    f"{font_base_name}bold",  # 小写
                    f"{font_base_name}_bold",  # 带下划线
                    f"{font_base_name}.bold"  # 带点号
                ])
            elif self.watermark_italic:
                # 斜体 - 增加更多常见的变体格式
                font_variants.extend([
                    f"{font_base_name} Italic",
                    f"{font_base_name}-Italic",
                    f"{font_base_name}It",
                    f"{font_base_name}Oblique",
                    f"{font_base_name}_Italic",
                    f"{font_base_name}ita",  # 可能的缩写
                    f"{font_base_name}italic",  # 小写
                    f"{font_base_name}_italic",  # 带下划线
                    f"{font_base_name}.italic"  # 带点号
                ])
            
            # 尝试加载有样式的字体 - 增强实现
            styled_font = None
            if font_variants and os.path.exists(system_font_dir):
                for variant in font_variants:
                    for ext in ['.ttf', '.ttc', '.otf', '.fon', '.ttx']:
                        # 尝试直接匹配
                        variant_path = os.path.join(system_font_dir, variant + ext)
                        if os.path.isfile(variant_path):
                            try:
                                styled_font = ImageFont.truetype(variant_path, self.watermark_font_size)
                                break
                            except:
                                continue
                        # 尝试小写版本
                        variant_lower = variant.lower()
                        variant_path = os.path.join(system_font_dir, variant_lower + ext)
                        if os.path.isfile(variant_path):
                            try:
                                styled_font = ImageFont.truetype(variant_path, self.watermark_font_size)
                                break
                            except:
                                continue
                        # 尝试大写版本
                        variant_upper = variant.upper()
                        variant_path = os.path.join(system_font_dir, variant_upper + ext)
                        if os.path.isfile(variant_path):
                            try:
                                styled_font = ImageFont.truetype(variant_path, self.watermark_font_size)
                                break
                            except:
                                continue
                        # 尝试无空格版本
                        variant_nospace = variant.replace(' ', '')
                        variant_path = os.path.join(system_font_dir, variant_nospace + ext)
                        if os.path.isfile(variant_path):
                            try:
                                styled_font = ImageFont.truetype(variant_path, self.watermark_font_size)
                                break
                            except:
                                continue
                    if styled_font:
                        break
            
            # 如果找不到有样式的字体，尝试备选方案：
            # 1. 尝试使用PIL的字体样式支持
            if not styled_font and (self.watermark_bold or self.watermark_italic):
                try:
                    # 创建基础字体
                    base_font = ImageFont.truetype(font_path, self.watermark_font_size)
                    # 注意：PIL实际上不支持动态添加粗体/斜体样式，所以这里只是保留尝试逻辑
                    styled_font = base_font
                except:
                    pass
            
            # 如果找不到有样式的字体，则使用原始字体
            font = styled_font if styled_font else ImageFont.truetype(font_path, self.watermark_font_size)
            
        except (IOError, OSError):
            # 尝试使用更通用的字体加载方法 - 增加更多备选方案和常见字体特殊处理
            try:
                # 特殊处理常见字体
                font_lower = self.watermark_font.lower()
                for common_name, common_filename in common_fonts.items():
                    if common_name in font_lower:
                        # 尝试使用系统字体目录
                        system_font_dir = r'C:\Windows\Fonts'
                        if os.path.exists(system_font_dir):
                            candidate = os.path.join(system_font_dir, common_filename)
                            if os.path.isfile(candidate):
                                font = ImageFont.truetype(candidate, self.watermark_font_size)
                                break
                else:
                    # 尝试使用PIL的字体查找功能
                    font = ImageFont.truetype(self.watermark_font, self.watermark_font_size)
            except:
                try:
                    # 尝试去除字体名称中的空格
                    simplified_font = self.watermark_font.replace(' ', '')
                    font = ImageFont.truetype(simplified_font, self.watermark_font_size)
                except:
                    try:
                        # 尝试使用字体名称的一部分
                        font_parts = self.watermark_font.split(' ')
                        for i in range(1, len(font_parts) + 1):
                            try:
                                partial_font = ' '.join(font_parts[:i])
                                font = ImageFont.truetype(partial_font, self.watermark_font_size)
                                break
                            except:
                                continue
                        else:
                            raise Exception("Partial font not found")
                    except:
                        try:
                            # 尝试使用字体名称的大写形式
                            font = ImageFont.truetype(self.watermark_font.upper(), self.watermark_font_size)
                        except:
                            try:
                                # 尝试使用字体名称的小写形式
                                font = ImageFont.truetype(self.watermark_font.lower(), self.watermark_font_size)
                            except:
                                # 最后尝试使用默认字体
                                font = ImageFont.load_default()
        
        # 计算文本尺寸
        try:
            # 兼容Pillow 9.0+的API变化
            bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # 旧版Pillow
            text_width, text_height = draw.textsize(self.watermark_text, font=font)
        
        # 计算水印位置
        pos_x = int(self.watermark_position[0] * width - text_width / 2)
        pos_y = int(self.watermark_position[1] * height - text_height / 2)
        
        # 确保位置在图片范围内
        pos_x = max(0, min(pos_x, width - text_width))
        pos_y = max(0, min(pos_y, height - text_height))
        
        # 将颜色名称转换为RGB值
        color_rgb = self.get_rgb_from_color(self.watermark_color)
        stroke_rgb = self.get_rgb_from_color(self.watermark_stroke_color)
        
        # 构建带透明度的颜色
        fill_color = (*color_rgb, self.watermark_opacity)
        
        # 添加特效
        if self.watermark_shadow:
            # 添加阴影
            shadow_offset = 2
            shadow_color = (0, 0, 0, int(self.watermark_opacity * 0.5))
            draw.text((pos_x + shadow_offset, pos_y + shadow_offset), self.watermark_text, 
                      fill=shadow_color, font=font)
        
        if self.watermark_stroke:
            # 添加描边
            for x_offset in range(-self.watermark_stroke_width, self.watermark_stroke_width + 1):
                for y_offset in range(-self.watermark_stroke_width, self.watermark_stroke_width + 1):
                    if x_offset != 0 or y_offset != 0:
                        draw.text((pos_x + x_offset, pos_y + y_offset), self.watermark_text, 
                                  fill=(*stroke_rgb, self.watermark_opacity), font=font)
        
        # 添加水印文本
        draw.text((pos_x, pos_y), self.watermark_text, fill=fill_color, font=font)
        
        return image
    
    def get_rgb_from_color(self, color):
        """将颜色名称或代码转换为RGB值，确保颜色一致性"""
        if isinstance(color, str):
            # 如果是颜色名称，使用QColor转换
            q_color = QColor(color)
            # 确保颜色值有效
            if q_color.isValid():
                return (q_color.red(), q_color.green(), q_color.blue())
            else:
                # 尝试处理常见的十六进制格式
                if color.startswith('#'):
                    try:
                        # 处理 #RGB 格式
                        if len(color) == 4:
                            r = int(color[1] * 2, 16)
                            g = int(color[2] * 2, 16)
                            b = int(color[3] * 2, 16)
                            return (r, g, b)
                        # 处理 #RRGGBB 格式
                        elif len(color) == 7:
                            r = int(color[1:3], 16)
                            g = int(color[3:5], 16)
                            b = int(color[5:7], 16)
                            return (r, g, b)
                    except ValueError:
                        pass
                # 默认返回白色
                return (255, 255, 255)
        elif isinstance(color, tuple):
            # 确保RGB值在有效范围内
            if len(color) == 3:
                return tuple(max(0, min(255, int(c))) for c in color)
            elif len(color) == 4:
                # 忽略alpha通道，只返回RGB值
                return tuple(max(0, min(255, int(c))) for c in color[:3])
        # 默认返回白色
        return (255, 255, 255)
        
    def on_watermark_text_changed(self, text):
        """水印文本变化时更新"""
        self.watermark_text = text
        self.update_preview()
        
    def on_font_size_changed(self, size_str):
        """字体大小变化时更新"""
        try:
            self.watermark_font_size = int(size_str)
            self.update_preview()
            self.save_current_settings()
        except ValueError:
            pass
        
    def on_opacity_changed(self, value):
        """透明度变化时更新"""
        self.watermark_opacity = value
        self.update_preview()
        self.save_current_settings()
        
    def on_font_changed(self, font_name):
        """字体变化时更新"""
        self.watermark_font = font_name
        self.update_preview()
        self.save_current_settings()
        
    def on_bold_toggled(self, state):
        """粗体设置变化时更新"""
        self.watermark_bold = (state == Qt.Checked)
        self.update_preview()
        self.save_current_settings()
        
    def on_italic_toggled(self, state):
        """斜体设置变化时更新"""
        self.watermark_italic = (state == Qt.Checked)
        self.update_preview()
        self.save_current_settings()
        
    def choose_color(self):
        """选择字体颜色"""
        color = QColorDialog.getColor(QColor(self.watermark_color), self, "选择字体颜色")
        if color.isValid():
            self.watermark_color = color.name()
            self.color_button.setStyleSheet(f"background-color: {self.watermark_color}")
            self.color_label.setText(color.name())
            self.update_preview()
            self.save_current_settings()
            
    def choose_stroke_color(self):
        """选择描边颜色"""
        color = QColorDialog.getColor(QColor(self.watermark_stroke_color), self, "选择描边颜色")
        if color.isValid():
            self.watermark_stroke_color = color.name()
            self.stroke_color_button.setStyleSheet(f"background-color: {self.watermark_stroke_color}")
            self.stroke_color_label.setText(color.name())
            self.update_preview()
            self.save_current_settings()
            
    def on_shadow_toggled(self, state):
        """阴影设置变化时更新"""
        self.watermark_shadow = (state == Qt.Checked)
        self.update_preview()
        self.save_current_settings()
        
    def on_stroke_toggled(self, state):
        """描边设置变化时更新"""
        self.watermark_stroke = (state == Qt.Checked)
        self.update_preview()
        self.save_current_settings()
        
    def on_stroke_width_changed(self, value):
        """描边宽度变化时更新"""
        self.watermark_stroke_width = value
        self.stroke_width_label.setText(str(value))
        self.update_preview()
        self.save_current_settings()
        
    def set_watermark_position(self, position_name):
        """设置水印预设位置"""
        if position_name in self.position_presets:
            self.watermark_position = self.position_presets[position_name]
            self.update_preview()
            
            # 高亮选中的位置按钮
            for name, button in self.position_buttons.items():
                if name == position_name:
                    button.setStyleSheet("background-color: #4CAF50; color: white;")
                else:
                    button.setStyleSheet("")
        
    def apply_watermark_to_preview(self):
        """应用水印到预览"""
        self.update_preview()
        
    def on_format_changed(self):
        """导出格式变化时更新"""
        if self.jpeg_radio.isChecked():
            self.export_format = "JPEG"
        elif self.png_radio.isChecked():
            self.export_format = "PNG"
    
    def on_quality_changed(self, value):
        """导出质量变化时更新"""
        self.export_quality = value
        self.quality_label.setText(f'{value}%')
    
    def on_suffix_toggled(self, state):
        """是否使用后缀变化时更新"""
        self.use_suffix = (state == Qt.Checked)
        self.suffix_edit.setEnabled(self.use_suffix)
    
    def on_suffix_text_changed(self, text):
        """后缀文本变化时更新"""
        self.suffix_text = text
        self.save_current_settings()
        
    def on_save_dir_toggled(self, state):
        """保存目录选项变化时更新"""
        old_state = self.save_to_same_dir
        self.save_to_same_dir = (state == Qt.Checked)
        self.save_current_settings()
        
        # 如果用户选择保存到原目录，显示警告
        if self.save_to_same_dir and not old_state:
            reply = QMessageBox.warning(
                self, 
                '警告', 
                '保存到原目录可能会覆盖原图，是否继续？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self.save_same_dir_checkbox.setChecked(False)
                self.save_to_same_dir = False
                self.save_current_settings()
    
    def generate_output_filename(self, original_path):
        """生成输出文件名"""
        dir_path, file_name = os.path.split(original_path)
        base_name, ext = os.path.splitext(file_name)
        
        # 如果使用后缀，添加后缀
        if self.use_suffix:
            output_name = f"{base_name}{self.suffix_text}"
        else:
            output_name = base_name
        
        # 根据导出格式设置扩展名
        if self.export_format == "JPEG":
            output_ext = ".jpg"
        else:
            output_ext = ".png"
        
        # 根据保存选项确定保存目录
        if self.save_to_same_dir:
            save_dir = dir_path
        else:
            save_dir = self.last_export_dir
        
        return os.path.join(save_dir, output_name + output_ext)
    
    def export_image(self):
        """导出图片功能"""
        if self.current_image_index < 0 or not self.image_list:
            QMessageBox.warning(self, '错误', '请先导入图片')
            return
        
        try:
            # 获取当前图片路径
            current_image_path = self.image_list[self.current_image_index]
            
            # 生成默认保存路径
            default_save_path = self.generate_output_filename(current_image_path)
            
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                '保存图片', 
                default_save_path,
                'JPEG文件 (*.jpg);;PNG文件 (*.png);;所有文件 (*)'
            )
            
            if file_path:
                # 更新上次导出目录
                self.last_export_dir = os.path.dirname(file_path)
                
                # 加载原图
                image = Image.open(current_image_path)
                
                # 应用水印
                if self.watermark_text:
                    image = self.add_watermark_to_image(image)
                
                # 保存图片
                if self.export_format == "JPEG":
                    # 确保图片模式兼容JPEG
                    if image.mode == 'RGBA':
                        background = Image.new('RGB', image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[3])  # 3 is the alpha channel
                        image = background
                    image.save(file_path, 'JPEG', quality=self.export_quality)
                else:
                    image.save(file_path, 'PNG')
                
                # 显示成功消息
                QMessageBox.information(self, '成功', f'图片已成功保存到：\n{file_path}')
        except Exception as e:
            # 显示错误消息
            QMessageBox.critical(self, '错误', f'导出图片时出错：\n{str(e)}')
    
    def show_about(self):
        QMessageBox.about(self, '关于', '图片水印工具 v1.0\n\n一款用于为图片添加自定义文本水印的工具。')
    
    # 拖拽功能实现
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        file_paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_images(file_paths)
    
    # 调整窗口大小时更新预览
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if 0 <= self.current_image_index < len(self.image_list):
            self.update_preview()
            
    def save_current_settings(self):
        """保存当前设置到文件"""
        try:
            # 确保模板目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 准备设置数据
            settings = {
                "watermark_text": self.watermark_text,
                "watermark_position": self.watermark_position,
                "watermark_font_size": self.watermark_font_size,
                "watermark_opacity": self.watermark_opacity,
                "watermark_font": self.watermark_font,
                "watermark_bold": self.watermark_bold,
                "watermark_italic": self.watermark_italic,
                "watermark_color": self.watermark_color,
                "watermark_shadow": self.watermark_shadow,
                "watermark_stroke": self.watermark_stroke,
                "watermark_stroke_width": self.watermark_stroke_width,
                "watermark_stroke_color": self.watermark_stroke_color,
                "export_format": self.export_format,
                "export_quality": self.export_quality,
                "use_suffix": self.use_suffix,
                "suffix_text": self.suffix_text,
                "save_to_same_dir": self.save_to_same_dir,
                "last_export_dir": self.last_export_dir
            }
            
            # 保存到文件
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置时出错: {e}")
            
    def load_last_settings(self):
        """加载上次保存的设置"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 恢复设置
                if "watermark_text" in settings:
                    self.watermark_text = settings["watermark_text"]
                    if hasattr(self, 'watermark_input'):
                        self.watermark_input.setText(self.watermark_text)
                
                if "watermark_position" in settings:
                    self.watermark_position = tuple(settings["watermark_position"])
                
                if "watermark_font_size" in settings:
                    self.watermark_font_size = settings["watermark_font_size"]
                    if hasattr(self, 'font_size_combo'):
                        size_str = str(self.watermark_font_size)
                        index = self.font_size_combo.findText(size_str)
                        if index >= 0:
                            self.font_size_combo.setCurrentIndex(index)
                
                if "watermark_opacity" in settings:
                    self.watermark_opacity = settings["watermark_opacity"]
                    if hasattr(self, 'opacity_slider'):
                        self.opacity_slider.setValue(self.watermark_opacity)
                        
                if "watermark_font" in settings:
                    self.watermark_font = settings["watermark_font"]
                    if hasattr(self, 'font_combo'):
                        index = self.font_combo.findText(self.watermark_font)
                        if index >= 0:
                            self.font_combo.setCurrentIndex(index)
                
                if "watermark_bold" in settings:
                    self.watermark_bold = settings["watermark_bold"]
                    if hasattr(self, 'bold_checkbox'):
                        self.bold_checkbox.setChecked(self.watermark_bold)
                
                if "watermark_italic" in settings:
                    self.watermark_italic = settings["watermark_italic"]
                    if hasattr(self, 'italic_checkbox'):
                        self.italic_checkbox.setChecked(self.watermark_italic)
                
                if "watermark_color" in settings:
                    self.watermark_color = settings["watermark_color"]
                    if hasattr(self, 'color_button') and hasattr(self, 'color_label'):
                        self.color_button.setStyleSheet(f"background-color: {self.watermark_color}")
                        self.color_label.setText(self.watermark_color)
                
                if "watermark_shadow" in settings:
                    self.watermark_shadow = settings["watermark_shadow"]
                    if hasattr(self, 'shadow_checkbox'):
                        self.shadow_checkbox.setChecked(self.watermark_shadow)
                
                if "watermark_stroke" in settings:
                    self.watermark_stroke = settings["watermark_stroke"]
                    if hasattr(self, 'stroke_checkbox'):
                        self.stroke_checkbox.setChecked(self.watermark_stroke)
                
                if "watermark_stroke_width" in settings:
                    self.watermark_stroke_width = settings["watermark_stroke_width"]
                    if hasattr(self, 'stroke_width_spin') and hasattr(self, 'stroke_width_label'):
                        self.stroke_width_spin.setValue(self.watermark_stroke_width)
                        self.stroke_width_label.setText(str(self.watermark_stroke_width))
                
                if "watermark_stroke_color" in settings:
                    self.watermark_stroke_color = settings["watermark_stroke_color"]
                    if hasattr(self, 'stroke_color_button') and hasattr(self, 'stroke_color_label'):
                        self.stroke_color_button.setStyleSheet(f"background-color: {self.watermark_stroke_color}")
                        self.stroke_color_label.setText(self.watermark_stroke_color)
                
                if "export_format" in settings:
                    self.export_format = settings["export_format"]
                    if hasattr(self, 'jpeg_radio') and hasattr(self, 'png_radio'):
                        if self.export_format == "JPEG":
                            self.jpeg_radio.setChecked(True)
                        else:
                            self.png_radio.setChecked(True)
                
                if "export_quality" in settings:
                    self.export_quality = settings["export_quality"]
                    if hasattr(self, 'quality_slider') and hasattr(self, 'quality_label'):
                        self.quality_slider.setValue(self.export_quality)
                        self.quality_label.setText(f'{self.export_quality}%')
                
                if "use_suffix" in settings:
                    self.use_suffix = settings["use_suffix"]
                    if hasattr(self, 'suffix_checkbox'):
                        self.suffix_checkbox.setChecked(self.use_suffix)
                
                if "suffix_text" in settings:
                    self.suffix_text = settings["suffix_text"]
                    if hasattr(self, 'suffix_edit'):
                        self.suffix_edit.setText(self.suffix_text)
                
                if "save_to_same_dir" in settings:
                    self.save_to_same_dir = settings["save_to_same_dir"]
                    if hasattr(self, 'save_same_dir_checkbox'):
                        self.save_same_dir_checkbox.setChecked(self.save_to_same_dir)
                
                if "last_export_dir" in settings:
                    self.last_export_dir = settings["last_export_dir"]
        except Exception as e:
            print(f"加载设置时出错: {e}")
            # 如果加载失败，使用默认设置
            pass
            
    def save_template(self):
        """保存当前设置为模板"""
        try:
            # 确保模板目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 获取模板名称
            template_name, ok = QInputDialog.getText(self, "保存模板", "请输入模板名称:")
            
            if ok and template_name.strip():
                # 准备模板数据
                template = {
                    "name": template_name,
                    "watermark_text": self.watermark_text,
                    "watermark_position": self.watermark_position,
                    "watermark_font_size": self.watermark_font_size,
                    "watermark_opacity": self.watermark_opacity,
                    "watermark_font": self.watermark_font,
                    "watermark_bold": self.watermark_bold,
                    "watermark_italic": self.watermark_italic,
                    "watermark_color": self.watermark_color,
                    "watermark_shadow": self.watermark_shadow,
                    "watermark_stroke": self.watermark_stroke,
                    "watermark_stroke_width": self.watermark_stroke_width,
                    "watermark_stroke_color": self.watermark_stroke_color,
                    "export_format": self.export_format,
                    "export_quality": self.export_quality,
                    "use_suffix": self.use_suffix,
                    "suffix_text": self.suffix_text,
                    "save_to_same_dir": self.save_to_same_dir
                }
                
                # 生成模板文件名
                template_filename = f"template_{template_name.replace(' ', '_')}.json"
                template_path = os.path.join(self.templates_dir, template_filename)
                
                # 保存模板
                with open(template_path, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                
                QMessageBox.information(self, "成功", f"模板 '{template_name}' 已保存")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存模板时出错: {str(e)}")
            
    def load_template(self):
        """加载已保存的模板"""
        try:
            # 确保模板目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 获取所有模板文件
            template_files = []
            for file in os.listdir(self.templates_dir):
                if file.startswith("template_") and file.endswith(".json"):
                    template_files.append(file)
            
            if not template_files:
                QMessageBox.information(self, "提示", "没有找到已保存的模板")
                return
            
            # 显示模板选择对话框
            template_names = []
            template_paths = []
            for file in template_files:
                try:
                    template_path = os.path.join(self.templates_dir, file)
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        if "name" in template:
                            template_names.append(template["name"])
                            template_paths.append(template_path)
                except:
                    continue
            
            if not template_names:
                QMessageBox.information(self, "提示", "没有有效的模板文件")
                return
            
            selected_name, ok = QInputDialog.getItem(
                self, "选择模板", "请选择要加载的模板:", template_names, 0, False
            )
            
            if ok and selected_name:
                # 查找选中的模板文件
                index = template_names.index(selected_name)
                template_path = template_paths[index]
                
                # 加载模板
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = json.load(f)
                
                # 应用模板设置
                if "watermark_text" in template:
                    self.watermark_text = template["watermark_text"]
                    self.watermark_input.setText(self.watermark_text)
                
                if "watermark_position" in template:
                    self.watermark_position = tuple(template["watermark_position"])
                    # 更新位置按钮状态
                    for name, position in self.position_presets.items():
                        if position == self.watermark_position:
                            self.set_watermark_position(name)
                            break
                
                if "watermark_font_size" in template:
                    self.watermark_font_size = template["watermark_font_size"]
                    size_str = str(self.watermark_font_size)
                    index = self.font_size_combo.findText(size_str)
                    if index >= 0:
                        self.font_size_combo.setCurrentIndex(index)
                
                if "watermark_opacity" in template:
                    self.watermark_opacity = template["watermark_opacity"]
                    self.opacity_slider.setValue(self.watermark_opacity)
                
                if "export_format" in template:
                    self.export_format = template["export_format"]
                    if self.export_format == "JPEG":
                        self.jpeg_radio.setChecked(True)
                    else:
                        self.png_radio.setChecked(True)
                
                if "export_quality" in template:
                    self.export_quality = template["export_quality"]
                    self.quality_slider.setValue(self.export_quality)
                    self.quality_label.setText(f'{self.export_quality}%')
                
                if "use_suffix" in template:
                    self.use_suffix = template["use_suffix"]
                    self.suffix_checkbox.setChecked(self.use_suffix)
                
                if "suffix_text" in template:
                    self.suffix_text = template["suffix_text"]
                    self.suffix_edit.setText(self.suffix_text)
                
                if "save_to_same_dir" in template:
                    self.save_to_same_dir = template["save_to_same_dir"]
                    self.save_same_dir_checkbox.setChecked(self.save_to_same_dir)
                
                # 更新预览
                self.update_preview()
                
                # 保存当前设置
                self.save_current_settings()
                
                QMessageBox.information(self, "成功", f"模板 '{selected_name}' 已加载")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载模板时出错: {str(e)}")
            
    def manage_templates(self):
        """管理和删除已保存的模板"""
        try:
            # 确保模板目录存在
            os.makedirs(self.templates_dir, exist_ok=True)
            
            # 获取所有模板文件
            template_files = []
            for file in os.listdir(self.templates_dir):
                if file.startswith("template_") and file.endswith(".json"):
                    template_files.append(file)
            
            if not template_files:
                QMessageBox.information(self, "提示", "没有找到已保存的模板")
                return
            
            # 显示模板选择对话框
            template_names = []
            template_paths = []
            for file in template_files:
                try:
                    template_path = os.path.join(self.templates_dir, file)
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        if "name" in template:
                            template_names.append(template["name"])
                            template_paths.append(template_path)
                except:
                    continue
            
            if not template_names:
                QMessageBox.information(self, "提示", "没有有效的模板文件")
                return
            
            selected_name, ok = QInputDialog.getItem(
                self, "管理模板", "请选择要管理的模板:", template_names, 0, False
            )
            
            if ok and selected_name:
                # 查找选中的模板文件
                index = template_names.index(selected_name)
                template_path = template_paths[index]
                
                # 显示管理选项
                options = ["删除模板", "重命名模板", "查看模板详情"]
                choice, ok = QInputDialog.getItem(
                    self, "模板管理", "请选择操作:", options, 0, False
                )
                
                if ok:
                    if choice == "删除模板":
                        reply = QMessageBox.question(
                            self, "确认删除", f"确定要删除模板 '{selected_name}' 吗？",
                            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                        )
                        
                        if reply == QMessageBox.Yes:
                            os.remove(template_path)
                            QMessageBox.information(self, "成功", f"模板 '{selected_name}' 已删除")
                    elif choice == "重命名模板":
                        new_name, ok = QInputDialog.getText(
                            self, "重命名模板", "请输入新的模板名称:", text=selected_name
                        )
                        
                        if ok and new_name.strip() and new_name != selected_name:
                            # 读取原模板内容
                            with open(template_path, 'r', encoding='utf-8') as f:
                                template = json.load(f)
                            
                            # 更新模板名称
                            template["name"] = new_name
                            
                            # 删除原文件
                            os.remove(template_path)
                            
                            # 保存新模板
                            new_filename = f"template_{new_name.replace(' ', '_')}.json"
                            new_path = os.path.join(self.templates_dir, new_filename)
                            
                            with open(new_path, 'w', encoding='utf-8') as f:
                                json.dump(template, f, ensure_ascii=False, indent=2)
                            
                            QMessageBox.information(self, "成功", f"模板已重命名为 '{new_name}'")
                    elif choice == "查看模板详情":
                        # 读取模板内容
                        with open(template_path, 'r', encoding='utf-8') as f:
                            template = json.load(f)
                        
                        # 格式化模板详情
                details = []
                details.append(f"模板名称: {template.get('name', '未知')}")
                details.append(f"水印文本: {template.get('watermark_text', '无')}")
                details.append(f"字体: {template.get('watermark_font', '默认')}")
                details.append(f"字体大小: {template.get('watermark_font_size', '默认')}")
                details.append(f"粗体: {'是' if template.get('watermark_bold', False) else '否'}")
                details.append(f"斜体: {'是' if template.get('watermark_italic', False) else '否'}")
                details.append(f"颜色: {template.get('watermark_color', '白色')}")
                details.append(f"透明度: {template.get('watermark_opacity', 128)}")
                details.append(f"阴影: {'是' if template.get('watermark_shadow', False) else '否'}")
                details.append(f"描边: {'是' if template.get('watermark_stroke', False) else '否'}")
                if template.get('watermark_stroke', False):
                    details.append(f"描边宽度: {template.get('watermark_stroke_width', 1)}")
                    details.append(f"描边颜色: {template.get('watermark_stroke_color', '黑色')}")
                details.append(f"导出格式: {template.get('export_format', 'JPEG')}")
                details.append(f"导出质量: {template.get('export_quality', 90)}%")
                details.append(f"使用后缀: {'是' if template.get('use_suffix', False) else '否'}")
                if template.get('use_suffix', False):
                    details.append(f"后缀文本: {template.get('suffix_text', '')}")
                details.append(f"保存到原目录: {'是' if template.get('save_to_same_dir', False) else '否'}")
                         
                QMessageBox.information(
                    self, "模板详情", "\n".join(details)
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"管理模板时出错: {str(e)}")
            
# 重写closeEvent方法，确保关闭时保存设置
    def closeEvent(self, event):
        self.save_current_settings()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageWatermarkTool()
    window.show()
    sys.exit(app.exec_())