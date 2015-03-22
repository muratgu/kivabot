#kivabot
import mechanize 
import getpass
import sys
from BeautifulSoup import BeautifulSoup

br = mechanize.Browser()
br.set_handle_robots(False)    
br.set_handle_refresh(False)   
br.addheaders =[('User-agent', 'Firefox')]
url = 'https://www.kiva.org/login?doneUrl=https%3A%2F%2Fwww.kiva.org%2Fportfolio'
resp = br.open(url)
print br.title()

br.form = list(br.forms())[0]    
uid = br.form.find_control("email")
uid.value = raw_input("Username [%s]: " % getpass.getuser())
pwd = br.form.find_control("password")
pwd.value = getpass.getpass()
resp = br.submit()
print br.title()

soup = BeautifulSoup(resp.read())
credit = soup.findAll('span', {'class': 'creditNumber'})
if len(credit) != 1:
    raise Exception('Credit amount not found')

credit_amount = float(credit[0].contents[0].replace('$','').replace('&#36;',''))
if credit_amount < 25.0:
    print 'Credit amount not enough: $%d' % credit_amount
    sys.exit(1)

resp = br.open("http://www.kiva.org/lend")
lendLink = br.links(url_regex='http://www.kiva.org/lend/*').next()
print lendLink.url
print lendLink.text

br.follow_link(lendLink)
br.form = list(br.forms())[0] 
resp = br.submit()

br.form = None
for f in list(br.forms()):
    if 'id' in f.attrs and f.attrs['id'] == 'my-basket-form':
        br.form = f        
        break
if not br.form:
    raise Exception('Basket form not found.')
        
resp = br.submit()

soup = BeautifulSoup(resp.read())
div = soup.findAll('span', {'class': lambda(v): v and v.find('value') > -1 and v.find('biggest') > -1})
if len(div) != 1:
    raise Exception('Basket amount not found.')  

basket_amount_str = div[0].contents[0]
if not basket_amount_str.startswith('$'):
    raise Exception('Basket amount not recognized.')

basket_amount = float(basket_amount_str.replace('$',''))
if basket_amount > 0:
    print 'Basket amount not zero.'
    sys.exit(-1)

print 'basket amount = %f' % basket_amount    

print 'to be continued'  