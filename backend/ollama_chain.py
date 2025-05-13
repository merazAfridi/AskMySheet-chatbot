import requests
import json
import os

# prompt
PROMPT_TEMPLATE = """You are a data analysis assistant. Answer questions ONLY using the data provided in the spreadsheet. DO NOT use any external knowledge.

Rules:
- Use ONLY the data provided in the spreadsheet
- NEVER make assumptions or use external knowledge
- If the data doesn't contain the answer, say "I cannot find this information in the provided data"
- Keep answers concise and direct
- Use bullet points for multiple items if needed
- Include exact numbers from the data
- Answer should be 1-2 lines maximum if user do not ask for more details



Data:
Name: {spreadsheet_name}
Columns: {total_columns}
Rows: {total_rows}

Summary:
{data_summary}

Columns:
{column_descriptions}

Actual Data:
{actual_data}

Question: {user_question}
Answer:"""

def format_prompt(user_question, spreadsheet_data=None, conversation_history=None):
    #default data if none provided
    if spreadsheet_data is None:
        spreadsheet_data = {
            "name": "Unknown",
            "sheets": ["Sheet1"],
            "columns": "Unknown",
            "rows": "Unknown",
            "time_period": "Unknown",
            "summary": "No summary available.",
            "column_descriptions": "No column descriptions available.",
            "data": "No data available."
        }
    
    try:
        #format data summary
        data_summary = spreadsheet_data.get("summary", "No summary available.")
        if hasattr(data_summary, 'to_dict'):
            data_summary = data_summary.to_string()
        
        # format column descriptions
        col_descriptions = spreadsheet_data.get("column_descriptions", "No column descriptions available.")
        if hasattr(col_descriptions, 'to_dict'):
            col_descriptions = col_descriptions.to_string()
        
        #format actual data
        actual_data = spreadsheet_data.get("data", "No data available.")
        if isinstance(actual_data, list):
            actual_data = json.dumps(actual_data, indent=2)
        
        #fill template
        filled_prompt = PROMPT_TEMPLATE.format(
            spreadsheet_name=spreadsheet_data.get("name", "Unknown"),
            total_columns=spreadsheet_data.get("columns", "Unknown"),
            total_rows=spreadsheet_data.get("rows", "Unknown"),
            data_summary=data_summary,
            column_descriptions=col_descriptions,
            actual_data=actual_data,
            user_question=user_question
        )
    except Exception as e:
        filled_prompt = "Answer data questions with bullet points only, using only the provided data."
    
    return filled_prompt

def convert_to_serializable(obj):
    #convert objects to serializable format
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return str(obj)
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    else:
        return obj

def ask_llm(prompt, model="deepseek-r1", spreadsheet_data=None, conversation_history=None):
    try:
        #make data serializable
        if spreadsheet_data:
            spreadsheet_data = convert_to_serializable(spreadsheet_data)
        
        #format prompt
        formatted_prompt = format_prompt(prompt, spreadsheet_data, conversation_history)
        
        #call ollama api
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": formatted_prompt,
                "stream": False
            },
            timeout=1200
        )
        
        if response.status_code == 200:
            raw_response = response.json().get("response", "No response received")
            
            #clean response
            if raw_response.startswith(("Based on", "Looking at", "According to", "From the", "In the", "The data")):
                bullet_points = [line.strip() for line in raw_response.split('\n') if line.strip().startswith('•')]
                if bullet_points:
                    return '\n'.join(bullet_points)
            
            return raw_response
        else:
            return f"Error: Received status code {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Ollama: {str(e)}"
    except json.JSONDecodeError as e:
        return f"Error processing JSON response: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}" 