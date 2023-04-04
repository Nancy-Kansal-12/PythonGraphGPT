from bs4 import BeautifulSoup
import requests
import win32api
import json
from tkinter import *
import time
from flask import Flask, render_template



DEFAULT_PARAMS = { 
  "model": "text-davinci-003",
  "temperature": 0.3,
  "max_tokens": 800,
  "top_p": 1,
  "frequency_penalty": 0,
  "presence_penalty": 0
}

SELECTED_PROMPT = "STATELESS"

options = { "layout": { "hierarchical": False }, "edges": {"color": "#34495e" } }

class App :
    
    def __init__(self) :
        self.setGraphState({ "nodes": [], "edges": []})
        return 
    
    def setGraphState(self, value) :
        self.graphState = value 
        return      
    
    def clearState(self) :
        self.setGraphState({"nodes": [], "edges": []})
        return
    
    def findNode(self, nodeList, entity) :
        node = None
        for each in nodeList :
            if each["id"] == entity :
                node = each
                break
        return node
    
    def findEdge(self, edgeList, entity1, entity2) :
        edge = None
        for each in edgeList :
            if each["id"] == entity1 and each["to"] == entity2 :
                edge = each
                break
        return edge
    
    def changeCursor(self, value) :
        root = Tk()
        root.config(cursor=value)
        root.update()
        time.sleep(5)
        root.config(cursor="")

    
    def updateGraph(self,updates) :
        
        current_graph = self.graphState
        
        if (updates.len() == 0) :
            return  
        
        if (type(updates[0]) == str) :
            updates = [updates] 
            
        for update in updates :
            if (update.length == 3) :
                [entity1, relation, entity2] = update
                
                node1 = self.findNode(current_graph["nodes"], entity1)
                node2 = self.findNode(current_graph["nodes"], entity2)
                    
                if (node1 == None) :
                    current_graph["nodes"].append({ "id": entity1, "label": entity1, "color": "#ffffff" })
                    
                if (node2 == None) :
                    current_graph["nodes"].append({ "id": entity2, "label": entity2, "color": "#ffffff" })
                    
                edge = self.findEdge(current_graph["edges"], entity1, entity2)
                
                if (edge != None) :
                    edge["label"] = relation
                    return
                
                current_graph["edges"].append({"from": entity1, "to": entity2, "label": relation })
                
            elif (update.length == 2 and update[1].startswith("#")) :
                [entity, color] = update
                
                node = self.findNode(current_graph["nodes"], entity)
                    
                if (node == None) :
                    current_graph["nodes"].append({"id": entity, "label": entity, "color": color })
                    return
                
                #  update the color of the node
                node[color] = color
                
            elif (update.length == 2 and update[0] == "DELETE") :
                #  delete the node at the given index
                [_, index] = update

                #  check if the node already exists
                node = self.findNode(current_graph["nodes"], index)
                
                if (node == None) :
                    return

                # delete the node
                nodeArray = []
                
                for each in current_graph["nodes"] :
                    if (each["id"]!=index) :
                        nodeArray.append(each)
                        
                current_graph["nodes"] = nodeArray

                # delete all edges that contain the node
                edgeArray = []
                
                for each in current_graph["edges"] :
                    if (each["from"]!=index and each["to"]!=index) :
                        edgeArray.append(each)
                        
                current_graph["edges"] = edgeArray
                
                
        self.setGraphState(current_graph)
        
        
    def queryStatelessPrompt(self, prompt, apiKey) :
        
        # fetch
        fp = open(r'prompts/stateless.prompt', 'r')
        fp.replace("$prompt", prompt)
        # read file
        print(fp.read())

        
        params = {"prompt": fp , "stop": "\n"}
        
        params.update(DEFAULT_PARAMS)
        
        fp.close()
        
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + str(apiKey)}
        
        try:
            response = requests.post("https://api.openai.com/v1/completions", headers, json=params)
        except requests.exceptions.RequestException as e: 
            win32api.MessageBox("Error")
            raise SystemExit(e)
        
        if (not(response.ok)) :
            status = response.status_code
            if (status == 401) :
                raise Exception("Please double-check your API key.")
            elif (status == 429) :
                raise Exception("You exceeded your current quota, please check your plan and billing details.")
            else :
                raise Exception("Something went wrong with the request, please check the Network log")
            
        else :
            
            choices = response["choices"]
            text = choices[0]["text"]
            print(text)
            
            updates = json.load(text)
            print(updates)
            
            self.updateGraph(updates)
            
            soup = BeautifulSoup(self.content(), 'html.parser')
            
            soup.find('input', class_="searchBar").value = ""
            self.changeCursor("default")
            soup.find('input', class_="generateButton").disabled = False
            
        return
    
    def queryStatefulPrompt(self, prompt, apiKey) :
        
        # fetch
        fp = open(r'prompts/statelful.prompt', 'r')
        fp.replace("$prompt", prompt)
        fp.replace("$state", str(self.graphState))
        # read file
        print(fp.read())
        
        params = {"prompt": fp , "stop": "\n"}
        
        params.update(DEFAULT_PARAMS)
        
        fp.close()
        
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + str(apiKey)}
        
        try:
            response = requests.post("https://api.openai.com/v1/completions", headers, json=params)
        except requests.exceptions.RequestException as e: 
            win32api.MessageBox("Error")
            raise SystemExit(e)
        
        if (not(response.ok)) :
            status = response.status_code
            if (status == 401) :
                raise Exception("Please double-check your API key.")
            elif (status == 429) :
                raise Exception("You exceeded your current quota, please check your plan and billing details.")
            else :
                raise Exception("Something went wrong with the request, please check the Network log")
            
        else :
            
            choices = response["choices"]
            text = choices[0]["text"]
            print(text)
        
            new_graph = json.load(text)
            
            self.setGraphState(new_graph)
            
            soup = BeautifulSoup(self.content(), 'html.parser')
            
            soup.find('input', class_="searchBar").value = ""
            self.changeCursor("default")
            soup.find('input', class_="generateButton").disabled = False
        return
    
    def queryPrompt(self, prompt, apiKey) :
        
        soup = BeautifulSoup(self.content(), 'html.parser')
        
        if (SELECTED_PROMPT == "STATELESS") :
            self.queryStatelessPrompt(prompt, apiKey)
        elif (SELECTED_PROMPT == "STATEFUL") :
            self.queryStatefulPrompt(prompt, apiKey)
        else :
            win32api.MessageBox("Please select a prompt")
            self.changeCursor("default")
            soup.find('input', class_="generateButton").disabled = False
        return
    
    def createGraph(self) :
        
        soup = BeautifulSoup(self.content(), 'html.parser')
        data = soup.find('button', class_="generateButton")
        print(data)
        # soup.find_all('button', {'class': 'inputContainer'})[0].disabled = True
        
        self.changeCursor("wait")

        prompt = soup.find('input', class_="searchBar").value
        apiKey = soup.find('input', class_="apiKeyTextField").value

        self.queryPrompt(prompt, apiKey)
        return
    
    def content(self) :
        return ("""<script>
        function createGraph(){
            var request = new XMLHttpRequest()
            request.open("GET", "/createGraph" , true)
            request.send()
        }
    </script>
    <script>
        function clearState(){
            var request = new XMLHttpRequest()
            request.open("GET", "/clearState" , true)
            request.send()
        }
    </script>
    <div class='container'>
      <h1 class="headerText">GraphGPT 🔎</h1>
      <p class='subheaderText'>Build complex, directed graphs to add structure to your ideas using natural language. Understand the relationships between people, systems, and maybe solve a mystery.</p>
      <p class='opensourceText'><a href="https://github.com/varunshenoy/graphgpt">GraphGPT is open-source</a>&nbsp;🎉</p>
      <center>
        <div class='inputContainer'>
          <input class="searchBar" placeholder="Describe your graph..."></input>
          <input class="apiKeyTextField" type="password" placeholder="Enter your OpenAI API key..."></input>
          <button class="generateButton" onClick="createGraph()">Generate</button>
          <button class="clearButton" onClick="clearState()">Clear</button>
        </div>
      </center>
      <div class='graphContainer'>
        <Graph graph={graphState} options={options} style={{ height: "640px" }} />
      </div>
      <p class='footer'>Pro tip: don't take a screenshot! You can right-click and save the graph as a .png  📸</p>
    </div>""")
        
app = Flask(__name__)

appGraphGPT = App()

@app.route('/')
def indexpage():
    return appGraphGPT.content()

@app.route('/createGraph')
def createGraph() :
    appGraphGPT.createGraph()
    
@app.route('/clearState')
def clearState() :
    appGraphGPT.clearState()

if __name__ == '__main__':
    port = 8000 #the custom port you want
    app.run(host='0.0.0.0', port=port)
        