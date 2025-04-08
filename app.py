from retrieval import api_utils_graphrag, api_utils_rag
import streamlit as st


st.set_page_config(page_title="Academic Advisor", layout="wide")
with open("ui/custom_styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 🔗 Inject Font Awesome for social icons
# Force-load Font Awesome icons for use in HTML
st.markdown("""
    <script src="https://kit.fontawesome.com/your-kit-id.js" crossorigin="anonymous"></script>
""", unsafe_allow_html=True)

# ---------- Sidebar Navigation ----------
# st.sidebar.image(
#     "https://logodix.com/logo/879808.png",
#     use_column_width=True
# )
# 🔵 Logo image at the top of sidebar
# 🔵 Sidebar logo image (scaled, centered)
st.sidebar.markdown(
    """
    <div style='text-align: center; padding: 0px 0 10px 0;'>
        <img src='https://manageimages-prod.s3.amazonaws.com/1632854912486-428046443.jpg'
             width='250' style='border-radius: 10px;' />
    </div>
    """,
    unsafe_allow_html=True
)

menu = st.sidebar.radio("Navigate",
                        ["Home", "About", "Contact US", "Documentation", "Future Developments", "💡How to Use"])
# Sidebar Logo or Image

# --- File Upload in Sidebar ---
st.sidebar.markdown("### 📥 Upload a File")
uploaded_file = st.sidebar.file_uploader("Upload academic material (PDF, CSV, etc.)", type=["pdf", "csv", "txt"])

if uploaded_file:
    st.sidebar.success(f"Uploaded: {uploaded_file.name}")
    # Optional: process or store the file
    # file_bytes = uploaded_file.read()
    # st.sidebar.write(file_bytes[:100])  # preview first 100 bytes

# ---------- Session State Initialization ----------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi there! How can I assist you today?"}]
if "header_shown" not in st.session_state:
    st.session_state.header_shown = True
if "all_rephrased_queries" not in st.session_state:
    st.session_state.all_rephrased_queries = []
if "last_rephrased_query" not in st.session_state:
    st.session_state.last_rephrased_query = ""


# ---------- Global Styles ----------
st.markdown("""
    <style>
        body, .stApp {
            background-color: #F8F9FA;
            margin: 0;
            padding-bottom: 60px;  /* Make space for footer */
        }

        .header-block {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            margin-top: 3rem;
            margin-bottom: 2rem;
        }

        .header-block img {
            width: 120px;
            height: auto;
            margin-bottom: 1rem;
        }

        .header-block h1 {
            font-size: 2.7rem;
            font-weight: bold;
            color: #16325c;
            margin: 0;
        }
        
        .SubHeading-block h4 {
            font-size: 1.7rem;
            font-weight: bold;
            color: #16325c;
            margin: 0;
        }
        .header-block .subtitle {
            font-size: 1.1rem;
            font-weight: bold;
            color: #16325c;
            margin-top: 0.5rem;
        }
        .stChatMessageContent, .stMarkdown, .stMarkdown p {
            color: #111 !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #16325c !important;
            color: white !important;
        }

        section[data-testid="stSidebar"] * {
            color: white !important;
        }

        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stFileUploader label {
            color: white !important;
            font-weight: 600;
        }


        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #16325c;
            color: white;
            text-align: center;
            padding: 10px 0;
            font-size: 14px;
            z-index: 100;
        }
    </style>
""", unsafe_allow_html=True)

# ---------- Page Content ----------
if menu == "Home":
    if st.session_state.header_shown:
        st.markdown("""
            <div class="header-block">
                <img src="http://d28htnjz2elwuj.cloudfront.net/wp-content/uploads/2013/11/Indiana_State_University_Logo.jpg" />
                <h1 style="margin-bottom: 0;">ISU Course Genie AI 🧞</h1>
                <p style="margin-top: 0; font-weight: bold; font-size: 0.9rem; color: #16325c;">
                    Presented by ECET Department from Bailey College of Engineering and Technology
                </p>
            </div>
        """, unsafe_allow_html=True)

    # 🔄 Reset button (only after user sends a message)
    if not st.session_state.header_shown:
        if st.button("🔄 Reset Chat View"):
            st.session_state.messages = [{"role": "assistant", "content": "Hi there! How can I assist you today?"}]
            st.session_state.header_shown = True
            st.experimental_rerun()

    ## ✅ Retrieval Mode Selector using Dropdown
    st.markdown(""" <div class="SubHeading-block">
                        <h4 style="margin-bottom: 0;">🤖 Pick Your AI Advisor Mode</h1>
                     </div>
                     """, unsafe_allow_html=True)
    retrieval_mode_options = {"1": "Graph Genie Mode (GraphRAG)", "2": "Direct Genie Mode (RAG)"}
    selected_mode_key = st.selectbox(
        "Choose a mode:",
        options=list(retrieval_mode_options.keys()),
        format_func=lambda x: f"{x}. {retrieval_mode_options[x]}"
    )
    st.session_state.retrieval_mode = retrieval_mode_options[selected_mode_key]

    st.markdown("</div>", unsafe_allow_html=True)

    # 💬 1. Chat Input at the top
    user_input = st.chat_input("Type your question...")

    st.markdown("""
           <style>
               .stChatMessage.user .stMarkdown {
                   background-color: #6c757d;
                   color: white !important;
                   padding: 12px;
                   border-radius: 10px;
               }

               .stChatMessage.assistant .stMarkdown {
                   background-color: #f1f3f4;
                   color: black !important;
                   padding: 12px;
                   border-radius: 10px;
               }
           </style>
       """, unsafe_allow_html=True)
    if user_input:
        st.session_state.header_shown = False
        st.session_state.messages.append({"role": "user", "content": user_input})

        if st.session_state.retrieval_mode == "Direct Genie Mode (RAG)":
            # st.session_state.header_shown = False
            # st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner("Rephrasing and finding matching programs..."):
                rephrased, programs = api_utils_rag.initial_program_matches(user_input,
                                                                        chat_history=st.session_state.last_rephrased_query)
                st.session_state.last_rephrased_query = rephrased  # ✅ Save the latest

            # ✅ Store for later use
            st.session_state.rephrased_query = rephrased
            st.session_state.all_rephrased_queries.append(rephrased)
            st.session_state.program_options = programs
            st.write("🔁 Re-computed rephrased:", rephrased)

            if programs:
                # assistant_reply = f"**Rephrased Query:** {rephrased}\n\nFound related programs:\n\n" + \
                #                   "\n".join([f"- {prog}" for prog in programs])
                assistant_reply = "**Related Programs Found:**\n\n" + \
                                  "\n".join([f"{i + 1}. {prog}" for i, prog in enumerate(programs)])

            else:
                assistant_reply = "Sorry, I couldn't find any related programs."

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

        elif st.session_state.retrieval_mode == "Graph Genie Mode (GraphRAG)":

            with st.spinner("Identifying best-matching program..."):

                # Get last rephrased GraphRAG query from session, if it exists
                previous_rephrased = st.session_state.get("last_graph_rephrased", "")

                # Pass previous query as context for coreference-aware rephrasing
                rephrased = api_utils_graphrag.rephrase_query(user_input, previous_rephrased)

                # Save the new rephrased query for next turn
                st.session_state.last_graph_rephrased = rephrased
                st.write("🔁 Re-computed rephrased:", rephrased)

                entities = api_utils_graphrag.extract_entities_and_intent(rephrased)

                matched_program = api_utils_graphrag.find_best_matching_programs(entities)

                matched_programs = api_utils_graphrag.find_best_matching_programs(entities)

                if matched_programs:
                    st.session_state.graph_entities = entities
                    st.session_state.graph_user_query = user_input
                    st.session_state.graph_rephrased_query = rephrased
                    st.session_state.all_rephrased_queries.append(rephrased)

                    st.session_state.graph_program_options = matched_programs

                    if len(matched_programs) == 1:
                        # ✅ Auto-handle single match
                        st.session_state.graph_entities["program"] = matched_programs[0]
                        cypher = api_utils_graphrag.generate_cypher(intent=entities["intent"],
                                                                 entities=st.session_state.graph_entities)
                        result = api_utils_graphrag.run_cypher_query(cypher)
                        context = api_utils_graphrag.format_response(entities["intent"], result)
                        final_answer = api_utils_graphrag.generate_response_from_context(rephrased_query=rephrased,
                                                                                      context=context)
                        st.session_state.messages.append({"role": "assistant", "content": final_answer})

                        # 🔁 Cleanup
                        del st.session_state.graph_program_options
                        del st.session_state.graph_entities
                        del st.session_state.graph_user_query
                        del st.session_state.graph_rephrased_query
                    else:
                        # ✅ Multiple programs matched → prompt for selection
                        assistant_reply = "**Found matching programs:**\n\n" + \
                                          "\n".join([f"{i + 1}. {prog}" for i, prog in enumerate(matched_programs)])
                        st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                else:
                    assistant_reply = "Sorry, I couldn't match your query to any known academic program."
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

    # --- Display chat history ---
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # --- RAG: Program Selection ---
    if "program_options" in st.session_state and st.session_state.program_options:
        if len(st.session_state.program_options) > 1:  # ✅ Only show if multiple programs
            program_list = st.session_state.program_options
            program_dict = {str(i + 1): prog for i, prog in enumerate(program_list)}

            st.markdown("### Please select the most relevant program:")
            for idx, name in program_dict.items():
                st.markdown(f"**{idx}.** {name}")

            selected_index = st.selectbox(
                "Choose a number:",
                options=list(program_dict.keys()),
                index=0,
                format_func=lambda x: f"Option {x}"
            )

            if st.button("Generate Final Response"):
                selected_program = program_dict[selected_index]

                st.write("📌 Program selected:", selected_program)
                # st.write("🔁 Using rephrased query:", st.session_state.get("rephrased_query"))

                # Just in case rephrased is somehow missing
                if "rephrased_query" not in st.session_state:
                    rephrased, _ = api_utils_rag.initial_program_matches(st.session_state.messages[-2]["content"])
                    st.session_state.rephrased_query = rephrased
                    st.write("🔁 Re-computed rephrased:", rephrased)

                with st.spinner("Generating detailed academic response..."):
                    final_answer = api_utils_rag.final_response_from_selection(
                        user_query=st.session_state.messages[-2]["content"],
                        rephrased_query=f"{st.session_state.rephrased_query} specifically in the {selected_program} program.",
                        selected_program=selected_program
                    )

                st.session_state.messages.append({"role": "assistant", "content": final_answer})
                del st.session_state.program_options
                del st.session_state.rephrased_query

    # --- GraphRAG Program Selection (UI) ---
    if (
            "graph_program_options" in st.session_state and
            st.session_state.graph_program_options and
            "graph_entities" in st.session_state and
            "graph_user_query" in st.session_state and
            "graph_rephrased_query" in st.session_state and
            st.session_state.retrieval_mode == "Graph Genie Mode (GraphRAG)"
    ):
        program_list = st.session_state.graph_program_options
        program_dict = {str(i + 1): prog for i, prog in enumerate(program_list)}

        st.markdown("### Please select the most relevant program:")
        for idx, name in program_dict.items():
            st.markdown(f"**{idx}.** {name}")

        selected_index = st.selectbox(
            "Choose a number (GraphRAG):",
            options=list(program_dict.keys()),
            index=0,
            format_func=lambda x: f"Option {x}",
            key="graph_program_selectbox"
        )

        if st.button("Generate GraphRAG Response"):
            selected_program = program_dict[selected_index]
            st.session_state.graph_entities["program"] = selected_program

            with st.spinner("Generating structured academic response..."):
                cypher = api_utils_graphrag.generate_cypher(
                    intent=st.session_state.graph_entities["intent"],
                    entities=st.session_state.graph_entities
                )
                result = api_utils_graphrag.run_cypher_query(cypher)
                context = api_utils_graphrag.format_response(st.session_state.graph_entities["intent"], result)
                final_answer = api_utils_graphrag.generate_response_from_context(
                    rephrased_query=st.session_state.graph_rephrased_query,
                    context=context
                )

            st.session_state.messages.append({"role": "assistant", "content": final_answer})

            # 🔁 Cleanup
            del st.session_state.graph_program_options
            del st.session_state.graph_entities
            del st.session_state.graph_user_query
            del st.session_state.graph_rephrased_query

    if msg["role"] == "assistant":
        with st.expander('🌥️🌥️ Provide feedback on this response',
                         expanded=False):
            thumbs = st.radio(
                "Was this helpful?",
                ["👍", "👎"],
                index=None,
                key=f"thumbs_{len(st.session_state.messages)}",
                horizontal=True,
            )

            if thumbs:
                feedback = st.text_input(
                    "Optional comment:",
                    key=f"feedback_text_{len(st.session_state.messages)}",
                    label_visibility="visible"
                )

                if st.button("Submit Feedback", key=f"submit_{len(st.session_state.messages)}"):
                    st.success("✅ Thanks for your feedback!")
                    # Optional: store feedback


elif menu == "About":
    st.markdown("""
        <style>
        .custom-subheader {
            color: #000000;  /* Black text for visibility */
            background-color: #ffffff;  /* White background */
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Use custom HTML for the "ℹ️ About" subheader
    st.markdown('<h2 class="custom-subheader">ℹ️ About</h2>', unsafe_allow_html=True)
    st.markdown("""
    This chatbot is your dedicated academic advisor designed to support Indiana State University students, parents, and prospective students. It offers valuable insights into:

    - **Academic Programs:**  
      Explore a wide range of academic programs offered at Indiana State University. Learn about the course curriculum for each program, including core and elective courses, and discover how these programs align with your academic and career goals.

    - **Semester-wise Course Details:**  
      Get detailed guidance on which courses to take each semester. Understand the structure of each program, including prerequisites, co-requisites, and recommended study paths to ensure a smooth academic journey.

    - **Project Outcomes and Skill Development:**  
      (Currently Developing this Feature) Stay informed about the future outcomes of your academic projects. The chatbot highlights the tasks you will perform, the skills you will develop, and the knowledge you will gain by the end of each semester. This helps you prepare for real-world challenges and build a competitive edge in your field.

    - **Curriculum Guidance for All:**  
      Whether you are an incoming student, a current student, or a parent, this advisor provides clear, actionable advice on academic planning. From course selection and scheduling to understanding program requirements, it ensures you have all the information needed to make informed decisions.
    """)

elif menu == "Documentation":
    # Custom header style
    st.markdown("""
        <style>
        .custom-header {
            color: #000000;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown('<h2 class="custom-header">🔧 Process & Development</h2>', unsafe_allow_html=True)

    st.markdown("""
    ### 🏗️ How We Built This Chatbot

    This intelligent academic advisor combines **Traditional (RAG)** and **Structured Retrieval (GraphRAG)** to give students 
    precise, contextual answers about courses, majors, semesters, and more.

    ---
    ### Comparison
    | Traditional RAG 🧾 | GraphRAG 🌐 |
    |--------------------|------------|
    | Uses **vector search** (e.g., Pinecone) to retrieve relevant text chunks. | Uses **structured graph queries** (e.g., Cypher in Neo4j) to retrieve connected facts. |
    | Chunks passed to the LLM for response generation. | Retrieved **graph triples**/paths injected into the LLM context. """,
                unsafe_allow_html=True)

    st.image(
        "https://substackcdn.com/image/fetch/w_1456,c_limit,f_webp,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F8b4ee6fd-fcc2-4e02-9f6c-472615c77730_800x830.gif",
        caption="📊 Comparison: Traditional RAG vs. GraphRAG",
        use_column_width=True
    )
    st.markdown("""

    #### ✅ Pros

    | Strength | Traditional RAG 🧾 | GraphRAG 🌐 |
    |---------|-------------------|------------|
    | 🔍 Simple Retrieval | Just vectorize and search | 🧠 Structure-aware: understands program hierarchies |
    | ⚡ Fast to prototype | Works with raw PDFs/docs | 🔗 Logical traversal (e.g., "Year 2 courses for Accounting") |
    | 🌍 General QA | Good for policy handbooks, FAQs | 📚 Handles prerequisites and dependencies |
    |              |                        | 🧼 Cleaner, deduplicated context |
    |              |                        | 🧑‍🎓 Ideal for advising/curriculum queries |

    ---

    #### ❌ Cons

    | Limitation | Traditional RAG 🧾 | GraphRAG 🌐 |
    |------------|-------------------|------------|
    | ❓ No structure awareness | Can't understand program → course hierarchy | 🧱 Initial setup: modeling and ingesting the graph |
    | 💬 Hallucinations | May invent relationships | 🔍 Needs smart Cypher query design |
    | 🔁 Repetition risk | Chunk overlap = duplicate info | 📏 Limited to modeled data |

    ---

    ### 🆚 Summary: Which to Use?

    | Feature | Traditional RAG 🧾 | GraphRAG 🌐 |
    |---------|--------------------|------------|
    | 🚀 Setup speed | ✅ Fast | ❌ Slower |
    | 🧠 Understands structure | ❌ No | ✅ Yes |
    | 🔗 Handles dependencies | ❌ No | ✅ Yes |
    | ❓ Complex curriculum Q&A | ❌ Often wrong | ✅ Accurate, explainable |
    | 📈 Scaling programs | ❌ Messy, redundant | ✅ Clean, linked |

    ---

    ### 🧠 Tools & Technologies Used

    | Component              | Technology                                     |
    |------------------------|------------------------------------------------|
    | UI Framework           | Streamlit                                      |
    | LLMs                   | Ollama 3.2, GPT-4o                              |
    | Embeddings             | OpenAI `text-embedding-3-small`                |
    | Vector Search (RAG)    | Pinecone                                        |
    | Graph Database (GraphRAG) | Neo4j Aura                                   |
    | Query Rewriting        | GPT-4o with Chat History for coreference       |
    | Indexing               | Neo4j Full-Text Search (Programs, Courses, Years) |
    | Intent Routing         | Cypher Templates based on structured schema    |
    | Version Control        | Git, GitHub                                    |

    ---

    ### 🧭 Traditional RAG


    [User Query]
         ↓
    [Rephrasing (grammar, spelling, coref)]
         ↓
    [Embedding (OpenAI)]
         ↓
    [Vector Search in Pinecone]
         ↓
    [Top-K Matches Retrieved]
         ↓
    [LLM generates contextual response]
    ```

    **Legend:**  
    🔵 Semantic-based | 📘 LLM powered | 📦 Vector storage

    ---

    ### 🧭 Structured Retrieval (GraphRAG)

    ```mermaid
    graph TD
        A[User Query + Chat History] --> B[Grammar Fix (GPT-4o)]
        B --> C[Entity & Keyword Extraction]
        C --> D[Fuzzy Match using Neo4j Full-Text Index]
        D --> E[Intent Classification]
        E --> F[Cypher Template Selection]
        F --> G[Cypher Execution in Neo4j]
        G --> H[Structured Results]
        H --> I[LLM generates final response]
    ```

    **Legend:**  
    🟩 Structured data | 🧠 Intent-based routing | 🟨 Graph traversal

    ---

    ### 🧠 Supported Intents + Sample Cypher

    **1. `list_program_courses`**  
    _"Show me all courses for Business Analytics"_  
    ```cypher
    MATCH (p:Program {name: "Business Analytics"})
    MATCH (p)-[:HAS_MAIN]->()-[:HAS_SECTION]->()-[:HAS_COURSE]->(c)
    RETURN DISTINCT c.code, c.name, c.credits
    ```

    **2. `course_details`**  
    _"Tell me about MATH 101 in Computer Science"_  
    ```cypher
    MATCH (p:Program {name: "Computer Science"})
    MATCH (p)-[:HAS_MAIN]->()-[:HAS_SECTION]->()-[:HAS_COURSE]->(c {code: "MATH 101"})
    OPTIONAL MATCH (c)-[:HAS_YEAR]->(y)
    RETURN c.name, c.credits, y.name AS year
    ```

    **3. `semester_plan`**  
    _"What courses do I take in Year 2 of Accounting?"_  
    ```cypher
    MATCH (p:Program {name: "Accounting"})
    MATCH (p)-[:HAS_MAIN]->(:MainGroup {title: "Degree Map"})
    MATCH (:MainGroup)-[:HAS_SECTION]->(:Section)-[:HAS_COURSE]->(c)-[:HAS_YEAR]->(y {name: "Year 2"})
    RETURN c.code, c.name, c.credits
    ```

    **4. `program_overview`**  
    _"Tell me about the Data Science degree"_  
    ```cypher
    MATCH (p:Program {name: "Data Science"})
    MATCH (p)-[:HAS_MAIN]->(m)-[:HAS_SECTION]->(s)
    RETURN m.title AS MainGroup, s.name AS Section, s.content
    ```

    ---

    ### 🚧 Challenges & How We Solved Them

    | Challenge                     | Solution                                                                 |
    |-------------------------------|--------------------------------------------------------------------------|
    | Query ambiguity               | Rephrasing + chat history aware grammar correction                      |
    | Program/course overlap        | Full hierarchy-based matching (Program → MainGroup → Section → Course)  |
    | Course leakage across sections| Clean section scoping + program-specific course linking                 |
    | Entity disambiguation         | Neo4j full-text indexes and fuzzy `~` search                            |
    | Attribute enrichment          | Additional course info updated via matching Excel metadata              |

    ---

    ### ✅ Conclusion

    This system empowers users with the flexibility of **RAG (semantic retrieval)** and the structure of **GraphRAG (explicit schema-based traversal)** — ensuring relevant and reliable academic advising through both natural language and graph intelligence.
    """)

elif menu == "Future Developments":
    st.markdown("""
        <style>
        .custom-future {
            color: #000000;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h2 class="custom-future">🚀 Future Developments</h2>', unsafe_allow_html=True)

    st.markdown("""
    - **Continuous Curriculum Enhancement:**  
      We are continually enhancing our curriculum and academic support tools to reflect the latest industry trends and academic research. Our goal is to empower you with the knowledge and skills required for success in today’s competitive environment.

    - **Project Outcome Awareness:**  
      Stay informed about the future outcomes of your academic projects. The chatbot highlights the tasks you will perform, the skills you will develop, and the knowledge you will gain by the end of each semester. This helps you prepare for real-world challenges and build a competitive edge in your field.

    - **🔁 Chat History in Traditional RAG:**  
      We’re working on adding session-aware chat history for traditional RAG to support pronouns, coreferences, and follow-up questions more effectively.

    - **🧠 FallBack for Out-of-Domain Queries:**  
      Soon, the chatbot will gracefully handle queries outside its scope and guide users toward what it can support — with helpful suggestions or rerouting.
    """)


elif menu == "Contact US":
    st.markdown("""
        <style>
        .custom-title {
            color: #000000;  /* Black text color */
            background-color: #ffffff;  /* White background */
            padding: 10px;
            border-radius: 5px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Display the title using custom HTML
    st.markdown('<h1 class="custom-title">Contact Information</h1>', unsafe_allow_html=True)

    # Header section: image and "Contact Information" text side by side
    header_col1, header_col2 = st.columns([1, 2])
    with header_col1:
        st.image(
            "https://via.placeholder.com/200.png?text=Contact+Image",
            use_container_width=True
        )
    with header_col2:
        st.markdown("""
        <div style="color: #000000; font-size: 18px;">
        Welcome to our contact page. Please find the details below.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
            """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(
            "https://media.licdn.com/dms/image/v2/C4D03AQEmBgSiuEsHKA/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1516812348345?e=1749081600&v=beta&t=2yXasvZQPH9lFgAUT66_lhvrfxUPrdjqY7nK7afZcLs",
            caption="Professor Alister McLeod",
            use_container_width=True
        )
    with col2:
        st.subheader("👤 Professor Alister McLeod")
        st.markdown("""
    **Chair & Professor**  
    Bailey College of Engineering & Technology  
    Electronic & Computer Engineering Technology  
    **Email:** Alister.McLeod@indstate.edu  
    **LinkedIn:** <a href="https://www.linkedin.com/in/alister-mcleod-phd-13959b19/" target="_blank"><i class="fab fa-linkedin fa-2x"></i></a>

    **Credentials:**  
    - **Ph.D.**, Purdue University - West Lafayette, 2009  
      *Major: Industrial Technology*  
    - **M.S.**, Purdue University, 2005  
      *Major: Industrial/Electrical Technology*  
    - **B.S.**, North Carolina Agricultural & Technical State University, 2003  
      *Major: Electronics Engineering Technology*
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Include Font Awesome CDN
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        """, unsafe_allow_html=True)

    col3, col4 = st.columns([1, 3])
    with col3:
        st.image(
            "https://media.licdn.com/dms/image/v2/D5603AQHRjr97w6lI2w/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1724377586197?e=1749081600&v=beta&t=vDSP7D0aWtyA07nnsPTX535aNr4lKeweQ5QkQ9N4bQU",
            caption="Dinesh Karnati",
            use_container_width=True
        )
    with col4:
        st.subheader("👤 Dinesh Karnati")
        st.markdown("""
    **Masters Student, Computer Science**  
    Bailey College of Engineering & Technology  
    Specialization: Data Science  
    Electronic & Computer Engineering Technology  

    **Email:** dkarnati1@indstate.edu  
    **LinkedIn:** <a href="https://www.linkedin.com/in/dineshkarnati/" target="_blank"><i class="fab fa-linkedin fa-2x"></i></a>

    **Credentials:**  
    - **Graph AI/ML Consultant** at Circuitry AI, 2024-  
    - **Senior Machine Learning Engineer** at Ideapoke, 2020-2024  
      *Major: Industrial/Electrical Technology*  
    - **B.S.**, SRM University, India, 2019  
      *Major: Electronics and Communication Engineering*  
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        """, unsafe_allow_html=True)
    col3, col4 = st.columns([1, 3])
    with col3:
        st.image(
            "https://media.licdn.com/dms/image/v2/D4D03AQGT7horVMaUjw/profile-displayphoto-shrink_400_400/profile-displayphoto-shrink_400_400/0/1726670381736?e=1749081600&v=beta&t=ar-fjLn_a6zmfY_b7HsUlp_VM7BLNDxoFpoiFebkp58",
            caption="Dinesh Karnati",
            use_container_width=True
        )
    with col4:
        st.subheader("👤James Robert")
        st.markdown("""
    **Bachelors Student, Computer Science**  
    Bailey College of Engineering & Technology  
    Specialization: Data Science  
    Electronic & Computer Engineering Technology  
    **Email:** jroberts@indstate.edu  
    **LinkedIn:** <a href="https://www.linkedin.com/in/james-t-roberts/" target="_blank"><i class="fab fa-linkedin fa-2x"></i></a>

        """, unsafe_allow_html=True)

elif menu == "💡How to Use":
    st.markdown("""
        <style>
        .custom-help {
            color: #000000;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h2 class="custom-help">💡 How to use this Advisor</h2>', unsafe_allow_html=True)
    st.markdown("""
    This advisor helps you explore Indiana State University academic programs with ease.

    ### 🔍 What You Can Do:
    - Ask questions like:
      - *"Tell me about ECT 165"*
      - *"What are all the Prerequisites for registering to ECT 281"*
      - *"When can i take PHYS 105"*

    ### 🧭 Retrieval Modes:
    - **RAG:** Uses Pinecone + Embeddings (semantic search).
    - **GraphRAG:** Uses Neo4j + structured graph queries (precise program/curriculum search).

    ### 📌 Tips:
    - You'll be prompted to pick a program if your query matches multiple.
    - Use "Reset Chat View" to start fresh.
    - You can upload documents (e.g., degree plans) via the sidebar to personalize guidance.
    - Feedback box is shown after each assistant response — let us know if it was helpful!
    """)

# -----/--- Footer with only image ----------
st.markdown("""
    <div class="footer">
        <div style="display: flex; justify-content: center; align-items: center;">
            <img src="https://indianastate.edu/themes/isu/dist/img/sycamores-logo.png"
                 alt="ISU Logo" width="40" style="border-radius: 5px; margin-right: 10px;" />
            <span style="color: white;">
                Indiana State University | Terre Haute, IN | All rights reserved © 2025
            </span>
            <img src="https://logodix.com/logo/879808.png"
                 alt="ISU Right Logo" width="40" style="border-radius: 5px; margin-right: 10px;" />
        </div>
    </div>
""", unsafe_allow_html=True)