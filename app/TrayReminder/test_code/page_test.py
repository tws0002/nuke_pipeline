# -*- coding:utf-8 -*-
__date__ = '2017/3/27 14:25'
__author__ = 'liaokong'

import sys
import os
import json
import glob

from PyQt4 import QtGui
from PyQt4 import QtCore
import pythoncom
from win32com.shell import shell
import locale
import win32ui
import win32gui
import win32con
import win32api

reload(sys)
sys.setdefaultencoding('utf-8')


def read_json(conf_path):
	# 从配置文件中获取信息
	if not os.path.isfile(conf_path):
		raise Exception(u"配置文件未找到")

	with open(TestPage.conf_path) as json_file:
		json_str = json_file.read()
		tool_info_list = json.loads(json_str)

	return tool_info_list


class TestPage(QtGui.QWidget):
	# 配置文件路径
	conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

	def __init__(self, parent=None):
		super(TestPage, self).__init__(parent)

		main_layout = QtGui.QVBoxLayout(self)
		self.button_layout = QtGui.QHBoxLayout()
		main_layout.addLayout(self.button_layout)

		self.page_stack = QtGui.QStackedWidget()
		main_layout.addWidget(self.page_stack)

		self.init_page(self.conf_path)

	def init_page(self, conf_path):

		tool_info_list = read_json(conf_path)

		# 创建页面按钮按钮
		for tool_info_dict in tool_info_list:
			page_name = tool_info_dict.get("name")
			page_tool_list = tool_info_dict.get("app_list")

			page_button = QtGui.QPushButton(page_name)
			page_button.setObjectName("%s_page_btn" % page_name)
			self.button_layout.addWidget(page_button)

			page_widget = ToolListWgt(page_name)
			self.page_stack.addWidget(page_widget)
			self.init_tool_page(page_widget, page_tool_list)
			page_button.clicked.connect(self.change_page)

	def init_tool_page(self, page_widget, page_tool_list):
		for tool_name in page_tool_list:
			tool_item = ToolItem(tool_name)
			page_widget.addItem(tool_item)

	def change_page(self):
		# 获取当前点击按钮的名字
		current_button = self.sender()
		button_name = current_button.objectName()
		page_name = button_name.replace("_btn", "_wgt")

		# 根据当前widget名字获取当前widget
		current_widget = self.findChild(QtGui.QListWidget, page_name)
		self.page_stack.setCurrentWidget(current_widget)


class ToolListWgt(QtGui.QListWidget):
	def __init__(self, obj_name, parent=None):
		super(ToolListWgt, self).__init__(parent)

		self.setObjectName("%s_page_wgt" % obj_name)
		self.setViewMode(self.IconMode)
		self.setDragEnabled(False)
		self.setDefaultDropAction(QtCore.Qt.MoveAction)
		self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
		self.setAcceptDrops(True)

		self.itemDoubleClicked.connect(self.double_clicked)
		self.itemChanged.connect(self.item_gaibian)

	def item_gaibian(self):
		print "gaibianla"

	def double_clicked(self):
		"""打开程序"""
		tool_info_list = read_json(TestPage.conf_path)

		# 寻找json文件中对应的路径
		for tool_info_dict in tool_info_list:
			if tool_info_dict.get("name") == self.objectName().split("_")[0]:
				for app in tool_info_dict.get("app_list"):
					if app.get("app_name") == self.currentItem().text().replace("\n", " "):
						os.startfile(app.get("app_path"))

	def dragEnterEvent(self, event):
		event.acceptProposedAction()

	def dragMoveEvent(self, event):
		pass

	def dropEvent(self, event):
		mimeData = event.mimeData()
		links = []
		if mimeData.hasUrls:
			for url in mimeData.urls():
				# 获取拖入的完整路径
				links.append(str(url.toLocalFile()).decode("utf8"))
			add_tool_item = AddToolItem(links, self.objectName())
			self.addItem(add_tool_item)


class ToolItem(QtGui.QListWidgetItem):
	root_path = os.path.dirname(os.path.abspath(__file__))

	def __init__(self, tool_name, parent=None):
		super(ToolItem, self).__init__(parent)

		self.setSizeHint(QtCore.QSize(80, 90))

		# 设置按钮名字
		self.setText(tool_name.get("app_name").replace(" ", "\n"))
		# 根据名字查找按钮图标
		main_icon_path = self.get_icon_path(tool_name)

		# 设置按钮图标
		if os.path.isfile(main_icon_path):
			icon = QtGui.QIcon(main_icon_path)
			self.setIcon(icon)

		# 找到按钮功能
		# self.script_path = self.get_script_path()

		# todo：添加右键菜单
		#
		# 右键菜单添加删除功能

	@staticmethod
	def get_icon_path(tool_name):
		main_icon_name = tool_name.get("app_ico")
		main_icon_path = os.path.join(ToolItem.root_path, main_icon_name)
		return main_icon_path


class AddToolItem(QtGui.QListWidgetItem):
	def __init__(self, links, widget_name, parent=None):
		super(AddToolItem, self).__init__(parent)

		self.widget_name = widget_name.split("_")[0]

		for link in links:
			if os.path.splitext(link)[-1] == ".exe" or os.path.splitext(link)[-1] == ".lnk":
				# todo: 添加app时先判断拖入的exe是否已经存在，如果已存在则不创建并给出提示
				with open(TestPage.conf_path) as conf_file:
					conf_str = conf_file.read()
				get_true_path = str(unicode(QtCore.QString(self.__get_lnk_path(link)).toUtf8(), 'utf-8', 'ignore'))

				print type(conf_str), type(get_true_path)

				# todo: 判断这里有问题，明天继续弄
				if conf_str.find(get_true_path) == -1:

					if self.make_icon(get_true_path, "icon/%s.ico" % link.split("/")[-1].split(".")[0]):
						self.setText(link.split("/")[-1].split(".")[0].replace(" ", "\n"))
						icon = QtGui.QIcon(os.path.dirname(os.path.abspath(__file__)) + "/icon/%s.ico" %
										   link.split("/")[-1].split(".")[0])
						self.setIcon(icon)

						self.setSizeHint(QtCore.QSize(80, 90))

						self.write_json(self.widget_name, link.split("/")[-1].split(".")[0],
										"icon/%s.ico" % link.split("/")[-1].split(".")[0], get_true_path)
					else:
						QtGui.QMessageBox.information(None, u"提示", u"请拖入exe文件的快捷方式")

				else:
					QtGui.QMessageBox.information(None, u"提示", u"程序已添加，请不要重复添加")

			else:
				QtGui.QMessageBox.information(None, u"提示", u"请拖入快捷方式或者exe文件")

	def write_json(self, widget_name, app_name, ico_path, app_path):
		"""将拖入的程序写入json文件中"""
		apend_dict = read_json(TestPage.conf_path)

		widget_name = unicode(QtCore.QString(widget_name).toUtf8(), 'utf-8', 'ignore')
		app_name = unicode(QtCore.QString(app_name).toUtf8(), 'utf-8', 'ignore')
		ico_path = unicode(QtCore.QString(ico_path).toUtf8(), 'utf-8', 'ignore')
		app_path = unicode(QtCore.QString(app_path).toUtf8(), 'utf-8', 'ignore')

		add_app = {"app_name": app_name,
				   "app_ico": ico_path,
				   "app_path": app_path}

		for index_page, item_page in enumerate(apend_dict):
			if item_page.get("name") == widget_name:
				app_list = item_page.get("app_list")
				app_list.append(add_app)
				apend_dict.remove(apend_dict[index_page])
				new_app_list = {
					"name": widget_name,
					"app_list": app_list
				}
				apend_dict.insert(index_page, new_app_list)

		with open(TestPage.conf_path, "w") as json_file:
			json_str = json.dumps(apend_dict, ensure_ascii=False, indent=2)
			json_file.write(json_str)

	@staticmethod
	def __get_lnk_path(file_path):
		try:
			pythoncom.CoInitialize()
			shortcut = pythoncom.CoCreateInstance(
				shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
			shortcut.QueryInterface(pythoncom.IID_IPersistFile).Load(file_path)
			fileRealPath = shortcut.GetPath(shell.SLGP_SHORTPATH)[0]
			fileRealPath = fileRealPath.decode(locale.getdefaultlocale()[1])
			return fileRealPath
		except Exception, e:
			print e
			return file_path

	def make_icon(self, link_path, save_path):
		"""获取exe文件的图标"""
		if os.path.splitext(link_path)[-1].lower() == ".exe":  # 此处程序后缀有可能为大写的EXE
			large, small = win32gui.ExtractIconEx(link_path, 0)
			win32gui.DestroyIcon(small[0])
			self.pixmap = QtGui.QPixmap.fromWinHBITMAP(self.__bitmap_from_hIcon(large[0]), 2)
			self.pixmap.save(save_path, "ico")
			return True
		else:
			return False

	@staticmethod
	def __bitmap_from_hIcon(hIcon):
		hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
		hbmp = win32ui.CreateBitmap()
		hbmp.CreateCompatibleBitmap(hdc, 32, 32)
		hdc = hdc.CreateCompatibleDC()
		hdc.SelectObject(hbmp)
		hdc.DrawIcon((0, 0), hIcon)
		hdc.DeleteDC()
		return hbmp.GetHandle()


if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	test_page = TestPage()
	test_page.show()
	app.exec_()
