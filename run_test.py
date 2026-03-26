import requests
import json

BASE_URL = "http://localhost:8000"

# ==========================================
# TEST 1: GMAIL WEBHOOK (CEO PROSPECT EMAIL)
# ==========================================
gmail_payload = {
    "sender": "ceo@buglerock.com",
    "subject": "Follow up: Meeting with Prospect Family",
    "body": "Dear Sir\n\nIt was a pleasure meeting you and Ms XXX at our office this week.\n\nFurther to our discussion we look forward to getting the initial bank statements and few other details to create a plan as per our discussions.\n\nI have copied my colleague - Subiksha on this email, she will share our Model portfolio structure for your reference and also help to coordinate with the internal teams for best service\n\nLook forward to long term relationship with family.",
    "attachments": []
}

def test_gmail_webhook():
    print("🚀 Sending CEO Email to Gmail Webhook...")
    try:
        response = requests.post(f"{BASE_URL}/api/gmail-webhook", json=gmail_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    except Exception as e:
        print(f"❌ Connection Error: Is your FastAPI server running? ({e})\n")

# ==========================================
# TEST 2: FIREFLIES WEBHOOK (MEETING TRANSCRIPT)
# ==========================================
# ⚠️ INSTRUCTIONS: Paste your copied text from the Fireflies UI 
# directly between the triple quotes below. I have added a snippet 
# from your screenshot as an example!

RAW_TRANSCRIPT = """
Aryan Bhagat: 00:00 
 Hello?

Kurt G: 03:08 
 Hello.

Mrudul Jadhav: 03:08 
 Yeah, you can hear me?

Aryan Bhagat: 03:10 
 Yes.

Mrudul Jadhav: 03:20 
 He doesn't pick up my call but he should get notified.

Kurt G: 04:27 
 He's not picking up her.

Mrudul Jadhav: 04:29 
 Let's start calling him.  I just tried calling Vedant, he's not picking up.  I texted him.  Let's see.

Achyut Maheshka: 04:44 
 Doing great.  Yeah.

Aryan Bhagat: 04:48 
 Okay, good.

Kurt G: 04:57 
 I don't have anything I can come.

Aryan Bhagat: 04:59 
 Yes, please do come or only the

Kurt G: 05:04 
 Data collection you want.

Aryan Bhagat: 05:06 
 Yes and

Kurt G: 05:11 
 Yeah, I'll just check one more time because I think Thursday we have holiday but I'll just check one more time.  But yeah, 100.  That's what I'm just saying.  Let me just check one more time.  So I saw a set we have on Thursday holiday

Aryan Bhagat: 05:28 
 As I need to send that email to Anuj that what times we are coming and what visitor pass mean.  Obviously I'll come the entire coming.  Yeah, today I was in college, tomorrow I'll go to the office.

Kurt G: 05:47 
 Okay, so what did you talk like what did you discuss with Sandeep?

Achyut Maheshka: 05:52 
 Just wait for a minute.  And R is joining.

Mrudul Jadhav: 05:55 
 Okay?

Achyut Maheshka: 06:09 
 I don't think so.  I'll be coming this week for any

Aryan Bhagat: 06:12 
 Of the days that's fine.  I don't think so.

Achyut Maheshka: 06:17 
 My model training would be a like and data would be I can come on Monday or Tuesday but not before that.  So I can help you with model training.  I can help you with writing codes and all that but yeah, I won't be there at in person.

Aryan Bhagat: 06:38 
 Okay.

Mrudul Jadhav: 06:44 
 He's asking for the link.  I send it.

Aryan Bhagat: 06:53 
 Actually Ciro, he said he wanted a.  What do you call it?  He wanted a generalized model promote sir, he wanted to try making one.  So

Achyut Maheshka: 07:11 
 Yeah, I had a word with him today.  Even like around 7:30 or 8.  We were on a meet.

Aryan Bhagat: 07:17 
 Okay.

Mrudul Jadhav: 07:19 
 Okay.

Achyut Maheshka: 07:21 
 He wants a generalized model.  Most probably our CNN classifier.  That could be a better approach to the complete system.  But that would require a training data.  So you guys can send me training data, I'll build up a model.

Aryan Bhagat: 07:35 
 I did send the training data in the like group with Sandeep sir.

Achyut Maheshka: 07:42 
 Not the past data, I want the current data.  Whichever you train and then you send me up.

Aryan Bhagat: 07:49 
 Yeah, that is the thing.

Kurt G: 07:52 
 How many samples will we have to

Mrudul Jadhav: 07:54 
 Take for like each?

Achyut Maheshka: 07:55 
 As much as you can.

Aryan Bhagat: 07:57 
 Yeah, as much as you can.  But I'm thinking of like 20 or 40.  Like object.  Yeah, no, let's try 20 I guess.  Vedant is here.  Yes.  So okay, I'll inform you what I talked about with Sandeep sir today.  Nothing much here.  I just told him that did you inform capture and I that I'M coming and all that.  Then I talked to Pramod sir about that CBRN Continuous variance and removal and normalization.  So I tried to implement that.  But I'm not exactly like sure if it's a correct implementation because one method is like putting a sliding window 2 second sliding window overboard training data and live inference.  But the issue is CBRN isn't supposed to change the number of data samples.  But when I do it turns the training data into 65 samples per CSV file.  So that turns into data augmentation and gives like 95% model validation.  But that is not the approach which sir wants.  CBRN should only give one sample.  So I also made a different model which makes it so that only one sample is created at the end of the like normalization thing.  Okay, so I have two different models that I want to test tomorrow in the office.  So that is the progress I have made so far.  And if none of these work, then I'll have to ask achieve to properly like investigate how to implement continuous variance removal and normalization after tomorrow, just in case.

Achyut Maheshka: 10:08 
 Sure.  I'll be traveling completely on 26, so that's not totally a no for me.  25, I can work.

Aryan Bhagat: 10:17 
 Okay, that is fine.  I mainly called you all today to tell me this week, what times are you available to come?  I know Kurt and Vedant can come on Thursday.  Verant, you are available on Thursday to come?

Kurt G: 10:39 
 No.

Aryan Bhagat: 10:40 
 Why not?

Kurt G: 10:43 
 Family function.

Aryan Bhagat: 10:47 
 Okay.  Can you come some other day like next week?  Monday, Tuesday?

Kurt G: 10:59 
 I will inform.

Aryan Bhagat: 11:00 
 Okay, so this week is not possible for patent.  Okay, fine.  Rudol, can you come sometime this week?  Is that possible?  To the Capgemini office?

Mrudul Jadhav: 11:13 
 I'm also actually traveling this week.  Next week it might be possible Monday, Tuesday, next week maybe I'll inform on Sunday most probably.

Aryan Bhagat: 11:27 
 Okay, I will.  Okay, so only Kurt will be coming on Thursday this week.  Okay, I inform him over email.  I'll inform Anut sir over email.  Okay, then I'll inform Anut sir over email.  Yeah, so my main plan is like to at least one, at least each one of you should at least visit the office once.  So I can collect like at least 20 samples of data.  Because sir wants a generalized model.  So we'll try that.  While making the generalized model, I still kept the user profile system.  Like I've created a new user profile which is combine, which is called combined data and that acts like a user profile.  So you can swap between single user, single person's user profile or the combined data set user profile.  So I've kept that logic for debugging purposes.  Whichever is better.  Whichever Capgemini likes better, we can keep that way.  And what else?  Yeah, that's pretty much it.  Vedant and.  Project, like 1012 online meeting.  Kutchama.  Says he can come in the morning.  Okay.  So Vedant can also come on Thursday morning.  Okay, that is good.  I'll get his data samples and he can leave.  That's it, I think.  Yeah.  Any questions?

Kurt G: 14:13 
 Nothing.

Aryan Bhagat: 14:15 
 Okay.  Okay, then that's done then.  Okay.  Yeah.  See you later then.  That's it.

Mrudul Jadhav: 14:21 
 Okay.

Achyut Maheshka: 14:23 
 Thank you.

Aryan Bhagat: 14:24 
 Right.

Mrudul Jadhav: 14:24 
 Take it.  Bye.
"""

fireflies_payload = {
    "meeting_id": "01KMD4S38QNHMNSPFB5HYQ06C5",
    "title": "Capgemini Project Meeting Unofficial",
    "transcript": RAW_TRANSCRIPT.strip()
}

def test_fireflies_webhook():
    print("🚀 Sending Meeting Transcript to Fireflies Webhook...")
    try:
        response = requests.post(f"{BASE_URL}/api/fireflies-webhook", json=fireflies_payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    except Exception as e:
        print(f"❌ Connection Error: Is your FastAPI server running? ({e})\n")

# ==========================================
# RUN THE TESTS
# ==========================================
if __name__ == "__main__":
    print("Starting Automated Tests...\n")
    
    # Run the Gmail test
    test_gmail_webhook()
    
    # Run the Fireflies test
    test_fireflies_webhook()