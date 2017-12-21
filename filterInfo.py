#-*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import os
import chardet
import urllib2
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser  
from pdfminer.pdfdocument import PDFDocument  
from pdfminer.pdfpage import PDFPage  
from pdfminer.pdfpage import PDFTextExtractionNotAllowed  
from pdfminer.pdfinterp import PDFResourceManager  
from pdfminer.pdfinterp import PDFPageInterpreter  
from pdfminer.pdfdevice import PDFDevice  
from pdfminer.layout import *  
from pdfminer.converter import PDFPageAggregator  
from io import StringIO
from io import open
import traceback
import docx
import re


def filterInfo(data_path, output_file):
	# 得到文章标题、年份、作者、href等基本信息
	place = {
		'2017': 'Vancouver_Canada',
		'2016': 'Berlin_Germany',
		'2015': 'Beijing_China',
		'2014': 'Baltimore_MD_USA',
		'2013': 'Sofia_Bulgaria'
	}
	final_content = []
	for root, directory, files in os.walk(data_path):
		for file in files:
			if 'html' not in file:
				continue
			print file
			with open(file, mode='r') as input_data:
				year, essay_type = file.split('.')[0].split(' ')
				position = place[year]
				html_text = input_data.read()
				# enc=chardet.detect(html_text) 
				# print enc['encoding'] 
				doc = BeautifulSoup(html_text, 'lxml')
				items = doc.select('ul.publ-list li.inproceedings')
				for item in items:
					href = item.select('nav.publ ul li:nth-of-type(1) div.head a')[0].get('href')
					title = ''
					authors = ''
					for sp in item.select('div.data span'):
						if 'author' == sp['itemprop']:
							authors += sp.string + ';'
						elif 'name' == sp['itemprop']:
							title = sp.string
					if not title:
						print(href)
					res = '\t'.join([title, year, position, essay_type, authors, '', href])
					final_content.append(res)
	with open(output_file, mode='a') as output_info:
		output_info.write('\n'.join(final_content).encode('utf-8'))

def make_file_name(**args)：
	n = args['n']
	seg = args['seg']
	url = seg[-1]
	url = url.replace(':', '').replace('/', '').replace('.', '').replace('\n', '')
	name = str(n)+'_'+seg[1]+'_'+url
	return name

def downloadPDF(input_file, pdf_path, error_msg_file):
	# 批量下载pdf文件并写入本地
	text = []
	Errormsg = ''
	with open(input_file, 'r') as input_data:
		text = input_data.readlines()
	for line in text:
		n = n + 1
		seg = line.split('\t')
		if not seg[4]:
			continue
		url = seg[-1]
		pdf = getPDF(url)
		if not pdf:
			with open(error_msg_file, 'a') as outerr:
				outerr.write(line+'\n')
		url = url.replace(':', '').replace('/', '').replace('.', '').replace('\n', '')
		with open(pdf_path+str(n)+'_'+seg[1]+'_'+url+'.pdf', 'wb') as outpdf:
			outpdf.write(pdf)

def getPDF(pdfurl):
	# 根据url网络请求pdf
	MAX_RETRY = 15
	try_time = 0
	while try_time < MAX_RETRY:
		pdfFile = None
		print try_time
		try:
			pdfFile = urllib2.urlopen(pdfurl)
			# print pdfFile.getcode()
			if pdfFile.getcode() <300:
				content  = pdfFile.read()
				return content
			else:
				try_time += 1
		except urllib2.URLError as e:
			try_time += 1
			print '[ERROR] '+ e
			if hasattr(e, 'code'):
				print 'Error code:',e.code
				print e.geturl()
				print e.info()
			elif hasattr(e, 'reason'):
				print 'Reason:',e.reason
		except Exception as e:
			traceback.print_exc()
			print e
			try_time += 1
			pass
	return None

def filterAuthorsOrganazition(input_file, output_file, docx_path):
	# 根据包含基本信息的文件识别相应pdf信息
	text = []
	Errormsg = ''
	with open(input_file, 'r') as input_data:
		text = input_data.readlines()
	n = 0
	final_text = []
	for line in text:
		n = n + 1
		seg = line.split('\t')
		if not seg[4]:
			continue
		url = seg[-1]
		url = url.replace(':', '').replace('/', '').replace('.', '').replace('\n', '')
		docx_name = docx_path+str(num)+'_'+seg[1]+'_'+url+'.docx'
		new_line = recogOrgnz(n, docx_name, seg)
		final_text.append(new_line)
	with open(output_file, mode='w', encoding='utf-8') as outputInfo:
		outputInfo.write(''.join(final_text))

def recogOrgnz(num, docx_name, seg):
	# 根据论文读取对应word文件并识别其中的信息
	if not os.path.exists(docx_name):
		seg[5] = u'[ERROR_NO_FILE]'
	else:
		doc = docx.opendocx(docx_name)
		doc_text = ''
		for paragh in docx.getdocumenttext(doc):
			if paragh.find('Abstract') != 0:
				doc_text += paragh.replace('\n', ';').replace(u'\u2021', '').replace(u'\u2020', '').replace('\t', ';')+';'
			else:
				break
		authors = seg[4].split(';')
		# print title
		first_author = authors[0]
		flag = re.split('[ ,.]+', first_author)[0]
		# print flag
		# print doc_text.find(flag)
		if doc_text.find(flag) != -1:
			seg[5] = doc_text[doc_text.find(flag):]
		else:
			seg[5] = doc_text[doc_text.find(';')+1:]
		if len(seg[5]) < 5:
			seg[5] = '[ERROR_FILTER_INFO]'
		seg[5] = doc_text
	return u'\t'.join(seg)

def test(num):
	# 测试使用
	with open('final.csv', 'r') as input_data:
		text = input_data.readlines()
	line = text[num-1]
	seg = line.split('\t')
	if not seg[4]:
		print '[ERROR] NO AUTHORS'
		return
	new_line = recogOrgnz(num,seg)
		# seg[5] = doc_text
	with open('text.csv', mode='w', encoding='utf-8') as o:
		o.write(new_line)


if __name__ == '__main__':
	html_path = './'  # 包含要过滤的论文列表的html网页文件（仅限dblp）
	basic_info_file = './basic.csv' # 从html能够过滤的基本信息
	downloaded_pdf_path = './pdf/' # 根据论文url下载pdf存放路径
	pdf2word_path = downloaded_pdf_path # 存放pdf对应word的路径，文件名相同，仅仅后缀不同
	downloadPDF_error_msg = './error' # 下载pdf时的网络错误日志
	final_file = './final.csv' # 最后的结果文件
	# 第一步，从html过滤出基本维度信息，除了需要查看pdf的信息
	filterInfo(html_path, basic_info_file)
	# 第二步，根据过滤出来的url下载相应的pdf论文
	downloadPDF(basic_info_file, downloaded_pdf_path, downloadPDF_error_msg)
	# 第三步，将pdf转成word之后，读取word信息，过滤出作者单位
	filterAuthorsOrganazition(basic_info_file, final_file, pdf2word_path)
	# 调试basic_file的某一行对应的pdf进行word文字识别
	test(771)












	# ***************************************** 以下备用代码 ************************************************

# def PDF2Text(args) :
# 	# pdf识别，转型成字符串，但是目前结果单词之间没有空格,因此暂时弃用
# 	outfile = 'a.txt'

# 	debug = 0
# 	pagenos = set()
# 	password = ''
# 	maxpages = 0
# 	rotation = 0
# 	codec = 'utf-8'
# 	caching = True
# 	imagewriter = None
# 	laparams = LAParams()
# 	#
# 	PDFResourceManager.debug = debug
# 	PDFPageInterpreter.debug = debug

# 	rsrcmgr = PDFResourceManager(caching=caching)
# 	outfp = file(outfile,'w')

# 	device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
# 		imagewriter=imagewriter)
# 	for fname in args:
# 		fp = file(fname,'rb')
# 		interpreter = PDFPageInterpreter(rsrcmgr, device)
# 		#处理文档对象中每一页的内容
# 		for page in PDFPage.get_pages(fp, pagenos,
# 				maxpages=maxpages, password=password,
# 				caching=caching, check_extractable=True) :
# 			page.rotate = (page.rotate+rotation) % 360
# 			interpreter.process_page(page)
# 		fp.close()
# 	device.close()
# 	outfp.close()
# 	return

# def readPDF(pdfFile):
# 	#来创建一个pdf文档分析器 

# 	fp = open('document.pdf', 'rb')

# 	parser = PDFParser(fp)
# 	cc = ''
# 	#创建一个PDF文档对象存储文档结构  
# 	document = PDFDocument(parser)  
# 	# 检查文件是否允许文本提取  
# 	if not document.is_extractable:  
# 		raise PDFTextExtractionNotAllowed
# 		return
# 	# parser.set_document(document)  
# 	# document.set_parser(parser) 
# 	# document.initialize("")  
# 	# 创建一个PDF资源管理器对象来存储共赏资源  
# 	rsrcmgr=PDFResourceManager()
# 	# 设定参数进行分析  
# 	laparams=LAParams()  
# 	# 创建一个PDF设备对象  
# 	device=PDFPageAggregator(rsrcmgr,laparams=laparams)  
# 	# 创建一个PDF解释器对象  
# 	interpreter=PDFPageInterpreter(rsrcmgr,device)  
# 	# 处理每一页 
# 	for page in PDFPage.create_pages(document):
# 		interpreter.process_page(page)
# 		# 接受该页面的LTPage对象  
# 		layout=device.get_result()  
# 		for x in layout: 
# 			if hasattr(x,'get_text'):  
# 				with open('a','a') as f:
# 						f.write(x.get_text()+u'\n')
# 	return p

# def pdf(path):
# 	rsrcmgr = PDFResourceManager()
# 	retstr = StringIO()
# 	device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=LAParams())
# 	interpreter = PDFPageInterpreter(rsrcmgr, device)
# 	with open(path, 'rb') as fp:
# 		for page in PDFPage.get_pages(fp, set()):
# 			interpreter.process_page(page)
# 		text = retstr.getvalue()
# 	device.close()
# 	retstr.close()
# 	return text
