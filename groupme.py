import os
from dotenv import load_dotenv
import json
import requests
from datetime import datetime, timezone

# load environment variables and jsons
load_dotenv()
API_TOKEN = os.environ.get("GROUPME_ACCESS_TOKEN")
with open("ids.json") as f:
    j = json.load(f)
    GROUP_ID = j["GROUP_ID"]
    USER_ID = j["USER_ID"]

# global variables
DCLUB = [USER_ID["aidan"], USER_ID["ben"], USER_ID["dubem"], USER_ID["lucas"], USER_ID["nate"]]
DBOT = USER_ID["dbot"]

def fetch(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["response"]

def getMessages(url):
    res = fetch(url)
    messages = res["messages"]
    if messages == []:
        return None, None
    filteredMessages = []
    for message in messages:
        filteredMessages.append({
            "created": datetime.fromtimestamp(message["created_at"]),
            "likes": message["favorited_by"],
            "id": message["id"],
            "name": message["name"],
            "sender_id": message["sender_id"],
            "text": message["text"],
        })
    lastMessageId = messages[-1]["id"] # for paging back
    return filteredMessages, lastMessageId

def getAllMessages(url):
    messages = getMessages(url)
    allMessages = []
    before_id = None
    while (True): # messages != None doesn't work because of an error with GroupMe's API
        allMessages.extend(messages[0])
        before_id = messages[1]
        try:
            messages = getMessages(url + "&before_id=" + before_id)
        except json.decoder.JSONDecodeError:
            break
    return allMessages

def printMessages(messages):
    content = ""
    for message in messages:
        created = message["created"].strftime("%b %d %Y %H:%M:%S")
        name = message["name"]
        text = message["text"]
        try:
            if (text != None):
                padding = " " * (25 + len(name))
                text = text.replace("\n", "\n" + padding)
                messageDetails = "(" + created + ") " + name + ": " + text
            else:
                messageDetails = "(" + created + ") " + name + ": <attachment>"
            print(messageDetails)
            content += messageDetails + "\n"
        except TypeError:
            messageDetails = "Cannot display <NoneType>\n"
            print(messageDetails)
            content += messageDetails + "\n"
    return content

def printConsecutiveDiff(consecutiveMessages):
    content = ""
    for messages in consecutiveMessages:
        content += printMessages(messages) + "---\n"
        print("---")
    summary = "Number of consecutive messages with different senders: " + str(len(consecutiveMessages))
    print(summary)
    content += summary + "\n"
    return content

# Instances in D Club where all 5 members send messages consecutively
def consecutiveDiff(sender_ids):
    url = "https://api.groupme.com/v3/groups/" + GROUP_ID["dclub"] + "/messages?token=" + API_TOKEN + "&limit=100"
    messages = getAllMessages(url)
    consecutiveMessages = []
    for i in range(len(messages) - 5):
        consecutiveSubset = []
        senders = []
        for j in range(5):
            message = messages[i+j]
            consecutiveSubset.append(message)
            senders.append(message["sender_id"])
        success = True
        for sender in sender_ids:
            success = success and (sender in senders) # len(senders) == len(set(senders))
        if success:
            consecutiveMessages.append(consecutiveSubset)
    content = printConsecutiveDiff(consecutiveMessages)
    with open("consecutiveDiff.txt", "w", encoding="utf-8") as f:
        f.write(content)
    return consecutiveMessages

# Percentage of D Club contributions in GLOZZ
def dclubInGlozz(glozzMessageCount):
    url = "https://api.groupme.com/v3/groups/" + GROUP_ID["glozz"] + "/messages?token=" + API_TOKEN + "&limit=100"
    messages = getAllMessages(url)
    filteredMessages = []
    dclubMessageCount = 0
    dbotMessageCount = 0
    for message in messages:
        id = message["sender_id"]
        if (id in DCLUB or id == DBOT):
            if (id == DBOT):
                dbotMessageCount += 1
            else:
                dclubMessageCount += 1
            filteredMessages.append(message)
    content = "Number of D Club messages: " + str(dclubMessageCount) + "\n"
    content += "Number of Dbot messages: " + str(dbotMessageCount) + "\n"
    content += "Number of GLOZZ messages: " + str(glozzMessageCount) + "\n"
    content += "---\n"
    content += "D Club messages in GLOZZ: " + '{0:.3g}%'.format(dclubMessageCount / glozzMessageCount * 100) + "\n"
    content += "D Club + Dbot messages in GLOZZ: " + '{0:.3g}%'.format((dclubMessageCount + dbotMessageCount) / glozzMessageCount * 100)
    print(content)
    return filteredMessages

def printGroupInfo(res):
    info = {
        "name": res["name"],
        "desc": res["description"],
        "members": [member["nickname"] for member in res["members"]],
        "messageCount": res["messages"]["count"],
        "lastMessageDate": datetime.fromtimestamp(res["messages"]["last_message_created_at"])
    }
    content = info["name"] + "\n"
    members = info["members"]
    for i in range(len(members)):
        content += members[i]
        if i != len(members) - 1:
            content += ", "
        else:
            content += "\n"
    content += "Description: " + info["desc"] + "\n"
    content += "Message count: " + str(info["messageCount"]) + "\n"
    content += "Last message sent: " + info["lastMessageDate"].strftime("%b %d %Y %H:%M:%S") + "\n"
    content += "-----\n"
    print(content)
    return info

def main():
    print(os.path.basename(__file__) + " is running...\n")
    try:
        url = "https://api.groupme.com/v3/groups/" + GROUP_ID["glozz"] + "?token=" + API_TOKEN
        res = fetch(url)
        info = printGroupInfo(res)

        # custom function starts
        dclubInGlozz(info["messageCount"])
        # custom function ends

    except requests.Exceptions.HTTPError as err:
        print(err)
    except:
        print("Error: main method terminated unexpectedly.")

if __name__ == "__main__":
    main()
    try:
        print("")
        # main()
    except:
        print("Usage: python groupme.py")
