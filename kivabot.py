"""
Kiva Bot

If current credit is more than $25
lends $25 to a recommended loan. 

Usage: python kivabot.py

Enter Kiva user id (email address) [not stored]
Enter Kiva password [not stored]

"""
import mechanize 
import getpass
import sys
from BeautifulSoup import BeautifulSoup
import json
import requests as r
import urllib

LOAN_AMOUNT = 25.0
LOAN_AMOUNT_STR = '25'

def open_basket(br):
    resp = br.open("https://www.kiva.org/basket")
    br.form = None
    for f in list(br.forms()):
        if 'id' in f.attrs and f.attrs['id'] == 'my-basket-form':
            br.form = f        
            break
    if not br.form:
        print br.forms
        raise Exception('Basket form not found.')    
    return resp

def remove_donation(br):    
    resp = br.open("https://www.kiva.org/ajax/theNudge")
    br.form = None
    for f in list(br.forms()):
        if 'id' in f.attrs and f.attrs['id'] == 'nudgeForm':
            br.form = f        
            break
    if not br.form:
        raise Exception('Nudege form not found.')    
    otherDonationAmount = br.form.find_control("otherDonationAmount")
    otherDonationAmount.value = "0"
    br.submit()
    print 'donation removed' 

def verify_order_total(br, soup):
    div = soup.findAll('span', {'class': 'value', 'id': 'orderTotal'})
    if len(div) != 1:
        raise Exception('Order total not found')

    order_total_str = div[0].contents[0]
    if not order_total_str.startswith('$'):
        raise Exception('Order total not recognized.')

    order_total = float(order_total_str.replace('$',''))
    if order_total > LOAN_AMOUNT:
        print 'Order total too much: %f' % order_total
        return -1

    print 'Order total: %f' % order_total
    return 1   

arguid = sys.argv[1] if len(sys.argv) > 1 else None
argpwd = sys.argv[2] if len(sys.argv) > 2 else None
dryrun = sys.argv[3] == 'dryrun' if len(sys.argv) > 3 else None

br = mechanize.Browser()
br.set_handle_robots(False)    
br.set_handle_refresh(False)   
br.addheaders =[('User-agent', 'Firefox')]
url = 'https://www.kiva.org/login?doneUrl=https%3A%2F%2Fwww.kiva.org%2Fportfolio'
resp = br.open(url)

loginTitle = br.title()
print loginTitle

br.form = list(br.forms())[1]    

uid = br.form.find_control("email")
uid.value = arguid if arguid else raw_input("Username [%s]: " % getpass.getuser)

pwd = br.form.find_control("password")
pwd.value = argpwd if argpwd else getpass.getpass()

resp = br.submit()
if br.title() == loginTitle:
    print 'Login failed'
    sys.exit(-1)

print br.title()

soup = BeautifulSoup(resp.read())
credit = soup.findAll('span', {'class': 'amount'})
if len(credit) != 1:
    raise Exception('Credit amount not found')

credit_amount = float(credit[0].contents[0].replace('$','').replace('&#36;',''))
if credit_amount < LOAN_AMOUNT:
    print 'Credit amount not enough: $%d' % credit_amount    
    sys.exit(1)

loans = json.loads(r.get("https://api.kivaws.org/v2/loans?limit=24&facets=true&type=lite&sortBy=amountLeft").content)
print 'number of loans = %s' % len(loans['entities'])
loan = loans['entities'][0]
lendLinkUrl = 'https://www.kiva.org/lend/%s' % loan['properties']['id']
print lendLinkUrl

resp = br.open(lendLinkUrl)
soup = BeautifulSoup(resp.read())
borrowerName = soup.findAll('h1',{'class':'borrower-name'})[0].text.encode('utf-8')
countrySection = soup.findAll('a', {'href':'#country-section'})[0].text.encode('utf-8')
print '%s from %s' % (borrowerName, countrySection)

lendTitle = br.title()
print lendTitle

if dryrun:
    print 'This was a dry run'
    sys.exit(2)

postData = {'id':loan['properties']['id'], 'loanAmount': LOAN_AMOUNT_STR}
postLink = 'https://www.kiva.org/ajax/xbAddToBasket'
resp = br.open(postLink, urllib.urlencode(postData))

print 'posted' 

resp = open_basket(br)
soup = BeautifulSoup(resp.read())

if verify_order_total(br, soup) == -1:
    remove_donation(br)
    print 'reopening basket'
    resp = open_basket(br)
    soup = BeautifulSoup(resp.read())
    if verify_order_total(br, soup) == -1:
        print 'exiting'
        sys.exit(-1)

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

print 'Basket amount: %f' % basket_amount    

resp = br.submit()
print br.title()   

payment_form = [x for x in list(br.forms()) if x.attrs['id'] == 'payment_form']
if len(payment_form) != 1:
    raise Exception('Payment form not found.') 

br.form = payment_form[0]
resp = br.submit()
print br.title()

try:
    twitter_status = "Just loaned $%s to %s from %s %s #kiva" % (LOAN_AMOUNT_STR, borrowerName, countrySection, lendLinkUrl)
    from subprocess import call
    call(["twitter", "set", twitter_status])
except Exception as ex:
    print "Cannot update twitter"
    print ex

print 'Completed'

