import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFileDialog, 
    QSplitter, QFrame, QGroupBox, QFormLayout, QAction, qApp, QMessageBox
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
        
        # 水印设置组（第二阶段实现）
        watermark_group = QGroupBox('水印设置')
        watermark_layout = QFormLayout()
        
        # 占位符，第二阶段实现
        placeholder = QLabel('此功能将在第二阶段实现')
        placeholder.setAlignment(Qt.AlignCenter)
        watermark_layout.addRow(placeholder)
        
        watermark_group.setLayout(watermark_layout)
        right_layout.addWidget(watermark_group)
        
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
            pixmap = QPixmap(current_image_path)
            if not pixmap.isNull():
                # 调整图片大小以适应预览窗口
                preview_size = self.preview_label.size()
                scaled_pixmap = pixmap.scaled(
                    preview_size.width() - 20, preview_size.height() - 20, 
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                
                # 更新预览标签
                self.preview_label.setPixmap(scaled_pixmap)
    
    def export_image(self):
        # 此功能将在第三阶段实现
        QMessageBox.information(self, '提示', '导出功能将在第三阶段实现')
    
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