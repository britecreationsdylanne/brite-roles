"""
BriteTalent - Job Description Generator Configuration
Company info, standard benefits, system prompts, and JD templates.
"""

# ──────────────────────────────────────────
# Company Description (pre-loaded, consistent across all JDs)
# Replace with real BriteCo company description
# ──────────────────────────────────────────

COMPANY_DESCRIPTION = (
    "BriteCo specializes in innovative and comprehensive insurance solutions for "
    "jewelry, watches, weddings, and special events, delivering convenient, fast, "
    "and affordable coverage. Backed by an AM Best A+ rated carrier, we ensure "
    "peace of mind by offering up to 125% of appraised value with $0 deductibles, "
    "protecting precious items against loss, theft, damage, and more anywhere in "
    "the world. Our wedding and event insurance safeguards your big day from "
    "unforeseen events, such as cancellations or disruptions, so you can celebrate "
    "confidently. At BriteCo, we prioritize seamless, white-glove customer support "
    "and modern protection for life's most meaningful moments. Based in Evanston, IL, "
    "we bring a unique blend of innovation and dedication to our customers."
)


# ──────────────────────────────────────────
# Standard Benefits
# Replace with real BriteCo benefits
# ──────────────────────────────────────────

STANDARD_BENEFITS = [
    "Competitive salary and performance bonuses",
    "Comprehensive health, dental, and vision insurance",
    "401(k) with company match",
    "Flexible PTO policy",
    "Remote and hybrid work options",
    "Professional development budget",
    "Company-sponsored team events and retreats",
    "Parental leave",
    "Life and disability insurance",
    "Employee wellness programs",
]


# ──────────────────────────────────────────
# Department Options
# ──────────────────────────────────────────

DEPARTMENTS = [
    "Claims",
    "Customer Success",
    "Marketing",
    "Sales",
    "Underwriting",
    "Other",
]


# ──────────────────────────────────────────
# Experience Levels
# ──────────────────────────────────────────

EXPERIENCE_LEVELS = [
    {"value": "entry", "label": "Entry Level (0-2 years)"},
    {"value": "mid", "label": "Mid Level (3-5 years)"},
    {"value": "senior", "label": "Senior (6-10 years)"},
    {"value": "lead", "label": "Lead / Staff (8-12+ years)"},
    {"value": "director", "label": "Director (10+ years)"},
    {"value": "vp", "label": "VP / Executive (12+ years)"},
]


# ──────────────────────────────────────────
# AI System Prompt
# ──────────────────────────────────────────

BRITEROLES_SYSTEM_PROMPT = (
    "You are a professional job description writer for BriteCo, an insurtech company "
    "that provides insurance for jewelry, watches, weddings, and special events.\n\n"
    "ABOUT BRITECO:\n"
    "BriteCo specializes in innovative and comprehensive insurance solutions for "
    "jewelry, watches, weddings, and special events. Backed by an AM Best A+ rated "
    "carrier, we offer up to 125% of appraised value with $0 deductibles. We also "
    "provide wedding and event insurance. Based in Evanston, IL.\n\n"
    "VOICE & TONE:\n"
    "- Professional but warm — not corporate-generic\n"
    "- Reflects a modern, innovative tech company\n"
    "- Inclusive and welcoming language\n"
    "- Enthusiastic about the role without being over-the-top\n"
    "- Specific and concrete — avoid vague buzzwords\n\n"
    "AVOID:\n"
    "- Generic corporate boilerplate that could apply to any company\n"
    "- Overly long lists of requirements (keep it focused)\n"
    "- Gendered language or exclusive terminology\n"
    "- 'Rock star', 'ninja', 'guru' or similar cringe terms\n"
    "- Unrealistic combination of requirements\n"
    "- Words like 'leverage', 'synergy', 'paradigm', 'spearhead'"
)


# ──────────────────────────────────────────
# AI Prompt Templates
# ──────────────────────────────────────────

# ──────────────────────────────────────────
# Google Cloud Storage Configuration
# ──────────────────────────────────────────

GCS_CONFIG = {
    "bucket": "britetalent-data",
    "drafts_prefix": "drafts/",
    "saved_prefix": "saved/",
}


AI_PROMPTS = {
    "generate_jd": (
        "Write a complete job description for the following role at BriteCo.\n\n"
        "ROLE DETAILS:\n"
        "- Title: {title}\n"
        "- Department: {department}\n"
        "- Reports To: {reports_to}\n"
        "- Location: {location}\n"
        "- Experience Level: {experience_level}\n"
        "{remote_line}"
        "\nUSER'S NOTES ABOUT THE ROLE:\n"
        "{notes}\n\n"
        "Generate the following sections in this exact order:\n\n"
        "## Role Description\n"
        "A paragraph describing the role, what they'll do day-to-day, and how it fits "
        "at BriteCo. Mention if it's hybrid/remote. 3-5 sentences.\n\n"
        "## Key Responsibilities\n"
        "6-10 bullet points of key responsibilities. Group under sub-headers if the role "
        "spans multiple areas (e.g., 'B2B Demand Generation', 'D2C Growth Support').\n\n"
        "## Qualifications\n"
        "5-8 bullet points of required qualifications and experience.\n\n"
        "IMPORTANT:\n"
        "- Base the content on the user's notes — expand and polish, don't ignore them\n"
        "- Make responsibilities specific to BriteCo and this role, not generic\n"
        "- Keep requirements realistic for the experience level\n"
        "- Use 'you' and 'we' language where natural\n"
        "- Return in markdown format with ## section headers\n"
        "- Do NOT include Company Description or Compensation — those are added separately\n\n"
        "EXAMPLES OF PAST BRITECO JOB DESCRIPTIONS (match this voice and specificity):\n\n"
        "---\n"
        "Example 1 (Customer Service Representative, hybrid in Evanston, IL):\n\n"
        "Role Description:\n"
        "This is a full-time hybrid role for a Customer Service Representative. Based in "
        "Evanston, IL, the role allows for some flexibility to work from home. As a Customer "
        "Service Representative, you will interact with customers to address inquiries, "
        "resolve concerns, ensure satisfaction, and optimize customer experience. You will be "
        "responsible for handling communication through various channels and providing "
        "meticulous assistance while maintaining a customer-first approach.\n\n"
        "Qualifications:\n"
        "- Proven ability to deliver exceptional Customer Service, ensuring quality Customer "
        "Experience and fostering Customer Satisfaction\n"
        "- Proficiency in Customer Support and working with clients to resolve issues promptly\n"
        "- Strong communication skills and the ability to engage with customers professionally\n"
        "- Problem-solving skills with a focus on achieving solutions collaboratively\n"
        "- Familiarity with customer service tools and technology\n"
        "- Ability to work both independently and collaboratively in a hybrid environment\n"
        "- An empathetic, patient, and proactive attitude when addressing customer needs\n"
        "- College degree required\n\n"
        "---\n"
        "Example 2 (Senior Demand Generation & Growth Marketing, with sub-headers):\n\n"
        "Role Overview:\n"
        "We're hiring a senior Demand Generation & Growth Marketing leader to help scale "
        "pipeline and revenue across multiple B2B channels while also supporting D2C growth "
        "initiatives and new product launches. You'll operate as a cross-functional "
        "\"quarterback\" alongside Sales, Sales Ops, and Marketing, ensuring programs are "
        "planned well, executed reliably, and measured clearly.\n\n"
        "Key Responsibilities:\n"
        "B2B Demand Generation (Primary)\n"
        "- Own and scale pipeline programs across multiple B2B channels\n"
        "- Manage and evolve ABM campaigns and lead-generation initiatives\n"
        "- Partner with Sales leadership to align campaign strategy to pipeline goals\n\n"
        "D2C Growth and New Product Launch Support\n"
        "- Support D2C marketing initiatives by improving conversion performance\n"
        "- Partner with marketing and product teams on new product launches\n\n"
        "Qualifications:\n"
        "- 5-10 years of experience in demand generation or growth marketing\n"
        "- Strong B2B demand generation experience\n"
        "- Proven ability to build funnel infrastructure: lifecycle stages, routing, scoring\n"
        "- Strong project management and cross-functional leadership skills\n"
        "---"
    ),
    "adapt_jd": (
        "You have been given an existing job description from another company or source. "
        "Rewrite it to match BriteCo's voice, tone, and style.\n\n"
        "ORIGINAL JD:\n{original_jd}\n\n"
        "ROLE DETAILS:\n"
        "- Title: {title}\n"
        "- Department: {department}\n"
        "- Reports To: {reports_to}\n"
        "- Location: {location}\n"
        "- Experience Level: {experience_level}\n"
        "{remote_line}"
        "\nADDITIONAL NOTES FROM HIRING MANAGER:\n"
        "{notes}\n\n"
        "INSTRUCTIONS:\n"
        "- Rewrite this JD in BriteCo's voice (professional but warm, specific, modern)\n"
        "- Adapt the responsibilities and qualifications to be BriteCo-specific\n"
        "- Keep the same general scope but make it feel like it was written for BriteCo\n"
        "- If the original has good content, preserve the substance while improving the voice\n"
        "- Use the hiring manager's notes to adjust emphasis or add missing elements\n"
        "- Return in markdown format with ## section headers\n"
        "- Do NOT include Company Description or Compensation — those are added separately\n\n"
        "Generate the following sections in this exact order:\n\n"
        "## Role Description\n"
        "A paragraph describing the role at BriteCo. 3-5 sentences.\n\n"
        "## Key Responsibilities\n"
        "6-10 bullet points. Group under sub-headers if the role spans multiple areas.\n\n"
        "## Qualifications\n"
        "5-8 bullet points of required qualifications and experience.\n"
    ),
    "rewrite_section": (
        "Rewrite the following section of a job description. Adjust the tone to be more {tone}.\n\n"
        "Original:\n{content}\n\n"
        "Requirements:\n"
        "- Maintain the same information and structure\n"
        "- Improve clarity and BriteCo brand voice\n"
        "- Keep the same approximate length\n"
        "- Return ONLY the rewritten text, no extra labels or headers"
    ),
}
