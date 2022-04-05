'''
Wrapper 装饰模式
poo_solve中使用的xlrd版本时2.0.1，和原来的版本1.2.0不兼容
如果升级了xlrd，原有程序中的pandas将无法读取excel文件，安装辅助包也会出现各种问题，所以这里不打算升级xlrd版本
poo_solve中大量使用了新版xlrd中sheet对象的索引器来获取cell对象，更改为旧版cell对象的获取方法会比较不方便
所以这里把sheet对象封装一下，添加一个索引器
'''
class SheetWrapper(object):
    sheet:object
    nrows:int
    def __init__(self,sheet):
        self.sheet = sheet
        self.nrows = sheet.nrows
    def __getitem__(self,row):
        return self.sheet.cell(row[0],row[1])