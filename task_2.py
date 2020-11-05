############################################################################################################
#
#	Задача 2. Путь к XML файлу передается первым позиционным аргументом.
# 	python task_2.py ./sample.xml
#
############################################################################################################

from sys import argv
from lxml import etree

# Поиск в глубину максимальной вложенности
def deepsearch( element, depth=0 ):
	maxdepth = depth

	for node in element:
		dp = deepsearch(node, depth+1)
		if maxdepth < dp:
			maxdepth = dp
	
	return maxdepth

def main( xmlpath ):

	if not xmlpath:
		print('Необходимо передать путь к XML файлу')
		return

	try:
		# Парсим исходный XML
		xml = etree.parse( xmlpath )

		# Получаем корневой элемент
		root = xml.getroot()

		# Ищем в глубину
		depth = deepsearch(root)

		# Выводим результат на экран
		print( f'Максимальная глубина вложенности в XML-документе: {depth}' )
		
	except etree.XMLSyntaxError as synterror:
		print( f'Файл "{xmlpath}" не является валидным файлом XML. --- {synterror}')

	except Exception as ex:
		print( f'Ошибка: --- {ex}"' )
	


if __name__ == '__main__':
	main( argv[1] )