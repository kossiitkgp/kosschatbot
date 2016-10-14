import requests
from bs4 import BeautifulSoup as bs 
from cgi import escape
def main(query) :
	formatted_query=query.replace(" ","%20")
	page_no = 1
	result_list = list()
	while True :
		base_url = "http://stackoverflow.com/search?page={}&pagesize=50&tab=relevance&q={}".format(page_no,formatted_query)
		response = requests.get(base_url)
		soup = bs(response.text , 'html.parser')
		results = soup.findAll('div',{'class':'question-summary search-result'})
		flag = True
		for result in results :
			flag =False
			accepted_answered=result.find('div',{'class','status answered-accepted'}) #getting accepted answered questions
			answered = result.find('div',{'class','status answered'})
			if accepted_answered != None :
				no_of_ans = accepted_answered.contents[1].string
			elif answered != None :
				no_of_ans = answered.contents[1].string
			else :
				continue 
			#print no_of_ans
			result_link_div=result.find('div',{'class':'result-link'})
			link = result_link_div.find('a')
			if len(link['title']) > 75 :
				title = link['title'][:75]+'...'
			else :
				title = link['title']
			votes_span = result.find('span',{'class':'vote-count-post '})
			no_of_votes=votes_span.string
			ques_url = "http://stackoverflow.com/{}".format(link['href'])
			subtitle = "This question received a total of {} answers and {} votes.".format(no_of_ans,no_of_votes)
			result_dict={'item_url':ques_url,'subtitle':subtitle,'title':title,'buttons':[{"type":"element_share"}]}
			result_list.append(result_dict)
			if len(result_list) == 10 :
				return result_list
		page_no+=1
		if flag:
			return result_list
x= main('i am getting index error in python')
print len(x)
print x