from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .mcp_connectors import query_regulatory_db
import os

from dotenv import load_dotenv
load_dotenv()


llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))

def apply_demo_rules(ingredient: str, conc: str):
    try:
        val = float(conc.replace("%", "").strip())
    except:
        return "✅ Compliant"

    rules = {
        "Methylparaben": 0.4,
        "Titanium Dioxide": 25.0,
        "Myristica Fragrans Powder": 0.001,
    }

    if ingredient in rules and val > rules[ingredient]:
        return f"⚠️ Non-compliant (limit {rules[ingredient]}%)"
    return "✅ Compliant"
async def check_formulation(name: str, ingredients: dict):
    validation_results = []

    # Step 1: Build validation results (rules + Atlas search)
    for ingredient, conc in ingredients.items():
        reg_info = query_regulatory_db(ingredient)  # <-- Atlas Hybrid Search
        status = apply_demo_rules(ingredient, conc)

        validation_results.append({
            "ingredient": ingredient,
            "concentration": conc,
            "status": status,
            "regulatory_info": reg_info
        })

    # Step 2: Force GPT to use ONLY these results
    prompt = ChatPromptTemplate.from_template("""
You are a Regulatory Intelligence Agent.

You are given structured validation results:

{results}

RULES:
- ONLY use the ingredients in results.
- Do NOT add extra ingredients.
- Use this exact Markdown structure (no variations):

Compliance Report: {name}

### Safe Ingredients

- <Ingredient Name> (<Concentration>)  
  - **Status:** ✅/⚠️  
  - **Regulatory Info:** short summary  
  - **Functions:** from DB if available  

### Flagged Ingredients

- <Ingredient Name> (<Concentration>)  
  - **Status:** ⚠️ Non-compliant (limit X%)  
  - **Regulatory Info:** short summary  
  - **Issue:** reason  
  - **Safer Alternatives:** list  

### Summary

<Narrative summary>

IMPORTANT: 
- Always use bullets `-` for every line. 
- Never use `##` headings inside ingredients.
- Keep text concise and wrap at ~80 chars.
""")

    final_report = llm.invoke(
        prompt.format_messages(name=name,results=validation_results)
    )

    return {
        "raw_results": validation_results,    # for green/red UI cards
        "markdown_report": final_report.content  # for narrative
    }
