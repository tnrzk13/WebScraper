from urllib.request import urlopen
from bs4 import BeautifulSoup
import pymysql
import re

conn = pymysql.connect(host="localhost", user="root", passwd="@9Diw5678", db="speakfeel", charset="utf8")
cur = conn.cursor()
cur.execute("USE speakfeel")

#Get html info from page
html = urlopen("http://datatest.dev.speakfeel.com/")
bsObj = BeautifulSoup(html, "lxml")
tablesObj = bsObj.find_all("table")

#Inserts a comma at the end of the string if needed
def insertcomma (s):
    last = s[-1]
    if ((last != "(") and (last != ",")):
        s += ", "
    return s

#player_id and jersey_number are (int), all others are (str)
#stores items into a record in MySQL
def store(player_id, jersey_number, first_name, last_name, team, position):
    
    cmd = "INSERT INTO teams ("
    insert = "("

    if (jersey_number):
        cmd = insertcomma (cmd)
        cmd += "jersey_number"
        insert = insertcomma (insert)
        insert += jersey_number
    if (first_name):
        cmd = insertcomma (cmd)
        cmd += "first_name"
        insert = insertcomma (insert)
        first_name = '"' + first_name + '"'
        insert += first_name
    if (last_name):
        cmd = insertcomma (cmd)
        cmd += "last_name"
        insert = insertcomma (insert)
        last_name = '"' + last_name + '"'
        insert += last_name
    if (team):
        cmd = insertcomma (cmd)
        cmd += "team"
        insert = insertcomma (insert)
        team = '"' + team + '"'
        insert += team
    if (position):
        cmd = insertcomma (cmd)
        cmd += "pos"
        insert = insertcomma (insert)
        position = '"' + position + '"'
        insert += position
    cmd += ") VALUES "
    insert += ")"
        
    exc = cmd + insert
    print(exc)
    cur.execute(exc)
    cur.connection.commit()

#table (tag)
#Returns array of header names (str)
def getHead(table):

    head_tags = table.find_all('tr')
    head = []
    
    #check where the lowest level headers are
    lowest_head = 0
    search = True
    while (search):
        if (head_tags[lowest_head].find("th")):
            lowest_head += 1
        else:
            break
    
    #Remove outer tags & convert to string
    head_tags = head_tags[lowest_head-1].find_all("th")
    for th in head_tags:
        no_tag = str(th.contents[0])
        head.append(no_tag)
        
    return head

#Takes in tag of tables
#Returns array of team names (str)
def getTeam(tablesObj):
    teams = []
    for table in tablesObj:
        cur_team = table.previous_sibling.previous_sibling
        teams.append(cur_team)
    return teams

#fullName (str)
#Returns the first name (str)
def getFirstName (fullName):
    if ((fullName=="-") or (fullName=="~missing~")):
        return None
    elif ("," in fullName):
        end = fullName.index(",")
        return fullName[end+2:]
    else:
        end = fullName.index(" ")
        return fullName[0:end]

#fullName (str)
#Returns the last name (str)
def getLastName (fullName):
    print(fullName)
    if ((fullName=="-") or (fullName=="~missing~")):
        return None
    elif ("," in fullName):
        fullName = re.sub('[^a-zA-Z0-9_ ,]', '', fullName)
        end = fullName.index(",")
        return fullName[0:end]
    elif ("." in fullName):
        fullName = re.sub('[^a-zA-Z0-9_ .]', '', fullName)
        end = fullName.index(".")
        return fullName[end+2:]
    else:
        fullName = re.sub('[^a-zA-Z0-9_ ]', '', fullName)
        end = fullName.index(" ")
        return fullName[end+1:]

#headNames (array of str), head(array of str)
#returns dict {headName: pos of headName in head}
def getHeadPos (headNames, head):
    HeadPos = {}
    for Name in headNames:
        if (Name in head):
            HeadPos[Name] = head.index(Name)
    return HeadPos

#Maps every data point to it's row and header
def MapData(Data_len, HeadPos):
    
    cur_td = 0
    cur_col = 0
    FirstName = ""
    LastName = ""
    HeadPos_len = len(HeadPos)
    
    while (cur_td < Data_len):
        if (cur_col==0):
            dataMap = {"player_id":None,"jersey_number":None,"first_name":None,"last_name":None,"team":None,"position":None}
        item = Data[cur_td]
        value = item.get_text()
        
        if ("data-person" in item.attrs):
            dataMap["player_id"] = item["data-person"]
        elif ("colspan" in item.attrs):
            cur_col += (int(item["colspan"]) - 1)
        
        #Map info
        if (HeadPos.get("Jersey#") == cur_col):
            dataMap["jersey_number"] = value
        elif (HeadPos.get("Name") == cur_col):
            FirstName = getFirstName(value)
            LastName = getLastName(value)
            dataMap["first_name"] = FirstName
            dataMap["last_name"] = LastName
        elif (HeadPos.get("Position") == cur_col):
            if (value != "-"):
                dataMap["position"] = value
        dataMap["team"] = curTeam
        
        cur_td += 1
        if (((cur_col+1) % HeadPos_len) == 0):
            store(dataMap["player_id"], dataMap["jersey_number"], 
                  dataMap["first_name"], dataMap["last_name"],
                  dataMap["team"], dataMap["position"])
            print(dataMap)
        cur_col += 1
        
        #Reset column
        if ((cur_col % HeadPos_len) == 0):
            cur_col = 0

#Get all team names
teams = getTeam(tablesObj)
teamNo = 0

#Header Names
headNames = ["Jersey#", "Name", "Position"]

#Get all player info
#loop through each table, and store it at the end
for table in tablesObj:
    curTeam = teams[teamNo].get_text()
    head = getHead(table)
    HeadPos = getHeadPos (headNames, head)
    
    Data = table.find_all("td")
    Data_len = len(Data)

    MapData(Data_len, HeadPos)
            
    teamNo += 1
    
cur.close()
conn.close()