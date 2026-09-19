#========LOAD MODULES====================
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
import langchain
from langchain.agents import create_agent
import langchain_community
from tavily import TavilyClient
import pytesseract as pyt
import streamlit as st
import os
import time
from PIL import Image
import pandas as pd
import numpy as np


#============API KEYS===================
TAVILY_API_KEY = "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"
GOOGLE_API_KEY = "AQ.Ab8RN6JWAS9vcT6ZtC2ESg_rNIZeGqWYdsVFLhUTgJ3htX3LuA"
GROQ_API_KEY =  "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"


#===========MODEL CREATION==============
model = ChatGoogleGenerativeAI(
    model = 'gemini-3.5-flash-lite',
    google_api_key = GOOGLE_API_KEY
)

response = model.invoke("Hello Buddy!")
response.content[-1]["text"]


#===========TOOL 1======================
def search_latest_news_jobs(query):
  """This function helps to fetch lastest
  news or jobs related article using
  tavily"""

  client = TavilyClient(
      api_key  = TAVILY_API_KEY)

  response = client.search(query)
  return response


#==========Agent Creation================
agent = create_agent(
    model = model,
    tools = [search_latest_news_jobs]
)
agent


#==============MAIN AGENT===============
def main_agent(agent, query):
  """This is the main agent, or leader agent
  orchestrate sub agents"""

  # Giving prompt to create detailed prompt
  # for code generation
  prompt = """You are AI assistant and
  below given is prompt, your
  task is to give detailed prompt for
  this.
  You are a professional Resume generator
  where user will give their personal info,
  you have to create detailed Resume
  for students or professional one,
  it must be with dynamic UI and UX and,
  with advanced CSS Professional Designing
  Make sure to give output in HTML format only
  no markdowns allowed
  """

  response = agent.invoke({"messages":[{'role':'user',
                                        'content':prompt}]})
  detailed_prompt = response['messages'][-1].content[-1]['text']

  # SAVE PROMPT using File Handling

  with open("prompt.txt",'w') as f:
    f.write(detailed_prompt)

  user_details = f"""Below Given is a user details
  generate Resume based on that, if not
  given keep: Default Resume: Python Developer
  user details: {query}"""

  final_prompt = prompt + detailed_prompt + user_details

  # CODE GENERATION

  response = agent.invoke({"messages":[{'role':'user',
                                        'content':final_prompt}]})

  code = response['messages'][-1].content[-1]['text']

  return code


#==========CALLING MAIN AGENT===============
info = """Name: Samir Khan
        Email: sksamirkhan@gmail.com
        Education: 12th from jindal public school
                   BCA from institue of innovation and management
        Target Role: DATA ANALYST
        Location: Dabri,Delhi
        professional summary: according to you
        work experiance: TCS 0-2 years as junior data analyst and infosys 0-5 as senior data analyst
        skills: python,java,sql,excel,power bi, word, canva"""
code = main_agent(agent,info)
from IPython import display as DISPLAY
DISPLAY.HTML(code)



#===========Fetch Latest Domain related Jobs using Tavily==========

def get_jobs(agent,Location = "Noida,Delhi",Profile = "ML Engineer"):
  Location = "Noida,Delhi"
  Profile = "Data Analysts, AI Engineer"
  prompt = f"""Based on user given Job profile,
  fetch latest jobs or job apply article
  using Naukri, Linkedin, Indeed, or all popular
  Job applyplatforms, Show Results with
  JOB PROFILE NAME, LOCATION, SALARY, COMPANY NAME,
  SHOW jobs only related to given
  {Location} and {Profile}, output must be in
  Professional HTML Naukri theme cards with Dynamic Design
  Show atleast Top 10-20 results with direct apply"""

  response = agent.invoke({"messages":[{'role':'user',
                                          'content':prompt}]})

  code = response['messages'][-1].content[-1]['text']

  return code

#========CALLING GET JOBS====================
code = get_jobs(agent)
DISPLAY.HTML(code)