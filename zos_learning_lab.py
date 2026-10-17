"""Interactive, offline-first z/OS learning lab."""

from __future__ import annotations

import base64
import html
import os
from datetime import date
from io import BytesIO
from typing import Any

import joblib
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


IBM_DOCS = "https://www.ibm.com/docs/en/zos/3.2.0"

KNOWLEDGE = [
    {
        "title": "TSO/E, ISPF, and interactive work",
        "topic": "Getting around z/OS",
        "content": (
            "- **TSO/E:** interactive environment for logging on and running commands.\n"
            "- **ISPF:** panel-driven tools often used to edit data sets and submit jobs.\n"
            "- **SDSF:** commonly used to view JES jobs and spool output when authorized.\n"
            "- **3270:** a terminal interaction model; this app imitates its layout only.\n"
            "- Training examples include HELP, LISTCAT, LISTDS, SUBMIT, TIME, ISPF, and SDSF.\n"
            "- `D A` is shown as an authorized operator-console example, not a normal TSO command.\n"
            "- Available commands depend on site configuration and user authorization."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: z/OS TSO/E and ISPF product documentation",
        "example": "TSO LISTCAT LEVEL('USER1')",
    },
    {
        "title": "JCL essentials",
        "topic": "Jobs and data sets",
        "content": (
            "- **JOB:** identifies the batch job to JES.\n"
            "- **EXEC:** identifies a program or procedure step.\n"
            "- **DD:** describes a step's data sets, SYSOUT, or other resources.\n"
            "- Statements conventionally start with `//` in columns 1 and 2.\n"
            "- `DD *` introduces in-stream data, terminated by `/*` on a later record.\n"
            "- `SUBMIT` sends JCL to site JES; this simulator only checks a few structural features."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: z/OS MVS JCL User's Guide and JCL Reference",
        "example": (
            "//TRAIN    JOB (ACCT),'LEARN JCL',CLASS=A,MSGCLASS=X\n"
            "//STEP1    EXEC PGM=IEFBR14\n"
            "//OUTPUT   DD SYSOUT=*"
        ),
    },
    {
        "title": "Address spaces",
        "topic": "z/OS storage and isolation",
        "content": (
            "- An address space is a logical execution context with virtual addressing and associated resources.\n"
            "- It provides private areas for a job or system task; z/OS also maps common areas.\n"
            "- Virtual storage is backed by real storage and paging resources as needed.\n"
            "- An address space is not a fixed block of physical RAM.\n"
            "- The diagram is conceptual; details vary by release, mode, and storage area."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: z/OS MVS Initialization and Tuning Guide",
        "example": "Use DISPLAY A (often abbreviated D A) to request active address-space information on an authorized console.",
    },
    {
        "title": "Dump and restore are different operations",
        "topic": "Problem diagnosis and recovery",
        "content": (
            "- A **diagnostic dump** captures selected storage/control information to investigate a failure.\n"
            "- **IPCS** formats and analyzes supported diagnostic dump data.\n"
            "- A diagnostic dump is not itself a backup or restore operation.\n"
            "- **DFSMSdss DUMP/RESTORE** supports storage backup and recovery workflows.\n"
            "- Distinguish failure diagnosis from backup recovery; test restore procedures safely."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: z/OS MVS Diagnosis (IPCS) and DFSMSdss",
        "example": "Diagnostic path: capture dump -> preserve it -> use IPCS -> correlate symptoms and logs. Backup path: plan -> DFSMSdss DUMP -> validate -> controlled RESTORE test.",
    },
    {
        "title": "SMP/E and SYSMOD lifecycle",
        "topic": "Software maintenance",
        "content": (
            "- SMP/E manages z/OS software maintenance using a CSI and zones.\n"
            "- A SYSMOD is a maintenance package, for example a PTF, APAR, USERMOD, or function.\n"
            "- Common flow: RECEIVE, inspect, APPLY CHECK, resolve requisites/HOLDs, then approved APPLY.\n"
            "- ACCEPT is separate and updates distribution libraries; follow local change control.\n"
            "- A USERMOD requires valid MCS and element data matching the installed product."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: SMP/E for z/OS User's Guide and Commands",
        "example": "SET BDY(GLOBAL). RECEIVE SYSMODS. Then SET BDY(target-zone). APPLY CHECK SELECT(UM00001).",
    },
    {
        "title": "SMP/E sandbox walkthrough",
        "topic": "Receive and test a USERMOD",
        "content": (
            "- Use a disposable CSI, matching installed FMID, target zone, and valid USERMOD MCS/element content.\n"
            "- Replace every placeholder with sandbox values for the exact product level.\n"
            "- RECEIVE reads the package; LIST SYSMOD can inspect received metadata.\n"
            "- APPLY CHECK reports applicability and missing requisites without applying the change.\n"
            "- APPLY and ACCEPT are separate controlled operations; the sample JCL cannot be run unchanged."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: SMP/E for z/OS User's Guide",
        "example": (
            "1. Prepare a valid test USERMOD MCS and its element data.\n"
            "2. RECEIVE into the GLOBAL zone from SMPPTFIN.\n"
            "3. Inspect SMP/E messages and list the SYSMOD.\n"
            "4. APPLY CHECK SELECT(UM00001) in the sandbox target zone.\n"
            "5. Resolve all prerequisites/HOLDs; review output and backout plan.\n"
            "6. APPLY only with approval; test the product. ACCEPT only under change control."
        ),
    },
    {
        "title": "JES job output and SDSF",
        "topic": "Batch operations",
        "content": (
            "- JES manages batch job input and output.\n"
            "- A submitted job may wait, execute, or complete; spool contains system, step, and program messages.\n"
            "- SDSF is a common job/spool interface, subject to installation-specific access and commands.\n"
            "- A return code alone is not a complete diagnosis; review the log and messages."
        ),
        "url": IBM_DOCS,
        "source": "IBM Documentation: z/OS JES and SDSF product documentation",
        "example": "Training sequence: submit JCL -> locate job in SDSF -> inspect JESMSGLG/JESJCL/SYSOUT -> interpret completion code.",
    },
]


QUIZ = [
    {
        "question": "Which statement starts a typical batch job?",
        "options": ["//STEP EXEC", "//JOB JOB", "//DD DATA"],
        "answer": "//JOB JOB",
        "explanation": "A JOB statement identifies the job; EXEC describes a step and DD describes a data definition.",
    },
    {
        "question": "What does an address space primarily provide?",
        "options": [
            "A logical virtual-addressing and execution context",
            "A dedicated physical processor",
            "A guaranteed fixed amount of RAM",
        ],
        "answer": "A logical virtual-addressing and execution context",
        "explanation": "Virtual storage is not a fixed block of physical RAM.",
    },
    {
        "question": "What is the principal purpose of a diagnostic dump?",
        "options": [
            "To investigate a failure using captured diagnostic data",
            "To automatically restore a data set",
            "To accept a PTF into distribution libraries",
        ],
        "answer": "To investigate a failure using captured diagnostic data",
        "explanation": "IPCS can help format and analyze dump data; backup/restore is a separate workflow.",
    },
    {
        "question": "What does APPLY CHECK do in the SMP/E learning workflow?",
        "options": [
            "Checks applicability and reports issues without applying the change",
            "Accepts maintenance into distribution libraries",
            "Creates a valid USERMOD from an empty data set",
        ],
        "answer": "Checks applicability and reports issues without applying the change",
        "explanation": "Review prerequisites, HOLDDATA, and SMP/E output before any APPLY.",
    },
    {
        "question": "Which action is a separate SMP/E operation that updates distribution libraries?",
        "options": ["RECEIVE", "ACCEPT", "LIST"],
        "answer": "ACCEPT",
        "explanation": "ACCEPT is distinct from RECEIVE and APPLY, and requires appropriate controls.",
    },
]


@st.cache_resource(show_spinner=False)
def build_index() -> tuple[TfidfVectorizer, Any]:
    documents = [
        f"{item['topic']} {item['title']} {item['content']} {item['example']}"
        for item in KNOWLEDGE
    ]
    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), sublinear_tf=True
    )
    return vectorizer, vectorizer.fit_transform(documents)


def retrieve(query: str, top_k: int = 4) -> list[dict[str, str]]:
    vectorizer, matrix = build_index()
    scores = cosine_similarity(vectorizer.transform([query]), matrix).ravel()
    matches = scores.argsort()[::-1][:top_k]
    return [KNOWLEDGE[i] for i in matches if scores[i] > 0]


@st.cache_data(show_spinner=False)
def _serialized_index() -> bytes:
    vectorizer, matrix = build_index()
    artifact = BytesIO()
    joblib.dump(
        {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "documents": KNOWLEDGE,
            "format_version": 1,
        },
        artifact,
        compress=3,
    )
    return artifact.getvalue()


def _generate_tutor_answer(question: str, matches: list[dict[str, str]]) -> str:
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    api_key = os.environ["WATSONX_APIKEY"]
    url = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    kwargs: dict[str, str] = {}
    if os.environ.get("WATSONX_PROJECT_ID"):
        kwargs["project_id"] = os.environ["WATSONX_PROJECT_ID"]
    elif os.environ.get("WATSONX_SPACE_ID"):
        kwargs["space_id"] = os.environ["WATSONX_SPACE_ID"]
    else:
        raise ValueError("Set WATSONX_PROJECT_ID or WATSONX_SPACE_ID to use watsonx.ai.")

    context = "\n\n".join(
        f"TOPIC: {item['title']}\nNOTES: {item['content']}\n"
        f"EXAMPLE: {item['example']}\nSOURCE: {item['source']} — {item['url']}"
        for item in matches
    )
    model = ModelInference(
        model_id=os.environ.get("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct"),
        credentials=Credentials(url=url, api_key=api_key),
        **kwargs,
    )
    response = model.chat(
        messages=[
            {
                "role": "system",
                "content": (
                    "Teach z/OS concepts accurately using only the supplied notes. "
                    "Do not invent commands, outputs, or system-specific instructions. "
                    "Say when the notes do not cover something. Mention that the "
                    "terminal is simulated. Include the supplied IBM source URLs."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nRetrieved notes:\n{context}",
            },
        ],
        params={"max_tokens": 900, "temperature": 0},
    )
    return response["choices"][0]["message"]["content"]


def _simulate(command: str, jcl: str) -> str:
    normalized = " ".join(command.strip().upper().split())
    if normalized.startswith("TSO "):
        normalized = normalized[4:].strip()
    if normalized in {"HELP", "?"}:
        return (
            "TRAINING COMMANDS\n"
            "HELP      - show this list\n"
            "TIME      - show simulated status\n"
            "LISTCAT   - show sample catalog entries\n"
            "LISTDS    - show a sample data-set lookup\n"
            "LOGON     - enter a simulated session\n"
            "LOGOFF    - leave the simulated session\n"
            "ISPF      - show a sample primary menu\n"
            "SDSF      - show a sample job status\n"
            "D A       - show sample active address spaces\n"
            "SUBMIT    - structurally check JCL in the editor\n"
            "D A is an operator-console example, not a normal TSO command.\n"
            "No z/OS connection; commands are not sent to a host."
        )
    if normalized == "TIME":
        return "READY\nSIMULATED SYSTEM TIME: training environment"
    if normalized == "LOGON" or normalized.startswith("LOGON "):
        return "IKJ56700I USER LOGGED ON (SIMULATED)\nUSER: STUDENT\nNo credentials were checked."
    if normalized == "LOGOFF":
        return "IKJ56450I USER LOGGED OFF (SIMULATED)\nNo host session was active."
    if normalized == "ISPF":
        return "ISPF PRIMARY OPTION MENU (SIMULATED)\n0  SETTINGS\n1  VIEW\n2  EDIT\n3  UTILITIES\n4  FOREGROUND\n5  BATCH\nX  EXIT\nSelect an option by entering the corresponding number."
    if normalized == "SDSF":
        return (
            "SDSF STATUS (SIMULATED)\n"
            "JOBNAME : TRAIN\nJOBID   : JOB00001\nOWNER   : STUDENT\n"
            "STATUS  : OUTPUT\n\nNo job was submitted."
        )
    if normalized in {"D A", "DISPLAY A", "D ACTIVE"}:
        return (
            "IEE200I DISPLAY ACTIVITY (SIMULATED)\n"
            "JOBNAME : TRAIN\nASID    : 002A\nSTATUS  : ACTIVE\n\n"
            "Example only; authorization and output vary by installation."
        )
    if normalized.startswith("LISTCAT"):
        return (
            "IDCAMS LISTCAT (SIMULATED)\n"
            "ENTRY : USER1.LEARN.JCL\nTYPE  : NONVSAM\n\n"
            "ENTRY : USER1.LEARN.OUTPUT\nTYPE  : NONVSAM\n\n"
            "Sample entries only; no catalog was queried."
        )
    if normalized.startswith("LISTDS"):
        name = command.partition(" ")[2].strip() or "'USER1.LEARN.JCL'"
        return f"LISTDS {name} (SIMULATED)\n-- DATA SET NOT CONNECTED --\nOutput is illustrative; nothing was accessed."
    if normalized == "SUBMIT":
        if not jcl.strip():
            return "IKJ56250I ENTER JCL IN THE JCL EDITOR ABOVE, THEN SUBMIT AGAIN."
        lines = [line for line in jcl.splitlines() if line.strip()]
        has_job = any(line.lstrip().upper().startswith("//") and " JOB " in f" {line.upper()} " for line in lines)
        has_exec = any(line.lstrip().upper().startswith("//") and " EXEC " in f" {line.upper()} " for line in lines)
        if not has_job or not has_exec:
            return "JCL CHECK FAILED (SIMULATED)\nA JOB statement and at least one EXEC statement are required.\nThis is only a basic teaching check; JES performs full validation."
        step_count = sum(
            1
            for line in lines
            if line.lstrip().upper().startswith("//") and " EXEC " in f" {line.upper()} "
        )
        return (
            "JCL STRUCTURE CHECK PASSED (SIMULATED)\n"
            f"Nonblank records: {len(lines)}\n"
            f"EXEC steps: {step_count}\n"
            "No JCL was submitted and no program was run."
        )
    return "IKJ56500I COMMAND NOT IMPLEMENTED IN THIS TRAINING SIMULATOR.\nEnter HELP to see supported examples."


def _append_terminal(command: str, jcl: str) -> None:
    output = _simulate(command, jcl)
    history = st.session_state.setdefault("mvs_history", [])
    history.append((command, output))
    st.session_state["mvs_history"] = history[-8:]


def _terminal_screen() -> str:
    lines = [
        "IBM 3270-STYLE z/OS TRAINING SESSION                              SIMULATED",
        "----------------------------------------------------------------------------",
        "TSO/E READY                                              USER: STUDENT",
        "",
    ]
    for command, output in st.session_state.get("mvs_history", []):
        lines.append(f"COMMAND ===> {command}")
        lines.extend(output.splitlines())
        lines.append("")
    lines.extend(
        [
            "----------------------------------------------------------------------------",
            "COMMAND ===> _",
            "PF1=HELP   PF3=EXIT                 TRAINING ONLY - NOT CONNECTED TO z/OS",
        ]
    )
    return "\n".join(lines)


def _certificate_html(name: str, score: int, logo_bytes: bytes | None, logo_type: str) -> bytes:
    logo = ""
    if logo_bytes and logo_type in {"image/png", "image/jpeg"}:
        encoded = base64.b64encode(logo_bytes).decode("ascii")
        logo = f'<img class="logo" src="data:{logo_type};base64,{encoded}" alt="Uploaded logo">'
    safe_name = html.escape(name.strip())
    today = date.today().isoformat()
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Learning Certificate</title>
<style>
@page {{ size: landscape; margin: 16mm; }}
body {{ margin:0; background:#f4f4f4; color:#161616; font-family:Arial,sans-serif; }}
.certificate {{ box-sizing:border-box; min-height:175mm; border:10px double #0f62fe;
padding:24mm 20mm; text-align:center; background:white; }}
.logo {{ max-width:150px; max-height:70px; object-fit:contain; display:block; margin:0 auto 14px; }}
.eyebrow {{ color:#0f62fe; font-weight:bold; letter-spacing:3px; }}
h1 {{ font-size:40px; margin:16px 0; }} .name {{ font-size:34px; border-bottom:1px solid #777;
display:inline-block; min-width:55%; padding:10px; }} .note {{ margin-top:40px; color:#525252; }}
</style></head><body><main class="certificate">{logo}
<div class="eyebrow">MAINFRAME LEARNING LAB · UNOFFICIAL</div>
<h1>Certificate of Completion</h1>
<p>This certificate is presented to</p><div class="name">{safe_name}</div>
<p>for completing the z/OS fundamentals learning assessment.</p>
<p>Assessment score: <strong>{score}%</strong> · Date: {today}</p>
<p class="note">Independent training exercise. Not issued, endorsed, or accredited by IBM.</p>
</main></body></html>"""
    return document.encode("utf-8")


def _render_terminal() -> None:
    st.markdown("#### 3270-style MVS/TSO training terminal")
    st.caption(
        "A visual and command-parser simulation only. It is not an IBM terminal, "
        "does not connect to a host, and cannot execute JCL or alter a system."
    )
    st.markdown(
        "<style>.mvs-screen{background:#101820;color:#9ef7a5;padding:1rem;"
        "font-family:Consolas,'Courier New',monospace;white-space:pre-wrap;"
        "line-height:1.35;border:2px solid #525252;max-width:850px;overflow-wrap:anywhere}"
        "</style>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="mvs-screen">{html.escape(_terminal_screen())}</div>',
        unsafe_allow_html=True,
    )
    with st.form("mvs_command_form", clear_on_submit=True):
        command = st.text_input(
            "Command ===>",
            max_chars=128,
            placeholder="HELP, LISTCAT LEVEL('USER1'), ISPF, SDSF, D A, or SUBMIT",
        )
        jcl_input = st.text_area(
            "Optional JCL editor (used only by the simulated SUBMIT checker)",
            key="mvs_jcl",
            height=170,
            max_chars=5000,
            placeholder=(
                "//TRAIN    JOB (ACCT),'LEARN JCL',CLASS=A,MSGCLASS=X\n"
                "//STEP1    EXEC PGM=IEFBR14\n"
                "//OUTPUT   DD SYSOUT=*"
            ),
        )
        submitted = st.form_submit_button("Enter")
    if submitted:
        if command.strip():
            _append_terminal(command, jcl_input)
            st.rerun()
        st.warning("Enter a training command.")
    if st.button("Clear simulated screen", key="clear_mvs"):
        st.session_state["mvs_history"] = []
        st.rerun()


def _render_lessons() -> None:
    lesson_names = [item["title"] for item in KNOWLEDGE]
    chosen = st.selectbox("Choose a topic", lesson_names, key="lesson_choice")
    item = next(entry for entry in KNOWLEDGE if entry["title"] == chosen)
    st.markdown(f"#### {item['topic']}")
    st.markdown(item["content"])
    if item["title"] == "Address spaces":
        st.markdown(
            """
            **Conceptual address-space view (not to scale)**

            ```text
            +----------------------------------+
            | System/common mappings           |
            +----------------------------------+
            | Private virtual storage          |
            |  - program code and data          |
            |  - task / region-specific use     |
            +----------------------------------+
            | Other shared/common mappings      |
            +----------------------------------+
            ```

            z/OS maps these areas into a virtual address space; this is not a
            physical-RAM layout. Exact maps and limits depend on architecture,
            addressing mode, configuration, and release.
            """
        )
    if item["title"] == "Dump and restore are different operations":
        st.info(
            "**Two meanings to keep separate:** a diagnostic dump is captured for "
            "failure analysis; a DFSMSdss backup dump is used with a planned "
            "restore/recovery process. Neither guarantees a successful recovery "
            "without tested procedures."
        )
    if item["title"] == "SMP/E sandbox walkthrough":
        st.warning(
            "The following JCL is a teaching template, not a runnable job. Replace "
            "all values for a disposable CSI and a valid, product-matched USERMOD. "
            "Never point it at production zones."
        )
        st.markdown(
            "**Illustrative USERMOD identity header (incomplete by design):**"
        )
        st.code(
            "++USERMOD(UM00001) FMID(HXX7700) .\n"
            "This header is not a complete or installable SYSMOD; the real package "
            "must include valid element MCS statements and the matching element data.",
            language="text",
        )
        st.code(
            """//SMPRCV   JOB (ACCT),'SMPE SANDBOX',CLASS=A,MSGCLASS=X
//SMP      EXEC PGM=GIMSMP,PARM='CSI=YOUR.GLOBAL.CSI'
//SMPCSI   DD DISP=SHR,DSN=YOUR.GLOBAL.CSI
//SMPLOG   DD SYSOUT=*
//SMPOUT   DD SYSOUT=*
//SMPRPT   DD SYSOUT=*
//SMPHOLD  DD SYSOUT=*
//SMPPTFIN DD DISP=SHR,DSN=YOUR.TEST.USERMOD.MCS
//SMPCNTL  DD *
  SET BDY(GLOBAL).
  RECEIVE SYSMODS.
  SET BDY(TARGET).
  APPLY CHECK SELECT(UM00001).
/*""",
            language="text",
        )
        st.markdown(
            """
            **What the example teaches**

            1. The package on `SMPPTFIN` must be a valid MCS package with its actual
               element content; an empty/dummy header is not installable.
            2. `RECEIVE` records the SYSMOD in SMP/E's global zone.
            3. `APPLY CHECK` checks the requested target-zone change without
               applying it; review all SMP/E messages, prerequisites, and HOLDs.
            4. A separately approved `APPLY` installs to the target libraries.
               Test and prepare backout before considering it.
            5. `ACCEPT` is not included: it updates distribution libraries and
               requires explicit local change-control approval.

            The sample uses placeholder values and illustrates sequence only.
            Confirm exact syntax, data sets, zones, and options in your release's
            IBM SMP/E documentation and site procedures.
            """
        )
    st.markdown(f"**Example**\n\n```text\n{item['example']}\n```")
    st.link_button("Open the related IBM documentation ↗", item["url"])
    st.caption(f"Reference: {item['source']}. IBM Docs landing page: {IBM_DOCS}")


def _render_tutor() -> None:
    st.markdown("#### Ask the z/OS tutor")
    st.caption(
        "Retrieval uses TF-IDF word/bigram features and cosine similarity over curated "
        "notes linked to IBM manuals. Optional watsonx.ai Granite generation is grounded "
        "in those retrieved notes; IBM pages are not crawled at runtime."
    )
    query = st.text_input(
        "Ask a question",
        placeholder="What is an address space? How does APPLY CHECK differ from ACCEPT?",
        key="learning_question",
    )
    top_k = st.slider("Retrieved notes", 1, 6, 4, key="learning_top_k")
    if query:
        matches = retrieve(query, top_k)
        if not matches:
            st.info("No relevant notes found. Try a term such as JCL, dump, address space, or SMP/E.")
            return
        if os.environ.get("WATSONX_APIKEY") and (
            os.environ.get("WATSONX_PROJECT_ID") or os.environ.get("WATSONX_SPACE_ID")
        ):
            if st.button("Generate a grounded answer with watsonx.ai Granite", key="tutor_generate"):
                try:
                    with st.spinner("Generating an answer from retrieved notes..."):
                        answer = _generate_tutor_answer(query, matches)
                    st.markdown(answer)
                except (ImportError, KeyError, ValueError) as exc:
                    st.error(f"watsonx.ai answer generation failed: {exc}")
        else:
            st.info(
                "Granite answer generation is optional and is not configured. "
                "Review the retrieved notes and IBM references below."
            )
        st.markdown("##### Retrieved source notes")
        for item in matches:
            with st.expander(f"{item['topic']} — {item['title']}", expanded=True):
                st.markdown(item["content"])
                st.code(item["example"], language="text")
                st.markdown(f"[{item['source']}]({item['url']})")

    st.download_button(
        "Download trained retrieval index (.joblib)",
        _serialized_index(),
        file_name="zos_learning_rag_index.joblib",
        mime="application/octet-stream",
        help="Trusted index artifact for this app's curated notes; do not load untrusted joblib files.",
    )


def _render_assessment() -> None:
    st.markdown("#### Knowledge check and certificate")
    st.caption("Score at least 4 of 5 to unlock the independent, unofficial completion certificate.")
    with st.form("learning_quiz"):
        answers = []
        for index, question in enumerate(QUIZ):
            answers.append(
                st.radio(
                    question["question"],
                    question["options"],
                    key=f"quiz_{index}",
                )
            )
        checked = st.form_submit_button("Check answers")
    if checked:
        score = sum(
            answer == question["answer"]
            for answer, question in zip(answers, QUIZ)
        )
        st.session_state["learning_quiz_score"] = score
        st.session_state["learning_quiz_answers"] = answers
    score = st.session_state.get("learning_quiz_score")
    if score is not None:
        for index, question in enumerate(QUIZ):
            answer = st.session_state["learning_quiz_answers"][index]
            if answer == question["answer"]:
                st.success(f"Q{index + 1}: Correct. {question['explanation']}")
            else:
                st.error(
                    f"Q{index + 1}: Correct answer: {question['answer']}. "
                    f"{question['explanation']}"
                )
        st.metric("Your score", f"{score}/{len(QUIZ)}")
        if score >= 4:
            st.success("Assessment passed. You can generate your certificate below.")
            learner = st.text_input("Name to print on certificate", key="certificate_name")
            logo_file = st.file_uploader(
                "Optional: upload your logo (PNG/JPG, maximum 1.5 MB)",
                type=["png", "jpg", "jpeg"],
                key="certificate_logo",
            )
            logo_data = None
            logo_type = ""
            if logo_file is not None:
                logo_data = logo_file.getvalue()
                logo_type = logo_file.type
                if len(logo_data) > 1_500_000:
                    st.error("Logo is larger than 1.5 MB. Upload a smaller image.")
                    logo_data = None
            if learner.strip():
                st.download_button(
                    "Download certificate (printable HTML)",
                    _certificate_html(
                        learner, round(score * 100 / len(QUIZ)), logo_data, logo_type
                    ),
                    file_name="mainframe_learning_certificate.html",
                    mime="text/html",
                )
            else:
                st.info("Enter a name to enable the certificate download.")
        else:
            st.info("Review the lessons and try again. A score of 4/5 is required.")


def render_learning_lab() -> None:
    """Render the interactive training area."""
    st.markdown(
        """
        <div class="dashboard-hero">
          <div class="eyebrow">z/OS · Learning simulator</div>
          <h1>MVS SYSPROG training lab</h1>
          <p>Practice familiar screens, learn core concepts, and explore safe JCL/SMP/E examples.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.warning(
        "This is an educational simulation, not an IBM product or host connection. "
        "Commands and job output are illustrative; nothing is submitted or changed."
    )
    terminal_tab, lessons_tab, tutor_tab, assessment_tab = st.tabs(
        ["3270 terminal", "Topics and IBM links", "RAG tutor", "Exercise and certificate"]
    )
    with terminal_tab:
        _render_terminal()
    with lessons_tab:
        _render_lessons()
    with tutor_tab:
        _render_tutor()
    with assessment_tab:
        _render_assessment()
