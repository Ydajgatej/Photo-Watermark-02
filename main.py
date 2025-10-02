import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog, 
    QSplitter, QFrame, QGroupBox, QFormLayout, QAction, qApp, QMessageBox,
    QLineEdit, QGridLayout, QComboBox, QSlider, QCheckBox, QRadioButton, QButtonGroup
)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import Qt, QSize, QPoint
from PIL import Image, ImageQt, ImageDraw, ImageFont

class ImageWatermarkTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.image_list = []  # 存储导入的图片路径
        self.current_image_index = -1  # 当前选中的图片索引
        
        # 水印相关变量
        self.watermark_text = ""
        self.watermark_position = (0.5, 0.5)  # 默认居中位置（相对坐标）
        self.watermark_font_size = 30
        self.watermark_color = "white"
        self.watermark_opacity = 128  # 0-255，默认为半透明
        
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
        # 打开文件选择对话框
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, '选择图片', '', '图片文件 (*.jpg *.jpeg *.png);;所有文件 (*)'
        )
        
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
        """将PIL Image转换为QImage"""
        if pil_image.mode == "RGB":
            r, g, b = pil_image.split()
            pil_image = Image.merge("RGB", (b, g, r))
        elif pil_image.mode == "RGBA":
            r, g, b, a = pil_image.split()
            pil_image = Image.merge("RGBA", (b, g, r, a))
        
        data = pil_image.tobytes("raw", pil_image.mode)
        q_image = QImage(data, pil_image.size[0], pil_image.size[1], pil_image.size[0] * len(pil_image.mode),
                        QImage.Format_RGB888 if pil_image.mode == "RGB" else QImage.Format_RGBA8888)
        return q_image
        
    def add_watermark_to_image(self, image):
        """向图片添加文本水印"""
        # 创建可绘制对象
        draw = ImageDraw.Draw(image, 'RGBA')
        
        # 获取图片尺寸
        width, height = image.size
        
        # 尝试加载字体，失败则使用默认字体
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("simhei.ttf", self.watermark_font_size)
        except IOError:
            # 使用默认字体
            font = ImageFont.load_default()
        
        # 计算文本尺寸
        try:
            text_width, text_height = draw.textsize(self.watermark_text, font=font)
        except:
            # 兼容Pillow 9.0+的API变化
            bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        
        # 计算水印位置
        pos_x = int(self.watermark_position[0] * width - text_width / 2)
        pos_y = int(self.watermark_position[1] * height - text_height / 2)
        
        # 确保位置在图片范围内
        pos_x = max(0, min(pos_x, width - text_width))
        pos_y = max(0, min(pos_y, height - text_height))
        
        # 添加水印文本，带透明度
        draw.text((pos_x, pos_y), self.watermark_text, fill=(255, 255, 255, self.watermark_opacity), font=font)
        
        return image
        
    def on_watermark_text_changed(self, text):
        """水印文本变化时更新"""
        self.watermark_text = text
        self.update_preview()
        
    def on_font_size_changed(self, size_str):
        """字体大小变化时更新"""
        try:
            self.watermark_font_size = int(size_str)
            self.update_preview()
        except ValueError:
            pass
        
    def on_opacity_changed(self, value):
        """透明度变化时更新"""
        self.watermark_opacity = value
        self.update_preview()
        
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
    
    def on_save_dir_toggled(self, state):
        """保存目录选项变化时更新"""
        old_state = self.save_to_same_dir
        self.save_to_same_dir = (state == Qt.Checked)
        
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageWatermarkTool()
    window.show()
    sys.exit(app.exec_())