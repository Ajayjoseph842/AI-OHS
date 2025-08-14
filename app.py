import os
import json
import hashlib
import tempfile
from pathlib import Path

import streamlit as st
import pandas as pd
from PIL import Image

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - openai may not be installed during tests
    OpenAI = None

# -----------------------------
# Helper data
# -----------------------------

# Base hazard definitions with keywords, example controls, rationales, risk types, references
BASE_HAZARDS = {
    "Slips/Trips/Falls": {
        "keywords": ["wet", "spill", "cord", "cable", "walkway", "entry", "clutter"],
        "controls": [
            "Keep walkways dry and free of obstacles",
            "Use signage and barriers for wet areas",
            "Maintain housekeeping standards",
        ],
        "rationales": {
            "wet": "Wet entry floors can cause slips.",
            "cord": "Cords across walkways create trip hazards.",
            "walkway": "Obstructions in walkways increase trip risk.",
        },
        "default_rationale": "Uncontrolled surfaces may cause slips or trips.",
        "risk": "Physical",
        "reference": "OHSA s.25(2)(h)",
    },
    "Working at Heights": {
        "keywords": ["scaffold", "ladder", "roof", "midrail", "fall"],
        "controls": [
            "Install guardrails or fall arrest systems",
            "Inspect scaffolds and ladders before use",
            "Provide fall prevention training",
        ],
        "rationales": {
            "scaffold": "Scaffolds missing midrails expose workers to falls.",
            "ladder": "Unsecured ladders can shift and cause falls.",
        },
        "default_rationale": "Elevated work areas without protection increase fall risk.",
        "risk": "Physical",
        "reference": "O. Reg. 213/91 s.26",
    },
    "Silica Dust": {
        "keywords": ["silica", "concrete", "dry cutting", "masonry"],
        "controls": [
            "Use wet cutting or local exhaust ventilation",
            "Provide respiratory protection",
            "Implement exposure monitoring",
        ],
        "rationales": {
            "dry cutting": "Dry cutting concrete creates respirable silica dust.",
            "concrete": "Cutting concrete releases silica particles.",
        },
        "default_rationale": "Activities generate airborne silica dust.",
        "risk": "Chemical",
        "reference": "O. Reg. 833",
    },
    "Fire/Explosion": {
        "keywords": ["propane", "flammable", "gas", "cylinder"],
        "controls": [
            "Store cylinders upright in ventilated areas",
            "Keep ignition sources away from fuels",
            "Inspect hoses and regulators",
        ],
        "rationales": {
            "propane": "Improper propane storage elevates fire risk.",
        },
        "default_rationale": "Flammable materials can ignite or explode.",
        "risk": "Chemical",
        "reference": "O. Reg. 851 s.43",
    },
    "Electrical": {
        "keywords": ["cord", "electrical", "wiring", "power"],
        "controls": [
            "Inspect cords for damage",
            "Keep cables away from walk paths",
            "Use GFCI protection",
        ],
        "rationales": {
            "cord": "Damaged or misplaced cords increase shock hazards.",
        },
        "default_rationale": "Exposed electrical components may cause shock.",
        "risk": "Electrical/Energy",
        "reference": "CSA Z462",
    },
    "PPE Compliance": {
        "keywords": ["ppe", "hard hat", "glove", "goggles", "respirator"],
        "controls": [
            "Ensure appropriate PPE is worn",
            "Provide training on PPE use",
            "Maintain PPE in good condition",
        ],
        "rationales": {
            "scaffold": "Fall protection PPE is needed when working at heights.",
            "concrete": "Concrete cutting requires respiratory protection.",
        },
        "default_rationale": "Appropriate PPE must be used for tasks.",
        "risk": "Administrative",
        "reference": "OHSA s.79",
    },
}

# Industry-specific hazards (one example per industry for brevity)
INDUSTRY_SPECIFIC = {
    "Construction": {
        "Trenching/Excavation": {
            "keywords": ["trench", "excavation", "shoring"],
            "controls": ["Shore or slope trenches", "Keep spoil piles away"],
            "rationales": {"trench": "Unshored trenches may collapse."},
            "default_rationale": "Excavations can cave in without protection.",
            "risk": "Physical",
            "reference": "O. Reg. 213/91 s.224",
        }
    },
    "Healthcare": {
        "Patient Handling": {
            "keywords": ["patient", "lifting", "transfer"],
            "controls": ["Use mechanical lifts", "Train in proper body mechanics"],
            "rationales": {"lifting": "Manual patient lifts strain the back."},
            "default_rationale": "Handling patients can strain workers.",
            "risk": "Ergonomic",
            "reference": "CSA Z1004",
        }
    },
    "Mining": {
        "Rock Falls": {
            "keywords": ["rock", "blast", "tunnel"],
            "controls": ["Install ground support", "Monitor for movement"],
            "rationales": {"rock": "Loose rock overhead may fall."},
            "default_rationale": "Underground work faces fall of ground risks.",
            "risk": "Physical",
            "reference": "Reg. 854 s.46",
        }
    },
    "Oil and Gas": {
        "Hydrocarbon Release": {
            "keywords": ["hydrocarbon", "well", "pipeline", "propane"],
            "controls": ["Monitor for leaks", "Maintain valves"],
            "rationales": {"hydrocarbon": "Uncontrolled hydrocarbons may ignite."},
            "default_rationale": "Releases can cause fires or explosions.",
            "risk": "Chemical",
            "reference": "CSA Z662",
        }
    },
    "Utilities and Energy": {
        "Arc Flash": {
            "keywords": ["arc flash", "switchgear", "substation"],
            "controls": ["De-energize equipment", "Wear arc-rated PPE"],
            "rationales": {"arc flash": "Exposed switchgear can arc."},
            "default_rationale": "Electrical equipment may arc under fault.",
            "risk": "Electrical/Energy",
            "reference": "CSA Z462",
        }
    },
    "Transportation and Logistics": {
        "Vehicle Movement": {
            "keywords": ["vehicle", "truck", "traffic", "forklift"],
            "controls": ["Separate pedestrians", "Use spotters"],
            "rationales": {"forklift": "Forklifts in aisles can strike workers."},
            "default_rationale": "Vehicle traffic poses struck-by risks.",
            "risk": "Physical",
            "reference": "CSA B335",
        }
    },
    "Agriculture and Farming": {
        "Animal Handling": {
            "keywords": ["livestock", "cattle", "animal"],
            "controls": ["Use proper restraints", "Train workers"],
            "rationales": {"livestock": "Uncontrolled livestock may kick."},
            "default_rationale": "Animals can injure handlers.",
            "risk": "Physical",
            "reference": "CSA Z151",
        }
    },
    "Emergency Services": {
        "Scene Safety": {
            "keywords": ["scene", "firefighting", "rescue"],
            "controls": ["Establish zones", "Use incident command"],
            "rationales": {"scene": "Unsecured scenes expose responders to hazards."},
            "default_rationale": "Emergency scenes are dynamic and hazardous.",
            "risk": "Administrative",
            "reference": "NFPA 1500",
        }
    },
    "Environmental Services": {
        "Waste Handling": {
            "keywords": ["waste", "chemical", "biohazard"],
            "controls": ["Segregate waste streams", "Use appropriate containers"],
            "rationales": {"waste": "Improper waste handling releases contaminants."},
            "default_rationale": "Handling waste exposes workers to contaminants.",
            "risk": "Chemical",
            "reference": "O. Reg. 347",
        }
    },
    "Laboratory": {
        "Biohazards": {
            "keywords": ["culture", "lab", "biosafety"],
            "controls": ["Work in biosafety cabinets", "Use sterilization"],
            "rationales": {"culture": "Exposure to cultures may cause infection."},
            "default_rationale": "Laboratory agents can be infectious.",
            "risk": "Biological",
            "reference": "CSA Z316.5",
        }
    },
    "Manufacturing": {
        "Machine Guarding": {
            "keywords": ["machine", "guard", "press"],
            "controls": ["Install fixed guards", "Implement LOTO"],
            "rationales": {"guard": "Missing guards expose moving parts."},
            "default_rationale": "Machines can injure if unguarded.",
            "risk": "Physical",
            "reference": "CSA Z432",
        }
    },
    "Warehousing": {
        "Material Handling": {
            "keywords": ["pallet", "stack", "racking"],
            "controls": ["Secure stacking", "Inspect racking"],
            "rationales": {"pallet": "Poorly stacked pallets may collapse."},
            "default_rationale": "Improper storage can lead to collapse.",
            "risk": "Physical",
            "reference": "O. Reg. 851 s.45",
        }
    },
}

INDUSTRY_OPTIONS = [
    "General industry",
    "Construction",
    "Manufacturing",
    "Healthcare",
    "Warehousing",
    "Laboratory",
    "Mining",
    "Oil and Gas",
    "Utilities and Energy",
    "Transportation and Logistics",
    "Agriculture and Farming",
    "Emergency Services",
    "Environmental Services",
]

# Map hazard to risk type is embedded in definitions

# -----------------------------
# Utility functions
# -----------------------------

def model_supports_vision(model_name: str, base_url: str) -> bool:
    model_name = model_name.lower()
    vision_models = {
        "gpt-4o", "gpt-4o-mini", "openai/gpt-4o", "openai/gpt-4o-mini",
        "openai/gpt-4.1", "claude-3-haiku", "claude-3-sonnet",
        "anthropic/claude-3-haiku", "anthropic/claude-3-sonnet",
    }
    return model_name in vision_models

def reset_session():
    for p in st.session_state.get("image_paths", []):
        try:
            os.remove(p)
        except OSError:
            pass
    st.session_state.clear()
    st.experimental_rerun()


def add_image(uploaded_file):
    data = uploaded_file.read()
    file_hash = hashlib.md5(data).hexdigest()
    uploaded_file.seek(0)
    if file_hash in st.session_state.image_hashes:
        return
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        st.session_state.image_paths.append(tmp.name)
        st.session_state.image_hashes.add(file_hash)


def offline_analyze(text, image_paths, industry, max_hazards, show_refs, multi=False):
    hazards = BASE_HAZARDS.copy()
    if industry and industry in INDUSTRY_SPECIFIC:
        hazards.update(INDUSTRY_SPECIFIC[industry])

    text_lower = text.lower()
    image_tokens = []
    for path in image_paths:
        fname = os.path.basename(path).lower()
        image_tokens.extend(fname.replace('.', ' ').split())

    results = []
    for category, data in hazards.items():
        score = 0
        matched = None
        for kw in data["keywords"]:
            if kw in text_lower:
                score += 1
                matched = kw
            for token in image_tokens:
                if kw in token:
                    score += 1
                    matched = kw
        if score > 0:
            rationale = data["rationales"].get(matched, data.get("default_rationale", "Hazard present."))
            likelihood = "High" if score > 1 else "Medium"
            results.append({
                "Hazard Category": category,
                "Likelihood": likelihood,
                "Rationale": rationale,
                "Suggested Controls": "; ".join(data["controls"][:4]),
                "Industry": industry if multi else None,
                "References": data["reference"] if show_refs else None,
                "Risk Type": data["risk"],
            })

    if results and not any(r["Hazard Category"] == "PPE Compliance" for r in results):
        ppe = BASE_HAZARDS["PPE Compliance"]
        results.append({
            "Hazard Category": "PPE Compliance",
            "Likelihood": "Medium",
            "Rationale": ppe["default_rationale"],
            "Suggested Controls": "; ".join(ppe["controls"][:4]),
            "Industry": industry if multi else None,
            "References": ppe["reference"] if show_refs else None,
            "Risk Type": ppe["risk"],
        })

    if not results:
        results.append({
            "Hazard Category": "General site safety",
            "Likelihood": "Low",
            "Rationale": "Basic safety practices are recommended.",
            "Suggested Controls": "Maintain clean work areas; conduct inspections",
            "Industry": industry if multi else None,
            "References": "OHSA s.25(2)(h)" if show_refs else None,
            "Risk Type": "Administrative",
        })
    return results[:max_hazards]


def run_offline(text, image_paths, industry, max_hazards, show_refs, multi_industry):
    if multi_industry:
        merged = {}
        for ind in INDUSTRY_OPTIONS:
            res = offline_analyze(text, image_paths, ind, max_hazards, show_refs, multi=True)
            for r in res:
                cat = r["Hazard Category"]
                if cat in merged:
                    if r["Industry"] not in merged[cat]["Industry"].split(", "):
                        merged[cat]["Industry"] += f", {r['Industry']}"
                else:
                    merged[cat] = r
        results = list(merged.values())
    else:
        results = offline_analyze(text, image_paths, industry, max_hazards, show_refs)
    df = pd.DataFrame(results)
    if not show_refs and "References" in df.columns:
        df = df.drop(columns=["References"])
    if not multi_industry and "Industry" in df.columns:
        df = df.drop(columns=["Industry"])
    return df


def encode_image(path):
    import base64
    with open(path, "rb") as f:
        b = base64.b64encode(f.read()).decode("utf-8")
    ext = Path(path).suffix.replace('.', '') or 'png'
    return f"data:image/{ext};base64,{b}"


def run_online(text, image_paths, industry, model, base_url, api_key, max_hazards, show_refs, multi_industry):
    if OpenAI is None:
        raise RuntimeError("openai SDK not available")
    client = OpenAI(api_key=api_key, base_url=base_url)

    seed = {k: v["controls"][:3] for k, v in BASE_HAZARDS.items()}
    seed_json = json.dumps(seed)
    if multi_industry:
        industries = ", ".join(INDUSTRY_OPTIONS)
        user_desc = text or "Image-only analysis: infer hazards visible in photos."
        user_prompt = (
            f"Analyze hazards across industries ({industries}). "
            f"Description: {user_desc}. Return JSON array with fields: industry, category, likelihood, rationale, suggested_controls."
            f" Use these seed hazards and controls: {seed_json}"
        )
    else:
        user_desc = text or "Image-only analysis: infer hazards visible in photos."
        user_prompt = (
            f"Industry: {industry}. Description: {user_desc}. "
            f"Use seed hazards: {seed_json}. Return JSON array with objects: category, likelihood, rationale, suggested_controls."
        )

    messages = [
        {"role": "system", "content": "You are an OHS risk analyst. Be precise, concise, actionable."},
    ]

    content = [{"type": "text", "text": user_prompt}]
    if image_paths and model_supports_vision(model, base_url):
        for p in image_paths:
            content.append({"type": "image_url", "image_url": {"url": encode_image(p)}})
    elif image_paths and not text and not model_supports_vision(model, base_url):
        raise RuntimeError("Selected model lacks vision support")

    messages.append({"role": "user", "content": content})

    resp = client.chat.completions.create(model=model, messages=messages)
    output = resp.choices[0].message.content
    try:
        data = json.loads(output)
        if not isinstance(data, list):
            raise ValueError("Not a list")
    except Exception:
        raise RuntimeError("Model did not return JSON")

    results = []
    for item in data[:max_hazards]:
        cat = item.get("category") or item.get("hazard")
        likelihood = item.get("likelihood", "Medium")
        rationale = item.get("rationale", "")
        controls = item.get("suggested_controls", [])
        if isinstance(controls, list):
            controls = "; ".join(controls)
        ind = item.get("industry") if multi_industry else None
        results.append({
            "Hazard Category": cat,
            "Likelihood": likelihood,
            "Rationale": (f"From the image(s): {rationale}" if not text and image_paths else rationale),
            "Suggested Controls": controls,
            "Industry": ind,
            "References": None,
            "Risk Type": BASE_HAZARDS.get(cat, {}).get("risk", "Physical"),
        })
    df = pd.DataFrame(results)
    if not show_refs and "References" in df.columns:
        df = df.drop(columns=["References"])
    if not multi_industry and "Industry" in df.columns:
        df = df.drop(columns=["Industry"])
    return df

# -----------------------------
# App setup
# -----------------------------

if "image_paths" not in st.session_state:
    st.session_state.image_paths = []
if "image_hashes" not in st.session_state:
    st.session_state.image_hashes = set()
if "last_run_online" not in st.session_state:
    st.session_state.last_run_online = False
if "last_run_error" not in st.session_state:
    st.session_state.last_run_error = ""
if "results" not in st.session_state:
    st.session_state.results = None

st.title("SafeSight AI – Hazard Identification")
st.markdown("Identify workplace hazards from task descriptions or images.")

# -----------------------------
# Inputs
# -----------------------------
col_txt, col_img = st.columns(2)
with col_txt:
    description = st.text_area("Work/task description (optional if image uploaded)")
with col_img:
    uploads = st.file_uploader(
        "Images",
        type=["jpg", "jpeg", "png", "webp", "heic", "heif", "tiff"],
        accept_multiple_files=True,
    )
    if uploads:
        for u in uploads:
            add_image(u)

# Show image thumbnails
if st.session_state.image_paths:
    cols = st.columns(len(st.session_state.image_paths))
    for c, p in zip(cols, st.session_state.image_paths):
        img = Image.open(p)
        img.thumbnail((256, 256))
        c.image(img)

# -----------------------------
# Sidebar settings
# -----------------------------
with st.sidebar:
    with st.expander("Settings", expanded=False):
        industry = st.selectbox("Industry", INDUSTRY_OPTIONS)
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        base_url = (
            "https://api.openai.com/v1" if os.environ.get("OPENAI_API_KEY")
            else "https://openrouter.ai/api/v1" if os.environ.get("OPENROUTER_API_KEY")
            else None
        )
        detected_key = api_key is not None
        use_ai = st.checkbox("Use AI (Online)", value=detected_key)
        model = None
        if use_ai and detected_key:
            if base_url == "https://api.openai.com/v1":
                model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"], index=0)
            else:
                model = st.selectbox(
                    "Model",
                    [
                        "openai/gpt-4o-mini",
                        "openai/gpt-4o",
                        "anthropic/claude-3-haiku",
                        "anthropic/claude-3-sonnet",
                        "mistralai/mistral-large",
                        "meta-llama/llama-3-70b-instruct",
                    ],
                    index=0,
                )
        max_hazards = st.slider("Max hazards", 3, 20, 10)
        show_refs = st.checkbox("Show Ontario/CSA references", value=True)
        group_by_risk = st.checkbox("Group by risk type (report style)", value=True)
        multi_industry = st.checkbox("Multi-industry scan", value=False)

# -----------------------------
# Action buttons
# -----------------------------
col_a, col_b, col_c = st.columns([1, 1, 1])
with col_a:
    analyze_btn = st.button("Analyze Hazards", type="primary")
with col_b:
    reset_btn = st.button("Reset Session")
with col_c:
    if st.session_state.last_run_online:
        st.markdown(
            "<span style='background-color:#d4edda;color:#155724;padding:4px 8px;border-radius:8px;'>ONLINE (LLM)</span>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<span style='background-color:#fff3cd;color:#856404;padding:4px 8px;border-radius:8px;'>OFFLINE (Rules)</span>",
            unsafe_allow_html=True,
        )

if reset_btn:
    reset_session()

# -----------------------------
# Analysis
# -----------------------------
if analyze_btn:
    if use_ai and st.session_state.image_paths and not description and not model_supports_vision(model, base_url):
        st.warning("Selected model does not support vision. Provide text or choose a vision-capable model.")
    else:
        with st.spinner("Analyzing..."):
            if use_ai and api_key:
                try:
                    df = run_online(
                        description,
                        st.session_state.image_paths,
                        industry,
                        model,
                        base_url,
                        api_key,
                        max_hazards,
                        show_refs,
                        multi_industry,
                    )
                    st.session_state.last_run_online = True
                    st.session_state.last_run_error = ""
                except Exception as e:
                    st.session_state.last_run_online = False
                    st.session_state.last_run_error = str(e)
                    st.error(f"↩️ Fallback to OFFLINE (rule-based). Reason: {e}")
                    df = run_offline(
                        description,
                        st.session_state.image_paths,
                        industry,
                        max_hazards,
                        show_refs,
                        multi_industry,
                    )
            else:
                st.session_state.last_run_online = False
                st.session_state.last_run_error = ""
                df = run_offline(
                    description,
                    st.session_state.image_paths,
                    industry,
                    max_hazards,
                    show_refs,
                    multi_industry,
                )
        st.session_state.results = df

# -----------------------------
# Output
# -----------------------------
if st.session_state.results is not None:
    df = st.session_state.results
    if st.session_state.last_run_error:
        st.error(st.session_state.last_run_error)
    if group_by_risk and "Risk Type" in df.columns:
        for risk, group in df.groupby("Risk Type"):
            st.subheader(risk)
            st.dataframe(group.drop(columns=["Risk Type"]).reset_index(drop=True))
    else:
        st.dataframe(df.reset_index(drop=True))
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="hazards.csv", mime="text/csv")

