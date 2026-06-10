import re
import streamlit as st
from database import get_db_instance
from utils import fix_arabic_for_terminal, make_links_clickable, log_to_file_and_terminal
from prompts import build_system_prompt, get_drug_prompt
from search_service import get_altibbi_context, get_serper_context, get_manual_scrape_context

from llm_service import (
    refine_query, generate_dynamic_fallback, classify_uploaded_image, 
    analyze_image_with_prompt, extract_drug_name_from_image, call_text_model,
    generate_follow_ups
)
from eval_service import trigger_eval
import logging

logging.basicConfig(
    level=logging.INFO, 
    format="\n%(asctime)s | [%(levelname)s] | %(message)s",
    datefmt="%H:%main:%S"
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Altibbi Chatbot", layout="wide")
db = get_db_instance()

if "messages" not in st.session_state: st.session_state.messages = []
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

with st.sidebar:
    st.title("Settings")
    selected_model = st.radio("Used Model:", ["GPT-4o mini", "Gemini 2.5 Flash Lite"])
    search_method = st.selectbox("Context Retrieval Method:", ["Serper", "Tavily", "Manual Scraping"])

    if st.button("New Chat", use_container_width=True):
        st.session_state.messages, st.session_state.current_chat_id = [], None
        st.rerun()
    
    st.divider()
    st.subheader("Recent History")
    for chat in db.get_all_history(limit=15) or []:
        chat_label = chat.get("chat_title") or chat.get("last_preview", "Empty Chat")[:25] + "..."
        col1, col2 = st.columns([0.8, 0.15])
        
        if col1.button(chat_label, key=f"load_{chat['_id']}", use_container_width=True):
            st.session_state.messages = db.get_chat_by_id(str(chat["_id"])) or []
            st.session_state.current_chat_id = str(chat["_id"])
            st.rerun()
            
        with col2.popover("⋮"):
            if st.button("Delete", key=f"del_{chat['_id']}", type="primary"):
                db.delete_chat(str(chat["_id"]))
                if st.session_state.current_chat_id == str(chat["_id"]):
                    st.session_state.messages, st.session_state.current_chat_id = [], None
                st.rerun()

def execute_rag_pipeline(actual_query, selected_model, search_method):
    with st.spinner("Searching Altibbi..."):
        refine_result = refine_query(actual_query, st.session_state.messages, selected_model)
        lq, chat_title, lang = refine_result["refined_query"], refine_result["chat_title"], refine_result["language"]
        
        search_funcs = {"Serper": get_serper_context, "Tavily": get_altibbi_context, "Manual Scraping": get_manual_scrape_context}
        new_context, new_sources, raw_urls = search_funcs.get(search_method, get_serper_context)(lq)

    if not new_sources: 
        with st.spinner("Refining guidance..."): fallback_msg = generate_dynamic_fallback(actual_query, lang, selected_model)
        st.session_state.messages.append({"role": "assistant", "content": fallback_msg, "sources": {}})
        st.chat_message("assistant").markdown(fallback_msg)
        
        new_id, _ = db.log_interaction(
            st.session_state.current_chat_id, actual_query, fallback_msg, {"query": lq}, {}, 
            {"model": selected_model, "method": search_method, "chat_title": chat_title, "language": lang, "status": "fallback"}
        )
        if not st.session_state.current_chat_id: st.session_state.current_chat_id = new_id
        st.rerun()
        return

    with st.spinner("Consulting Altibbi AI..."):
        sys_prompt = build_system_prompt(new_context, lang)
        prompt = f"Please provide medical information about: {actual_query}"
        
        # Inject OCR context if previous message was drug identification
        if st.session_state.get("is_ocr_query"):
            prompt = get_drug_prompt(actual_query, lang)
            st.session_state.is_ocr_query = False
            
        ai_reply = call_text_model(prompt, selected_model, system_prompt=sys_prompt, history=st.session_state.messages)
        used_sources = {k: v for k, v in new_sources.items() if str(k) in set(re.findall(r"\[(\d+)\]", ai_reply))}

        st.session_state.messages.append({"role": "assistant", "content": ai_reply, "sources": used_sources})
        
        log_to_file_and_terminal(actual_query, lq, raw_urls, new_sources, new_context, ai_reply)

        suggestions = generate_follow_ups(actual_query, ai_reply, lang, selected_model)
        if suggestions:
            st.session_state.messages[-1]["suggestions"] = suggestions #  save them specifically to the last message object

        with st.chat_message("assistant"):
            st.markdown(make_links_clickable(ai_reply, used_sources))
            if used_sources:
                with st.expander("View Sources"):
                    for sid, link in used_sources.items(): st.write(f"[{sid}] {link}")

        new_id, msg_id = db.log_interaction(
            st.session_state.current_chat_id, actual_query, ai_reply, {"query": lq}, used_sources, 
            {"model": selected_model, "method": search_method, "chat_title": chat_title, "language": lang}
        )
        
        trigger_eval(db, msg_id, actual_query, ai_reply, new_context)
        
        if not st.session_state.current_chat_id:
            st.session_state.current_chat_id = new_id
        
        st.rerun() # bubbles

st.title("Altibbi Chatbot")

for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        # Render the main message content
        st.markdown(make_links_clickable(message["content"], message.get("sources", {})))
        
        # Render sources if they exist
        sources = message.get("sources", {})
        if sources:
            with st.expander("Sources", expanded=False):
                for sid, link in sources.items():
                    st.markdown(f"- [{sid}] {link}")
            
        # Render Suggestions Bubbles ONLY under the very last assistant message
        if message["role"] == "assistant" and idx == len(st.session_state.messages) - 1 and message.get("suggestions"):            
            cols = st.columns(len(message["suggestions"]))
            for i, sugg in enumerate(message["suggestions"]):
                # Unique key based on index and suggestion text
                unique_key = f"sugg_btn_{idx}_{hash(sugg + str(i))}"
                if cols[i].button(sugg, key=unique_key, use_container_width=True):
                    st.session_state.pending_action = sugg
                    st.rerun()

user_input = st.chat_input("Ask Altibbi... ", accept_file=True, file_type=["png", "jpg", "jpeg"])

# if a suggestion button was clicked
if "pending_action" in st.session_state and st.session_state.pending_action:
    simulated_query = st.session_state.pending_action
    st.session_state.pending_action = None # Clear it immediately
    
    st.chat_message("user").markdown(simulated_query)
    st.session_state.messages.append({"role": "user", "content": simulated_query})
    execute_rag_pipeline(simulated_query, selected_model, search_method)

elif user_input:
    if user_input.files:
        img_file = user_input.files[0]
        img_bytes = img_file.getvalue()
        user_msg = f"[Uploaded an Image: {img_file.name}]{f' (Message: {user_input.text})' if user_input.text else ''}"
        
        st.session_state.messages.append({"role": "user", "content": user_msg})
        st.chat_message("user").markdown(user_msg)
            
        with st.spinner("Classifying image type..."): img_type = classify_uploaded_image(img_bytes, selected_model)
        logger.info(f"Vision Layer Detected Type: {img_type}")
        
        if img_type not in ["report", "drug"]:
            reply = "هذا النوع من الصور غير مدعوم. يرجى رفع صورة لتحاليل طبية أو دواء."
            st.session_state.messages.append({"role": "assistant", "content": reply, "sources": {}})
            st.chat_message("assistant").markdown(reply)
            db.log_interaction(st.session_state.current_chat_id, user_msg, reply, metadata={"model": selected_model, "content_type": "unsupported"})
            st.rerun()
            
        elif img_type == "report":
            with st.spinner("Analyzing report..."): reply = analyze_image_with_prompt(img_bytes, img_type, selected_model)
            st.session_state.messages.append({"role": "assistant", "content": reply, "sources": {}})
            st.chat_message("assistant").markdown(reply)
            new_id, _ = db.log_interaction(st.session_state.current_chat_id, user_msg, reply, metadata={"model": selected_model, "content_type": "report"})
            if not st.session_state.current_chat_id: st.session_state.current_chat_id = new_id
            st.rerun()

        elif img_type == "drug":
            with st.spinner("Extracting medication..."): drug_name = extract_drug_name_from_image(img_bytes, selected_model)
            logger.info("Extracted Drug Name: '{drug_name}'")
            st.session_state.is_ocr_query = True
            execute_rag_pipeline(drug_name, selected_model, search_method)

    elif user_input.text:
        st.chat_message("user").markdown(user_input.text)
        st.session_state.messages.append({"role": "user", "content": user_input.text})
        execute_rag_pipeline(user_input.text, selected_model, search_method)