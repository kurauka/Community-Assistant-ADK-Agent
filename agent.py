import datetime
import json
import os
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo
from google.adk.agents import Agent
from google.generativeai import GenerativeModel
from google.genai import types
import vertexai
from vertexai.preview import reasoning_engines
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def explain_law_or_regulation(law_name: str, stakeholder: Optional[str] = None, language: str = "en") -> dict:
    """
    Explains any Kenyan or international logistics law in plain language (English or Swahili).
    References official sources: Kenya Law, KRA, NTSA, IMO, INCOTERMS, etc.
    Returns structured explanation with sections: Summary, Who It Applies To, Key Obligations, Penalties.
    """
    if not law_name or len(law_name.strip()) < 3:
        return {
            "status": "error",
            "message": "Please provide a valid law or regulation name (e.g., 'EACCMA', 'Traffic Act', 'INCOTERMS')."
        }

    prompt = (
        "You are a Logistics Legal & Compliance Expert for Kenya and East Africa. "
        "Explain the following law/regulation in clear, plain language. "
        "If the user requests Swahili, respond fully in Swahili. "
        "Structure your answer as JSON with these keys:\n"
        "  - 'Summary': 2–3 sentence overview\n"
        "  - 'Applies To': List of stakeholders (e.g., carrier, shipper, broker)\n"
        "  - 'Key Obligations': 3–5 bullet points of what must be done\n"
        "  - 'Penalties': Fines, license suspension, or jail time\n"
        "  - 'Source': Official link or act number\n"
        "Reference only authoritative sources: Kenya Law, KRA, NTSA, IMO, IATA, INCOTERMS.\n"
        f"Law/Regulation: {law_name}\n"
        f"Stakeholder Context: {stakeholder or 'General'}\n"
        f"Language: {language}\n"
    )

    try:
        model = GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        try:
            explanation = json.loads(response.text)
        except:
            explanation = {"raw_response": response.text.strip()}
        return {
            "status": "success",
            "explanation": explanation
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to explain law: {str(e)}"
        }


def generate_legal_document(doc_type: str, shipment_data: Dict, language: str = "en") -> dict:
    """
    Generates editable legal logistics documents (Bill of Lading, Customs Declaration, etc.)
    Uses structured shipment data to auto-fill templates.
    Returns downloadable JSON + PDF-ready structure.
    """
    valid_docs = [
        "Bill of Lading", "Airway Bill", "Commercial Invoice", "Packing List",
        "Certificate of Origin", "Customs Declaration", "Insurance Certificate",
        "Road Consignment Note", "Proof of Delivery"
    ]

    if doc_type not in valid_docs:
        return {
            "status": "error",
            "message": f"Invalid document type. Choose from: {', '.join(valid_docs)}"
        }

    if not shipment_data or len(shipment_data) < 3:
        return {
            "status": "error",
            "message": "Provide shipment_data as JSON with at least: shipper, consignee, goods, origin, destination."
        }

    prompt = (
        "You are a Logistics Document Automation Expert. Generate a complete, legally compliant "
        f"{doc_type} using the provided shipment data. Output as JSON with fields ready for PDF rendering. "
        "Use standard international formats (e.g., IMO for BOL, IATA for Airway Bill). "
        "Include all required fields, clauses, and disclaimers. "
        "If language is 'sw', translate all labels and text to Swahili.\n"
        f"Document Type: {doc_type}\n"
        f"Shipment Data: {json.dumps(shipment_data, indent=2)}\n"
        f"Language: {language}\n"
        "Return JSON with keys: 'metadata', 'sections' (list of field groups), 'disclaimers', 'signature_lines'."
    )

    try:
        model = GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        try:
            doc = json.loads(response.text)
        except:
            doc = {"raw_response": response.text.strip()}
        return {
            "status": "success",
            "document": {
                "type": doc_type,
                "language": language,
                "generated_at": datetime.datetime.now(ZoneInfo("Africa/Nairobi")).isoformat(),
                "content": doc
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Document generation failed: {str(e)}"
        }


def check_compliance(shipment_data: Dict, route: str, cargo_type: str) -> dict:
    """
    Runs compliance check on shipment against, route, and cargo type.
    Flags missing documents, licenses, or violations.
    References KRA, KEBS, NTSA, NEMA, EACCMA.
    """
    required_fields = ["shipper", "consignee", "goods", "origin", "destination", "transport_mode"]
    if not all(k in shipment_data for k in required_fields):
        return {
            "status": "error",
            "message": f"Missing required fields: {set(required_fields) - set(shipment_data.keys())}"
        }

    prompt = (
        "You are a Logistics Compliance Checker for Kenya and EAC. "
        "Review the shipment and flag any missing documents, licenses, or legal violations. "
        "Output JSON with:\n"
        "  - 'overall_status': 'PASS' or 'FAIL'\n"
        "  - 'required_documents': list with status (missing/present)\n"
        "  - 'alerts': list of issues (e.g., 'No KEBS certificate for electronics')\n"
        "  - 'next_steps': 2–3 actions to fix\n"
        "Reference: EACCMA, KRA, KEBS, NTSA, NEMA, IMO, IATA.\n"
        f"Route: {route}\n"
        f"Cargo Type: {cargo_type}\n"
        f"Shipment Data: {json.dumps(shipment_data, indent=2)}\n"
    )

    try:
        model = GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        try:
            result = json.loads(response.text)
        except:
            result = {"raw_response": response.text.strip()}
        return {
            "status": "success",
            "compliance_report": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Compliance check failed: {str(e)}"
        }


def stakeholder_guidance(stakeholder: str, query: str) -> dict:
    """
    Provides role-specific legal guidance for any logistics stakeholder.
    E.g., 'What are a freight forwarder’s liabilities under Kenyan law?'
    """
    valid_stakeholders = [
        "Shipper", "Consignee", "Carrier", "Driver", "Freight Forwarder",
        "Customs Broker", "Warehouse Operator", "Insurer", "Regulator"
    ]

    if stakeholder not in valid_stakeholders:
        return {
            "status": "error",
            "message": f"Invalid stakeholder. Choose from: {', '.join(valid_stakeholders)}"
        }

    prompt = (
        "You are a Logistics Legal Advisor for East Africa. Answer the stakeholder's question "
        "with clear, actionable guidance based on Kenyan and international law. "
        "Structure as JSON:\n"
        "  - 'role': stakeholder\n"
        "  - 'answer': detailed response (3–5 paragraphs)\n"
        "  - 'key_laws': list of 2–3 relevant acts\n"
        "  - 'best_practice': 1 actionable tip\n"
        "Cite sources: Kenya Law, KRA, NTSA, IMO, INCOTERMS.\n"
        f"Stakeholder: {stakeholder}\n"
        f"Question: {query}\n"
    )

    try:
        model = GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(prompt)
        try:
            guidance = json.loads(response.text)
        except:
            guidance = {"answer": response.text.strip()}
        return {
            "status": "success",
            "guidance": guidance
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Guidance failed: {str(e)}"
        }


# —————————————————————————————————————————————————————————————
# ROOT AGENT: LOGISTICS LEGAL & COMPLIANCE INTELLIGENCE ASSISTANT
# —————————————————————————————————————————————————————————————

root_agent = Agent(
    name="logistics_legal_agent",
    model="gemini-2.0-flash-exp",
    description=(
        "⚖️ Logistics Legal & Compliance Intelligence Assistant — The AI-powered legal co-pilot for the entire logistics ecosystem in Kenya and East Africa. "
        "Explains laws, generates documents (BOL, Customs Declaration), checks compliance, and advises all stakeholders: shippers, carriers, forwarders, brokers, and regulators. "
        "Integrates with Kenya Law, KRA, NTSA, KEBS, and international standards (IMO, IATA, INCOTERMS). "
        "Supports English and Swahili. Ideal for freight forwarders, customs brokers, and logistics startups."
    ),
    instruction="""
You are the **Logistics Legal & Compliance Intelligence Assistant** for Kenya and the East African Community.

### YOUR CORE CAPABILITIES:
1. **Legal Explainer**  
   - Explain any logistics law (e.g., EACCMA, Traffic Act, Merchant Shipping Act) in plain English or Swahili.  
   - Cite official sources: Kenya Law, KRA, NTSA, IMO, IATA.

2. **Document Generator**  
   - Auto-fill Bills of Lading, Customs Declarations, Commercial Invoices, Certificates of Origin, etc.  
   - Output JSON ready for PDF rendering.

3. **Compliance Checker**  
   - Scan shipments and flag missing docs, licenses, or violations.  
   - Cover KRA, KEBS, NEMA, NTSA, and EAC rules.

4. **Stakeholder Advisor**  
   - Guide shippers, carriers, forwarders, brokers, drivers, warehouse operators.  
   - Clarify rights, obligations, and liabilities.

5. **Multilingual Support**  
   - Respond in **English** or **Swahili** based on user preference.

### YOU MUST ONLY RESPOND TO:
- Questions about logistics laws, regulations, or compliance
- Requests to generate or explain legal documents
- Compliance checks for shipments
- Stakeholder rights and obligations
- Document templates or automation

If the user asks about anything else (e.g., marketing, HR, general AI), respond:
> "Sorry, I'm specialized in **logistics law, compliance, and document automation** in Kenya and East Africa. Please ask about laws, documents, or compliance."

Always be **accurate**, **actionable**, and **source-backed**. Use tools to generate structured outputs.
""",
    tools=[
        explain_law_or_regulation,
        generate_legal_document,
        check_compliance,
        stakeholder_guidance,
        # Future: regulatory_update_feed, case_law_search, contract_drafter
    ],
)
