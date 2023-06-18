#!usr/bin/env python
# encoding:utf-8
from __future__ import division
 
"""
__Author__:沂水寒城
功能： pdf转png
"""
 
import os
import fitz
 
 
def pdf2Png(pdfPath, saveDir, name, zoom_x=2, zoom_y=2, rotation_angle=0):
    """
    pdf文件转为png文件
    """
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)
    pdf = fitz.open(pdfPath)
    print(pdf)
    # 逐页读取pdf
    for page_num in range(0, pdf.pageCount):
        print("Parse And Transfome Page: ", page_num)
        page = pdf[page_num]
        # 设置缩放和旋转系数
        trans = fitz.Matrix(zoom_x, zoom_y).preRotate(rotation_angle)
        p2p = page.getPixmap(matrix=trans, alpha=False)
        if pdf.pageCount == 1:
        	p2p.writePNG(saveDir + name + ".png")
        else:
        	p2p.writePNG(saveDir + name + "_" + str(page_num) + ".png")
    pdf.close()
 
 
if __name__ == "__main__":
 
    print(
        "===================================Loading PDF2PNG==================================="
    )
    pdffile = '/home/zhoukanglei/Documents/SynologyDrive/SynologyDrive/HGCN/figs/framework_1.pdf'
    saveDir = "/home/zhoukanglei/Documents/GitHub/HGCN_AQA/imgs/"
    pdf2Png(pdffile, saveDir, "overview")